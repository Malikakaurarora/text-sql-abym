"""
MCP Server (Python 3.8 compatible version — no mcp package needed).
Exposes library DB as 3 standardized tools.

In real MCP: this runs as a separate process over stdio.
Here: same architecture, same tool interface, same separation of concerns.
Any client that calls list_available_tools() + call_tool() works identically.
"""
import os
import sqlite3
import json

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'library2.db')

# ── Tool definitions (what MCP calls "tool schema") ──────────────────────────

TOOL_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "List all tables in the university library database. Call this first.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "describe_table",
            "description": (
                "Get exact column names and data types for a table. "
                "Always call this before writing SQL — never guess column names."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {"type": "string", "description": "Name of the table to inspect"}
                },
                "required": ["table_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_query",
            "description": (
                "Execute a SQLite SELECT query. Returns up to 50 rows. "
                "If you get an error, call describe_table again and fix the SQL."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Valid SQLite SELECT statement"}
                },
                "required": ["query"],
            },
        },
    },
]


# ── Tool implementations ──────────────────────────────────────────────────────

def _list_tables() -> str:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    conn.close()
    return json.dumps({"tables": tables, "count": len(tables)})


def _describe_table(table_name: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        return json.dumps({"error": f"Table '{table_name}' does not exist"})
    return json.dumps({
        "table": table_name,
        "columns": [
            {"name": r[1], "type": r[2], "not_null": bool(r[3]), "primary_key": bool(r[5])}
            for r in rows
        ],
    })


def _run_query(query: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(query)
        rows = cur.fetchmany(50)
        cols = [d[0] for d in cur.description] if cur.description else []
        conn.close()
        return json.dumps({"columns": cols, "rows": [list(r) for r in rows], "row_count": len(rows)})
    except Exception as e:
        conn.close()
        return json.dumps({"error": str(e)})


# ── MCP interface (what the client calls) ────────────────────────────────────

def list_available_tools() -> list:
    """MCP: list_tools — client discovers what this server can do."""
    return TOOL_SCHEMA


def call_tool(name: str, args: dict) -> str:
    """MCP: call_tool — client executes a tool by name with arguments."""
    if name == "list_tables":
        return _list_tables()
    elif name == "describe_table":
        return _describe_table(args.get("table_name", ""))
    elif name == "run_query":
        return _run_query(args.get("query", ""))
    else:
        return json.dumps({"error": f"Unknown tool: {name}"})
