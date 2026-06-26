import os
import json
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DATABASE_URL = os.environ.get("DATABASE_URL")
SQLITE_PATH = os.path.join(os.path.dirname(__file__), '..', 'library2.db')
#the postgree link is at notepad
USE_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith("postgresql"))

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras

mcp = FastMCP("LibraryDB")


def get_conn():
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        import sqlite3
        return sqlite3.connect(SQLITE_PATH)


@mcp.tool()
def list_tables() -> str:
    """List all tables in the university library database. Call this first."""
    conn = get_conn()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        )
        tables = [r[0] for r in cur.fetchall()]
    else:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]
    conn.close()
    return json.dumps({"tables": tables})


@mcp.tool()
def describe_table(table_name: str) -> str:
    """Get exact column names and types for a table. Call before writing any SQL)important mark."""
    conn = get_conn()
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute(
            """SELECT column_name, data_type
               FROM information_schema.columns
               WHERE table_name = %s AND table_schema = 'public'
               ORDER BY ordinal_position""",
            (table_name.lower(),)
        )
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return json.dumps({"error": f"Table '{table_name}' not found"})
        return json.dumps({
            "table": table_name,
            "columns": [{"name": r[0], "type": r[1]} for r in rows]
        })
    else:
        cur.execute(f"PRAGMA table_info({table_name})")
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return json.dumps({"error": f"Table '{table_name}' not found"})
        return json.dumps({
            "table": table_name,
            "columns": [{"name": r[1], "type": r[2]} for r in rows]
        })


@mcp.tool()
def run_query(query: str) -> str:
    """Execute a SELECT query on the library database. Returns up to 50 rows. If error, fix SQL and retry."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(query)
        rows = cur.fetchmany(50)
        cols = [d[0] for d in cur.description] if cur.description else []
        conn.close()
        return json.dumps({"columns": cols, "rows": [list(r) for r in rows], "count": len(rows)})
    except Exception as e:
        conn.close()
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
