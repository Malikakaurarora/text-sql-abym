# Library Management System — NL to SQL Chatbot

A two-stage Library Management System featuring a Natural Language to SQL chatbot and a full Admin Panel — built entirely with free, local tools.

## Tech Stack

| Layer | Technology |
|---|---|
| Database | SQLite |
| LLM | Llama 3.2 (via Ollama — free, runs locally) |
| Backend Logic | Python + LangChain |
| UI | Streamlit |

## LLM Decision — Why Ollama Instead of Groq

The original plan was to use **Groq API (Llama 3.3 70B)** as the LLM backend due to its speed and performance. However, during development, access to the Groq API was denied/restricted, which blocked that path.

As an alternative, **Ollama** was chosen because:
- Completely free with no API key required
- Runs entirely on the local machine (no internet needed)
- Uses the same Llama model family (Llama 3.2)
- Suitable for demos and prototypes

The tradeoff is speed — Ollama on CPU takes 30–60 seconds per query compared to Groq's 1–2 seconds. In a production setup, Groq or OpenAI API would be preferred.

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
- Ask questions in plain English
- LLM converts question to SQL automatically
- Answers pulled directly from SQLite database
- Only SELECT queries allowed (read-only, secure)

### Stage 2 — Admin Panel
- Return a borrowed book (auto-updates stock)
- Update available copies for any book
- Add new books to the database
- Register new members
- Resolve stock alerts

## Setup & Run

### Step 1 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Install Ollama

Download from: https://ollama.com/download

After installing, pull the model:
```bash
ollama pull llama3.2
```

### Step 3 — Create the Database

```bash
python app/create_db.py
```

### Step 4 — Start Ollama Server

```bash
ollama serve
```

### Step 5 — Run the App

```bash
python -m streamlit run app/streamlit_app.py
```

Open browser at: `http://localhost:8501`

## Sample Chatbot Questions

- `Show all books with low stock`
- `Which books are currently borrowed?`
- `When will Clean Code be restocked?`
- `List all suppliers`
- `Show all pending stock alerts`

## How It Works

```
User Question (English)
        ↓
LLM (Ollama / Llama 3.2)
Converts question to SQL
        ↓
SQLite Database (library.db)
Executes the SQL
        ↓
LLM again
Converts result to human-friendly answer
        ↓
Streamlit UI displays the answer
```

## Database Schema

8 tables: `Supplier`, `Publication`, `Supplier_Publication`, `Supplier_Visit_Schedule`, `Book`, `Stock_Alert`, `Member`, `Issue_Record`

Key feature: `vw_stock_alert_trigger` VIEW automatically calculates the expected restock arrival date based on supplier visit schedule and lead time days — demonstrating a cross-table dependency.


attaching screenshots:
<img width="1918" height="878" alt="image" src="https://github.com/user-attachments/assets/dee264da-8617-4bd4-a182-680e3d0c0682" />

<img width="1240" height="871" alt="image" src="https://github.com/user-attachments/assets/b8497917-4fe0-4fd7-a20f-7b33314f48f4" />

## Security

- Only `SELECT` queries are allowed through the chatbot
- Dangerous SQL keywords (`DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`) are blocked at both input and query level
- Admin Panel uses parameterized queries to prevent SQL injection
- User input is validated before being sent to the LLM
