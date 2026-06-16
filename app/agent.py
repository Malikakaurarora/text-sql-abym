import os
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_ollama import ChatOllama

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'library.db')

def get_agent():
    db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
    llm = ChatOllama(
        model="llama3.2",
        temperature=0
    )
    agent = create_sql_agent(
        llm=llm,
        db=db,
        verbose=True,
        agent_type="tool-calling"
    )
    return agent

def ask(question: str) -> str:
    agent = get_agent()
    result = agent.invoke({"input": question})
    return result.get("output", "No answer found.")
