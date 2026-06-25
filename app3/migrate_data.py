"""
One-time script: copies all data from library2.db (SQLite) → PostgreSQL.
Run after migrate_postgres.py has created the tables.

Usage:
    DATABASE_URL=postgresql://... python app3/migrate_data.py
"""

import os
import sys
import sqlite3

try:
    import psycopg2
except ImportError:
    print("psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

SQLITE_PATH = os.path.join(os.path.dirname(__file__), '..', 'library2.db')
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("DATABASE_URL not set.")
    sys.exit(1)

# Tables in order that respects foreign key dependencies
TABLES = [
    "Publisher",
    "Category",
    "Shelf",
    "Department",
    "Author",
    "Supplier",
    "Librarian",
    "Student",
    "Faculty",
    "Book",
    "BookAuthor",
    "Journal",
    "DigitalResource",
    "Loan",
    "Fine",
    "Reservation",
    "BookReview",
    "BookRequest",
    "LibraryEvent",
    "EventRegistration",
    "DigitalAccess",
    "PurchaseOrder",
    "PurchaseOrderItem",
]

sqlite_conn = sqlite3.connect(SQLITE_PATH)
sqlite_conn.row_factory = sqlite3.Row
sqlite_cur = sqlite_conn.cursor()

pg_conn = psycopg2.connect(DATABASE_URL)
pg_conn.autocommit = False
pg_cur = pg_conn.cursor()

total_rows = 0

for table in TABLES:
    sqlite_cur.execute(f'SELECT * FROM "{table}"')
    rows = sqlite_cur.fetchall()

    if not rows:
        print(f"  {table}: 0 rows (skipped)")
        continue

    cols = [d[0] for d in sqlite_cur.description]
    placeholders = ", ".join(["%s"] * len(cols))
    col_names = ", ".join([f'"{c}"' for c in cols])

    # lowercase table name for PostgreSQL (migrate_postgres.py creates lowercase)
    pg_table = table.lower()

    pg_cur.execute(f'DELETE FROM "{pg_table}"')

    values = [tuple(row) for row in rows]
    pg_cur.executemany(
        f'INSERT INTO "{pg_table}" ({col_names}) VALUES ({placeholders})',
        values
    )

    print(f"  {table}: {len(rows)} rows copied")
    total_rows += len(rows)

# Reset all sequences so next INSERT gets correct auto-increment IDs
for table in TABLES:
    pg_table = table.lower()
    # find primary key column
    sqlite_cur.execute(f"PRAGMA table_info({table})")
    pk_col = next((r[1] for r in sqlite_cur.fetchall() if r[5] == 1), None)
    if pk_col:
        pg_cur.execute(f"""
            SELECT setval(
                pg_get_serial_sequence('"{pg_table}"', '{pk_col}'),
                COALESCE((SELECT MAX("{pk_col}") FROM "{pg_table}"), 1)
            )
        """)

pg_conn.commit()
pg_cur.close()
pg_conn.close()
sqlite_cur.close()
sqlite_conn.close()

print(f"\nDone. {total_rows} total rows migrated to PostgreSQL.")
