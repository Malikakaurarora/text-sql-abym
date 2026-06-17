# Library Management System — NL to SQL Chatbot

A Natural Language to SQL chatbot built on a Library Management System database. Ask questions in plain English and get answers from a real SQLite database — no SQL knowledge required.

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
│   └── streamlit_app.py   # Chatbot UI (browser-based)
├── library_schema.sql     # Full DB schema with VIEW definition
├── sample_data.sql        # Sample data (5 rows per table)
├── requirements.txt       # Python dependencies
└── README.md
```

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

### Step 5 — Run the Chatbot UI

```bash
python -m streamlit run app/streamlit_app.py
```

Open browser at: `http://localhost:8501`

## Sample Questions to Try

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
Converts question to SQL query
        ↓
SQLite Database (library.db)
Executes the SQL query
        ↓
LLM again
Converts result to a human-friendly answer
        ↓
Streamlit UI
Displays the answer to the user
```

## Database Schema

8 tables: `Supplier`, `Publication`, `Supplier_Publication`, `Supplier_Visit_Schedule`, `Book`, `Stock_Alert`, `Member`, `Issue_Record`

Key feature: `vw_stock_alert_trigger` VIEW automatically calculates the expected restock arrival date based on the supplier visit schedule and lead time days — demonstrating a cross-table dependency.

## Security

- Only `SELECT` queries are allowed to run against the database
- Dangerous SQL keywords (`DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`) are blocked at both input and query level
- User input is validated before being sent to the LLM
