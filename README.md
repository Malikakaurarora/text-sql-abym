# Library Management System — NL to SQL Chatbot

A Natural Language to SQL chatbot built on a Library Management System database. Ask questions in plain English and get answers from a real SQLite database.

## Tech Stack

| Layer | Technology |
|---|---|
| Database | SQLite |
| LLM | Llama 3.2 (via Ollama — free, local) |
| Backend Logic | Python (LangChain + SQLite3) |
| UI | Streamlit |

## Project Structure

```
text-sql/
├── app/
│   ├── create_db.py       # Creates SQLite database with sample data
│   ├── agent.py           # NL to SQL logic using Ollama LLM
│   └── streamlit_app.py   # Chatbot UI
├── library_schema.sql     # Full DB schema with VIEW
├── sample_data.sql        # Sample data (5 rows per table)
├── requirements.txt       # Python dependencies
└── README.md
```

## Setup & Run

### Step 1 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Install Ollama

Download from: https://ollama.com/download

Then pull the model:
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

## Database Schema

8 tables: `Supplier`, `Publication`, `Supplier_Publication`, `Supplier_Visit_Schedule`, `Book`, `Stock_Alert`, `Member`, `Issue_Record`

Key feature: `vw_stock_alert_trigger` VIEW auto-calculates expected restock arrival date based on supplier visit schedule and lead time.
