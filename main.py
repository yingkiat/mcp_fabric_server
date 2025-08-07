#main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import time
import json
from starlette.middleware.base import BaseHTTPMiddleware
from mcp_server.tools.sql_tools import run_sql_query, get_metadata
from mcp_server.tools.analysis_tools import summarize_results, generate_visualization
from agentic_layer.routing.intent_router import classify_intent, execute_tool_chain
from logging_config import tracker, generate_request_id

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

# Logging middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = generate_request_id()
        
        # Get request body for logging
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            # Recreate request with body
            request = Request(scope=request.scope, receive=request.receive)
            request._body = body
        
        # Parse user question if available
        user_question = None
        if body:
            try:
                body_data = json.loads(body.decode())
                user_question = body_data.get('question') or body_data.get('args', {}).get('question')
            except:
                pass
        
        # Start tracking
        tracker.start_request(request_id, str(request.url.path), user_question)
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            success = response.status_code < 400
            
            # End tracking
            tracker.end_request(request_id, success)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            tracker.log_error(request_id, e, "request_processing")
            tracker.end_request(request_id, False)
            raise

# Add middleware in correct order
app.add_middleware(LoggingMiddleware)

# Add CORS middleware for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the test UI
@app.get("/")
def serve_ui():
    return FileResponse("test_ui.html")

class QueryRequest(BaseModel):
    question: str


class ToolCallRequest(BaseModel):
    tool: str
    args: dict

class AgenticRequest(BaseModel):
    question: str

@app.get("/list_tools")
def list_tools():
    return {
        "tools": [
            {
                "name": "run_sql_query",
                "description": "Execute SQL query from natural language question or direct SQL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Natural language question to convert to SQL"
                        },
                        "sql": {
                            "type": "string", 
                            "description": "Direct SQL query to execute"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "get_metadata",
                "description": "Get database metadata for specific table or entire schema",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Specific table name (optional)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "summarize_results",
                "description": "Generate business-friendly summary of query results",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "description": "Query result data to summarize"
                        },
                        "context": {
                            "type": "string",
                            "description": "Business context for summary"
                        }
                    },
                    "required": ["data"]
                }
            },
            {
                "name": "generate_visualization",
                "description": "Create charts from structured data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "description": "Data for visualization"
                        },
                        "chart_type": {
                            "type": "string",
                            "description": "Type of chart: table, bar, line, pie"
                        },
                        "title": {
                            "type": "string",
                            "description": "Chart title"
                        }
                    },
                    "required": ["data"]
                }
            }
        ]
    }

@app.post("/call_tool")
def call_tool(request: ToolCallRequest):
    try:
        if request.tool == "run_sql_query":
            result = run_sql_query(**request.args)
            return {"result": result}
        elif request.tool == "get_metadata":
            result = get_metadata(**request.args)
            return {"result": result}
        elif request.tool == "summarize_results":
            result = summarize_results(**request.args)
            return {"result": result}
        elif request.tool == "generate_visualization":
            result = generate_visualization(**request.args)
            return {"result": result}
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp")
def mcp_agentic_endpoint(request: AgenticRequest, http_request: Request):
    """Agentic reasoning endpoint that routes questions through prompt modules and tool chains"""
    request_id = getattr(http_request.state, 'request_id', generate_request_id())
    
    try:
        # Classify intent and determine tool chain
        classification = classify_intent(request.question, request_id)
        tracker.log_classification(request_id, classification)
        
        # Execute the tool chain
        results = execute_tool_chain(request.question, classification, request_id)
        
        return {
            "question": request.question,
            "response": results["final_response"],
            "classification": results["classification"],
            "tool_chain_results": results["tool_results"],
            "request_id": request_id
        }
    except Exception as e:
        tracker.log_error(request_id, e, "mcp_endpoint")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
