# Direct Tools Implementation Guide

## Overview

Direct tools provide fast, deterministic SQL execution for pattern-matched queries, bypassing AI SQL generation for performance optimization.

**Key Benefits:**
- 🚀 **Performance**: 100-200ms vs 2-5 second AI workflows
- 💰 **Cost**: Zero AI API calls and tokens
- 🎯 **Reliability**: Consistent SQL execution for known patterns

## Architecture

```
User Query → AI Classification → Pattern Matching → Direct Tool Execution → AI Evaluation → Response
```

**Important**: All direct tools return a consistent `"results"` field, regardless of input/query type.

## Steps to Add New Direct Tool

### 1. Create Tool Function in `direct_mapping_tools.py`

```python
def execute_your_tool_name(user_question: str, classification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Direct SQL execution for [your use case] using AI-extracted entities
    
    Args:
        user_question: User question containing relevant data
        classification: Intent classification result with extracted_entities
        
    Returns:
        dict: Direct lookup results
        
    Raises:
        ValueError: If required entities are not available
        Exception: If SQL execution fails (triggers fallback)
    """
    
    # Extract entities from AI classification
    extracted_entities = classification.get("extracted_entities", {})
    your_entities = extracted_entities.get("your_entity_field")
    
    if not your_entities:
        raise ValueError("No required entities extracted by AI classification")
    
    # Handle multiple inputs (list or comma-separated string)
    if isinstance(your_entities, list):
        items = [p.strip() for p in your_entities if p.strip()]
    else:
        items = [p.strip() for p in your_entities.split(',') if p.strip()]
    
    try:
        start_time = time.time()
        
        # Build efficient SQL query
        item_list = "', '".join(items)
        sql = f"""
        SELECT
            -- Your SQL columns here
            column1 as field1,
            column2 as field2
        FROM
            YourTable
        WHERE 
            your_key_column IN ('{item_list}')
        """
        
        results = execute_sql(sql)
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Track success/failure
        found_items = set()
        if results:
            found_items = {row.get('field1') for row in results if row.get('field1')}
        
        successful_items = [i for i in items if i in found_items]
        failed_items = [i for i in items if i not in found_items]
        
        # CRITICAL: Always return "results" field
        return {
            "success": True,
            "input_items": items,
            "results": results,  # <-- MUST be "results"
            "lookup_type": "multi_item" if len(items) > 1 else "single_item",
            "sql_executed": sql,
            "execution_time_ms": round(execution_time_ms, 2),
            "result_count": len(results) if results else 0,
            "successful_items": successful_items,
            "failed_items": failed_items,
            "extraction_method": "ai_classification"
        }
        
    except Exception as e:
        # Re-raise to trigger fallback to AI workflow
        raise Exception(f"Direct tool SQL execution failed: {str(e)}")
```

### 2. Create Pattern Matcher Function

```python
def _is_your_tool_applicable(user_question: str, classification: dict = None) -> bool:
    """
    AI-powered pattern matching for your tool
    """
    if not classification:
        return False
    
    # Check persona match
    if classification.get("persona") != "your_target_persona":
        return False
    
    # Use AI-extracted entities (no regex!)
    extracted_entities = classification.get("extracted_entities", {})
    has_required_entities = bool(extracted_entities.get("your_entity_field"))
    intent_type = extracted_entities.get("intent_type")
    
    # Match specific intent
    return has_required_entities and intent_type == "your_intent_type"
```

### 3. Register Tool in `direct_tools_registry.py`

```python
# Import your functions
from .direct_mapping_tools import execute_your_tool_name

# Add to appropriate persona section in DIRECT_TOOLS dict
"your_persona": [
    # ... existing tools ...
    {
        "name": "your_tool_name",
        "pattern_matcher": lambda q, classification=None: _is_your_tool_applicable(q, classification),
        "executor": execute_your_tool_name,
        "description": "Direct [description] lookup for [use case]",
        "example_triggers": [
            "example query 1",
            "example query 2"
        ],
        "expected_performance": {
            "avg_execution_time_ms": 150,  # Your expected performance
            "success_rate_target": 0.90,   # Your expected success rate
            "fallback_acceptable": True
        }
    }
]
```

### 4. Update AI Classification in `stage0_intent.md`

Add your entity type and intent:

```markdown
### Entity Extraction Requirements
Always extract these entities for direct tool optimization:
1. **competitor_name**: ...
2. **competitor_product**: ...  
3. **product_codes**: ...
4. **your_new_entity**: Your new entity description (e.g., ["item1", "item2"])
5. **intent_type**: Primary user intent category - one of:
   - "competitor_mapping": ...
   - "specs_lookup": ...
   - "your_new_intent": Description of your new intent type
   - "general_inquiry": ...
```

Add examples:

```markdown
### Example: Your New Tool
**Input**: "your example query here"
**Extracted Entities**:
```json
{
    "competitor_name": null,
    "competitor_product": [],
    "product_codes": [],
    "your_new_entity": ["extracted", "items"],
    "intent_type": "your_new_intent"
}
```

### 5. Test Your Tool

```bash
# Test the pattern matching
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" \
  -d '{"question": "your test query"}'

# Verify direct tool execution in logs:
# - "Direct tool executed successfully: your_tool_name" 
# - "execution_path": "direct_first_with_ai_evaluation"
# - Zero API calls and tokens
```

## Current Direct Tools

### 1. Product Specs Lookup
- **Persona**: `spt_sales_rep`
- **Intent**: `specs_lookup` 
- **Entities**: `product_codes`
- **Table**: `JPNMRSdb_SPT_SALES_DRAPE_SPECS`
- **Returns**: Product specifications

### 2. Competitor Mapping  
- **Persona**: `spt_sales_rep`
- **Intent**: `competitor_mapping`
- **Entities**: `competitor_product`
- **Table**: `JPNMRSdb_SPT_SALES_DRAPE_MAPPING`
- **Returns**: Our equivalent products

## Best Practices

### ✅ Do:
- Always return `"results"` field (consistent interface)
- Use AI-extracted entities (no regex pattern matching)
- Handle both single items and arrays
- Use efficient IN clause queries
- Include comprehensive error handling
- Log execution metrics

### ❌ Don't:
- Use regex patterns for entity extraction
- Return inconsistent field names (`our_equivalents`, `specifications`, etc.)
- Hardcode entity extraction in the tool function
- Skip fallback error handling
- Assume input format (always handle list/string)

## Monitoring

Direct tools automatically log:
- Execution success/failure
- Performance metrics  
- Pattern matching results
- Fallback reasons

Check session logs in `logs/sessions/` for:
```json
{
  "event_type": "REQUEST_FLOW_SUMMARY",
  "data": {
    "execution_path": "direct_first_with_ai_evaluation",
    "direct_tools": "success:your_tool_name"
  }
}
```

## Performance Targets

- **Execution time**: < 200ms
- **Success rate**: > 85%  
- **Token usage**: 0 (direct tools don't call AI APIs)
- **Fallback**: AI workflow handles edge cases gracefully