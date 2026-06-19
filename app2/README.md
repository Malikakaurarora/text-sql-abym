# Library Chatbot v2 — Vector Search + Dynamic Schema Selection

An upgraded NL-to-SQL chatbot for a university library system. Built on top of v1 (`app/`) with two major architectural improvements: **semantic table selection** and a **23-table complex database**.

---

## What's New in v2

### 1. Dynamic Schema Selection (Semantic Table Selection)

**Problem in v1:** The full database schema was sent to the LLM every time. As the number of tables grows, this hits the LLM's context limit and increases noise — the model sees irrelevant tables and generates wrong JOINs.

**Solution in v2:** Instead of sending the full schema, we:

1. Write a rich natural-language description for each table (e.g., `"student names, borrowers, enrollment year, unpaid fines, loan records"`)
2. Generate embeddings for all 23 table descriptions using `sentence-transformers` (`all-MiniLM-L6-v2`) — stored in a disk cache (`table_embeddings.pkl`) so they are only computed once
3. At query time, embed the user's question and compute **cosine similarity** against all 23 table embeddings
4. Select the **top 3–7 tables** (dynamic threshold = 0.42) and send only their `CREATE TABLE` schema to the LLM

This lets us scale from 8 to 23 tables without hitting context limits, and keeps the LLM prompt focused on relevant tables only.

```
User Question → sentence-transformers → question vector
Table Descriptions → sentence-transformers → 23 table vectors (cached)
cosine_similarity(question_vec, table_vecs) → top 3–7 tables selected
→ Only selected tables' schema sent to LLM
→ LLM generates SQL
```

### 2. Dynamic Table Recovery

If the LLM's generated SQL references a table that wasn't in the selected schema (e.g., it writes `JOIN Department` but Department wasn't selected), the system:

1. Detects the missing table from the SQL or the SQLite error message
2. Adds it to the schema
3. Retries the LLM call automatically — no user involvement needed

### 3. Retry Logic with Smart Hints

On SQL error, the system retries up to 3 times. Each retry includes a specific hint built from the error:
- Wrong column name → tells LLM the exact column that doesn't exist
- Wrong table name → tells LLM which table is missing
- Missing `borrower_type` filter → proactive validator catches this before hitting the DB (prevents silently wrong results from polymorphic joins)

### 4. Polymorphic Join Validator

`Loan` and `Reservation` tables store both Student and Faculty borrowers using `borrower_type` + `borrower_id`. Since `student_id=6` and `faculty_id=6` are different people, forgetting `borrower_type` in a JOIN produces silently wrong results (no SQL error, just incorrect data).

A proactive validator runs before DB execution and forces a retry with the correct hint if `borrower_type` is missing.

---

## Database: 23-Table University Library System

Expanded from 16 to 23 tables to stress-test complex multi-table JOINs:

| Table | Description |
|---|---|
| Department | Academic departments |
| Category | Book genres and subject areas |
| Publisher | Publishing houses |
| Author | Book authors |
| Shelf | Physical library shelves |
| Book | Book collection (20 rows) |
| BookAuthor | Book–author relationships |
| Journal | Academic journals |
| Student | Student members (17 rows) |
| Faculty | Faculty members |
| Loan | Borrowing records (20 rows) |
| Reservation | Book reservations |
| Fine | Late return fines |
| Supplier | Book suppliers |
| PurchaseOrder | Purchase orders |
| PurchaseOrderItem | Items in purchase orders |
| **Librarian** | Library staff (new) |
| **LibraryEvent** | Workshops, seminars, book fairs (new) |
| **EventRegistration** | Student event attendance (new) |
| **BookReview** | Student/faculty book ratings (new) |
| **DigitalResource** | E-books, online journals, databases (new) |
| **DigitalAccess** | Digital resource usage logs (new) |
| **BookRequest** | Student requests for new books (new) |

---

## How to Run

**1. Install dependencies**
```bash
pip install streamlit langchain-ollama sentence-transformers scikit-learn torch
```

**2. Start Ollama and pull the model**
```bash
ollama pull qwen2.5-coder:7b
ollama serve
```

**3. Create the database**
```bash
python app2/create_db2.py
python app2/expand_db2.py
```

**4. Run the app**
```bash
streamlit run app2/streamlit_app2.py
```

---

## Architecture

```
streamlit_app2.py    → UI (question input, table scores display, result display)
agent2.py            → Core logic:
                         - get_relevant_tables()   : cosine similarity table selection
                         - get_schema_for_tables() : PRAGMA-based schema fetch
                         - validate_polymorphic_join() : proactive borrower_type check
                         - ask_sql()               : LLM call + retry loop
                         - extract_missing_table() : dynamic recovery
                         - format_result()         : markdown table formatting
create_db2.py        → Creates 16-table base database
expand_db2.py        → Adds 7 new tables + more rows
```

---

## Sample Queries Tested

- `Show all book requests that are approved along with the student name and their department` — 3-table JOIN
- `Which students attended library events and what department are they from?` — 4-table JOIN with dynamic recovery
- `Show all books reviewed with rating 5 and show which shelf they are on` — 3-table JOIN
- `Which department do students with unpaid fines belong to?` — Fine → Loan → Student → Department (4-table JOIN)
- `Show all students who currently have an overdue book` — polymorphic join with borrower_type filter

---

## Model Used

`qwen2.5-coder:7b` via Ollama — best accuracy for SQL generation among models tested locally (llama3.2, sqlcoder:7b, qwen2.5-coder:7b).
