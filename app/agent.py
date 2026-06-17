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
        _llm = ChatOllama(model="llama3.2", temperature=0)
    return _llm

# Fix 3 — Auto Schema from DB
def get_schema_from_db() -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    schema = "Tables in the SQLite database:\n"
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        schema += f"- {table} ({', '.join(columns)})\n"
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = [row[0] for row in cursor.fetchall()]
    for view in views:
        cursor.execute(f"PRAGMA table_info({view})")
        columns = [row[1] for row in cursor.fetchall()]
        schema += f"- VIEW {view} ({', '.join(columns)})\n"
    conn.close()
    return schema

EXTRA_RULES = """
Rules:
- Stock_Alert status values are ONLY: 'Pending', 'Notified', 'Resolved'
- Currently borrowed books: Issue_Record WHERE return_date IS NULL
- Low stock books: Book WHERE available_copies <= reorder_threshold
- For restock date queries: use vw_stock_alert_trigger view
- Use plain table names, no double quotes

Example queries:
Q: When will Clean Code be restocked?
SQL: SELECT book_title, next_visit, lead_time_days, expected_arrival FROM vw_stock_alert_trigger WHERE book_title = 'Clean Code'

Q: Which books are currently borrowed?
SQL: SELECT Book.title, Member.name FROM Issue_Record JOIN Book ON Issue_Record.book_id = Book.book_id JOIN Member ON Issue_Record.member_id = Member.member_id WHERE Issue_Record.return_date IS NULL

Q: Show all books with low stock
SQL: SELECT title, available_copies, reorder_threshold FROM Book WHERE available_copies <= reorder_threshold

Q: Show all pending stock alerts
SQL: SELECT * FROM Stock_Alert WHERE status = 'Pending'

Q: List all suppliers
SQL: SELECT name, contact_person, phone, email FROM Supplier
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

# Fix 5 — Retry Logic
def ask_sql(question: str, schema: str, max_tries: int = 3) -> tuple:
    llm = get_llm()
    last_error = ""
    for attempt in range(max_tries):
        retry_note = f"\nPrevious attempt failed: {last_error}. Try a different query." if last_error else ""
        sql_prompt = f"""{schema}{EXTRA_RULES}
Write a single SQLite SQL query to answer: {question}{retry_note}
Return ONLY the SQL query, nothing else."""
        raw = llm.invoke([HumanMessage(content=sql_prompt)]).content
        sql = clean_sql(raw)
        result = run_sql(sql)
        if "Error" not in result and result != "No results found.":
            return sql, result
        last_error = result
    return sql, result

# Fix 6 — Timeout
def ask(question: str, timeout: int = 90) -> str:
    schema = get_schema_from_db()
    result_holder = [None]
    error_holder = [None]

    def run():
        try:
            sql, db_result = ask_sql(question, schema)
            if "Error" in db_result or db_result == "No results found.":
                result_holder[0] = f"Could not find data.\n\nGenerated SQL: `{sql}`\nDB Response: {db_result}"
                return
            llm = get_llm()
            answer_prompt = f"""You are a library assistant. Answer ONLY based on the database result below.
Do NOT use outside knowledge.

Question: {question}
Database Result:
{db_result}

Give a direct, short answer using ONLY the data above.
Answer:"""
            answer = llm.invoke([HumanMessage(content=answer_prompt)]).content.strip()
            result_holder[0] = f"{answer}\n\n_(SQL used: `{sql}`)_"
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
