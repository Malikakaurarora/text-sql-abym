import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import sys
import streamlit as st
sys.path.append(os.path.dirname(__file__))

st.set_page_config(page_title="Library Chatbot", page_icon="📚", layout="centered")
st.title("📚 Library Management Chatbot")
st.markdown("Ask anything about books, members, suppliers, or stock alerts in plain English.")
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

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

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking... (may take 30-60 seconds)"):
            try:
                from agent import ask
                answer = ask(question)
            except Exception as e:
                answer = f"Error: {str(e)}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
