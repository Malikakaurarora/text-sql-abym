import os
import re
import pickle
import sqlite3
import threading
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

DB_PATH          = os.path.join(os.path.dirname(__file__), '..', 'library2.db')
EMBEDDINGS_CACHE = os.path.join(os.path.dirname(__file__), 'table_embeddings.pkl')

# Richer descriptions → better semantic matching
TABLE_DESCRIPTIONS = {
    'Department':        'academic departments, faculty department, student department, building, department head name, which department a student or faculty belongs to, group by department, per department count',
    'Category':          'book categories, genres, dewey decimal classification, book types, subject areas',
    'Publisher':         'book publishers, publishing houses, countries, websites, established year',
    'Author':            'book authors, writers, their nationality, biography, who wrote a book',
    'Shelf':             'physical library shelves, shelf codes, floors, sections, storage capacity',
    'Book':              'books collection, isbn, title, available copies, price, edition, language, reorder threshold',
    'BookAuthor':        'which author wrote which book, book-author relationships, co-authors',
    'Journal':           'academic journals, periodicals, issn, impact factor, research publications',
    'Student':           'student names, student members, student borrowers, enrollment year, programs, undergraduate postgraduate phd, student fines, student loans',
    'Faculty':           'faculty names, professor members, faculty borrowers, designations, employees, teaching staff, faculty fines, faculty loans',
    'Loan':              'book borrowing records, issued books, due dates, return dates, who borrowed which book, overdue books, currently borrowed',
    'Reservation':       'book reservations, reserved books, waiting list, reservation status active fulfilled expired',
    'Fine':              'late return fines, penalties, overdue charges, paid unpaid waived fines, book damage charges',
    'Supplier':          'book suppliers, vendors, contact details, ratings, who supplies books',
    'PurchaseOrder':     'purchase orders for buying books, order status pending delivered cancelled, delivery dates, total amount spent',
    'PurchaseOrderItem': 'items in purchase orders, which books were ordered, quantities ordered received',
    'Librarian':         'library staff, librarians, employees, head librarian, catalogue staff, circulation desk, reference desk, shift morning afternoon evening, salary, joining date',
    'LibraryEvent':      'library events, workshops, seminars, book fair, orientation, career guidance, event date, venue, capacity, fee, upcoming completed cancelled events',
    'EventRegistration': 'event registration, who registered for an event, student attendance at events, attended absent registered, payment for events',
    'BookReview':        'book ratings, student reviews of books, faculty reviews, ratings 1 to 5, helpful count, review date, who reviewed which book',
    'DigitalResource':   'digital resources, e-books, online journals, video courses, databases, IEEE, ACM, JSTOR, Coursera, subscription expiry, access type open restricted, cost',
    'DigitalAccess':     'who accessed digital resources, student digital resource usage, access date, duration minutes, device type desktop laptop mobile tablet',
    'BookRequest':       'student book requests, new book requests, requested books not yet in library, request status pending approved rejected ordered, handled by librarian',
}

_llm              = None
_embedding_model  = None
_table_embeddings = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0)
    return _llm

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

def get_table_embeddings():
    global _table_embeddings
    if _table_embeddings is not None:
        return _table_embeddings
    if os.path.exists(EMBEDDINGS_CACHE):
        with open(EMBEDDINGS_CACHE, 'rb') as f:
            _table_embeddings = pickle.load(f)
        return _table_embeddings
    model = get_embedding_model()
    _table_embeddings = {
        table: model.encode(desc)
        for table, desc in TABLE_DESCRIPTIONS.items()
    }
    with open(EMBEDDINGS_CACHE, 'wb') as f:
        pickle.dump(_table_embeddings, f)
    return _table_embeddings

# ── Stage 1: Semantic table selection ──────────────────────────
def get_relevant_tables(question: str, threshold: float = 0.50, min_tables: int = 3, max_tables: int = 7) -> tuple:
    model = get_embedding_model()
    table_embeddings = get_table_embeddings()
    question_vec = model.encode(question).reshape(1, -1)
    scores = {}
    for table, emb in table_embeddings.items():
        scores[table] = float(cosine_similarity(question_vec, emb.reshape(1, -1))[0][0])
    sorted_tables = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # If even the top table is too far below threshold, question is too vague
    if sorted_tables[0][1] < 0.25:
        return [], scores

    # Pick tables above threshold, but always at least min_tables and at most max_tables
    selected = [t for t, s in sorted_tables if s >= threshold]
    if len(selected) < min_tables:
        selected = [t[0] for t in sorted_tables[:min_tables]]
    elif len(selected) > max_tables:
        selected = selected[:max_tables]
    return selected, scores

# ── Stage 2: Schema only for selected tables ────────────────────
def get_schema_for_tables(tables: list) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    schema = f"SQLite Database Schema ({len(tables)} relevant tables):\n"
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = cursor.fetchall()
        col_defs = [f"{c[1]} {c[2]}" for c in cols]
        schema += f"\nCREATE TABLE {table} (\n  " + ",\n  ".join(col_defs) + "\n);\n"
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        for fk in cursor.fetchall():
            schema += f"-- FK: {table}.{fk[3]} -> {fk[2]}.{fk[4]}\n"
    conn.close()
    return schema

RULES = """
Rules:
- This is SQLite — use only SQLite-compatible syntax
- SQLite has NO MONTH(), YEAR(), DAY() — use strftime('%m', col) or integer month columns
- Use ONLY the table names and column names exactly as shown in the schema above
- Only filter by status columns when user explicitly mentions a status
- Status values are CASE-SENSITIVE — use exact capitalisation:
  - BookRequest.status: 'Pending', 'Approved', 'Rejected', 'Ordered'
  - Loan.return_date IS NULL means book is currently borrowed (not yet returned)
  - Fine.status: 'Unpaid', 'Paid', 'Waived'
  - Reservation.status: 'Active', 'Fulfilled', 'Expired'
  - LibraryEvent.status: 'Upcoming', 'Completed', 'Cancelled'
  - EventRegistration.attendance_status: 'Registered', 'Attended', 'Absent'
  - PurchaseOrder.status: 'Pending', 'Delivered', 'Cancelled'
  - DigitalResource.access_type: 'Open', 'Restricted'
- Always use DISTINCT or GROUP BY to avoid duplicate rows in results unless user explicitly asks for all records
- CRITICAL — 3 tables use a type+id polymorphic pattern. NEVER use student_id/faculty_id directly on these tables:
  1. Loan       → borrower_type ('Student'/'Faculty') + borrower_id
  2. Reservation → borrower_type ('Student'/'Faculty') + borrower_id
  3. BookReview  → reviewer_type ('Student'/'Faculty') + reviewer_id
  - ALWAYS add the type filter when joining these tables to Student or Faculty:
    Loan/Reservation → Student : ON borrower_id = Student.student_id AND borrower_type = 'Student'
    Loan/Reservation → Faculty : ON borrower_id = Faculty.faculty_id AND borrower_type = 'Faculty'
    BookReview → Student       : ON reviewer_id = Student.student_id AND reviewer_type = 'Student'
    BookReview → Faculty       : ON reviewer_id = Faculty.faculty_id AND reviewer_type = 'Faculty'
  - LEFT JOIN direction (Student/Faculty as base):
    Student → Loan        : LEFT JOIN Loan ON Loan.borrower_id=Student.student_id AND Loan.borrower_type='Student'
    Student → Reservation : LEFT JOIN Reservation ON Reservation.borrower_id=Student.student_id AND Reservation.borrower_type='Student'
    Student → BookReview  : LEFT JOIN BookReview ON BookReview.reviewer_id=Student.student_id AND BookReview.reviewer_type='Student'
    Faculty → Loan        : LEFT JOIN Loan ON Loan.borrower_id=Faculty.faculty_id AND Loan.borrower_type='Faculty'
    Faculty → Reservation : LEFT JOIN Reservation ON Reservation.borrower_id=Faculty.faculty_id AND Reservation.borrower_type='Faculty'
    Faculty → BookReview  : LEFT JOIN BookReview ON BookReview.reviewer_id=Faculty.faculty_id AND BookReview.reviewer_type='Faculty'
- Key join paths for procurement tables:
  - Supplier → Book: Supplier JOIN PurchaseOrder PO ON PO.supplier_id=S.supplier_id JOIN PurchaseOrderItem POI ON POI.po_id=PO.po_id JOIN Book B ON B.book_id=POI.book_id
  - PurchaseOrderItem has NO supplier_id column — NEVER write POI.supplier_id
  - PurchaseOrderItem columns: poi_id, po_id, book_id, quantity_ordered, unit_price, quantity_received
  - quantity_received is an INTEGER (count of books received), NOT a date — NEVER use it in date()
  - "When books were delivered/received/added" → use PurchaseOrder.expected_delivery (closest available date)
  - To check books are actually delivered: add WHERE PO.status = 'Delivered'
- Key join paths (Fine has NO student_id or faculty_id — ALWAYS go through Loan):
  - Fine → Student: Fine JOIN Loan ON Fine.loan_id=Loan.loan_id JOIN Student ON Loan.borrower_id=Student.student_id AND Loan.borrower_type='Student'
  - Fine → Faculty: Fine JOIN Loan ON Fine.loan_id=Loan.loan_id JOIN Faculty ON Loan.borrower_id=Faculty.faculty_id AND Loan.borrower_type='Faculty'
  - Fine → Department: Fine JOIN Loan ON Fine.loan_id=Loan.loan_id JOIN Student ON Loan.borrower_id=Student.student_id AND Loan.borrower_type='Student' JOIN Department ON Student.department_id=Department.department_id
  - Student → Fine (LEFT JOIN direction): Student LEFT JOIN Loan ON Loan.borrower_id=Student.student_id AND Loan.borrower_type='Student' LEFT JOIN Fine ON Fine.loan_id=Loan.loan_id
  - NEVER write Fine.student_id or Fine.faculty_id — these columns do NOT exist
- CRITICAL JOIN rule: Every alias used in SELECT, WHERE, HAVING, or GROUP BY MUST be defined in FROM or JOIN.
  If you write B.category_id you MUST have JOIN Book B in the query. Never use an alias without joining its table first.
- Column names — use EXACTLY as shown, common mistakes to avoid:
  - Department table: column is 'name' NOT 'department_name'
  - Student table: columns are 'first_name', 'last_name' NOT 'student_name'
  - Category table: column is 'name' NOT 'category_name'
- Category.name exact values (CASE-SENSITIVE): 'Technology', 'Programming', 'Database', 'Science', 'Mathematics', 'Literature', 'Classic Fiction', 'Business', 'Self Help', 'History'
- For book titles and person names in WHERE clauses: use LIKE '%keyword%' instead of = to handle partial matches and typos
  Example: WHERE B.title LIKE '%Clean Code%' instead of WHERE B.title = 'Clean Code'
- COUNTING borrows: "how many times borrowed" / "borrow count" / "borrowed N times" → COUNT all Loan rows, NO return_date filter. Both active and returned loans count.
  NEVER add return_date IS NOT NULL when question is just about borrow frequency/count.
- LATE RETURN vs OVERDUE — these are different, never confuse them:
  - "returned late" / "late returns" / "late return pattern" → return_date IS NOT NULL AND return_date > due_date
  - "currently overdue" / "not yet returned" / "still borrowed" → return_date IS NULL AND due_date < date('now')
  - NEVER use return_date IS NULL for "late return" queries
- "MEMBERS" means BOTH Student AND Faculty — use UNION or handle both with borrower_type:
  - Always check: if question says "members", "borrowers", "people", "who" — include both Student and Faculty
  - Use UNION ALL to combine Student and Faculty results when listing members
- DATE RANGE RULES — very important, follow exactly:
  - "last N months/days/weeks" means FROM past TO now:
      col >= date('now', '-N months') AND col <= date('now')
  - "overdue books" = return_date IS NULL AND due_date < date('now')
  - "overdue books in last N months" = return_date IS NULL AND due_date < date('now') AND due_date >= date('now', '-N months')
  - "month-wise trend of overdue" → GROUP BY strftime('%Y-%m', L.due_date), filter on due_date range, NOT issue_date
  - NEVER write due_date < date('now', '-N months') for "last N months" — that means OLDER than N months ago (wrong direction)
  - "recent", "last year" = date >= date('now', '-1 year')
  - "this month" = strftime('%Y-%m', col) = strftime('%Y-%m', 'now')
"""

_SKIP_ALIAS_WORDS = {
    'on','where','set','left','right','inner','outer','cross','natural',
    'full','join','from','using','group','order','having','limit','union',
    'and','or','not','as','select','distinct','by','with'
}

def validate_columns(sql: str) -> str:
    """Programmatically verify every alias.column in the SQL exists in the actual DB schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    table_columns = {}
    for (tbl,) in cursor.fetchall():
        cursor.execute(f"PRAGMA table_info({tbl})")
        table_columns[tbl.lower()] = {row[1].lower() for row in cursor.fetchall()}
    conn.close()

    # Build alias → table map from FROM/JOIN clauses
    alias_map = {}
    for m in re.finditer(r'\b(?:FROM|JOIN)\s+(\w+)(?:\s+AS\s+(\w+)|\s+(\w+))?', sql, re.IGNORECASE):
        table = m.group(1)
        raw_alias = m.group(2) or m.group(3)
        if raw_alias and raw_alias.lower() in _SKIP_ALIAS_WORDS:
            raw_alias = None
        alias = raw_alias or table
        alias_map[alias.lower()] = table.lower()
        alias_map[table.lower()] = table.lower()

    errors = []
    seen = set()
    for m in re.finditer(r'\b(\w+)\.(\w+)\b', sql):
        alias, col = m.group(1).lower(), m.group(2).lower()
        key = (alias, col)
        if key in seen or alias not in alias_map:
            continue
        seen.add(key)
        tbl = alias_map[alias]
        if tbl in table_columns and col not in table_columns[tbl]:
            available = ', '.join(sorted(table_columns[tbl]))
            errors.append(
                f"'{m.group(1)}.{m.group(2)}' is invalid — "
                f"table '{tbl}' has no column '{col}'. "
                f"Available columns: {available}"
            )
    return " | ".join(errors)

FEW_SHOT_EXAMPLES = """
Correct SQL examples — follow these patterns exactly:

-- Supplier → Book (ALWAYS go Supplier→PurchaseOrder→PurchaseOrderItem→Book, never POI.supplier_id)
SELECT DISTINCT S.name
FROM Supplier S
JOIN PurchaseOrder PO ON PO.supplier_id = S.supplier_id
JOIN PurchaseOrderItem POI ON POI.po_id = PO.po_id
JOIN Loan L ON L.book_id = POI.book_id
WHERE PO.status = 'Delivered' AND L.return_date IS NULL AND L.due_date < date('now');

-- Members = Student + Faculty (always UNION ALL both types)
SELECT 'Student' AS type, S.first_name, S.last_name
FROM Student S
JOIN Loan L ON L.borrower_id = S.student_id AND L.borrower_type = 'Student'
JOIN Fine F ON F.loan_id = L.loan_id WHERE F.status = 'Unpaid'
UNION ALL
SELECT 'Faculty', F2.first_name, F2.last_name
FROM Faculty F2
JOIN Loan L ON L.borrower_id = F2.faculty_id AND L.borrower_type = 'Faculty'
JOIN Fine Fi ON Fi.loan_id = L.loan_id WHERE Fi.status = 'Unpaid';

-- Late return pattern (return_date > due_date, NOT return_date IS NULL)
SELECT S.first_name, S.last_name, COUNT(*) AS late_count
FROM Student S
JOIN Loan L ON L.borrower_id = S.student_id AND L.borrower_type = 'Student'
WHERE L.return_date IS NOT NULL AND L.return_date > L.due_date
AND L.return_date >= date('now', '-1 year')
GROUP BY S.student_id HAVING COUNT(*) > 3;

-- Month-wise trend last N months (filter by due_date range, group by due_date NOT issue_date)
SELECT strftime('%Y-%m', L.due_date) AS month, COUNT(*) AS overdue_count
FROM Loan L
WHERE L.return_date IS NULL AND L.due_date < date('now')
AND L.due_date >= date('now', '-6 months')
GROUP BY month ORDER BY month;

-- Fine → Department (MUST go Fine→Loan→Student→Department, no shortcut)
SELECT D.name, SUM(F.fine_amount) AS total
FROM Department D
JOIN Student S ON S.department_id = D.department_id
JOIN Loan L ON L.borrower_id = S.student_id AND L.borrower_type = 'Student'
JOIN Fine F ON F.loan_id = L.loan_id
GROUP BY D.department_id;
"""

def validate_polymorphic_join(sql: str) -> str:
    """Catch missing type filter for Loan/Reservation (borrower_type) and BookReview (reviewer_type)."""
    s = sql.lower()
    joins_student = bool(re.search(r'\bjoin\s+student\b', s))
    joins_faculty = bool(re.search(r'\bjoin\s+faculty\b', s))

    for tbl in ['loan', 'reservation']:
        if re.search(rf'\bjoin\s+{tbl}\b', s):
            if (joins_student or joins_faculty) and 'borrower_type' not in s:
                who = 'Student' if joins_student else 'Faculty'
                return (f"Missing borrower_type filter: when joining {tbl.capitalize()} to "
                        f"{who}, MUST add AND {tbl[0].upper()}.borrower_type = '{who}'")

    if re.search(r'\bjoin\s+bookreview\b', s):
        if (joins_student or joins_faculty) and 'reviewer_type' not in s:
            who = 'Student' if joins_student else 'Faculty'
            return (f"Missing reviewer_type filter: when joining BookReview to "
                    f"{who}, MUST add AND BR.reviewer_type = '{who}'")
    return ""

def clean_sql(raw: str) -> str:
    raw = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE)
    raw = raw.replace("```", "")
    match = re.search(r"(SELECT\s.+?)(?:;|$)", raw, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip() + ";"
    return raw.strip()

def run_sql(query: str) -> str:
    if not query.strip().upper().startswith("SELECT"):
        return "Error: Only SELECT queries are allowed."
    blocked = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "ATTACH", "DETACH"]
    for word in blocked:
        if re.search(rf'\b{word}\b', query.upper()):
            return f"Error: '{word}' not allowed."
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

def extract_missing_table(error: str, sql: str, current_tables: list):
    """Detect tables referenced in SQL but missing from selected schema."""
    all_tables = list(TABLE_DESCRIPTIONS.keys())

    # Tables referenced in JOINs but not in current schema
    joined = re.findall(r'\bJOIN\s+(\w+)', sql, re.IGNORECASE)
    for table in joined:
        if table in all_tables and table not in current_tables:
            return table

    # Explicit "no such table" error
    tbl_match = re.search(r"no such table: (\w+)", error)
    if tbl_match:
        missing = tbl_match.group(1)
        if missing in all_tables:
            return missing

    return None

def build_retry_hint(error: str, sql: str) -> str:
    hints = []
    col_match = re.search(r"no such column: (\S+)", error)
    if col_match:
        bad_col = col_match.group(1)
        # Check if it's an undefined alias (e.g. B.category_id where B never joined)
        alias_match = re.match(r"(\w+)\.", bad_col)
        if alias_match:
            alias = alias_match.group(1)
            defined = re.search(
                rf'\b(?:FROM|JOIN)\s+\w+\s+(?:AS\s+)?{alias}\b|\b(?:FROM|JOIN)\s+{alias}\b',
                sql, re.IGNORECASE
            )
            if not defined:
                hints.append(
                    f"Alias '{alias}' is used in the query but never defined — "
                    f"you referenced '{bad_col}' but forgot to JOIN that table. "
                    f"Add the missing JOIN before using this alias."
                )
            else:
                hints.append(f"Column '{bad_col}' does not exist — use exact column names from schema.")
        else:
            hints.append(f"Column '{bad_col}' does not exist — use exact column names from schema.")
    tbl_match = re.search(r"no such table: (\S+)", error)
    if tbl_match:
        hints.append(f"Table '{tbl_match.group(1)}' does not exist — use only tables shown in schema.")
    if re.search(r'\bdate_part\b|\bMONTH\s*\(|\bYEAR\s*\(', sql, re.IGNORECASE):
        hints.append("Do not use date_part/MONTH/YEAR — use strftime('%m', col) for SQLite.")
    return ("Fix: " + " | ".join(hints)) if hints else "Try a completely different approach."

def format_result(db_result: str) -> str:
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

def ask_sql(question: str, selected_tables: list, max_tries: int = 3) -> tuple:
    llm = get_llm()
    last_error = ""
    sql = ""
    result = "No results found."
    current_tables = list(selected_tables)

    for _ in range(max_tries):
        schema = get_schema_for_tables(current_tables)
        retry_note = f"\n{build_retry_hint(last_error, sql)}" if last_error else ""
        prompt = f"""You are a SQLite SQL expert.
USE ONLY the exact table names and column names shown in the schema below.
DATABASE ENGINE: SQLite (NOT PostgreSQL, NOT MySQL).

{schema}
{RULES}
{FEW_SHOT_EXAMPLES}
Question: {question}{retry_note}

Return ONLY the SQL query, no explanation, no markdown."""
        raw = llm.invoke([HumanMessage(content=prompt)]).content
        sql = clean_sql(raw)

        # Proactive check 1 — catch invalid columns before hitting DB
        col_error = validate_columns(sql)
        if col_error:
            last_error = f"Column Error: {col_error}"
            continue

        # Proactive check 2 — catch missing borrower_type before hitting DB
        poly_error = validate_polymorphic_join(sql)
        if poly_error:
            last_error = f"Logic Error: {poly_error}"
            continue

        result = run_sql(sql)

        if "Error" not in result and result != "No results found.":
            return sql, result, current_tables

        # Dynamic recovery — if SQL references a table not in schema, add it and retry
        missing = extract_missing_table(result, sql, current_tables)
        if missing and missing not in current_tables:
            current_tables.append(missing)

        last_error = result

    return sql, result, current_tables

def generate_fallback_query(question: str, original_sql: str, schema: str) -> str:
    llm = get_llm()
    prompt = f"""You are a SQLite SQL expert. A query returned no results.

{schema}
{RULES}

Original question: {question}
Original SQL (returned no results): {original_sql}

The original query was too specific or used narrow filters (e.g. a strict date range, a status filter, etc.).
Write a BROADER fallback SQL query that relaxes those filters to return related useful data.
Examples of relaxing:
- "last 6 months" → remove the date filter entirely, show all records
- specific status filter → remove the status filter
- exact name match → use LIKE '%keyword%'
- COUNT with HAVING → lower or remove the HAVING threshold

Return ONLY the fallback SQL query, no explanation, no markdown."""
    raw = llm.invoke([HumanMessage(content=prompt)]).content
    return clean_sql(raw)

def explain_no_results(question: str, sql: str) -> str:
    return (
        "**No records found** matching these criteria.\n\n"
        "This could mean:\n"
        "- The data genuinely doesn't exist in the database\n"
        "- The query conditions may be too specific (e.g. narrow date range or strict filter)\n\n"
        "_If you expected results, try rephrasing with broader conditions._"
    )

def ask(question: str, timeout: int = 180) -> dict:
    result_holder = [None]
    error_holder  = [None]

    def run():
        try:
            selected_tables, scores = get_relevant_tables(question)

            if not selected_tables:
                result_holder[0] = {
                    "answer": None,
                    "sql": "",
                    "selected_tables": [],
                    "scores": scores,
                }
                return

            sql, db_result, final_tables = ask_sql(question, selected_tables)

            if db_result == "No results found.":
                # Try a broader fallback query before giving up
                fallback_schema = get_schema_for_tables(final_tables)
                fallback_sql = generate_fallback_query(question, sql, fallback_schema)
                fallback_result = run_sql(fallback_sql)

                if "Error" not in fallback_result and fallback_result != "No results found.":
                    answer = "> _Exact match not found — showing closest available data:_\n\n"
                    answer += format_result(fallback_result)
                    result_holder[0] = {
                        "answer": answer,
                        "sql": fallback_sql,
                        "selected_tables": final_tables,
                        "scores": scores,
                    }
                    return

                explanation = explain_no_results(question, sql)
                result_holder[0] = {
                    "answer": explanation,
                    "sql": sql,
                    "selected_tables": final_tables,
                    "scores": scores,
                }
                return

            if "Error" in db_result:
                result_holder[0] = {
                    "answer": f"Could not find data.\n\nSQL: `{sql}`\nDB: {db_result}",
                    "sql": sql,
                    "selected_tables": final_tables,
                    "scores": scores,
                }
                return

            result_holder[0] = {
                "answer": format_result(db_result),
                "sql": sql,
                "selected_tables": final_tables,
                "scores": scores,
            }
        except Exception as e:
            error_holder[0] = str(e)

    thread = threading.Thread(target=run)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return {"answer": "Timed out (180s). Check if Ollama is running.", "sql": "", "selected_tables": [], "scores": {}}
    if error_holder[0]:
        return {"answer": f"Error: {error_holder[0]}", "sql": "", "selected_tables": [], "scores": {}}
    return result_holder[0]
