# Library Management System — NL to SQL Chatbot

A  library management system with a Natural Language to SQL chatbot — built in 3 versions, each improving on the last.

Built entirely with free tools — no paid APIs needed (except app3 which uses a free tier).

---

## Project Structure

```
text-sql/
├── app/                        ← Version 1: Basic NL-to-SQL (8 tables, Ollama)
├── app2/                       ← Version 2: Vector search + smarter SQL (23 tables, Ollama)
├── app3/                       ← Version 3: MCP + FastAPI server + PostgreSQL
│   ├── mcp_server.py           ← MCP server exposing DB as tools (works with SQLite + PostgreSQL)
│   ├── agent3.py               ← MCP client using OpenRouter free API
│   ├── server.py               ← FastAPI server: /query, /logs, /health
│   ├── streamlit_app3.py       ← Streamlit client (talks to server over HTTP)
│   ├── migrate_postgres.py     ← Creates all 24 tables in PostgreSQL
│   └── migrate_data.py         ← Copies data from SQLite → PostgreSQL
├── logs.json                   ← Single source of truth: all 24 table schemas
├── .env.example                ← Environment variable template
├── docker-compose.yml          ← PostgreSQL + Server + Streamlit
├── Dockerfile.server           ← FastAPI server container
├── Dockerfile.streamlit        ← Streamlit client container
├── library_schema.sql
├── sample_data.sql
└── requirements.txt
```

---

## Version 1 — app/
**Basic NL-to-SQL + Admin Panel**

The first version. Simple 8-table library database with a chatbot and a separate admin panel for librarians.

**What it does:**
- Ask questions like "which books are overdue" or "show low stock books"
- LLM converts your question to SQL and runs it on the database
- Admin panel for returning books, updating stock, adding members — no SQL needed

**Tech:**
- SQLite (8 tables)
- Ollama + qwen2.5-coder:7b (free, runs locally)
- Streamlit UI

**Run:**
```bash
python app/create_db.py
ollama serve  # in a separate terminal
streamlit run app/streamlit_app.py
```

---

## Version 2 — app2/
**Two-Stage Vector Search + SQL Generation (23 tables)**

Upgraded to a much bigger university library database with 23 tables. The problem with version 1 was that sending all 23 tables to the LLM at once was too much — the model would get confused. So I added a vector search stage that picks only the relevant tables before generating SQL.

**How it works:**
```
User question
     ↓
Stage 1: Sentence embeddings → cosine similarity → pick relevant tables
     ↓
Stage 2: Only those tables' schema sent to LLM → SQL generated
     ↓
SQLite result returned
```

**What got better:**
- Handles complex multi-table queries (loans + fines + departments + suppliers etc.)
- Schema validation catches wrong column names before hitting the DB
- Self-correcting retry loop with error hints
- Few-shot examples in the prompt for better SQL accuracy

**The honest problem:** qwen2.5-coder:7b is a 7B model and it's not perfect. Had to keep adding rules for edge cases — overdue vs late return logic, polymorphic joins, date direction errors etc. It works but it's high maintenance.

**Tech:**
- SQLite (23 tables — Student, Faculty, Book, Loan, Fine, Supplier, Event, Review, DigitalResource and more)
- Sentence Transformers (all-MiniLM-L6-v2) for table selection
- Ollama + qwen2.5-coder:7b
- Streamlit UI

**Run:**
```bash
# Make sure Ollama is running
python app2/create_db2.py
streamlit run app2/streamlit_app2.py
```

---

## Version 3 — app3/
**MCP + FastAPI Server + PostgreSQL (Production-ready)**

Rebuilt with proper architecture: MCP for SQL accuracy, client-server separation, PostgreSQL on Supabase, and a query log for every request.

### Architecture

```
Streamlit Client
      ↓  HTTP POST /query
FastAPI Server (server.py)
      ↓  MCP stdio protocol
MCP Server (mcp_server.py)
      ↓
PostgreSQL on Supabase  ←→  QueryLog (logs every request)
```

### What is MCP?

MCP (Model Context Protocol) is an open standard by Anthropic. Instead of the LLM blindly generating SQL from a hardcoded schema, it gets tools it can call:

| Tool | What it does |
|---|---|
| `list_tables` | Shows all tables in the database |
| `describe_table` | Returns exact column names + types |
| `run_query` | Executes SQL, returns results |

The LLM decides when to call which tool, checks the actual schema, then writes correct SQL. No hardcoded rules needed.

### What's new in this version

**1. logs.json — Single source of truth**
All 24 table schemas (columns, types, foreign keys) live in one file. To add or remove a table in future, only change `logs.json`.

**2. QueryLog table**
Every question asked through the chatbot is logged:
- `user_question` — what the user asked
- `generated_sql` — the SQL that was run
- `sql_execution_time` — how long it took (ms)
- `sql_success` — did it work or fail
- `error_message` — if it failed, why
- `response_text` — the answer shown to the user

**3. Client-Server separation**
- `server.py` runs as an independent FastAPI server
- `streamlit_app3.py` is a pure HTTP client — no direct DB access
- They can run on different machines

**4. PostgreSQL on Supabase**
- All 24 tables created on Supabase (free cloud PostgreSQL)
- Data migrated from SQLite → PostgreSQL
- Auto-detects: if `DATABASE_URL` is set → PostgreSQL, otherwise → local SQLite

### Setup

**1. Install dependencies (Python 3.11 required):**
```bash
pip install mcp openai fastapi "uvicorn[standard]" psycopg2-binary python-dotenv requests streamlit
```

**2. Create `.env` file:**
```bash
cp .env.example .env
# then edit .env and add your keys
```

Required keys in `.env`:
```
OPENROUTER_API_KEY=sk-or-...     # free at openrouter.ai
DATABASE_URL=postgresql://...    # Supabase or any PostgreSQL server
```

**3. Set up PostgreSQL (one time only):**
```bash
# Creates all 24 tables in your PostgreSQL database
python app3/migrate_postgres.py

# Copies existing data from SQLite → PostgreSQL
python app3/migrate_data.py
```

**4. Run:**
```bash
# Terminal 1 — start the API server
uvicorn app3.server:app --port 8000

# Terminal 2 — start the Streamlit client
streamlit run app3/streamlit_app3.py
```

**5. Available endpoints:**
```
GET  /health   → {"status": "ok", "database": "postgresql"}
POST /query    → {"question": "..."} → {response, sql, execution_time, query_id}
GET  /logs     → list of all logged queries
```

### Docker (run everything together)

```bash
# Copy and fill in .env first
cp .env.example .env

docker-compose up --build
# PostgreSQL on :5432, server on :8000, Streamlit on :8501
```

### Sample queries

- Which students have overdue books and unpaid fines?
- Which department has the highest total unpaid fines?
- Show suppliers whose books get borrowed the most
- Which books are reserved by one person but borrowed by someone else?
- Show month-wise trend of late returns for the last 6 months
- Which students registered for events but also have overdue books?
- Which department's students have borrowed the most digital resources?

---

## How Each Version Compares

| | app/ | app2/ | app3/ |
|---|---|---|---|
| Tables | 8 | 23 | 24 (+ QueryLog) |
| Table selection | All sent to LLM | Vector similarity | LLM discovers via MCP |
| SQL accuracy | Basic | Medium (needs rules) | High (schema-aware) |
| Self-correction | Basic retry | Hints + validate_columns | Tool feedback loop |
| Rules to maintain | Few | Many (20+) | None |
| Database | SQLite (local) | SQLite (local) | PostgreSQL (Supabase) |
| Architecture | Single script | Single script | Client-Server (FastAPI + Streamlit) |
| Query logging | No | No | Yes (QueryLog table) |
| Cost | Free | Free | Free (OpenRouter + Supabase free tier) |
| Speed | Slow (local) | Slow (local) | Fast (cloud) |

---

## Database Schema (app3)

24 tables covering the full university library system:

**Books & Catalog:** Book, Author, BookAuthor, Category, Publisher, Shelf, Journal

**Members:** Student, Faculty, Department

**Circulation:** Loan, Reservation, Fine

**Procurement:** Supplier, PurchaseOrder, PurchaseOrderItem

**Engagement:** LibraryEvent, EventRegistration, BookReview, BookRequest

**Digital:** DigitalResource, DigitalAccess

**Logging:** QueryLog ← tracks every chatbot query

Full schema with column types and relationships: see `logs.json`

---

## Tech Stack Summary

| | Version 1 | Version 2 | Version 3 |
|---|---|---|---|
| LLM | Ollama (local) | Ollama (local) | OpenRouter (cloud, free) |
| Model | qwen2.5-coder:7b | qwen2.5-coder:7b | gpt-oss-120b |
| DB | SQLite 8 tables | SQLite 23 tables | PostgreSQL 24 tables (Supabase) |
| Key feature | Basic chatbot + admin | Vector table selection | MCP + client-server + query logs |
| Python version | 3.8+ | 3.8+ | 3.11+ |

---

## Setup

**Install Ollama** (needed for app/ and app2/):
```bash
# download from ollama.com then:
ollama pull qwen2.5-coder:7b
```

**Install all dependencies:**
```bash
pip install -r requirements.txt
```

**For app3 — create a `.env` file in the project root:**
```
OPENROUTER_API_KEY=your_key_here    # free from openrouter.ai
DATABASE_URL=postgresql://...        # free from supabase.com
```

---

## Security

- Only `SELECT` queries allowed through chatbot — no data modification
- Dangerous keywords (`DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`) blocked at input level
- Admin panel uses parameterized queries to prevent SQL injection
- `.env` file with API keys is gitignored — never committed to git
- PostgreSQL credentials stored only in `.env`, never hardcoded

---

## Screenshots

<img width="1918" height="878" alt="image" src="https://github.com/user-attachments/assets/dee264da-8617-4bd4-a182-680e3d0c0682" />

<img width="1240" height="871" alt="image" src="https://github.com/user-attachments/assets/b8497917-4fe0-4fd7-a20f-7b33314f48f4" />

<img width="1577" height="870" alt="image" src="https://github.com/user-attachments/assets/08a1cc4f-8656-471e-ac8b-c88e78c1da99" />
