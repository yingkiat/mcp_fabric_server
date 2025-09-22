# Adding a New Persona with Direct Tool - Complete Guide

This guide walks you through the complete process of adding a new business persona with a corresponding direct tool for performance optimization.

## Overview

A **persona** represents a specific business domain (e.g., Japan SPT, ANZ SPT, Product Planning) with domain-specific knowledge, table schemas, and business context. A **direct tool** provides fast SQL execution (100-200ms) for pattern-matched queries, bypassing AI SQL generation.

## Files Modified

When adding a new persona with direct tool, you'll touch these files:

```
📁 agentic_layer/prompts/
├── 📁 personas/
│   └── 📄 your_new_persona.md                    # NEW - Domain expertise & table schemas
└── 📁 intent/
    └── 📄 stage0_intent.md                       # MODIFIED - Routing logic

📁 mcp_server/tools/
├── 📄 direct_mapping_tools.py                    # MODIFIED - Add executor function
└── 📄 direct_tools_registry.py                   # MODIFIED - Add pattern matcher & registry

📁 docs/
└── 📄 TESTING.md                                 # OPTIONAL - Add test cases
```

## Step-by-Step Implementation

### Step 1: Create Persona Definition

**File**: `agentic_layer/prompts/personas/your_persona_name.md`

Create a new persona file with:

```markdown
# Your Business Persona Name

## Role
Brief description of the business role and responsibilities

## Primary Use Case
Main workflow or business process this persona handles

## Key Tables
- **table_name_1**: Description and purpose
- **table_name_2**: Description and purpose

## Database Schema Understanding

### Primary Table: main_table_name
- **column1**: Description
- **column2**: Description
- **column3**: Description

## Query Patterns & Search Strategy

### Standard Queries
- "Example query pattern 1"
- "Example query pattern 2"

### Business Logic Rules
Explain any specific business rules or processing logic

## SQL Patterns

```sql
-- Example SQL pattern for this persona
SELECT
    column1,
    column2
FROM your_main_table
WHERE conditions
```

## Multi-Stage Execution Strategy
Explain when single-stage vs multi-stage execution is appropriate

## Response Format
- What the persona should return
- How to format business insights

## Business Context
Real-world use cases and scenarios this persona supports
```

### Step 2: Update Routing Logic

**File**: `agentic_layer/prompts/intent/stage0_intent.md`

Add routing rules to classify queries for your new persona:

```markdown
### Competitor Query Detection
**CRITICAL PRIORITY**:
- If the question contains "YOUR_KEYWORD" and "ADDITIONAL_CONTEXT", route to "your_persona_name"
- If the question contains "EXISTING_KEYWORDS", route to existing personas

### Available Personas
Add your new persona to the list with classification criteria
```

**Key Considerations:**
- Use specific keywords that uniquely identify your domain
- Consider geographic, department, or product-specific terms
- Ensure no conflicts with existing persona routing

### Step 3: Create Direct Tool Executor

**File**: `mcp_server/tools/direct_mapping_tools.py`

Add your executor function:

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
            column1,
            column2,
            column3
        FROM
            your_main_table
        WHERE
            your_key_column IN ('{item_list}')
            AND status = 'ACTIVE'
        ORDER BY column1
        """

        results = execute_sql(sql)
        execution_time_ms = (time.time() - start_time) * 1000

        # Track success/failure
        found_items = set()
        if results:
            found_items = {row.get('column1') for row in results if row.get('column1')}

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

### Step 4: Add Pattern Matcher

**File**: `mcp_server/tools/direct_tools_registry.py`

1. **Import your executor**:
```python
from .direct_mapping_tools import execute_competitor_mapping, execute_product_specs_lookup, execute_your_tool_name
```

2. **Add pattern matcher function**:
```python
def _is_your_tool_applicable(user_question: str, classification: dict = None) -> bool:
    """
    AI-powered pattern matching for your tool
    """
    if not classification:
        return False

    # Check persona match
    if classification.get("persona") != "your_persona_name":
        return False

    # Use AI-extracted entities (no regex!)
    extracted_entities = classification.get("extracted_entities", {})
    has_required_entities = bool(extracted_entities.get("your_entity_field"))
    intent_type = extracted_entities.get("intent_type")

    # Match specific intent
    return has_required_entities and intent_type == "your_intent_type"
```

### Step 5: Register in Direct Tools Registry

**File**: `mcp_server/tools/direct_tools_registry.py`

Add to the `DIRECT_TOOLS` dictionary:

```python
"your_persona_name": [
    {
        "name": "your_tool_name",
        "pattern_matcher": lambda q, classification=None: _is_your_tool_applicable(q, classification),
        "executor": execute_your_tool_name,
        "description": "Direct [description] lookup for [use case]",
        "example_triggers": [
            "example query 1",
            "example query 2",
            "example query 3"
        ],
        "expected_performance": {
            "avg_execution_time_ms": 150,  # Your expected performance
            "success_rate_target": 0.90,   # Your expected success rate
            "fallback_acceptable": True
        }
    }
]
```

### Step 6: Update AI Classification (Optional)

**File**: `agentic_layer/prompts/intent/stage0_intent.md`

If you need new entity types, add them to the extraction requirements:

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

## Testing

### Test the Complete Flow

```bash
# Test persona routing and direct tool execution
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" \
  -d '{"question": "your test query with required keywords"}'

# Verify in logs:
# - "Direct tool executed successfully: your_tool_name"
# - "execution_path": "direct_first_with_ai_evaluation"
# - Zero API calls for SQL generation
```

### Validate Pattern Matching

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

### Performance Verification

- **Execution time**: Should be < 200ms
- **Success rate**: Target > 85%
- **Token usage**: 0 (direct tools don't call AI APIs)
- **Fallback**: AI workflow handles edge cases gracefully

## Real-World Example: ANZ SPT Sales Rep

Here's the actual implementation from the ANZ SPT persona:

### 1. Persona File
- **File**: `agentic_layer/prompts/personas/anz_spt_sales_rep.md`
- **Domain**: ANZ competitive product replacement
- **Tables**: `anz_spt_competitor_mapping`, `ANZPRO2EEdb_pt_mstr`

### 2. Routing Logic
```markdown
- If the question contains "ANZ" and "SPT", route to "anz_spt_sales_rep"
```

### 3. Direct Tool
- **Function**: `execute_anz_competitor_mapping`
- **Pattern**: ANZ competitor products + competitor_mapping intent
- **Performance**: ~150ms execution time

### 4. Test Query
```bash
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" \
  -d '{"question": "ANZ SPT: Replace Terumo BD Luer-Lock Syringe 2.5mL with our equivalent"}'
```

## Best Practices

### ✅ Do:
- Always return `"results"` field from direct tools (consistent interface)
- Use AI-extracted entities (no regex pattern matching)
- Handle both single items and arrays in executors
- Use efficient IN clause queries for multiple items
- Include comprehensive error handling with fallback
- Log execution metrics for monitoring

### ❌ Don't:
- Use regex patterns for entity extraction (use AI classification)
- Return inconsistent field names from different tools
- Hardcode entity extraction in the tool function
- Skip fallback error handling
- Assume input format (always handle list/string)
- Create personas without clear business differentiation

## Troubleshooting

### Common Issues

1. **Direct tool not triggering**
   - Check persona routing in `stage0_intent.md`
   - Verify pattern matcher logic
   - Ensure AI extracts required entities

2. **SQL execution failures**
   - Validate table names and column references
   - Check database permissions
   - Test SQL manually first

3. **Performance issues**
   - Use IN clauses for multiple items
   - Avoid complex JOINs in direct tools
   - Monitor execution times

4. **Classification errors**
   - Add more specific keywords for routing
   - Update entity extraction examples
   - Test with various query formats

## Summary

Adding a new persona with direct tool involves:

1. **Define business domain** → Create persona `.md` file
2. **Add routing logic** → Update `stage0_intent.md`
3. **Create fast executor** → Add function to `direct_mapping_tools.py`
4. **Add pattern matching** → Update `direct_tools_registry.py`
5. **Register tool** → Add to `DIRECT_TOOLS` dictionary
6. **Test thoroughly** → Verify performance and accuracy

This approach provides **100-200ms** response times for common queries while maintaining the flexibility of the full AI workflow for complex scenarios.