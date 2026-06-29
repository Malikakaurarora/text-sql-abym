import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8000")

TABLE_DESCRIPTIONS = {
    "Student": "university students with membership details",
    "Faculty": "university faculty members",
    "Department": "university departments",
    "Book": "library book catalog with stock levels",
    "Author": "book authors",
    "BookAuthor": "many-to-many Book↔Author mapping",
    "Publisher": "book/journal publishers",
    "Category": "book categories with Dewey decimal",
    "Shelf": "physical shelf locations in the library",
    "Journal": "academic journals with impact factor",
    "DigitalResource": "online resources and e-books",
    "DigitalAccess": "student digital resource access logs",
    "Loan": "book borrowing records",
    "Fine": "overdue/damage fines",
    "Reservation": "book reservation queue",
    "BookReview": "student and faculty book reviews",
    "BookRequest": "student requests for new books",
    "LibraryEvent": "library workshops, talks, exhibitions",
    "EventRegistration": "student event sign-ups",
    "Supplier": "book suppliers and vendors",
    "PurchaseOrder": "procurement orders",
    "PurchaseOrderItem": "individual items per purchase order",
    "Librarian": "library staff",
}

st.set_page_config(page_title="Library Chatbot v3 — MCP", page_icon="🔗", layout="centered")
st.title("🔗 Library Chatbot v3")
st.caption("MCP: server discovers schema → generates SQL → queries DB")
st.divider()


def check_server():
    try:
        r = requests.get(f"{SERVER_URL}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


if not check_server():
    st.error(f"Cannot reach server at `{SERVER_URL}`. Start it with:")
    st.code("uvicorn app3.server:app --reload", language="bash")
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
                try:
                    resp = requests.post(
                        f"{SERVER_URL}/query",
                        json={"question": question},
                        timeout=300,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    answer = data.get("response", "No response.")
                    sql = data.get("sql")
                    exec_time = data.get("execution_time")
                except requests.exceptions.ConnectionError:
                    answer = f"Could not connect to server at `{SERVER_URL}`."
                    sql = None
                    exec_time = None
                except Exception as e:
                    answer = f"Error: {e}"
                    sql = None
                    exec_time = None

            st.markdown(answer)
            if sql:
                with st.expander("SQL used"):
                    st.code(sql, language="sql")
            if exec_time is not None:
                st.caption(f"Query completed in {exec_time:.0f} ms")

        st.session_state.messages3.append({"role": "assistant", "content": answer})

with st.sidebar:
    st.subheader("Architecture")
    st.markdown(f"""
**Streamlit client** → HTTP → **FastAPI server** (`{SERVER_URL}`)

Server flow:
1. Receives question via `/query`
2. MCP client calls `mcp_server.py` via stdio
3. LLM discovers schema with `list_tables` / `describe_table`
4. Runs SQL with `run_query`
5. Logs to `QueryLog` table
6. Returns `{{response, sql, execution_time}}`

View logs: `{SERVER_URL}/logs`
""")
    st.divider()
    st.subheader("23 Tables")
    for t, d in TABLE_DESCRIPTIONS.items():
        st.markdown(f"**{t}** — {d}")
