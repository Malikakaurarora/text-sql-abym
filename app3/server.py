import os, sys, uuid, time, sqlite3
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_URL = os.environ.get("DATABASE_URL")
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'library2.db')
POSTGRES = bool(DB_URL and DB_URL.startswith("postgresql"))

if POSTGRES:
    import psycopg2, psycopg2.extras

app = FastAPI(title="Library API")


class QueryRequest(BaseModel):
    question: str


def get_db():
    if POSTGRES:
        return psycopg2.connect(DB_URL)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_log(qid, question, sql, exec_time, success, error, response):
    conn = get_db()
    try:
        if POSTGRES:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO querylog (query_id, user_question, generated_sql, sql_execution_time, sql_success, error_message, response_text, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (qid, question, sql, exec_time, success, error, response, datetime.now(timezone.utc).isoformat())
            )
            conn.commit()
            cur.close()
        else:
            conn.execute(
                "INSERT INTO QueryLog (query_id, user_question, generated_sql, sql_execution_time, sql_success, error_message, response_text, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (qid, question, sql, exec_time, 1 if success else 0, error, response, datetime.now(timezone.utc).isoformat())
            )
            conn.commit()
    finally:
        conn.close()


@app.post("/query")
async def query(req: QueryRequest):
    from agent3 import _run

    qid = str(uuid.uuid4())
    t0 = time.perf_counter()

    try:
        result = await _run(req.question)
    except BaseException as e:
        actual = e
        while hasattr(actual, 'exceptions') and actual.exceptions:
            actual = actual.exceptions[0]
        exec_ms = round((time.perf_counter() - t0) * 1000, 2)
        save_log(qid, req.question, None, exec_ms, False, str(actual), None)
        return {"response": f"Error: {str(actual)}", "sql": None, "execution_time": exec_ms, "query_id": qid}

    exec_ms = round((time.perf_counter() - t0) * 1000, 2)
    ok = not result["answer"].startswith("Error:")
    save_log(qid, req.question, result.get("sql"), exec_ms, ok,
             result["answer"] if not ok else None,
             result["answer"] if ok else None)

    return {"response": result["answer"], "sql": result.get("sql"), "execution_time": exec_ms, "query_id": qid}


@app.get("/logs")
def get_logs(limit: int = 50):
    conn = get_db()
    try:
        if POSTGRES:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM querylog ORDER BY created_at DESC LIMIT %s", (limit,))
            rows = [{k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in dict(r).items()} for r in cur.fetchall()]
            cur.close()
        else:
            rows = [dict(r) for r in conn.execute("SELECT * FROM QueryLog ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()]
        return JSONResponse(rows)
    finally:
        conn.close()


@app.get("/health")
def health():
    return {"status": "ok", "db": "postgresql" if POSTGRES else "sqlite"}
