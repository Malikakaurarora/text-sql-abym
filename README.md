# Library Management System — NL to SQL Chatbot

A two-stage Library Management System featuring a Natural Language to SQL chatbot and a full Admin Panel — built entirely with free, local tools.

## Tech Stack

| Layer | Technology |
|---|---|
| Database | SQLite |
| LLM | Qwen2.5-Coder:7b (via Ollama — free, runs locally) |
| Backend Logic | Python + LangChain |
| UI | Streamlit |

## LLM Decision — Why Ollama and Why Qwen2.5-Coder

The original plan was to use **Groq API (Llama 3.3 70B)** as the LLM backend. However, during development, access to the Groq API was denied/restricted.

As an alternative, **Ollama** was chosen because:
- Completely free with no API key required
- Runs entirely on the local machine (no internet needed after setup)
- Suitable for demos and prototypes

**Model selection journey:**
- `llama3.2` — general purpose, struggled with complex JOIN queries (wrong column names, PostgreSQL syntax)
- `sqlcoder:7b` — SQL-specific but same issues persisted
- `qwen2.5-coder:7b` — code/SQL specialized model, significantly better accuracy on multi-table queries ✅

The tradeoff is speed — Ollama on CPU takes 1–3 minutes per query. In a production setup, Groq or OpenAI API would be preferred.

## Project Structure

```
text-sql/
├── app/
│   ├── create_db.py       # Creates SQLite database with all tables and sample data
│   ├── agent.py           # NL to SQL logic — LLM generates SQL, runs on DB, returns answer
│   ├── admin.py           # Admin CRUD operations (return book, update stock, add records)
│   └── streamlit_app.py   # Two-tab UI: Chatbot + Admin Panel
├── library_schema.sql     # Full DB schema with VIEW definition
├── sample_data.sql        # Sample data (5 rows per table)
├── requirements.txt       # Python dependencies
└── README.md
```

## Features

### Stage 1 — NL to SQL Chatbot
- Ask questions in plain English about books, members, suppliers, stock alerts
- LLM converts question to SQL automatically using the database schema
- Answers pulled directly from SQLite database — no hallucination in final output
- Only SELECT queries allowed (read-only, secure)
- Smart retry logic — if SQL fails, model gets targeted error hints and retries

### Stage 2 — Admin Panel
- Return a borrowed book (auto-updates stock)
- Update available copies for any book
- Add new books to the database
- Register new members
- Resolve stock alerts

## Setup & Run

### Prerequisites
- Python 3.11+
- Ollama installed ([download here](https://ollama.com/download))

---

### Step 1 — Install Python Dependencies

Open terminal and run:
```bash
pip install -r requirements.txt
```

---

### Step 2 — Install Ollama

Download and install Ollama from: https://ollama.com/download

After installing, open terminal and pull the model (4.7 GB download — takes a few minutes):
```bash
ollama pull qwen2.5-coder:7b
```

---

### Step 3 — Create the Database

```bash
python app/create_db.py
```

This creates `library.db` with all 8 tables, sample data, and the stock alert view.

---

### Step 4 — Start Ollama Server

Open a **new terminal window** and run:
```bash
ollama serve
```

Keep this terminal open while using the app.

> On Windows, you can also start Ollama from the system tray after installation.

---

### Step 5 — Run the App

In your original terminal:
```bash
python -m streamlit run app/streamlit_app.py
```

Open browser at: `http://localhost:8501`

---

## Sample Chatbot Questions

- `Show all books with low stock`
- `Which books are currently borrowed?`
- `When will Clean Code be restocked?`
- `List all suppliers`
- `Which suppliers are visiting in September?`
- `Tell me supplier name which supplied book in the month of July along with the book title`
- `Which books need reordering, and which supplier will deliver them?`

## How It Works

```
User Question (English)
        ↓
LLM (Ollama / Qwen2.5-Coder:7b)
Converts question to SQL using schema + rules
        ↓
SQLite Database (library.db)
Executes the SQL
        ↓
If SQL fails → retry with targeted error hint (up to 3 attempts)
        ↓
Result formatted directly as table/list
No second LLM call — eliminates hallucination
        ↓
Streamlit UI displays the answer
```

## Database Schema

8 tables: `Supplier`, `Publication`, `Supplier_Publication`, `Supplier_Visit_Schedule`, `Book`, `Stock_Alert`, `Member`, `Issue_Record`

Key feature: `vw_stock_alert_trigger` VIEW automatically calculates the expected restock arrival date based on supplier visit schedule and lead time days.

## Screenshots

<img width="1918" height="878" alt="image" src="https://github.com/user-attachments/assets/dee264da-8617-4bd4-a182-680e3d0c0682" />

<img width="1240" height="871" alt="image" src="https://github.com/user-attachments/assets/b8497917-4fe0-4fd7-a20f-7b33314f48f4" />

## Security

- Only `SELECT` queries are allowed through the chatbot
- Dangerous SQL keywords (`DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`) are blocked at both input and query level these can be done only on admin level for that i have another panel on teh ui 
- Admin Panel uses parameterized queries to prevent SQL injection
- User input is validated before being sent to the LLM


Stage 2 — Admin Panel
A separate Admin Panel was added for librarians to manage data directly — returning books, updating stock, adding new books and members, and resolving stock alerts — all through a simple UI without writing any SQL.
<img width="1577" height="870" alt="image" src="https://github.com/user-attachments/assets/08a1cc4f-8656-471e-ac8b-c88e78c1da99" />

Challenges Faced
Groq API access was denied during development, so Ollama was used as a free local alternative
Local LLM (Ollama) runs on CPU which results in slower response times (30–60 seconds per query) compared to cloud-based APIs
Ensuring the LLM generates correct SQL required providing detailed schema context and example queries in the prompt
Manager ko share karo — link bhi paste kar dena GitHub ka uske baad!
