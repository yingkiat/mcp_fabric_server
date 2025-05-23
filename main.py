#main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fabric_tool import get_schema_description, generate_sql, execute_sql

import os
import platform
# Only set REQUESTS_CA_BUNDLE on Linux/WSL, not Windows
import requests
import certifi
print("Using certifi at:", certifi.where())

try:
    print("Testing cert in FastAPI startup...")
    r = requests.get("https://login.microsoftonline.com", timeout=10)
    print("Test request status code:", r.status_code)
except Exception as e:
    print("Startup cert test failed:", e)

app = FastAPI()

class QueryRequest(BaseModel):
    question: str

@app.post("/ask")
def ask_query(req: QueryRequest):
    try:
        print("Received request:", req)
        schema = get_schema_description()
        print("Schema:", schema)
        sql = generate_sql(req.question, schema)
        print("Generated SQL:", sql)
        results = execute_sql(sql)
        print("Results:", results)
        return {
            "question": req.question,
            "sql": sql,
            "results": results
        }
    except Exception as e:
        import traceback
        print("Error in /ask:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/schema")
def get_schema():
    try:
        schema = get_schema_description()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ToolCallRequest(BaseModel):
    tool: str
    args: dict

@app.get("/list_tools")
def list_tools():
    return {
        "tools": [
            {
                "name": "run_sql_query",
                "description": "Generate and execute a SQL query based on a natural language question.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The natural language question to convert into a SQL query."
                        }
                    },
                    "required": ["question"]
                }
            },
            {
                "name": "get_schema",
                "description": "Retrieve the current database schema, including tables and views.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    }

@app.post("/call_tool")
def call_tool(request: ToolCallRequest):
    try:
        if request.tool == "run_sql_query":
            question = request.args.get("question")
            if not question:
                raise HTTPException(status_code=400, detail="Missing 'question' in arguments.")
            schema = get_schema_description()
            sql = generate_sql(question, schema)
            results = execute_sql(sql)
            return {
                "result": {
                    "question": question,
                    "sql": sql,
                    "results": results
                }
            }
        elif request.tool == "get_schema":
            schema = get_schema_description()
            return {
                "result": {
                    "schema": schema
                }
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
