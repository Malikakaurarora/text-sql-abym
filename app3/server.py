import os
import sys
import uuid
import time
import sqlite3
import json
from datetime import datetime

# allow `from agent3 import _run` regardless of working directory
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DATABASE_URL = os.environ.get("DATABASE_URL")
SQLITE_PATH = os.path.join(os.path.dirname(__file__), '..', 'library2.db')

USE_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith("postgresql"))

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras

app = FastAPI(title="Library NL-to-SQL API")


class QueryRequest(BaseModel):
    question: str


def get_db():
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def log_query(query_id, user_question, generated_sql,
              sql_execution_time, sql_success, error_message, response_text):
    conn = get_db()
    try:
        if USE_POSTGRES:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO querylog
                   (query_id, user_question, generated_sql, sql_execution_time,
                    sql_success, error_message, response_text, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (query_id, user_question, generated_sql, sql_execution_time,
                 sql_success, error_message, response_text,
                 datetime.utcnow().isoformat())
            )
            conn.commit()
            cur.close()
        else:
            conn.execute(
                """INSERT INTO QueryLog
                   (query_id, user_question, generated_sql, sql_execution_time,
                    sql_success, error_message, response_text, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (query_id, user_question, generated_sql, sql_execution_time,
                 1 if sql_success else 0, error_message, response_text,
                 datetime.utcnow().isoformat())
            )
            conn.commit()
    finally:
        conn.close()


@app.post("/query")
async def query(req: QueryRequest):
    from agent3 import _run

    query_id = str(uuid.uuid4())
    start = time.perf_counter()

    result = await _run(req.question)

    execution_time_ms = (time.perf_counter() - start) * 1000
    success = not result["answer"].startswith("Error:")

    log_query(
        query_id=query_id,
        user_question=req.question,
        generated_sql=result.get("sql"),
        sql_execution_time=round(execution_time_ms, 2),
        sql_success=success,
        error_message=result["answer"] if not success else None,
        response_text=result["answer"] if success else None,
    )

    return {
        "response": result["answer"],
        "sql": result.get("sql"),
        "execution_time": round(execution_time_ms, 2),
        "query_id": query_id,
    }


def _serialize(row: dict) -> dict:
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in row.items()}


@app.get("/logs")
def get_logs(limit: int = 50):
    conn = get_db()
    try:
        if USE_POSTGRES:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(
                "SELECT * FROM querylog ORDER BY created_at DESC LIMIT %s", (limit,)
            )
            rows = [_serialize(dict(r)) for r in cur.fetchall()]
            cur.close()
        else:
            rows = [
                dict(r) for r in conn.execute(
                    "SELECT * FROM QueryLog ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
            ]
        return JSONResponse(rows)
    finally:
        conn.close()


@app.get("/health")
def health():
    db_type = "postgresql" if USE_POSTGRES else "sqlite"
    return {"status": "ok", "database": db_type}
