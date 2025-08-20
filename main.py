#main.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
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

# Initialize secrets management
try:
    from config.secrets_manager import initialize_config
    config = initialize_config()
    print("✅ Secrets initialized successfully")
    print(f"Using Key Vault: {bool(os.getenv('KEY_VAULT_URL'))}")
except Exception as e:
    print(f"⚠️ Secrets initialization failed: {e}")
    print("Falling back to environment variables")

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

# Serve the test UI with dynamic API URL
@app.get("/")
def serve_ui():
    # Read the HTML template
    with open("test_ui.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Get API URL from environment or default to current server
    api_url = os.getenv("FABRIC_MCP_API_URL", "http://localhost:8000")
    subscription_key = os.getenv("APIM_SUBSCRIPTION_KEY", "YOUR_SUBSCRIPTION_KEY_HERE")
    
    # Replace the hardcoded API_BASE and subscription key with dynamic values
    html_content = html_content.replace(
        "const API_BASE = 'http://localhost:8000';",
        f"const API_BASE = '{api_url}';"
    )
    html_content = html_content.replace(
        "const SUBSCRIPTION_KEY = 'YOUR_SUBSCRIPTION_KEY_HERE';",
        f"const SUBSCRIPTION_KEY = '{subscription_key}';"
    )
    
    return HTMLResponse(content=html_content)

class QueryRequest(BaseModel):
    question: str


class ToolCallRequest(BaseModel):
    tool: str
    args: dict

class AgenticRequest(BaseModel):
    question: str

class PromptUpdateRequest(BaseModel):
    module_name: str
    content: str

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

@app.get("/prompts")
def list_prompts():
    """List all available prompt modules"""
    import os
    prompt_dir = "agentic_layer/prompts"
    prompts = []
    
    try:
        for file in os.listdir(prompt_dir):
            if file.endswith('.md'):
                module_name = file[:-3]  # Remove .md extension
                prompts.append(module_name)
        
        return {"prompts": prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing prompts: {str(e)}")

@app.get("/prompts/{module_name}")
def get_prompt(module_name: str):
    """Get content of a specific prompt module"""
    import os
    prompt_path = f"agentic_layer/prompts/{module_name}.md"
    
    try:
        if not os.path.exists(prompt_path):
            raise HTTPException(status_code=404, detail=f"Prompt module '{module_name}' not found")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "module_name": module_name,
            "content": content,
            "last_modified": os.path.getmtime(prompt_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading prompt: {str(e)}")

@app.put("/prompts/{module_name}")
def update_prompt(module_name: str, request: PromptUpdateRequest):
    """Update a prompt module with backup and validation"""
    import os
    import shutil
    from datetime import datetime
    
    # Validate prompt content
    validation_errors = validate_prompt_content(request.content)
    if validation_errors:
        raise HTTPException(status_code=400, detail=f"Prompt validation failed: {', '.join(validation_errors)}")
    
    prompt_path = f"agentic_layer/prompts/{module_name}.md"
    backup_path = f"agentic_layer/prompts/.backups/{module_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    try:
        # Create backup directory if it doesn't exist
        os.makedirs("agentic_layer/prompts/.backups", exist_ok=True)
        
        # Create backup of existing file if it exists
        if os.path.exists(prompt_path):
            shutil.copy2(prompt_path, backup_path)
        
        # Write new content
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(request.content)
        
        return {
            "success": True,
            "message": f"Prompt module '{module_name}' updated successfully",
            "backup_created": backup_path if os.path.exists(backup_path) else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating prompt: {str(e)}")

def validate_prompt_content(content: str) -> list:
    """Validate prompt content for common issues"""
    errors = []
    
    if not content.strip():
        errors.append("Prompt content cannot be empty")
    
    if len(content) < 50:
        errors.append("Prompt content seems too short (minimum 50 characters)")
    
    if len(content) > 50000:
        errors.append("Prompt content is too long (maximum 50,000 characters)")
    
    # Check for required sections in business prompts
    if "## Role" not in content and "# Role" not in content:
        errors.append("Prompt should include a Role section")
    
    # Check for potentially dangerous content
    dangerous_patterns = ['rm -rf', 'DELETE FROM', 'DROP TABLE', '__import__', 'eval(', 'exec(']
    for pattern in dangerous_patterns:
        if pattern.lower() in content.lower():
            errors.append(f"Potentially dangerous content detected: {pattern}")
    
    return errors

@app.get("/prompts/{module_name}/backups")
def list_prompt_backups(module_name: str):
    """List available backups for a prompt module"""
    import os
    backup_dir = "agentic_layer/prompts/.backups"
    backups = []
    
    try:
        if os.path.exists(backup_dir):
            for file in os.listdir(backup_dir):
                if file.startswith(f"{module_name}_") and file.endswith('.md'):
                    backup_path = os.path.join(backup_dir, file)
                    backups.append({
                        "filename": file,
                        "timestamp": os.path.getmtime(backup_path),
                        "size": os.path.getsize(backup_path)
                    })
        
        return {"module_name": module_name, "backups": sorted(backups, key=lambda x: x['timestamp'], reverse=True)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing backups: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
