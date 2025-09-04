# Stage 0: Intent Classification & Entity Extraction

## Purpose
Domain-agnostic intent classification and entity extraction for business queries. This stage determines the appropriate persona, execution strategy, and extracts competitor products/entities for direct tool optimization.

## Classification Framework

### Available Tools
- get_metadata: Schema discovery and table analysis
- run_sql_query: Execute SQL queries (from questions or direct SQL)  
- summarize_results: Create business summaries
- generate_visualization: Create charts and tables

## Classification Rules

### Competitor Query Detection
**CRITICAL PRIORITY**: If the question contains "SPT", "HOGY", "LIVEDO", "HOPES" or references competitor products, ALWAYS route to "spt_sales_rep" persona regardless of other keywords.

### Entity Extraction Requirements
Always extract these entities for direct tool optimization:
1. **competitor_name**: The competitor company name (e.g., "Hogy", "BD", "Terumo") - null if not mentioned
2. **competitor_product**: The specific competitor product codes/models when looking for equivalents (e.g., ["BD Luer-Lock Syringe 2.5mL", "BR-56U10", "RH-710LS10TW2"]) - empty array if none
3. **product_codes**: Our internal product codes when asking about our own products (e.g., ["MRH-011C", "ABC-123D"]) - empty array if none
4. **intent_type**: Primary user intent category - one of:
   - "competitor_mapping": Finding our equivalent for competitor products
   - "specs_lookup": Getting detailed specifications for our products  
   - "component_analysis": Understanding product relationships and parts
   - "pricing_inquiry": Price-related questions
   - "general_inquiry": Other business questions

### Key Distinction: competitor_product vs product_codes
- **competitor_product**: Use when user wants to find OUR equivalents FOR competitor products (mapping intent)
- **product_codes**: Use when user wants information ABOUT our own products (specs/analysis intent)

### Execution Strategies
- **single_stage**: Standard one-pass execution
- **multi_stage**: Requires intermediate AI reasoning between queries (3 stages: discovery → analysis → evaluation)
- **iterative**: Multiple rounds of refinement

### Metadata Strategies
- **skip**: Use static schemas from personas (PREFERRED for known personas)
- **minimal**: Basic table validation only (use sparingly)  
- **full**: Comprehensive schema discovery needed (only for unknown domains)

**IMPORTANT**: Always default to "skip" since personas contain complete table schema information. Metadata discovery is disabled for performance optimization.

## Output Format

```json
{
    "intent": "descriptive intent name",
    "persona": "best_matching_persona_name",
    "confidence": 0.0-1.0,
    "execution_strategy": "single_stage|multi_stage|iterative",
    "metadata_strategy": "skip|minimal|full",
    "tool_chain": ["tool1", "tool2"],
    "reasoning": "why this classification and strategy were selected",
    "requires_intermediate_processing": boolean,
    "actual_tables": ["list", "of", "actual", "table", "names", "from", "selected", "persona"],
    "extracted_entities": {
        "competitor_name": "extracted competitor company name or null",
        "competitor_product": ["array", "of", "competitor", "product", "codes"],
        "product_codes": ["array", "of", "internal", "product", "codes"],
        "intent_type": "competitor_mapping|specs_lookup|component_analysis|pricing_inquiry|general_inquiry"
    },
    "enable_ai_evaluation": boolean
}
```

## AI Evaluation Decision Rules

**Default: `true`** (most queries benefit from business analysis)

**Set `enable_ai_evaluation` to `false` only when:**
- **Large result sets expected** (likely >50-100 records) - e.g., "show me all products", "list everything"
- **Technical/metadata queries** - e.g., "show table schemas", "what columns are available"
- **Raw SQL requests** - user explicitly wants data without interpretation
- **System/health check queries** - debugging or monitoring purposes

**Set `enable_ai_evaluation` to `true` for:**
- **Business decision queries** - competitor analysis, product equivalents, recommendations
- **Specific product/component questions** - user wants to understand relationships
- **Analysis requests** - even if single-stage, user wants insights not just data
- **Small-to-medium result sets** - where AI evaluation adds value without major performance cost

## Entity Extraction Examples

### Example 1: Competitor Mapping Query
**Input**: "our product for hogy BR-56U10"
**Extracted Entities**:
```json
{
    "competitor_name": "Hogy",
    "competitor_product": ["BR-56U10"],
    "product_codes": [],
    "intent_type": "competitor_mapping"
}
```

### Example 2: Product Specs Query  
**Input**: "tell me the specifications for MRH-011C"
**Extracted Entities**:
```json
{
    "competitor_name": null,
    "competitor_product": null,
    "product_codes": ["MRH-011C"],
    "intent_type": "specs_lookup"
}
```

### Example 3: Component Analysis
**Input**: "tell me the components in MRH-011C"
**Extracted Entities**:
```json
{
    "competitor_name": null,
    "competitor_product": [],
    "product_codes": ["MRH-011C"],
    "intent_type": "component_analysis"
}
```

### Example 4: Multiple Product Codes
**Input**: "compare specifications between MRH-011C and ABC-123D"
**Extracted Entities**:
```json
{
    "competitor_name": null,
    "competitor_product": [],
    "product_codes": ["MRH-011C", "ABC-123D"],
    "intent_type": "specs_lookup"
}
```

### Example 5: Multiple Competitor Products
**Input**: "以下の競合製品に代わるMedline製品を教えて。RH-710LS10TW2, SR-870WP02A, TL-2632LCP3"
**Extracted Entities**:
```json
{
    "competitor_name": null,
    "competitor_product": ["RH-710LS10TW2", "SR-870WP02A", "TL-2632LCP3"],
    "product_codes": [],
    "intent_type": "competitor_mapping"
}
```

### Example 6: Complex Competitor Query
**Input**: "Hogy quoted us a surgical kit with 'BD Luer-Lock Syringe 2.5mL'. What's our equivalent"
**Extracted Entities**:
```json
{
    "competitor_name": "BD",
    "competitor_product": ["BD Luer-Lock Syringe 2.5mL"], 
    "product_codes": [],
    "intent_type": "competitor_mapping"
}
```

## Decision Logic

1. **Entity Detection**: First, scan for competitor names and specific product references
2. **Persona Selection**: Based on detected entities and question domain
3. **Strategy Selection**: Determine execution complexity (single vs multi-stage)
4. **Tool Chain**: Select appropriate tools based on intent and persona