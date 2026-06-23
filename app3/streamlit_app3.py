import os
import sys
import requests
import streamlit as st

sys.path.append(os.path.dirname(__file__))
from agent3 import ask, TABLE_DESCRIPTIONS


def api_key_present() -> bool:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    return bool(os.environ.get("OPENROUTER_API_KEY"))


st.set_page_config(page_title="Library Chatbot v3 — MCP", page_icon="🔗", layout="centered")
st.title("🔗 Library Chatbot v3")
st.caption("Proper MCP: Gemini discovers tools from MCP server → queries SQLite")
st.divider()

if not api_key_present():
    st.error("OPENROUTER_API_KEY missing in .env")
    st.code("OPENROUTER_API_KEY=sk-or-...")
    st.stop()

if "messages3" not in st.session_state:
    st.session_state.messages3 = []

col1, col2 = st.columns([6, 1])
with col2:
    if st.button("Clear", use_container_width=True):
        st.session_state.messages3 = []
        st.rerun()

chat_box = st.container()
with chat_box:
    for msg in st.session_state.messages3:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

with st.form("chat_form3", clear_on_submit=True):
    user_input = st.text_input(
        "Ask anything...",
        label_visibility="collapsed",
        placeholder="e.g. Which department has the highest unpaid fines?",
    )
    submitted = st.form_submit_button("Ask", use_container_width=True)

if submitted and user_input.strip():
    question = user_input.strip()
    st.session_state.messages3.append({"role": "user", "content": question})

    with chat_box:
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("MCP: discovering schema → generating SQL → querying DB..."):
                result = ask(question)

            st.markdown(result["answer"])
            if result.get("sql"):
                with st.expander("SQL used"):
                    st.code(result["sql"], language="sql")

        st.session_state.messages3.append({"role": "assistant", "content": result["answer"]})

with st.sidebar:
    st.subheader("MCP Flow")
    st.markdown("""
**1. MCP Server** (`mcp_server.py`)
Exposes 3 tools over stdio:
- `list_tables`
- `describe_table`
- `run_query`

**2. MCP Client** (`agent3.py`)
Gemini discovers tools at runtime,
calls them through MCP protocol.

**Result:** No hardcoded rules.
Schema checked before every query.
""")
    st.divider()
    st.subheader("23 Tables")
    for t, d in TABLE_DESCRIPTIONS.items():
        st.markdown(f"**{t}** — {d}")
