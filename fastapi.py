from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from sql_agent import agent_bulid, run_sql_agent, llm_to_df, llm_to_report
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Union
import requests
import warnings
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryInput(BaseModel):
    query: str

agent_executor = agent_bulid("SQLite")

@app.post("/query")
async def query_handler(query_input: QueryInput):
    user_query = query_input.query
    try:
        data = run_sql_agent(agent_executor, user_query)
        df = llm_to_df(data)
        report = llm_to_report(data)

        if isinstance(df, str):  
            return {"error": df}

        df_dict = df.to_dict(orient="records")
        return {
            "data": df_dict,
            "report": report
        }

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("back5:app", host="127.0.0.1", port=8000, reload=True)
