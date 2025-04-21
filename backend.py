from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import sqlite3
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
import json

import requests
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from urllib.parse import quote
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
    QuerySQLDataBaseTool,
)
from langchain.tools import tool
import re
import pandas as pd
import ast
from langgraph.prebuilt import create_react_agent


DB_PATHS = {
    "SQLite": r"C:\Users\Naveena\OneDrive\Desktop\Autogen\chinook.db",

}

GROQ_API_KEY = "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"

agent_executors = {}

def setup_database(dialect):
    if dialect not in DB_PATHS:
        raise ValueError(f"Unsupported dialect: {dialect}")
    
    db_path = DB_PATHS[dialect]
    
    if dialect == "SQLite":
        engine = create_engine(f"sqlite:///{db_path}")
    elif dialect == "MySQL":
        engine = create_engine(db_path)
    elif dialect == "PostgreSQL":
        engine = create_engine(db_path)
    else:
        raise ValueError(f"Unsupported dialect: {dialect}")
    
    return SQLDatabase(engine)

def create_llm():
    return ChatGroq(
        model = 'llama3-70b-8192', 
        temperature = 0.2, 
        groq_api_key = GROQ_API_KEY
    )

def create_tools(db, llm):
    @tool("list_tables")
    def list_tables(tool_input: str = "") -> str:
        """List the available tables from the database"""
        return ListSQLDatabaseTool(db=db).invoke("")

    @tool("tables_schema")
    def tables_schema(tables: str) -> str:
        """
        Input is a comma-separated list of tables, output is the schema and sample rows
        for those tables. Be sure that the tables actually exist by calling list_tables first!
        Example Input: table1, table2, table3
        """
        tool = InfoSQLDatabaseTool(db=db)
        return tool.invoke(tables)

    @tool("execute_query")
    def execute_query(query : str) -> str:
        """ Use this tool to execute the sql query against database and fetch result data from it """
        return QuerySQLDataBaseTool(db = db).invoke(query)

    @tool("query_checker")
    def query_checker(sql_query : str) -> str:
        """ Use this tool to double check whether the given query is proper or not before executing it. Always use this
        tool before executing a query with execute_query."""
        return QuerySQLCheckerTool(db = db, llm = llm).invoke({"query": sql_query})
    
    return [list_tables, tables_schema, execute_query, query_checker]

# Function to build agent executor
def build_agent_executor(dialect):
    if dialect in agent_executors:
        return agent_executors[dialect]
    
    db = setup_database(dialect)
    llm = create_llm()
    tools = create_tools(db, llm)
    
    prompt_template = """
    You are SQL Coding Agent.
    Understand the Task:
    - Given a question, create a correct SQL query for {dialect}.
    - Always query for the available tables and their schema first.
    - Order the results by the most relevant column for insight.
    - Never execute queries that alter the data (e.g., INSERT, UPDATE, DELETE).
    ### Instructions:
    follow this instruction in the same order do not miss or disobey this order
    1. *List Available Tables*: Always query the list of tables first using the tool list_tables. correctly identify the needed table from the user query and do not make query with random table name. 
    2. *Check Schema of Relevant Table*: Inspect the schema of the table using the tool tables_schema. Always find for relevent details from the table schema accoridng to the user prompt. Do not skip this step or make your own query with random field name.
    3. *Execute the Query*: After gathering schema information, formulate the query and execute it and fetch the result from the database. use this tool execute_query for execution and data fetching.
    4. *Error Handling*: If an error occurs, debug and fix the query before re-executing it. use this tool query_checker for query debugging.
    5. Always return the fetched in Dataframe by keeping schema name as their column name

    From the fetched data write a report with 500 words like a data analyst, 
    """
    system_message = prompt_template.format(dialect=dialect)
    
    agent_executor = create_react_agent(llm, tools=tools, prompt=system_message)
    
    agent_executors[dialect] = agent_executor
    
    return agent_executor

def run_sql_agent(agent_executor, user_query: str) -> dict:
    try:
        data = agent_executor.invoke({"messages": [("user", user_query)]})
        return data
    except Exception as e:
        return {"error": str(e)}
   
def llm_to_df(data):
    try:
        df = data["messages"][-2].content
        df2 = ast.literal_eval(df)
        df3 = pd.DataFrame(df2)
        return df3
    except Exception as e:
        return f"Error: {str(e)}"
    
def llm_to_report(data):
    try:
        report = data["messages"][-1].content
        return report
    except Exception as e:
        return f"Error: {str(e)}"

class QueryRequest(BaseModel):
    query: str
    dialect: str = "SQLite"  

class QueryResponse(BaseModel):
    data: List[Dict[str, Any]]
    report: str


app = FastAPI(title="SQL Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  
)

@app.get("/")
def read_root():
    return {"message": "SQL Agent API is running"}

@app.post("/query")
async def process_query(request: QueryRequest):
    """
    Process a natural language query and return the SQL results with analysis
    """
    try:
        if request.dialect not in DB_PATHS:
            return {
                "data": [],
                "report": f"Unsupported dialect: {request.dialect}. Supported dialects are: {', '.join(DB_PATHS.keys())}"
            }
            
        agent_executor = build_agent_executor(request.dialect)
        
        result = run_sql_agent(agent_executor, request.query)
        
        if "error" in result:
            return {
                "data": [],
                "report": f"Error processing query: {result['error']}"
            }
            
        data_result = []
        report = "No analysis available."
        
        try:
            df = llm_to_df(result)
            if isinstance(df, pd.DataFrame):
                data_result = df.to_dict(orient="records")
            else:
                return {
                    "data": [],
                    "report": f"Data processing error: {df}"
                }
        except Exception as e:
            return {
                "data": [],
                "report": f"Failed to process data: {str(e)}"
            }
        
        try:
            report = llm_to_report(result)
        except Exception as e:
            report = "Failed to generate analysis report."
            
        return {
            "data": data_result,
            "report": report
        }
        
    except Exception as e:
        
        return {
            "data": [],
            "report": f"Server error: {str(e)}"
        }


@app.post("/raw_query")
async def raw_query(request: QueryRequest):
    """
    Process a query and return all raw messages from the agent
    """
    try:
        agent_executor = build_agent_executor(request.dialect)
        result = run_sql_agent(agent_executor, request.query)
        
        
        messages = []
        for msg in result.get("messages", []):
            if hasattr(msg, "content") and hasattr(msg, "type"):
                messages.append({"type": msg.type, "content": msg.content})
            else:
                messages.append({"type": "unknown", "content": str(msg)})
        
        return {
            "messages": messages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/dialects")
async def list_dialects():
    """
    Return a list of supported SQL dialects
    """
    return {"dialects": list(DB_PATHS.keys())}

class FeedbackRequest(BaseModel):
    user_query: str
    dialect: str
    feedback_text: str
    rating: Optional[int] = None

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    try:
        feedback_entry = {
            "user_query": feedback.user_query,
            "dialect": feedback.dialect,
            "feedback_text": feedback.feedback_text,
            "rating": feedback.rating
        }

        with open("feedback.json", "a") as f:
            f.write(json.dumps(feedback_entry) + "\n")

        return {"message": "Feedback received successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store feedback: {str(e)}")


if __name__ == "__main__":

    uvicorn.run("back3:app", host="0.0.0.0", port=8000, reload=True)