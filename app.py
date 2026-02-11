import streamlit as st
import sqlite3
from datetime import datetime

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="AI-First CRM | HCP Interaction",
    layout="wide"
)

st.title("🧑‍⚕️ AI-First CRM – Log HCP Interaction")

# -------------------------------
# Database (SQLite)
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
# Layout
# -------------------------------
left_col, right_col = st.columns(2)

# -------------------------------
# LEFT: Structured Form
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

        st.success("Interaction saved successfully!")

# -------------------------------
# RIGHT: AI Chat Placeholder
# -------------------------------
with right_col:
    st.subheader("🤖 AI Assistant")

    st.info(
        "You can describe the interaction here.\n"
        "The AI agent will summarize, extract entities, "
        "and log or edit interactions."
    )

    user_message = st.text_area(
        "Describe interaction…",
        placeholder="Met Dr. Sharma, discussed Product X, doctor was positive..."
    )

    if st.button("Send to AI"):
        st.warning(
            "AI Agent will be connected in the next step "
            "(LangGraph +
          
