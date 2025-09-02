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

def get_model_params(model_name: str, max_tokens: int, temperature: float = 0) -> dict:
    """Get appropriate parameters for different model APIs"""
    params = {}
    
    # GPT-5 and newer models have different parameter requirements
    if 'gpt-5' in model_name.lower() or 'o1' in model_name.lower():
        params["max_completion_tokens"] = max_tokens
        # GPT-5 models don't support temperature=0, only default (1)
        if temperature != 1:
            params["temperature"] = 1  # Force to default
    else:
        # GPT-4o, GPT-4, and older models use max_tokens  
        params["max_tokens"] = max_tokens
        params["temperature"] = temperature
    
    return params

def load_prompt_module(module_name: str) -> str:
    """Load prompt module content from markdown file"""
    prompt_path = f"agentic_layer/prompts/{module_name}.md"
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Prompt module '{module_name}' not found at {prompt_path}"

def get_available_personas() -> Dict[str, str]:
    """Dynamically discover available persona modules"""
    import os
    personas = {}
    personas_dir = "agentic_layer/prompts/personas"
    
    if os.path.exists(personas_dir):
        for file in os.listdir(personas_dir):
            if file.endswith('.md'):
                persona_name = file[:-3]  # Remove .md extension
                # Read first few lines to get persona description
                try:
                    with open(os.path.join(personas_dir, file), 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extract description from markdown (first paragraph after title)
                        lines = content.split('\n')
                        description = "Available persona"
                        for i, line in enumerate(lines):
                            if line.startswith('### Context') or line.startswith('### Role') or (line.startswith('## ') and i > 0):
                                description = lines[i+1:i+3]  # Get next 1-2 lines
                                description = ' '.join([l.strip() for l in description if l.strip()])
                                break
                        personas[persona_name] = description[:100] + "..." if len(description) > 100 else description
                except:
                    personas[persona_name] = "Available persona"
    
    return personas

def load_intent_template(stage: str) -> str:
    """Load generic intent template for multi-stage execution"""
    template_path = f"agentic_layer/prompts/intent/{stage}.md"
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Intent template '{stage}' not found at {template_path}"

def load_persona_module(persona_name: str) -> str:
    """Load persona module content from personas folder"""
    persona_path = f"agentic_layer/prompts/personas/{persona_name}.md"
    try:
        with open(persona_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Persona module '{persona_name}' not found at {persona_path}"

def classify_intent(user_question: str, request_id: str = None) -> Dict[str, Any]:
    """
    Domain-agnostic intent classification and routing
    """
    
    # Get available personas dynamically with sample content for better classification
    available_personas = get_available_personas()
    
    # Pre-load key personas to get actual table names for classification
    persona_context = {}
    for persona_name in available_personas.keys():
        try:
            content = load_persona_module(persona_name)
            # Extract table references from persona
            import re
            tables = re.findall(r'JPNPROdb_\w+', content)
            persona_context[persona_name] = {
                "description": available_personas[persona_name],
                "tables": list(set(tables)),  # Remove duplicates
                "sample_content": content[:300] + "..." if len(content) > 300 else content
            }
        except:
            persona_context[persona_name] = {
                "description": available_personas[persona_name],
                "tables": [],
                "sample_content": "Persona content not available"
            }
    
    # Build enhanced persona list with actual table context
    persona_list = []
    for name, context in persona_context.items():
        tables_str = ", ".join(context["tables"]) if context["tables"] else "No specific tables"
        persona_list.append(f"- {name}: {context['description']}\n  Tables: {tables_str}")
    
    persona_list = "\n".join(persona_list)
    
    classification_prompt = f"""
You are a domain-agnostic intent classifier for a data warehouse assistant.

Available personas (business domain experts):
{persona_list}

Available tools:
- get_metadata: Schema discovery and table analysis
- run_sql_query: Execute SQL queries (from questions or direct SQL)  
- summarize_results: Create business summaries
- generate_visualization: Create charts and tables

Analyze this question: "{user_question}"

Determine:
1. Best matching persona based on question content and domain
2. Execution strategy (single-stage vs multi-stage)
3. Required metadata discovery approach
4. Appropriate tool chain

Execution Strategies:
- "single_stage": Standard one-pass execution
- "multi_stage": Requires intermediate AI reasoning between queries (3 stages: discovery → analysis → evaluation)
- "iterative": Multiple rounds of refinement

Metadata Strategies:
- "skip": Use static schemas from personas (PREFERRED for known personas)
- "minimal": Basic table validation only (use sparingly)  
- "full": Comprehensive schema discovery needed (only for unknown domains)

IMPORTANT: Always default to "skip" since personas contain complete table schema information. Metadata discovery is disabled for performance optimization.

Respond with JSON:
{{
    "intent": "descriptive intent name",
    "persona": "best_matching_persona_name",
    "confidence": 0.0-1.0,
    "execution_strategy": "single_stage|multi_stage|iterative",
    "metadata_strategy": "skip|minimal|full",
    "tool_chain": ["tool1", "tool2"],
    "reasoning": "why this classification and strategy were selected",
    "requires_intermediate_processing": boolean,
    "actual_tables": ["list", "of", "actual", "table", "names", "from", "selected", "persona"]
}}
"""
    
    # Get model-appropriate parameters
    model_params = get_model_params(AZURE_OPENAI_DEPLOYMENT, 500, 0)
    
    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are a JSON classifier. Return ONLY valid JSON, no other text."},
            {"role": "user", "content": classification_prompt}
        ],
        **model_params
    )
    
    # Log API call with session logger
    if request_id:
        try:
            from session_logger import get_session_logger
            session_logger = get_session_logger(request_id, user_question)
            usage = response.usage if hasattr(response, 'usage') else None
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            session_logger.log_api_call("intent_classification", AZURE_OPENAI_DEPLOYMENT, prompt_tokens, completion_tokens)
        except Exception as e:
            pass  # Don't fail if logging fails
    
    try:
        raw_content = response.choices[0].message.content
        
        # Check for empty responses (common with GPT-5 models)
        if not raw_content or raw_content.strip() == "":
            print(f"⚠️ Empty response from {AZURE_OPENAI_DEPLOYMENT}")
            raw_content = "{}"  # Treat as empty JSON to trigger fallback
        
        raw_content = raw_content.strip()
        
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
        
        # Check if we got an empty or incomplete result
        if not result or 'persona' not in result:
            print(f"⚠️ Incomplete JSON response from {AZURE_OPENAI_DEPLOYMENT}: {result}")
            raise ValueError("Missing required fields in classification response")
        
        return result
    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw response: {response.choices[0].message.content}")
        
        # Generic fallback - don't try to guess intent  
        return {
            "intent": "general_query", 
            "persona": "product_planning",
            "confidence": 0.5,
            "execution_strategy": "single_stage",
            "metadata_strategy": "skip",  # Always skip for performance
            "tool_chain": ["run_sql_query", "summarize_results"],
            "reasoning": f"Fallback due to {AZURE_OPENAI_DEPLOYMENT} response issue: {str(e)[:50]}",
            "requires_intermediate_processing": False,
            "actual_tables": ["JPNPROdb_ps_mstr", "JPNPROdb_pt_mstr"]
        }

def execute_tool_chain(user_question: str, classification: Dict[str, Any], request_id: str = None) -> Dict[str, Any]:
    """
    Domain-agnostic tool chain execution with multi-stage support
    """
    from mcp_server.tools.sql_tools import get_metadata, run_sql_query
    from mcp_server.tools.analysis_tools import summarize_results, generate_visualization
    
    # Load the appropriate persona
    persona_content = load_persona_module(classification["persona"])
    
    results = {
        "classification": classification,
        "persona_used": classification["persona"],
        "tool_results": {},
        "final_response": ""
    }
    
    try:
        # TODO: Future - intelligent metadata discovery
        # Handle metadata discovery
        # metadata_strategy = classification.get("metadata_strategy", "full")
        # if metadata_strategy != "skip":
        #     results["tool_results"]["get_metadata"] = handle_metadata_discovery(metadata_strategy, classification)
        
        # Execute based on strategy
        execution_strategy = classification.get("execution_strategy", "single_stage")
        
        if execution_strategy == "multi_stage":
            results["tool_results"] = execute_multi_stage_workflow(
                user_question, classification, persona_content, request_id, results["tool_results"]
            )
        elif execution_strategy == "iterative":
            results["tool_results"] = execute_iterative_workflow(
                user_question, classification, persona_content, request_id, results["tool_results"]
            )
        else:
            # Single-stage execution (current behavior)
            results["tool_results"] = execute_single_stage_workflow(
                user_question, classification, persona_content, request_id, results["tool_results"]
            )
        
        # Generate final response
        results["final_response"] = generate_final_response(user_question, results, persona_content)
        
    except Exception as e:
        results["error"] = str(e)
        results["final_response"] = f"Error executing tool chain: {str(e)}"
    
    return results

def handle_metadata_discovery(strategy: str, classification: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generic metadata discovery handler"""
    from mcp_server.tools.sql_tools import get_metadata
    
    if strategy == "minimal":
        # Use actual tables from classification if available
        actual_tables = classification.get("actual_tables", []) if classification else []
        if actual_tables:
            validation_results = {}
            for table in actual_tables:
                validation_results[table] = get_metadata(table)
            return {"strategy": "minimal", "validation_results": validation_results}
        else:
            return {"strategy": "minimal", "basic_schema": get_metadata()}
    elif strategy == "full":
        return {"strategy": "full", "full_schema": get_metadata()}
    else:
        return {"strategy": "skip"}

def execute_single_stage_workflow(user_question: str, classification: Dict[str, Any], 
                                persona_content: str, request_id: str, existing_results: Dict[str, Any]) -> Dict[str, Any]:
    """Standard single-pass execution"""
    from mcp_server.tools.sql_tools import run_sql_query
    from mcp_server.tools.analysis_tools import summarize_results, generate_visualization
    
    results = existing_results.copy()
    
    enhanced_question = f"""
Context from {classification['persona']} module:
{persona_content}

User question: {user_question}
"""
    
    # Execute tool chain sequentially
    for tool_name in classification["tool_chain"]:
        if tool_name == "run_sql_query":
            results["run_sql_query"] = run_sql_query(question=enhanced_question, request_id=request_id)
        elif tool_name == "summarize_results" and "run_sql_query" in results:
            sql_results = results["run_sql_query"].get("results", [])
            results["summarize_results"] = summarize_results(sql_results, classification["intent"])
        elif tool_name == "generate_visualization" and "run_sql_query" in results:
            sql_results = results["run_sql_query"].get("results", [])
            results["generate_visualization"] = generate_visualization(sql_results, "table", f"Results for: {user_question}")
    
    return results

def execute_multi_stage_workflow(user_question: str, classification: Dict[str, Any], 
                                persona_content: str, request_id: str, existing_results: Dict[str, Any]) -> Dict[str, Any]:
    """Multi-stage execution with intermediate AI reasoning using intent templates"""
    from mcp_server.tools.sql_tools import run_sql_query
    from mcp_server.tools.analysis_tools import summarize_results, generate_visualization
    
    results = existing_results.copy()
    
    # Load generic intent templates
    stage1_template = load_intent_template("stage1_discovery")
    stage2_template = load_intent_template("stage2_analysis")
    stage3_template = load_intent_template("stage3_evaluation")
    
    # Stage 1: Discovery using generic template + persona context
    stage1_context = f"""
{stage1_template}

PERSONA CONTEXT:
{persona_content}

USER QUESTION: {user_question}

STAGE 1 TASK: Execute discovery query to find relevant candidates based on user criteria using persona domain knowledge.
"""
    
    stage1_result = run_sql_query(question=stage1_context, request_id=request_id)
    results["stage1_query"] = stage1_result
    
    # Check if Stage 1 produced useful results
    if stage1_result.get("results") and len(stage1_result["results"]) > 0:
        
        # AI processes Stage 1 results for Stage 2 using persona context
        intermediate_analysis = process_intermediate_results(
            stage1_result["results"], user_question, persona_content
        )
        results["intermediate_analysis"] = intermediate_analysis
        
        # Stage 2: Analysis using generic template + persona context + Stage 1 results
        stage2_context = f"""
{stage2_template}

PERSONA CONTEXT:
{persona_content}

STAGE 1 RESULTS SUMMARY:
{intermediate_analysis.get("summary", "No summary available")}

SELECTED ITEMS FROM STAGE 1:
{intermediate_analysis.get("selected_items", "No items selected")}

USER QUESTION: {user_question}

STAGE 2 TASK: Execute detailed analysis query using selected items from Stage 1 to gather comprehensive information.
"""
        
        stage2_result = run_sql_query(question=stage2_context, request_id=request_id)
        results["stage2_query"] = stage2_result
        
        # Stage 3: Evaluation using generic template + all previous context
        final_data = stage2_result.get("results", [])
        if final_data:
            stage3_context = f"""
{stage3_template}

PERSONA CONTEXT:
{persona_content}

STAGE 1 RESULTS: {len(stage1_result.get("results", []))} candidates found
INTERMEDIATE ANALYSIS: {intermediate_analysis.get("reasoning", "No reasoning available")}
STAGE 2 RESULTS: {len(final_data)} detailed records retrieved

USER QUESTION: {user_question}

STAGE 3 TASK: Evaluate final results to extract clear business answer using persona domain expertise.

Final Data Sample (compressed):
{compress_data_for_llm(final_data, max_records=10) if final_data else "No data available"}
"""
            
            # Log compression stats for Stage 3 with session logger
            if final_data and request_id:
                try:
                    from session_logger import get_session_logger
                    session_logger = get_session_logger(request_id, user_question)
                    compressed_sample = compress_data_for_llm(final_data, max_records=10)
                    compression_stats = get_compression_stats(final_data, compressed_sample)
                    session_logger.log_data_compression(
                        "stage3_evaluation", 
                        compression_stats['original_size'], 
                        compression_stats['compressed_size'], 
                        compression_stats['compression_ratio']
                    )
                except Exception as e:
                    pass  # Don't fail if logging fails
            
            # Use LLM for evaluation (no SQL execution - just analysis)
            evaluation_result = evaluate_final_results(stage3_context, request_id)
            results["stage3_evaluation"] = evaluation_result
        else:
            final_data = stage1_result.get("results", [])
    else:
        # Fallback if Stage 1 failed
        final_data = stage1_result.get("results", [])
    
    # Execute remaining tools on final data
    if "summarize_results" in classification["tool_chain"] and final_data:
        results["summarize_results"] = summarize_results(final_data, classification["intent"])
    
    if "generate_visualization" in classification["tool_chain"] and final_data:
        results["generate_visualization"] = generate_visualization(final_data, "table", f"Results for: {user_question}")
    
    return results

def evaluate_final_results(evaluation_context: str, request_id: str = None) -> Dict[str, Any]:
    """Stage 3: Pure evaluation and analysis without SQL execution"""
    
    evaluation_prompt = f"""
{evaluation_context}

IMPORTANT: DO NOT generate any SQL queries. Your task is to analyze the data provided above and create a business answer.

Based on the data gathered from Stages 1 and 2, provide a comprehensive business evaluation in JSON format.

CRITICAL: Escape all special characters in JSON strings. Use simple ASCII characters where possible to avoid JSON parsing errors.

{{
    "business_answer": "Direct answer to user question - avoid special characters",
    "key_findings": ["finding1", "finding2", "finding3"],
    "recommended_action": "What user should do next",
    "supporting_data": {{
        "primary_values": "key metrics or values",
        "alternatives": "other options if applicable", 
        "confidence": "high|medium|low"
    }},
    "data_quality": "assessment of result reliability",
    "sql_executed": null
}}
"""
    
    try:
        # Get model-appropriate parameters
        model_params = get_model_params(AZURE_OPENAI_DEPLOYMENT, 500, 0)
        
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a business analyst. Analyze data and provide insights. DO NOT generate SQL queries."},
                {"role": "user", "content": evaluation_prompt}
            ],
            **model_params
        )
        
        # Log API call
        if request_id:
            from logging_config import tracker
            usage = response.usage if hasattr(response, 'usage') else None
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            tracker.log_api_call(request_id, AZURE_OPENAI_DEPLOYMENT, prompt_tokens, completion_tokens, "stage3_evaluation")
        
        import json
        raw_content = response.choices[0].message.content.strip()
        
        # Try to extract JSON if wrapped in code blocks
        if '```json' in raw_content:
            json_start = raw_content.find('```json') + 7
            json_end = raw_content.find('```', json_start)
            raw_content = raw_content[json_start:json_end].strip()
        elif '{' in raw_content:
            json_start = raw_content.find('{')
            json_end = raw_content.rfind('}') + 1
            raw_content = raw_content[json_start:json_end]
        
        try:
            result = json.loads(raw_content)
            result["sql_executed"] = None  # Ensure no SQL was executed
            return result
        except json.JSONDecodeError as json_error:
            # Extract key information from raw response instead of generic fallback
            import re
            
            # Try to extract business answer from raw text
            business_answer_match = re.search(r'"business_answer":\s*"([^"]*(?:\\.[^"]*)*)"', raw_content)
            business_answer = business_answer_match.group(1) if business_answer_match else "Analysis completed (JSON parsing issue)"
            
            # Try to extract key findings
            findings_match = re.search(r'"key_findings":\s*\[(.*?)\]', raw_content, re.DOTALL)
            key_findings = []
            if findings_match:
                findings_text = findings_match.group(1)
                findings = re.findall(r'"([^"]*(?:\\.[^"]*)*)"', findings_text)
                key_findings = findings[:5]  # Limit to 5 findings
            
            if not key_findings:
                key_findings = ["Analysis completed successfully", "Data analysis performed on available records"]
            
            # Try to extract recommended action
            action_match = re.search(r'"recommended_action":\s*"([^"]*(?:\\.[^"]*)*)"', raw_content)
            recommended_action = action_match.group(1) if action_match else "Review the analysis results for insights"
            
            # Clean up escaped characters
            business_answer = business_answer.replace('\\"', '"').replace('\\n', ' ')
            recommended_action = recommended_action.replace('\\"', '"').replace('\\n', ' ')
            key_findings = [finding.replace('\\"', '"').replace('\\n', ' ') for finding in key_findings]
            
            return {
                "business_answer": business_answer,
                "key_findings": key_findings,
                "recommended_action": recommended_action,
                "supporting_data": {
                    "primary_values": "Analysis extracted from LLM response",
                    "alternatives": "See raw response for additional details",
                    "confidence": "medium"
                },
                "data_quality": "good - LLM analysis completed",
                "sql_executed": None,
                "raw_response": raw_content[:500] + "..." if len(raw_content) > 500 else raw_content,
                "parsing_note": "JSON parsing failed, extracted from raw text"
            }
        
    except Exception as e:
        return {
            "business_answer": "Error during evaluation stage",
            "key_findings": [f"Evaluation error: {str(e)}"],
            "recommended_action": "Review previous stage results manually",
            "supporting_data": {
                "primary_values": "N/A",
                "alternatives": "N/A", 
                "confidence": "low"
            },
            "data_quality": "poor - evaluation failed",
            "sql_executed": None,
            "error": str(e)
        }

def get_compression_stats(original_records: list, compressed_output: str) -> dict:
    """Calculate compression effectiveness for monitoring"""
    if not original_records:
        return {"compression_ratio": 0, "token_savings": 0}
    
    original_size = len(str(original_records))
    compressed_size = len(compressed_output)
    compression_ratio = (original_size - compressed_size) / original_size if original_size > 0 else 0
    
    return {
        "original_size": original_size,
        "compressed_size": compressed_size, 
        "compression_ratio": round(compression_ratio, 3),
        "token_savings": original_size - compressed_size
    }

def compress_data_for_llm(records: list, max_records: int = 10) -> str:
    """Compress data by extracting common fields and reducing redundancy"""
    if not records or len(records) == 0:
        return "No data available"
    
    # Limit records first
    limited_records = records[:max_records]
    
    if len(limited_records) == 1:
        # Single record - just format cleanly
        record = limited_records[0]
        return ", ".join([f"{k}: {v}" for k, v in record.items() if v is not None])
    
    # Detect common fields across all records
    common_fields = {}
    first_record = limited_records[0]
    
    for key in first_record.keys():
        values = [record.get(key) for record in limited_records]
        unique_values = set(v for v in values if v is not None)
        
        # If all non-null values are identical, it's a common field
        if len(unique_values) <= 1:
            common_fields[key] = list(unique_values)[0] if unique_values else None
    
    # Extract varying fields only
    varying_records = []
    for record in limited_records:
        varying = {k: v for k, v in record.items() 
                  if k not in common_fields and v is not None}
        if varying:  # Only include if there are varying fields
            varying_records.append(varying)
    
    # Format compressed output
    if common_fields:
        common_str = ", ".join([f"{k}: {v}" for k, v in common_fields.items() if v is not None])
        varying_str = " | ".join([
            ", ".join([f"{k}: {v}" for k, v in record.items()]) 
            for record in varying_records[:5]  # Limit varying records too
        ])
        return f"Common: {common_str} | Variants: {varying_str}"
    else:
        # No common fields, just show first few records compactly
        return " | ".join([
            ", ".join([f"{k}: {v}" for k, v in record.items() if v is not None])
            for record in limited_records[:3]
        ])

def process_intermediate_results(stage1_data: list, user_question: str, prompt_context: str) -> Dict[str, Any]:
    """AI processes Stage 1 results to inform Stage 2"""
    
    # Use compressed data representation instead of raw stringification
    data_summary = compress_data_for_llm(stage1_data, max_records=10)
    
    # Log compression stats with session logger
    try:
        from session_logger import get_session_logger
        session_logger = get_session_logger(request_id or "unknown", user_question)
        compression_stats = get_compression_stats(stage1_data, data_summary)
        session_logger.log_data_compression(
            "stage1_intermediate", 
            compression_stats['original_size'], 
            compression_stats['compressed_size'], 
            compression_stats['compression_ratio']
        )
    except Exception as e:
        pass  # Don't fail if logging fails
    
    analysis_prompt = f"""
Analyze these Stage 1 results and select the most relevant items for Stage 2 detailed analysis.

Original question: {user_question}
Context: {prompt_context[:500]}...

Stage 1 Results:
{data_summary}

Provide:
1. Brief summary of findings
2. Select the most relevant 1-3 items for detailed Stage 2 analysis
3. Key identifiers (IDs, part numbers, etc.) to use in Stage 2

Return JSON format:
{{
    "summary": "brief summary of Stage 1 findings",
    "selected_items": ["item1_id", "item2_id"],
    "reasoning": "why these items were selected",
    "stage2_focus": "what Stage 2 should analyze"
}}
"""
    
    try:
        # Get model-appropriate parameters
        model_params = get_model_params(AZURE_OPENAI_DEPLOYMENT, 300, 0)
        
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[{"role": "user", "content": analysis_prompt}],
            **model_params
        )
        
        import json
        return json.loads(response.choices[0].message.content.strip())
    except:
        # Fallback if AI processing fails
        # Use compressed representation for fallback too
        compressed_items = compress_data_for_llm(stage1_data[:3], max_records=3)
        return {
            "summary": f"Found {len(stage1_data)} potential matches",
            "selected_items": compressed_items,
            "reasoning": "Automatic selection due to processing error",
            "stage2_focus": "detailed analysis of selected items"
        }

def execute_iterative_workflow(user_question: str, classification: Dict[str, Any], 
                              persona_content: str, request_id: str, existing_results: Dict[str, Any]) -> Dict[str, Any]:
    """Iterative refinement workflow (future enhancement)"""
    # For now, fallback to multi-stage
    return execute_multi_stage_workflow(user_question, classification, persona_content, request_id, existing_results)

def generate_final_response(user_question: str, results: Dict[str, Any], persona_context: str) -> str:
    """Generate a final business-friendly response using all tool results"""
    
    # Extract key information from tool results
    tool_results = results.get("tool_results", {})
    
    # Check if we have Stage 3 evaluation (multi-stage workflow)
    stage3_eval = tool_results.get("stage3_evaluation", {})
    if stage3_eval and stage3_eval.get("business_answer"):
        # Use Stage 3 business analysis as the primary response
        response_parts = []
        response_parts.append(f"**{stage3_eval['business_answer']}**")
        
        if stage3_eval.get("key_findings"):
            response_parts.append("\n**Key Findings:**")
            for finding in stage3_eval["key_findings"]:
                response_parts.append(f"• {finding}")
        
        if stage3_eval.get("recommended_action"):
            response_parts.append(f"\n**Recommended Action:** {stage3_eval['recommended_action']}")
        
        return "\n".join(response_parts)
    
    # Fallback to single-stage response format
    sql_results = tool_results.get("run_sql_query", {}).get("results", [])
    summary = tool_results.get("summarize_results", {})
    
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