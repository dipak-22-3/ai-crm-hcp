# ===============================
# AI-FIRST CRM | HCP INTERACTION
# Streamlit + LangGraph + Groq
# ===============================

import streamlit as st
import sqlite3
from datetime import datetime
from typing import TypedDict, Optional

from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="AI-First CRM | HCP Interaction",
    layout="wide"
)

st.title("🧑‍⚕️ AI-First CRM – Log HCP Interaction")

# -------------------------------
# DATABASE (SQLite)
# -------------------------------
conn = sqlite3.connect("crm.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hcp_name TEXT,
    interaction_type TEXT,
    interaction_datetime TEXT,
    topics_discussed TEXT,
    products_discussed TEXT,
    sentiment TEXT,
    follow_up_actions TEXT,
    ai_summary TEXT
)
""")
conn.commit()

# -------------------------------
# LLM (Groq)
# -------------------------------
llm = ChatGroq(
    model="gemma2-9b-it",
    temperature=0.3
)

# -------------------------------
# LANGGRAPH STATE
# -------------------------------
class AgentState(TypedDict):
    user_input: str
    action: Optional[str]
    result: Optional[str]

# -------------------------------
# TOOLS
# -------------------------------
def log_interaction_tool(state: AgentState):
    text = state["user_input"]

    cursor.execute("""
    INSERT INTO interactions (
        hcp_name,
        interaction_type,
        interaction_datetime,
        topics_discussed,
        ai_summary
    ) VALUES (?, ?, ?, ?, ?)
    """, (
        "Extracted via AI",
        "Meeting",
        datetime.now().isoformat(),
        text,
        text
    ))
    conn.commit()

    return {"result": "✅ Interaction logged successfully using AI."}


def edit_interaction_tool(state: AgentState):
    cursor.execute("""
    UPDATE interactions
    SET follow_up_actions = ?
    WHERE id = (SELECT MAX(id) FROM interactions)
    """, (state["user_input"],))
    conn.commit()

    return {"result": "✏️ Last interaction updated successfully."}


def summarize_tool(state: AgentState):
    summary = llm.invoke(
        f"Summarize this HCP interaction professionally:\n{state['user_input']}"
    )
    return {"result": summary.content}


def sentiment_tool(state: AgentState):
    sentiment = llm.invoke(
        f"Detect sentiment (Positive, Neutral, Negative):\n{state['user_input']}"
    )
    return {"result": sentiment.content}


def followup_tool(state: AgentState):
    followup = llm.invoke(
        f"Suggest next follow-up action for sales rep:\n{state['user_input']}"
    )
    return {"result": followup.content}

# -------------------------------
# AGENT DECISION LOGIC
# -------------------------------
def decide_action(state: AgentState):
    text = state["user_input"].lower()

    if "edit" in text:
        return "edit"
    elif "follow" in text:
        return "followup"
    elif "sentiment" in text:
        return "sentiment"
    elif "summarize" in text:
        return "summarize"
    else:
        return "log"

# -------------------------------
# LANGGRAPH BUILD
# -------------------------------
graph = StateGraph(AgentState)

# decision node
graph.add_node("decider", lambda state: state)

# tool nodes
graph.add_node("log", log_interaction_tool)
graph.add_node("edit", edit_interaction_tool)
graph.add_node("summarize", summarize_tool)
graph.add_node("sentiment", sentiment_tool)
graph.add_node("followup", followup_tool)

# entry point MUST be a node
graph.set_entry_point("decider")

# conditional routing
graph.add_conditional_edges(
    "decider",
    decide_action,
    {
        "log": "log",
        "edit": "edit",
        "summarize": "summarize",
        "sentiment": "sentiment",
        "followup": "followup"
    }
)

# end all tools
graph.add_edge("log", END)
graph.add_edge("edit", END)
graph.add_edge("summarize", END)
graph.add_edge("sentiment", END)
graph.add_edge("followup", END)

agent = graph.compile()


# -------------------------------
# UI LAYOUT
# -------------------------------
left_col, right_col = st.columns(2)

# -------------------------------
# LEFT: FORM
# -------------------------------
with left_col:
    st.subheader("📋 Log Interaction (Form)")

    with st.form("interaction_form"):
        hcp_name = st.text_input("HCP Name")
        interaction_type = st.selectbox(
            "Interaction Type",
            ["Meeting", "Call", "Virtual"]
        )
        interaction_datetime = st.datetime_input(
            "Date & Time",
            datetime.now()
        )
        topics_discussed = st.text_area("Topics Discussed")
        products_discussed = st.text_area("Products Discussed")
        sentiment = st.selectbox(
            "Observed Sentiment",
            ["Positive", "Neutral", "Negative"]
        )
        follow_up_actions = st.text_area("Follow-up Actions")

        submit = st.form_submit_button("Save Interaction")

    if submit:
        cursor.execute("""
        INSERT INTO interactions (
            hcp_name,
            interaction_type,
            interaction_datetime,
            topics_discussed,
            products_discussed,
            sentiment,
            follow_up_actions,
            ai_summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            hcp_name,
            interaction_type,
            interaction_datetime.isoformat(),
            topics_discussed,
            products_discussed,
            sentiment,
            follow_up_actions,
            None
        ))
        conn.commit()
        st.success("✅ Interaction saved via form.")

# -------------------------------
# RIGHT: AI CHAT
# -------------------------------
with right_col:
    st.subheader("🤖 AI Assistant (LangGraph Agent)")

    user_message = st.text_area(
        "Describe interaction or give instruction to AI",
        placeholder="Met Dr. Sharma, discussed Product X, doctor was positive..."
    )

    if st.button("Send to AI"):
        state = {
            "user_input": user_message,
            "action": None,
            "result": None
        }

        output = agent.invoke(state)

        st.success("AI Agent Response:")
        st.write(output["result"])

# -------------------------------
# VIEW LOGGED INTERACTIONS
# -------------------------------
st.subheader("📊 Logged Interactions")

rows = cursor.execute(
    "SELECT id, hcp_name, interaction_type, interaction_datetime, sentiment FROM interactions ORDER BY id DESC"
).fetchall()

if rows:
    for r in rows:
        st.write(
            f"🆔 {r[0]} | 👨‍⚕️ {r[1]} | {r[2]} | {r[3]} | Sentiment: {r[4]}"
        )
else:
    st.info("No interactions logged yet.")
    
        
