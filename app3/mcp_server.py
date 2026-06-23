import os
import sqlite3
import json
from mcp.server.fastmcp import FastMCP

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'library2.db')
mcp = FastMCP("LibraryDB")


@mcp.tool()
def list_tables() -> str:
    """List all tables in the university library database. Call this first."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    conn.close()
    return json.dumps({"tables": tables})


@mcp.tool()
def describe_table(table_name: str) -> str:
    """Get exact column names and types for a table. Call before writing any SQL."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
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
    """Execute a SQLite SELECT query. Returns up to 50 rows. If error, fix SQL and retry."""
    conn = sqlite3.connect(DB_PATH)
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
