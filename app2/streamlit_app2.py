import os
os.environ["TRANSFORMERS_OFFLINE"] = "0"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import sys
import streamlit as st
import requests
sys.path.append(os.path.dirname(__file__))

from agent2 import ask, TABLE_DESCRIPTIONS

def is_ollama_running():
    try:
        requests.get("http://localhost:11434", timeout=2)
        return True
    except:
        return False

st.set_page_config(page_title="Library Chatbot v2 — Vector Search", page_icon="🔬", layout="centered")
st.title("🔬 Library Chatbot v2")
st.caption("Two-Stage: Semantic Table Selection → SQL Generation")
st.divider()

if not is_ollama_running():
    st.error("Ollama is not running!")
    st.code('"C:\\Users\\Malika Kaur\\AppData\\Local\\Programs\\Ollama\\ollama.exe" serve')
    st.stop()

if "messages2" not in st.session_state:
    st.session_state.messages2 = []

col1, col2 = st.columns([6, 1])
with col2:
    if st.button("Clear", use_container_width=True):
        st.session_state.messages2 = []
        st.rerun()

chat_box = st.container()
with chat_box:
    for msg in st.session_state.messages2:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

with st.form("chat_form2", clear_on_submit=True):
    user_input = st.text_input("Ask anything...", label_visibility="collapsed", placeholder="e.g. Which students have unpaid fines?")
    submitted = st.form_submit_button("Ask", use_container_width=True)

if submitted and user_input.strip():
    question = user_input.strip()
    st.session_state.messages2.append({"role": "user", "content": question})

    with chat_box:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Stage 1: Finding relevant tables... Stage 2: Generating SQL..."):
                result = ask(question)

            if result["answer"] is None:
                # No table matched — ask user to clarify
                top_scores = sorted(result["scores"].items(), key=lambda x: x[1], reverse=True)[:3]
                score_info = ", ".join([f"{t} ({s:.2f})" for t, s in top_scores])
                clarify_msg = (
                    "I couldn't find relevant tables for your question. "
                    "Could you rephrase it using more specific terms?\n\n"
                    "**Try mentioning:** books, students, faculty, fines, loans, "
                    "events, suppliers, reviews, digital resources, or book requests.\n\n"
                    f"_(Best matches found: {score_info} — all below confidence threshold)_"
                )
                st.warning(clarify_msg)
                st.session_state.messages2.append({"role": "assistant", "content": clarify_msg})
            else:
                # Show which tables were selected
                if result["selected_tables"]:
                    table_scores = [(t, result["scores"][t]) for t in result["selected_tables"]]
                    table_info = " | ".join([f"`{t}` ({s:.2f})" for t, s in table_scores])
                    st.caption(f"Tables selected: {table_info}")

                st.markdown(result["answer"])
                if result.get("sql"):
                    st.caption(f"SQL: `{result['sql']}`")

                answer_display = result["answer"]
                if result["selected_tables"]:
                    table_info = " | ".join([f"`{t}`" for t in result["selected_tables"]])
                    answer_display += f"\n\n_Tables used: {table_info}_"
                st.session_state.messages2.append({"role": "assistant", "content": answer_display})

# Sidebar: show all table descriptions
with st.sidebar:
    st.subheader("23 Tables in DB")
    st.caption("Semantic similarity picks relevant ones per query")
    for table, desc in TABLE_DESCRIPTIONS.items():
        st.markdown(f"**{table}** — {desc}")
