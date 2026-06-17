import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import sys
import streamlit as st
import requests
sys.path.append(os.path.dirname(__file__))

from agent import ask
from admin import (
    get_all_books, get_all_members, get_all_publications,
    get_currently_borrowed, get_pending_alerts,
    return_book, update_stock, add_book, add_member, resolve_alert
)

def is_ollama_running() -> bool:
    try:
        requests.get("http://localhost:11434", timeout=2)
        return True
    except:
        return False

def validate_input(text: str):
    if not text or not text.strip():
        return False, "Please enter a question."
    if len(text) > 500:
        return False, "Question too long (max 500 characters)."
    blocked = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER"]
    if any(w in text.upper() for w in blocked):
        return False, "SQL commands are not allowed in questions."
    return True, ""

st.set_page_config(page_title="Library Management System", page_icon="📚", layout="centered")
st.title("📚 Library Management System")
st.divider()

tab1, tab2 = st.tabs(["Chatbot", "Admin Panel"])

# ══════════════════════════════════════════════════════════════
# TAB 1 — CHATBOT
# ══════════════════════════════════════════════════════════════
with tab1:
    st.markdown("Ask anything about books, members, suppliers, or stock alerts in plain English.")

    if not is_ollama_running():
        st.error("Ollama is not running! Please start it first.")
        st.code('"C:\\Users\\Malika Kaur\\AppData\\Local\\Programs\\Ollama\\ollama.exe" serve')
        st.stop()

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

    # Scrollable chat history
    chat_box = st.container()
    with chat_box:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Example buttons
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

    # Input always below chat box
    prefill = st.session_state.pop("prefill", "")
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Type your question here...", value=prefill, label_visibility="collapsed", placeholder="Ask anything about the library...")
        submitted = st.form_submit_button("Ask", use_container_width=True)
    question = user_input if submitted else None

    if question:
        valid, error_msg = validate_input(question)
        if not valid:
            st.warning(error_msg)
        else:
            st.session_state.messages.append({"role": "user", "content": question})
            with chat_box:
                with st.chat_message("user"):
                    st.markdown(question)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking... (may take 1-3 minutes on CPU)"):
                        try:
                            answer = ask(question)
                        except Exception as e:
                            answer = f"Error: {str(e)}"
                    st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

# ══════════════════════════════════════════════════════════════
# TAB 2 — ADMIN PANEL
# ══════════════════════════════════════════════════════════════
with tab2:
    st.markdown("Manage books, members, and stock directly.")
    st.divider()

    # ── Return a Book ──────────────────────────────────────────
    st.subheader("Return a Book")
    borrowed = get_currently_borrowed()
    if borrowed:
        options = {f"{row[1]} → '{row[2]}' (issued: {row[3]})": row[0] for row in borrowed}
        selected = st.selectbox("Select record to return:", list(options.keys()), key="return_select")
        if st.button("Mark as Returned", key="return_btn"):
            result = return_book(options[selected])
            if result == "success":
                st.success("Book marked as returned and stock updated!")
                st.rerun()
            else:
                st.error(result)
    else:
        st.info("No books currently borrowed.")

    st.divider()

    # ── Update Stock ───────────────────────────────────────────
    st.subheader("Update Book Stock")
    books = get_all_books()
    if books:
        book_options = {f"{row[1]} (current: {row[2]} copies)": row[0] for row in books}
        selected_book = st.selectbox("Select book:", list(book_options.keys()), key="stock_select")
        new_copies = st.number_input("New available copies:", min_value=0, max_value=999, value=0, key="stock_input")
        if st.button("Update Stock", key="stock_btn"):
            result = update_stock(book_options[selected_book], new_copies)
            if result == "success":
                st.success(f"Stock updated to {new_copies} copies!")
                st.rerun()
            else:
                st.error(result)

    st.divider()

    # ── Add New Book ───────────────────────────────────────────
    st.subheader("Add New Book")
    with st.form("add_book_form"):
        title     = st.text_input("Book Title *")
        author    = st.text_input("Author *")
        pubs      = get_all_publications()
        pub_map   = {row[1]: row[0] for row in pubs}
        pub_sel   = st.selectbox("Publication / Series", list(pub_map.keys()))
        copies    = st.number_input("Available Copies", min_value=0, value=1)
        threshold = st.number_input("Reorder Threshold", min_value=1, value=2)
        if st.form_submit_button("Add Book"):
            if not title or not author:
                st.error("Title and Author are required.")
            else:
                result = add_book(title, author, pub_map[pub_sel], copies, threshold)
                if result == "success":
                    st.success(f"'{title}' added successfully!")
                else:
                    st.error(result)

    st.divider()

    # ── Add New Member ─────────────────────────────────────────
    st.subheader("Add New Member")
    with st.form("add_member_form"):
        m_name  = st.text_input("Member Name *")
        m_email = st.text_input("Email *")
        m_phone = st.text_input("Phone")
        if st.form_submit_button("Add Member"):
            if not m_name or not m_email:
                st.error("Name and Email are required.")
            else:
                result = add_member(m_name, m_email, m_phone)
                if result == "success":
                    st.success(f"Member '{m_name}' added successfully!")
                else:
                    st.error(result)

    st.divider()

    # ── Resolve Stock Alert ────────────────────────────────────
    st.subheader("Resolve Stock Alerts")
    alerts = get_pending_alerts()
    if alerts:
        alert_options = {
            f"{row[1]} — Supplier: {row[2]} — Expected: {row[3]} [{row[4]}]": row[0]
            for row in alerts
        }
        sel_alert = st.selectbox("Select alert to resolve:", list(alert_options.keys()), key="alert_select")
        if st.button("Mark as Resolved", key="alert_btn"):
            result = resolve_alert(alert_options[sel_alert])
            if result == "success":
                st.success("Alert marked as Resolved!")
                st.rerun()
            else:
                st.error(result)
    else:
        st.info("No pending stock alerts.")
