# Library Management System — NL to SQL Chatbot

A university library management system with a Natural Language to SQL chatbot — built in 3 versions, each improving on the last. You can ask questions in plain English and it queries the database for you.

Built entirely with free tools — no paid APIs needed (except app3 which uses a free tier).

---

## Project Structure

```
text-sql/
├── app/          ← Version 1: Basic NL-to-SQL (8 tables, Ollama)
├── app2/         ← Version 2: Vector search + smarter SQL (23 tables, Ollama)
├── app3/         ← Version 3: Proper MCP implementation (23 tables, OpenRouter free)
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
**Proper MCP (Model Context Protocol) Implementation**

My manager asked me to use MCP, so I rebuilt the whole thing properly.

**What is MCP?**
MCP (Model Context Protocol) is an open standard by Anthropic. Instead of the LLM blindly generating SQL, it gets tools it can call — like `list_tables`, `describe_table`, `run_query`. The LLM decides when to call which tool, looks at the actual schema, then writes correct SQL.

**Architecture:**
```
User question
     ↓
MCP Client (agent3.py) — discovers tools from MCP server
     ↓  [stdio protocol]
MCP Server (mcp_server.py) — standalone process exposing DB as tools
     ↓
SQLite (library2.db)
```

**Why this is better than app2:**
- No hardcoded rules — the model checks schema itself before writing SQL
- No validate_columns() hacks — model already knows correct column names
- Self-correcting — if SQL errors, error goes back to model and it fixes it
- Any MCP-compatible client (Claude Desktop, etc.) can connect to this server

**What tools the MCP server exposes:**
| Tool | What it does |
|---|---|
| `list_tables` | Shows all 23 tables |
| `describe_table` | Returns exact column names + types |
| `run_query` | Executes SQL, returns results |

**Tech:**
- Python 3.11+ (required for `mcp` package)
- `mcp` package (Anthropic's official MCP SDK)
- OpenRouter free API (gpt-oss-120b model, completely free)
- Streamlit UI

**Setup:**
```bash
# needs Python 3.11+
pip install mcp openai streamlit python-dotenv requests

# add to .env file:
OPENROUTER_API_KEY=your_key_here
# get free key from openrouter.ai
```

**Run:**
```bash
streamlit run app3/streamlit_app3.py
```

**Sample queries that work well:**
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
| Tables | 8 | 23 | 23 |
| Table selection | All sent to LLM | Vector similarity | LLM discovers via MCP |
| SQL accuracy | Basic | Medium (needs rules) | High (schema-aware) |
| Self-correction | Basic retry | Hints + validate_columns | Tool feedback loop |
| Rules to maintain | Few | Many (20+) | None |
| Cost | Free | Free | Free (OpenRouter) |
| Speed | Slow (local) | Slow (local) | Fast (cloud) |

---

## Database Schema (app2 & app3)

23 tables covering the full university library system:

**Books & Catalog:** Book, Author, BookAuthor, Category, Publisher, Shelf, Journal

**Members:** Student, Faculty, Department

**Circulation:** Loan, Reservation, Fine

**Procurement:** Supplier, PurchaseOrder, PurchaseOrderItem

**Engagement:** Event, EventRegistration, Review, BookRequest, Notification

**Digital:** DigitalResource, DigitalAccess

---

## Tech Stack Summary

| | Version 1 | Version 2 | Version 3 |
|---|---|---|---|
| LLM | Ollama (local) | Ollama (local) | OpenRouter (cloud, free) |
| Model | qwen2.5-coder:7b | qwen2.5-coder:7b | gpt-oss-120b |
| DB | SQLite 8 tables | SQLite 23 tables | SQLite 23 tables |
| Key feature | Basic chatbot + admin | Vector table selection | MCP protocol |
| Python version | 3.8+ | 3.8+ | 3.11+ |

---

## Setup

**Install Ollama** (needed for app/ and app2/):
```bash
# download from ollama.com then:
ollama pull qwen2.5-coder:7b
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**For app3 only** — add to a `.env` file in the project root:
```
OPENROUTER_API_KEY=your_key_here
```
Get a free key from [openrouter.ai](https://openrouter.ai)

---

## Screenshots

<img width="1918" height="878" alt="image" src="https://github.com/user-attachments/assets/dee264da-8617-4bd4-a182-680e3d0c0682" />

<img width="1240" height="871" alt="image" src="https://github.com/user-attachments/assets/b8497917-4fe0-4fd7-a20f-7b33314f48f4" />

<img width="1577" height="870" alt="image" src="https://github.com/user-attachments/assets/08a1cc4f-8656-471e-ac8b-c88e78c1da99" />

---

## Security

- Only `SELECT` queries allowed through chatbot — no data modification
- Dangerous keywords (`DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`) blocked at input level
- Admin panel uses parameterized queries to prevent SQL injection
- `.env` file with API keys is gitignored
