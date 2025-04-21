import streamlit as st
import requests

# --- Page config ---
st.set_page_config(page_title=" SQL Assistant Chat", page_icon="", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS ---
st.markdown("""
<style>
.css-18e3th9 { background-color: #2c2f36; color: white; }
.css-1kyxreq, .css-1v0mbp4 { background-color: #1f2429; }
.css-1s2u09g { background-color: #2c2f36; color: white; }
</style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("🧠 SQL Assistant Chat")

# --- URLs ---
API_URL = "http://localhost:8000/query"
FEEDBACK_URL = "http://localhost:8000/feedback"

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "dialect" not in st.session_state:
    st.session_state.dialect = "SQLite"

# --- Sidebar ---
with st.sidebar:
    st.header("⚙ Settings")
    st.selectbox("Select SQL Dialect", ["SQLite", "MySQL", "PostgreSQL"], key="dialect")

    with st.expander("🔐 Enter Credentials"):
        if st.session_state.dialect == "SQLite":
            db_path = st.text_input("Database File Path", key="sqlite_path")
        elif st.session_state.dialect == "MySQL":
            mysql_host = st.text_input("Host")
            mysql_port = st.text_input("Port", "3306")
            mysql_user = st.text_input("Username")
            mysql_pass = st.text_input("Password", type="password")
            mysql_db = st.text_input("Database")
        elif st.session_state.dialect == "PostgreSQL":
            pg_host = st.text_input("Host")
            pg_port = st.text_input("Port", "5432")
            pg_user = st.text_input("Username")
            pg_pass = st.text_input("Password", type="password")
            pg_db = st.text_input("Database")

    st.divider()
    st.subheader("📜 Chat History")
    for i, hist in enumerate(st.session_state.history):
        if st.button(f"Chat {i+1}", key=f"hist_{i}"):
            st.session_state.messages = hist.copy()

# --- Display Messages ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Chat Input ---
if prompt := st.chat_input("Ask your database..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(API_URL, json={"query": prompt, "dialect": st.session_state.dialect})
                if response.status_code == 200:
                    result = response.json()
                    report = result.get("report", "No report available.")
                    st.markdown(report)
                    st.session_state.messages.append({"role": "assistant", "content": report})

                    data = result.get("data", [])
                    if data:
                        st.dataframe(data, use_container_width=True)

                    with st.expander("💬 Leave Feedback"):
                        feedback_text = st.text_area("What did you think about this answer?")
                        rating = st.slider("Rate this response (1 = Poor, 5 = Excellent)", 1, 5, 3)
                        if st.button("Submit Feedback"):
                            feedback_payload = {
                                "user_query": prompt,
                                "dialect": st.session_state.dialect,
                                "feedback_text": feedback_text,
                                "rating": rating
                            }
                            feedback_response = requests.post(FEEDBACK_URL, json=feedback_payload)
                            if feedback_response.status_code == 200:
                                st.success("✅ Feedback submitted successfully!")
                            else:
                                st.error(f"❌ Failed to submit feedback: {feedback_response.text}")
                else:
                    error_msg = f"Error from API: {response.text}"
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"Request failed: {str(e)}"
                st.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

    # Save current session to history
    st.session_state.history.append(st.session_state.messages.copy())