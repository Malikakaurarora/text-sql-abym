import os
import sqlite3
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'library.db')

SCHEMA = """
Tables in the SQLite database:
- Supplier (supplier_id, name, contact_person, phone, email, address)
- Publication (publication_id, title, category, publisher_name, language)
- Supplier_Publication (sp_id, supplier_id, publication_id, price_per_unit, lead_time_days)
- Supplier_Visit_Schedule (visit_id, supplier_id, visit_month, visit_date, notes)
- Book (book_id, publication_id, title, author, available_copies, reorder_threshold)
- Stock_Alert (alert_id, book_id, supplier_id, alert_date, expected_arrival_date, status, notified_user)
- Member (member_id, name, email, phone)
- Issue_Record (issue_id, member_id, book_id, issue_date, return_date)
- VIEW: vw_stock_alert_trigger (book_title, available_copies, reorder_threshold, supplier_name, next_visit, lead_time_days, expected_arrival)

Rules:
- Stock_Alert status values are ONLY: 'Pending', 'Notified', 'Resolved' — never 'restocked'
- Currently borrowed books: Issue_Record WHERE return_date IS NULL
- Low stock books: Book WHERE available_copies <= reorder_threshold
- Restock date query: use vw_stock_alert_trigger view
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

def run_sql(query: str) -> str:
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

def ask(question: str) -> str:
    llm = ChatOllama(model="llama3.2", temperature=0)

    sql_prompt = f"""{SCHEMA}

Write a single SQLite SQL query to answer this question: {question}

Return ONLY the SQL query, nothing else. No explanation, no markdown, just the SQL."""

    sql_response = llm.invoke([HumanMessage(content=sql_prompt)])
    sql_query = sql_response.content.strip()

    if sql_query.startswith("```"):
        sql_query = sql_query.split("```")[1]
        if sql_query.startswith("sql"):
            sql_query = sql_query[3:]
    sql_query = sql_query.strip()

    result = run_sql(sql_query)

    if "SQL Error" in result or result == "No results found.":
        return f"Could not find data. Database returned: {result}\n\nGenerated SQL: {sql_query}"

    answer_prompt = f"""You are a library assistant. Answer ONLY based on the database result below.
Do NOT use outside knowledge. Do NOT say the book is unavailable if the result has data.

Question: {question}
Database Result:
{result}

Give a direct, short answer using ONLY the data above.

Answer:"""

    answer = llm.invoke([HumanMessage(content=answer_prompt)])
    return f"{answer.content.strip()}\n\n_(SQL used: `{sql_query}`)_"
