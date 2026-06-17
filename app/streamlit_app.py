import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import sys
import streamlit as st
import requests
sys.path.append(os.path.dirname(__file__))

# Fix 7 — Import at top
from agent import ask

# Fix 9 — Ollama Check
def is_ollama_running() -> bool:
    try:
        requests.get("http://localhost:11434", timeout=2)
        return True
    except:
        return False

st.set_page_config(page_title="Library Chatbot", page_icon="📚", layout="centered")
st.title("📚 Library Management Chatbot")
st.markdown("Ask anything about books, members, suppliers, or stock alerts in plain English.")
st.divider()

if not is_ollama_running():
    st.error("Ollama is not running! Please start it first.")
    st.code('"C:\\Users\\Malika Kaur\\AppData\\Local\\Programs\\Ollama\\ollama.exe" serve')
    st.stop()

# Fix 8 — Chat History Limit + Clear Button
MAX_MESSAGES = 20

if "messages" not in st.session_state:
    st.session_state.messages = []

col1, col2 = st.columns([6, 1])
with col2:
    if st.button("Clear", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if len(st.session_state.messages) > MAX_MESSAGES:
    st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

examples = [
    "Show all books with low stock",
    "Which books are currently borrowed?",
    "List all suppliers",
    "When will Clean Code be restocked?",
    "Show all pending stock alerts",
]

st.markdown("**Try these questions:**")
cols = st.columns(len(examples))
for i, example in enumerate(examples):
    if cols[i].button(example, key=f"ex_{i}", use_container_width=True):
        st.session_state.prefill = example

prefill = st.session_state.pop("prefill", "")
user_input = st.chat_input("Type your question here...")
question = user_input or prefill

# Fix 10 — Input Validation
def validate_input(text: str):
    if not text or not text.strip():
        return False, "Please enter a question."
    if len(text) > 500:
        return False, "Question too long (max 500 characters)."
    blocked = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER"]
    if any(w in text.upper() for w in blocked):
        return False, "SQL commands are not allowed in questions."
    return True, ""

if question:
    valid, error_msg = validate_input(question)
    if not valid:
        st.warning(error_msg)
    else:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking... (may take 30-60 seconds)"):
                try:
                    answer = ask(question)
                except Exception as e:
                    answer = f"Error: {str(e)}"
            st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})
