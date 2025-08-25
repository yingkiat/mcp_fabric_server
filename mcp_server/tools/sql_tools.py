"""
SQL execution and metadata tools for MCP server
"""
import os
from openai import AzureOpenAI
from connectors.fabric_dw import execute_sql, get_table_metadata, get_all_schema
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure OpenAI config
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

client = AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-02-15-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

def generate_sql_from_question(question: str, schema_context: str = None, request_id: str = None) -> str:
    """Generate SQL from natural language question using schema context"""
    
    if not schema_context:
        # Get full schema if no specific context provided
        schema = get_all_schema()
        table_descriptions = []
        for table, cols in schema.items():
            col_descriptions = [f"{col['name']} {col['type']}" for col in cols]
            table_descriptions.append(f"Table: {table} ({', '.join(col_descriptions)})")
        schema_context = "\n".join(table_descriptions)
    
    prompt = f"""
You are an expert SQL assistant for a Microsoft Fabric Data Warehouse. Given the schema:

{schema_context}

User question: "{question}"

Write a correct, safe T-SQL query that answers the question.
- Use only tables and columns that exist in the schema
- Include proper JOINs when multiple tables are needed
- Use TOP clause for limiting results when appropriate
- Return ONLY the SQL query, nothing else.
"""
    
    # Import the model params helper
    from agentic_layer.routing.intent_router import get_model_params
    model_params = get_model_params(AZURE_OPENAI_DEPLOYMENT, 512, 0)
    
    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}],
        **model_params
    )
    
    # Log API call
    if request_id:
        from logging_config import tracker
        usage = response.usage if hasattr(response, 'usage') else None
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        tracker.log_api_call(request_id, AZURE_OPENAI_DEPLOYMENT, prompt_tokens, completion_tokens, "sql_generation")
    
    sql = response.choices[0].message.content.strip()
    # Clean up any code block formatting
    sql = re.sub(r"```[\s\S]*?```", lambda m: m.group(0).replace('```sql', '').replace('```', '').strip(), sql)
    
    return sql

def run_sql_query(question: str = None, sql: str = None, request_id: str = None):
    """
    MCP Tool: Execute SQL query from natural language question or direct SQL
    """
    try:
        if sql:
            # Direct SQL execution
            final_sql = sql
        elif question:
            # Generate SQL from natural language
            final_sql = generate_sql_from_question(question, request_id=request_id)
        else:
            raise ValueError("Either 'question' or 'sql' parameter is required")
        
        # Execute the query with timing
        import time
        start_time = time.time()
        results = execute_sql(final_sql)
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Log SQL execution
        if request_id:
            from logging_config import tracker
            result_count = len(results) if isinstance(results, list) else results.get('rows_affected', 0)
            tracker.log_sql_query(request_id, final_sql, execution_time_ms, result_count)
        
        return {
            "sql_executed": final_sql,
            "results": results,
            "row_count": len(results) if isinstance(results, list) else results.get('rows_affected', 0)
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "sql_attempted": final_sql if 'final_sql' in locals() else None
        }

def get_metadata(table_name: str = None):
    """
    MCP Tool: Get database metadata - either for specific table or all tables
    """
    try:
        if table_name:
            # Get specific table metadata
            metadata = get_table_metadata(table_name)
            return {
                "metadata_type": "table_specific",
                "table_metadata": metadata
            }
        else:
            # Get all schema information
            schema = get_all_schema()
            return {
                "metadata_type": "full_schema",
                "schema": schema,
                "table_count": len(schema)
            }
            
    except Exception as e:
        return {
            "error": str(e),
            "table_name": table_name
        }