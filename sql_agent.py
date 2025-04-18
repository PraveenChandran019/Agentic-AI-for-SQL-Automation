import sqlite3

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
from langchain.prompts import PromptTemplate
import re
import pandas as pd
import ast
from langgraph.prebuilt import create_react_agent

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from sqlalchemy import create_engine
from langchain_community.utilities.sql_database import SQLDatabase

db_path = r"C:\Users\Naveena\OneDrive\Desktop\Autogen\chinook.db"

from urllib.parse import quote_plus
encoded_path = quote_plus(db_path)

from sqlalchemy import create_engine, inspect

engine = create_engine(f"sqlite:///{db_path}")  

db = SQLDatabase(engine)



from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

llm = ChatGroq(model = 'llama3-70b-8192', temperature = 0.2, groq_api_key = "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") # i will revoke it so don't waste your time

from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
toolkit = SQLDatabaseToolkit(db = db, llm = llm)
toolkit.get_tools()

from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
    QuerySQLDataBaseTool,
)
from langchain.tools import tool
@tool("list_tables")
def list_tables(tool_input: str = "") -> str:
    """List the available tables from the database"""
    return ListSQLDatabaseTool(db=db).invoke("")

@tool("tables_schema")
def tables_schema(tables: str) -> str:
    """
    Input is a comma-separated list of tables, output is the schema and sample rows
    for those tables. Be sure that the tables actually exist by calling `list_tables` first!
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
    tool before executing a query with `execute_query`."""
    return QuerySQLCheckerTool(db = db, llm = llm).invoke({"query": sql_query})

from langchain.prompts import PromptTemplate

def agent_bulid(dialect):
    prompt_template = """
    You are SQL Coding Agent.
    Understand the Task:
    - Given a question, create a correct SQL query for {dialect}.
    - Always query for the available tables and their schema first.
    - Order the results by the most relevant column for insight.
    - Never execute queries that alter the data (e.g., INSERT, UPDATE, DELETE).
    ### Instructions:
    follow this instruction in the same order do not miss or disobey this order
    1. **List Available Tables**: Always query the list of tables first using the tool `list_tables`. correctly identify the needed table from the user query and do not make query with random table name. 
    2. **Check Schema of Relevant Table**: Inspect the schema of the table using the tool `tables_schema`. Always find for relevent details from the table schema accoridng to the user prompt. Do not skip this step or make your own query with random field name.
    3. **Execute the Query**: After gathering schema information, formulate the query and execute it and fetch the result from the database. use this tool `execute_query` for execution and data fetching.
    4. **Error Handling**: If an error occurs, debug and fix the query before re-executing it. use this tool `query_checker` for query debugging.
    5. Always return the fetched in Dataframe by keeping schema name as their column name

    From the fetched data write a report with 500 words like a data analyst, try to give insights and trend of the data
     
    """
    system_message = prompt_template.format(dialect=dialect)
    tools = [list_tables, tables_schema, execute_query, query_checker]
    from langgraph.prebuilt import create_react_agent
    agent_executor = create_react_agent(llm, tools=tools, prompt=system_message)
    return agent_executor

import re
import pandas as pd
import ast


def run_sql_agent(agent_executor,user_query: str) -> str:
    try:
        data = agent_executor.invoke({"messages": [("user", user_query)]})
        return data
    except Exception as e:
        return f"Error: {str(e)}"
 
# in frontend you guys need to make it like the question from chatbot should comes to run_sql_agent and result of run_sql_agent needs to go to llm_to_df and the ouput of llm_to_df should go back to frontend
   
def llm_to_df(data):
    try:
        df = data["messages"][-2].content
        df2 = ast.literal_eval(df)
        schema = data["messages"][-4].content
        pattern = r'\b(\w+)\s+(?:INTEGER|VARCHAR|TEXT|CHAR|FLOAT|REAL|BOOLEAN|DATE|DATETIME|BLOB)(?:\s+NOT NULL)?\s*,'
        column = re.findall(pattern, schema, re.MULTILINE)
        df3 = pd.DataFrame(df2, columns = column)
        return df3
    except Exception as e:
        return f"Error: {str(e)}"
    
    
def llm_to_report(data):
    try:
        report = data["messages"][-1].content
        return report
    except Exception as e:
        return f"Error: {str(e)}"
    
# to test locally

#agent_executor = agent_bulid("SQLite")
#data2 = run_sql_agent(agent_executor,"I want all the artist data")
#print(llm_to_df(data2))
#print(llm_to_report(data2))