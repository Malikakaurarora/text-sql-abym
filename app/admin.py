import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'library.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ── READ helpers (for dropdowns) ──────────────────────────────

def get_all_books():
    conn = get_connection()
    rows = conn.execute("SELECT book_id, title, available_copies FROM Book ORDER BY title").fetchall()
    conn.close()
    return rows

def get_all_members():
    conn = get_connection()
    rows = conn.execute("SELECT member_id, name FROM Member ORDER BY name").fetchall()
    conn.close()
    return rows

def get_all_publications():
    conn = get_connection()
    rows = conn.execute("SELECT publication_id, title FROM Publication ORDER BY title").fetchall()
    conn.close()
    return rows

def get_currently_borrowed():
    conn = get_connection()
    rows = conn.execute("""
        SELECT ir.issue_id, m.name, b.title, ir.issue_date
        FROM Issue_Record ir
        JOIN Member m ON ir.member_id = m.member_id
        JOIN Book b ON ir.book_id = b.book_id
        WHERE ir.return_date IS NULL
        ORDER BY ir.issue_date
    """).fetchall()
    conn.close()
    return rows

def get_pending_alerts():
    conn = get_connection()
    rows = conn.execute("""
        SELECT sa.alert_id, b.title, s.name, sa.expected_arrival_date, sa.status
        FROM Stock_Alert sa
        JOIN Book b ON sa.book_id = b.book_id
        JOIN Supplier s ON sa.supplier_id = s.supplier_id
        WHERE sa.status != 'Resolved'
        ORDER BY sa.expected_arrival_date
    """).fetchall()
    conn.close()
    return rows

# ── WRITE operations ───────────────────────────────────────────

def return_book(issue_id: int) -> str:
    try:
        conn = get_connection()
        today = date.today().isoformat()
        # Mark as returned
        conn.execute("UPDATE Issue_Record SET return_date = ? WHERE issue_id = ?", (today, issue_id))
        # Get book_id to update copies
        book_id = conn.execute("SELECT book_id FROM Issue_Record WHERE issue_id = ?", (issue_id,)).fetchone()[0]
        conn.execute("UPDATE Book SET available_copies = available_copies + 1 WHERE book_id = ?", (book_id,))
        conn.commit()
        conn.close()
        return "success"
    except Exception as e:
        return f"Error: {str(e)}"

def update_stock(book_id: int, new_copies: int) -> str:
    try:
        conn = get_connection()
        conn.execute("UPDATE Book SET available_copies = ? WHERE book_id = ?", (new_copies, book_id))
        conn.commit()
        conn.close()
        return "success"
    except Exception as e:
        return f"Error: {str(e)}"

def add_book(title: str, author: str, publication_id: int, copies: int, threshold: int) -> str:
    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO Book (publication_id, title, author, available_copies, reorder_threshold)
            VALUES (?, ?, ?, ?, ?)
        """, (publication_id, title, author, copies, threshold))
        conn.commit()
        conn.close()
        return "success"
    except Exception as e:
        return f"Error: {str(e)}"

def add_member(name: str, email: str, phone: str) -> str:
    try:
        conn = get_connection()
        conn.execute("INSERT INTO Member (name, email, phone) VALUES (?, ?, ?)", (name, email, phone))
        conn.commit()
        conn.close()
        return "success"
    except Exception as e:
        return f"Error: {str(e)}"

def resolve_alert(alert_id: int) -> str:
    try:
        conn = get_connection()
        conn.execute("UPDATE Stock_Alert SET status = 'Resolved' WHERE alert_id = ?", (alert_id,))
        conn.commit()
        conn.close()
        return "success"
    except Exception as e:
        return f"Error: {str(e)}"
