"""
Intent classification and routing for agentic layer
"""
import os
from openai import AzureOpenAI
from typing import Dict, Any, List
import json

# Load environment variables first
from dotenv import load_dotenv
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

def load_prompt_module(module_name: str) -> str:
    """Load prompt module content from markdown file"""
    prompt_path = f"agentic_layer/prompts/{module_name}.md"
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Prompt module '{module_name}' not found at {prompt_path}"

def classify_intent(user_question: str, request_id: str = None) -> Dict[str, Any]:
    """
    Classify user intent and determine appropriate prompt module and tool chain
    """
    
    classification_prompt = f"""
You are an intelligent intent classifier for a Fabric Data Warehouse assistant. 

Available prompt modules and their static schema coverage:
- product_planning: Complete schemas for JPNPROdb_ps_mstr, JPNPROdb_pt_mstr with sample data and proven query patterns
- spt_sales_rep: Anything to do with surgical packs, components, and related queries

Available tools:
- get_metadata: Dynamic schema discovery (costs time/tokens)
- run_sql_query: Execute SQL queries (from questions or direct SQL)  
- summarize_results: Create business-friendly summaries
- generate_visualization: Create charts and tables

Analyze this question: "{user_question}"

Determine:
1. Primary intent and best prompt module
2. Whether static schemas in prompt modules are sufficient 
3. If dynamic metadata discovery is needed

Metadata Strategy Rules:
- "skip": Question fits established patterns, all tables covered by static schemas
- "minimal": Need basic table validation only  
- "full": Novel query, unknown tables, or complex cross-domain analysis

Respond with JSON in this format:
{{
    "intent": "primary domain (e.g., product_planning, components_analysis, etc.)",
    "prompt_module": "module_name",
    "confidence": 0.0-1.0,
    "schema_confidence": "high|medium|low",
    "metadata_strategy": "skip|minimal|full",
    "tool_chain": ["tool1", "tool2", "tool3"],
    "reasoning": "explanation of classification and why this metadata strategy was selected",
    "table_coverage": {{
        "mentioned_tables": ["table1", "table2"],
        "covered_by_static": ["table1"], 
        "needs_discovery": ["table2"]
    }}
}}
"""
    
    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are a JSON classifier. Return ONLY valid JSON, no other text."},
            {"role": "user", "content": classification_prompt}
        ],
        temperature=0,
        max_tokens=500,
    )
    
    # Log API call
    if request_id:
        from logging_config import tracker
        usage = response.usage if hasattr(response, 'usage') else None
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        tracker.log_api_call(request_id, AZURE_OPENAI_DEPLOYMENT, prompt_tokens, completion_tokens, "intent_classification")
    
    try:
        raw_content = response.choices[0].message.content.strip()
        
        # Try to extract JSON if wrapped in code blocks or extra text
        if '```json' in raw_content:
            json_start = raw_content.find('```json') + 7
            json_end = raw_content.find('```', json_start)
            raw_content = raw_content[json_start:json_end].strip()
        elif '{' in raw_content:
            json_start = raw_content.find('{')
            json_end = raw_content.rfind('}') + 1
            raw_content = raw_content[json_start:json_end]
        
        result = json.loads(raw_content)
        return result
    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw response: {response.choices[0].message.content}")
        # Fallback with better reasoning
        return {
            "intent": "product_planning", 
            "prompt_module": "product_planning",
            "confidence": 0.9,
            "schema_confidence": "high",
            "metadata_strategy": "skip",
            "tool_chain": ["run_sql_query", "summarize_results"],
            "reasoning": f"Fallback to product_planning with static schemas (JSON parse error: {str(e)[:50]})",
            "table_coverage": {
                "mentioned_tables": ["JPNPROdb_ps_mstr", "JPNPROdb_pt_mstr"],
                "covered_by_static": ["JPNPROdb_ps_mstr", "JPNPROdb_pt_mstr"],
                "needs_discovery": []
            }
        }

def execute_tool_chain(user_question: str, classification: Dict[str, Any], request_id: str = None) -> Dict[str, Any]:
    """
    Execute the determined tool chain with appropriate prompt context
    """
    from mcp_server.tools.sql_tools import get_metadata, run_sql_query
    from mcp_server.tools.analysis_tools import summarize_results, generate_visualization
    
    # Load the appropriate prompt module
    prompt_content = load_prompt_module(classification["prompt_module"])
    
    results = {
        "classification": classification,
        "prompt_module_used": classification["prompt_module"],
        "tool_results": {},
        "final_response": ""
    }
    
    try:
        # Execute AI-determined metadata strategy first
        metadata_strategy = classification.get("metadata_strategy", "full")
        
        if metadata_strategy == "skip":
            # AI determined static schemas are sufficient
            results["tool_results"]["metadata_decision"] = {
                "strategy": "skip",
                "reasoning": "Static schemas sufficient for this query",
                "schema_confidence": classification.get("schema_confidence", "high")
            }
            
        elif metadata_strategy == "minimal":
            # AI wants basic table validation only
            table_coverage = classification.get("table_coverage", {})
            unknown_tables = table_coverage.get("needs_discovery", [])
            if unknown_tables:
                validation_metadata = {}
                for table in unknown_tables:
                    validation_metadata[table] = get_metadata(table)
                results["tool_results"]["get_metadata"] = {
                    "strategy": "minimal",
                    "validation_results": validation_metadata
                }
            else:
                results["tool_results"]["metadata_decision"] = {
                    "strategy": "minimal_skipped",
                    "reasoning": "No unknown tables found after AI analysis"
                }
                
        elif metadata_strategy == "full":
            # AI requested full discovery (novel/complex queries)
            if classification["intent"] == "product_planning":
                # Get metadata for both product tables
                ps_metadata = get_metadata("JPNPROdb_ps_mstr")
                pt_metadata = get_metadata("JPNPROdb_pt_mstr") 
                results["tool_results"]["get_metadata"] = {
                    "strategy": "full",
                    "ps_mstr": ps_metadata,
                    "pt_mstr": pt_metadata
                }
            else:
                results["tool_results"]["get_metadata"] = {
                    "strategy": "full",
                    "full_schema": get_metadata()
                }
        
        # Execute remaining tool chain
        for tool_name in classification["tool_chain"]:
            
            if tool_name == "get_metadata":
                # Skip - already handled above based on AI strategy
                continue
            
            elif tool_name == "run_sql_query":
                # Use the prompt context to generate better SQL
                enhanced_question = f"""
Context from {classification['prompt_module']} module:
{prompt_content}

User question: {user_question}
"""
                query_result = run_sql_query(question=enhanced_question, request_id=request_id)
                results["tool_results"]["run_sql_query"] = query_result
            
            elif tool_name == "summarize_results":
                # Summarize the SQL results if available
                if "run_sql_query" in results["tool_results"]:
                    sql_results = results["tool_results"]["run_sql_query"].get("results", [])
                    summary = summarize_results(sql_results, classification["intent"])
                    results["tool_results"]["summarize_results"] = summary
            
            elif tool_name == "generate_visualization":
                # Create visualization if we have data
                if "run_sql_query" in results["tool_results"]:
                    sql_results = results["tool_results"]["run_sql_query"].get("results", [])
                    viz = generate_visualization(sql_results, "table", f"Results for: {user_question}")
                    results["tool_results"]["generate_visualization"] = viz
        
        # Generate final response using all tool results
        results["final_response"] = generate_final_response(user_question, results, prompt_content)
        
    except Exception as e:
        results["error"] = str(e)
        results["final_response"] = f"Error executing tool chain: {str(e)}"
    
    return results

def generate_final_response(user_question: str, results: Dict[str, Any], prompt_context: str) -> str:
    """Generate a final business-friendly response using all tool results"""
    
    # Extract key information from tool results
    sql_results = results["tool_results"].get("run_sql_query", {}).get("results", [])
    summary = results["tool_results"].get("summarize_results", {})
    
    if not sql_results:
        return "I wasn't able to retrieve data to answer your question. Please check if the tables are accessible or rephrase your question."
    
    response_parts = []
    
    # Quick answer
    response_parts.append(f"**Answer to: {user_question}**")
    
    # Summary from summarize_results tool
    if summary.get("summary"):
        response_parts.append(f"\n**Summary**: {summary['summary']}")
    
    # Key details (first few records)
    if isinstance(sql_results, list) and sql_results:
        response_parts.append(f"\n**Key Details**:")
        for i, record in enumerate(sql_results[:3]):  # Show first 3 records
            record_str = ", ".join([f"{k}: {v}" for k, v in record.items() if v is not None])
            response_parts.append(f"• Record {i+1}: {record_str}")
    
    # Data summary
    if isinstance(sql_results, list):
        response_parts.append(f"\n**Data Summary**: Found {len(sql_results)} records")
    
    # Suggestions for product planning context
    if "product_planning" in results.get("classification", {}).get("intent", ""):
        response_parts.append("\n**Suggestions**: You can also ask about product comparisons, specifications, or part number relationships.")
    
    return "\n".join(response_parts)