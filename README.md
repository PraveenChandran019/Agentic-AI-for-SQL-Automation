# Agentic-AI-for-SQL-Automation

## 🧠 Agentic SQL Assistant
A conversational AI-powered SQL assistant that translates natural language questions into SQL queries, executes them, and returns both query results and a data analyst-style report. Built with FastAPI, LangChain, and Streamlit, and powered by Groq’s LLaMA3 model.

## 🚀 Features
🔍 Converts natural language queries into executable SQL.

📊 Returns both data (in DataFrame format) and analytical reports.

💬 Web-based chatbot interface using Streamlit.

🌐 Supports multiple SQL dialects: SQLite, MySQL, and PostgreSQL.

✨ Built using LangChain's ReAct Agent and SQL Toolkits.

📝 Optional feedback collection after each query.

## 🧱 Tech Stack

Component	Technology

LLM  -	Groq’s LLaMA3 (via LangChain);
Framework	- LangChain, LangGraph (ReAct Agent);
Backend	- FastAPI, Pydantic;
Frontend -	Streamlit;
Database -	MySQL, PostgreSQL, SQLite;
Tools	- SQLAlchemy;

## Hosting	Localhost (Dev)
⚙️ Setup Instructions

1. Clone the Repository
git clone https://github.com/your-username/sql-agent-assistant.git
cd sql-agent-assistant

2. Install Dependencies
Make sure you have Python 3.8+ installed.
pip install -r requirements.txt

3. Add Your Database
By default, the app connects to the provided chinook.db SQLite database. You can modify or upload your own .db file via the Streamlit sidebar.

4. Set Groq API Key
Replace the placeholder in backend.py:
GROQ_API_KEY = "your_groq_api_key"

5. Run Backend Server
bash
Copy code
uvicorn backend:app --reload

6. Run Streamlit Frontend
bash
Copy code
streamlit run streamlit.py

## 🧪 API Endpoints
GET / — Health check

GET /dialects — List supported SQL dialects

POST /query — Accepts a natural language query and returns results with analysis

POST /raw_query — Returns raw message history from the LLM agent

POST /feedback — Stores user feedback and ratings


## Copy code
├── backend.py           # FastAPI backend with LangChain agent
├── streamlit.py         # Streamlit frontend UI
├── requirements.txt     # Python dependencies
├── chinook.db           # Sample SQLite database

## 🛡️ Security Notes
No login/CAPTCHA required for access.

App does not expose or process confidential client/company data.

Only metadata and non-sensitive public queries are processed.

## 📌 Limitations
Currently tested on SQLite; other dialects (MySQL/PostgreSQL) need valid credentials.

No authentication or user management is implemented yet.

Model responses may vary based on query complexity and data availability.

## 📬 Feedback
User feedback is stored locally in feedback.json for improvement purposes. Each query allows optional rating and comments.

## 🧠 Future Enhancements

✅ User authentication and session history

✅ Enhanced database schema visualization

✅ Support for live database connection from UI

✅ Integration with cloud-hosted LLMs

✅ Visualization of results (charts, graphs)
