import os
import re
import sqlite3
import threading
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'library.db')

# Fix 1 — LLM Singleton
_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0)
    return _llm

# Fix 3 — Auto Schema from DB
def get_schema_from_db() -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    schema = "SQLite Database Schema with relationships:\n"
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = cursor.fetchall()
        col_defs = [f"{c[1]} {c[2]}" for c in cols]
        schema += f"\nCREATE TABLE {table} (\n  " + ",\n  ".join(col_defs) + "\n);\n"
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = cursor.fetchall()
        for fk in fks:
            schema += f"-- FK: {table}.{fk[3]} -> {fk[2]}.{fk[4]}\n"
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = [row[0] for row in cursor.fetchall()]
    for view in views:
        cursor.execute(f"PRAGMA table_info({view})")
        columns = [row[1] for row in cursor.fetchall()]
        schema += f"\n-- VIEW {view}: columns = ({', '.join(columns)})\n"
    conn.close()
    return schema

EXTRA_RULES = """
Rules:
- This is SQLite — use only SQLite-compatible syntax
- SQLite has NO MONTH(), YEAR(), DAY() functions — use strftime('%m', date_col) for dates, or integer columns directly
- Stock_Alert status values are ONLY: 'Pending', 'Notified', 'Resolved'
- Stock_Alert is ONLY for stock/reorder alerts — NEVER use it for supplier visit month filtering
- Only filter by Stock_Alert.status when the user explicitly mentions a status (e.g. "pending", "resolved", "notified") — do NOT add a status filter if the user did not ask for it
- Currently borrowed books: Issue_Record WHERE return_date IS NULL
- Low stock books: Book WHERE available_copies <= reorder_threshold
- vw_stock_alert_trigger has ONLY these columns: book_title, available_copies, reorder_threshold, supplier_name, next_visit, lead_time_days, expected_arrival — it has NO status column
- Use vw_stock_alert_trigger ONLY for low-stock detection or expected arrival date queries — NOT for status filtering
- For status-based filtering (Pending/Notified/Resolved), query Stock_Alert table directly, NOT the view
- Use plain table names, no double quotes

Key join paths (MUST follow exactly):
- Supplier to Book: Supplier JOIN Supplier_Publication ON supplier_id JOIN Publication ON publication_id JOIN Book ON publication_id
  NOTE: Supplier_Publication has NO book_id column — always go through Publication
- Supplier visit month: JOIN Supplier_Visit_Schedule ON supplier_id WHERE visit_month = N
  NOTE: visit_month stores the month as an integer (January=1, February=2, ..., December=12)
  NOTE: ALWAYS use visit_month integer column for month filtering — do NOT use strftime() on visit_date
"""

# Fix 4 — Robust SQL Cleaning
def clean_sql(raw: str) -> str:
    raw = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE)
    raw = raw.replace("```", "")
    match = re.search(r"(SELECT\s.+?)(?:;|$)", raw, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip() + ";"
    return raw.strip()

# Fix 2 — SQL Whitelist (SELECT only)
def run_sql(query: str) -> str:
    cleaned = query.strip().upper()
    if not cleaned.startswith("SELECT"):
        return "Error: Only SELECT queries are allowed."
    blocked = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "ATTACH", "DETACH"]
    for word in blocked:
        if re.search(rf'\b{word}\b', cleaned):
            return f"Error: '{word}' operation is not allowed."
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        conn.close()
        if not rows:
            return "No results found."
        result = ", ".join(columns) + "\n"
        for row in rows:
            result += ", ".join(str(v) for v in row) + "\n"
        return result.strip()
    except Exception as e:
        return f"SQL Error: {str(e)}"

SQLITE_BANNED = [
    (r'\bdate_part\s*\(', "SQLite has no date_part() — use integer column visit_month directly (e.g. WHERE visit_month = 7)"),
    (r'\bMONTH\s*\(', "SQLite has no MONTH() — use visit_month column directly (e.g. WHERE visit_month = 7)"),
    (r'\bYEAR\s*\(', "SQLite has no YEAR() — use strftime('%Y', column) instead"),
    (r'\bDAY\s*\(', "SQLite has no DAY() — use strftime('%d', column) instead"),
    (r'\bIFNULL\s*\(.*\bNULL\b', ""),
]

def validate_sqlite_syntax(sql: str) -> str:
    """Returns an error string if the SQL uses non-SQLite syntax, else empty string."""
    for pattern, msg in SQLITE_BANNED:
        if re.search(pattern, sql, re.IGNORECASE) and msg:
            return f"SQLite syntax error: {msg}"
    return ""

def build_retry_hint(error: str, sql: str) -> str:
    hints = []
    col_match = re.search(r"no such column: (\S+)", error)
    if col_match:
        bad_col = col_match.group(1).lower()
        hints.append(f"Column '{col_match.group(1)}' does not exist.")
        if "status" in bad_col and "vw_stock_alert_trigger" in sql.lower():
            hints.append(
                "vw_stock_alert_trigger has NO status column. "
                "For status-based filtering, query the Stock_Alert table directly — not the view."
            )
        if "book_id" in bad_col and ("sp." in bad_col or "supplier_publication" in sql.lower()):
            hints.append(
                "Supplier_Publication has NO book_id. "
                "To get books: JOIN Supplier_Publication ON supplier_id, "
                "then JOIN Publication ON publication_id, "
                "then JOIN Book ON publication_id."
            )
        if "visit_date" in bad_col or "alert_date" in bad_col:
            hints.append(
                "For month filtering use Supplier_Visit_Schedule.visit_month (integer 1-12) — "
                "e.g. WHERE visit_month = 8 for August. Do NOT use visit_date or alert_date."
            )
    tbl_match = re.search(r"no such table: (\S+)", error)
    if tbl_match:
        hints.append(f"Table '{tbl_match.group(1)}' does not exist — check table names in schema.")
    if re.search(r'\bdate_part\b|\bMONTH\s*\(|\bYEAR\s*\(|\bDAY\s*\(', sql, re.IGNORECASE):
        hints.append("Do not use date_part/MONTH/YEAR/DAY — SQLite only. Use: WHERE visit_month = N")
    if re.search(r'\bStock_Alert\b', sql) and re.search(r'strftime|visit_month|month', sql, re.IGNORECASE):
        hints.append(
            "Do NOT join Stock_Alert for month queries. "
            "Use Supplier_Visit_Schedule WHERE visit_month = N instead."
        )
    return ("Fix these issues: " + " | ".join(hints)) if hints else "Try a completely different approach."

# Fix 5 — Retry Logic
def ask_sql(question: str, schema: str, max_tries: int = 3) -> tuple:
    llm = get_llm()
    last_error = ""
    sql = ""
    for _ in range(max_tries):
        retry_note = f"\n{build_retry_hint(last_error, sql)}" if last_error else ""
        sql_prompt = f"""You are a SQLite SQL expert. The database schema is below.
USE ONLY the exact table names and column names shown in the schema — do NOT invent or guess names.
DATABASE ENGINE: SQLite (NOT PostgreSQL, NOT MySQL).

{schema}
{EXTRA_RULES}
Question: {question}{retry_note}

Return ONLY the SQL query, no explanation, no markdown."""
        raw = llm.invoke([HumanMessage(content=sql_prompt)]).content
        sql = clean_sql(raw)
        syntax_err = validate_sqlite_syntax(sql)
        if syntax_err:
            last_error = syntax_err
            continue
        result = run_sql(sql)
        if "Error" not in result and result != "No results found.":
            return sql, result
        last_error = result
    return sql, result

def format_db_result(db_result: str) -> str:
    lines = db_result.strip().split("\n")
    if len(lines) < 2:
        return db_result
    header = [h.strip() for h in lines[0].split(",")]
    rows = [[c.strip() for c in line.split(",")] for line in lines[1:] if line.strip()]
    if len(header) == 1:
        return "\n".join(f"- {row[0]}" for row in rows if row)
    table = "| " + " | ".join(header) + " |\n"
    table += "|" + " --- |" * len(header) + "\n"
    for row in rows:
        padded = row + [""] * (len(header) - len(row))
        table += "| " + " | ".join(padded[:len(header)]) + " |\n"
    return table

# Fix 6 — Timeout
def ask(question: str, timeout: int = 180) -> str:
    schema = get_schema_from_db()
    result_holder = [None]
    error_holder = [None]

    def run():
        try:
            sql, db_result = ask_sql(question, schema)
            if "Error" in db_result or db_result == "No results found.":
                result_holder[0] = f"Could not find data.\n\nGenerated SQL: `{sql}`\nDB Response: {db_result}"
                return
            formatted = format_db_result(db_result)
            result_holder[0] = f"{formatted}\n\n_(SQL used: `{sql}`)_"
        except Exception as e:
            error_holder[0] = str(e)

    thread = threading.Thread(target=run)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return "Request timed out (90s). Please try again or check if Ollama is running."
    if error_holder[0]:
        return f"Error: {error_holder[0]}"
    return result_holder[0]
