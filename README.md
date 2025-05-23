# Fabric SQL Agent MCP Tool

This FastAPI backend exposes your Microsoft Fabric Data Warehouse as an OpenAI MCP-compatible agent tool.

## Features

- **`run_sql_query`**:  
  Accepts a business question in natural language, generates a safe T-SQL query via OpenAI, executes it on your Fabric Warehouse, and returns the results.

- **`get_schema`**:  
  Returns the current schema (tables and views with columns/types) to help the agent understand the data warehouse structure.

- **MCP Compliance**:  
  Implements `/list_tools` and `/call_tool` endpoints per the [OpenAI MCP protocol](https://openai.github.io/openai-agents-python/mcp/).  
  Compatible with OpenAI agent tools and any LLM orchestration system supporting MCP.

## Endpoints

- **`GET /list_tools`**  
  Returns tool metadata and a list of available functions with argument schemas, per MCP spec.

- **`POST /call_tool`**  
  Executes the specified tool/function with arguments. Example input:
  ```json
  {
    "function": "run_sql_query",
    "arguments": { "question": "Show me all invoices for customer 123" }
  }
  ```

  ```json
  {
    "result": {
      "question": "...",
      "sql": "...",
      "results": [...]
    }
  }
  ```

## Usage

- **Start the server**

    python main.py
    (Ensure you have configured your .env for Azure credentials and Fabric connection.)

- **Test discovery**

    curl http://localhost:8000/list_tools

    See available functions/tools.

- **Run a query**

    curl -X POST http://localhost:8000/call_tool \
    -H "Content-Type: application/json" \
    -d '{"function": "run_sql_query", "arguments": {"question": "Show me all invoices for customer 123"}}'

- **Get schema**

    curl -X POST http://localhost:8000/call_tool \
    -H "Content-Type: application/json" \
    -d '{"function": "get_schema", "arguments": {}}'

- **MCP Agent Integration**
    Register this tool’s base URL with any agent platform supporting MCP.

    The agent will auto-discover capabilities via /describe and can call functions via /call.

- **Notes**
    This API is fully backward-compatible with any existing UI or script you have built atop /ask or /schema endpoints.

    Sensitive credentials should be provided only through environment variables or a secured .env file.    

## Configuration

The server requires the following environment variables in a `.env` file located in the project root:

| Variable                | Description                                                      |
|-------------------------|------------------------------------------------------------------|
| FABRIC_SQL_SERVER       | Fully qualified Fabric Data Warehouse server hostname            |
| FABRIC_SQL_DATABASE     | Target database name in Fabric                                   |
| AZURE_CLIENT_ID         | Azure Service Principal client ID (for AAD authentication)       |
| AZURE_CLIENT_SECRET     | Azure Service Principal secret                                   |
| AZURE_TENANT_ID         | Azure tenant (directory) ID                                      |
| AZURE_OPENAI_KEY        | API key for your Azure OpenAI deployment                         |
| AZURE_OPENAI_ENDPOINT   | Endpoint URL for Azure OpenAI (e.g., https://xxxx.openai.azure.com) |
| AZURE_OPENAI_DEPLOYMENT | Deployment name (e.g., "gpt-4o")                                |

### Sample `.env`

```env
FABRIC_SQL_SERVER=jzd3bvvlcs5udln5rq47r4qvqi-qdrgdhglbgcezlr5igxskwv6ki.datawarehouse.fabric.microsoft.com
FABRIC_SQL_DATABASE=unified_data_warehouse
AZURE_CLIENT_ID=<your-azure-service-principal-client-id>
AZURE_CLIENT_SECRET=<your-azure-service-principal-secret>
AZURE_TENANT_ID=<your-azure-tenant-id>
AZURE_OPENAI_KEY=<your-azure-openai-key>
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

### **Summary:**
- **For MCP agent use, only `/list_tools` and `/call_tool` are required.**
- **Remove `/ask` and `/schema` unless you need to support legacy direct integrations.**