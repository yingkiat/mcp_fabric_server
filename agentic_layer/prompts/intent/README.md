# Intent Templates - Multi-Stage Execution Framework

## Overview

Intent templates provide **domain-agnostic execution patterns** for the multi-stage agentic workflow. These templates define **how** to execute each stage, while persona modules define **what** domain knowledge to apply.

## Template Architecture

### 🎯 Stage 1: Discovery (`stage1_discovery.md`)
**Purpose**: Find candidate records using broad search patterns

**Generic Approach**:
- Initial exploration and filtering
- Cast wide net to capture potential matches
- Focus on key identifiers and search terms
- Applicable to any domain (products, customers, orders, inventory)

**Common Patterns**:
- Keyword-based searching with LIKE operators
- Multiple search criteria with OR logic
- Fuzzy matching for product names/descriptions
- Category-based filtering

**Example Use Cases**:
- Product discovery: Find products similar to competitor items
- Customer analysis: Identify customers by criteria
- Order analysis: Find orders matching patterns
- Inventory lookup: Locate parts by specifications

### 📊 Stage 2: Analysis (`stage2_analysis.md`)
**Purpose**: Gather comprehensive details on selected candidates

**Generic Approach**:
- Deep-dive analysis on filtered results from Stage 1
- Join multiple tables for complete picture
- Collect detailed attributes, relationships, and metrics
- Cross-reference data for validation

**Common Patterns**:
- Multi-table joins for comprehensive data
- Aggregations and calculations
- Detailed attribute collection
- Relationship mapping between entities

**Example Use Cases**:
- Product analysis: Get pricing, components, specifications
- Customer analysis: Full profile with order history
- Order analysis: Complete order details with line items
- Inventory analysis: Stock levels, locations, costs

### 🧠 Stage 3: Evaluation (`stage3_evaluation.md`)
**Purpose**: Generate business insights and recommendations

**Critical Constraint**: **NO SQL EXECUTION** - Pure analysis only

**Generic Approach**:
- Analyze data patterns from Stages 1 & 2
- Extract key business insights
- Generate actionable recommendations
- Assess confidence and data quality

**Output Structure**:
```json
{
    "business_answer": "Direct answer to user question",
    "key_findings": ["finding1", "finding2", "finding3"],
    "recommended_action": "What user should do next",
    "supporting_data": {
        "primary_values": "key metrics",
        "alternatives": "other options",
        "confidence": "high|medium|low"
    },
    "data_quality": "assessment of result reliability"
}
```

## Template Integration with Personas

### Runtime Combination
```
Intent Template (Generic "How") + Persona Knowledge (Domain "What") = Context-Aware Execution
```

**Example Integration**:
- **Stage 1 Template** provides generic discovery patterns
- **Product Planning Persona** provides table names (JPNPROdb_pt_mstr) and product-specific logic
- **Combined Context** generates product discovery query with domain expertise

### Execution Flow
1. **Intent Classification** determines `multi_stage` strategy
2. **Persona Selection** chooses domain expert (e.g., `spt_sales_rep`)
3. **Template Loading** loads generic stage templates
4. **Context Combination** merges template + persona for each stage
5. **Stage Execution** runs with combined context

## Template Design Principles

### Domain Agnostic
- Templates work with any business domain
- No hardcoded table names or specific business logic
- Generic patterns that adapt to persona context

### Modular and Reusable
- Each stage template can be updated independently
- New personas automatically benefit from template improvements
- Consistent execution patterns across all domains

### AI-Optimized
- Designed for LLM consumption and generation
- Clear instructions for each stage objective
- Structured output requirements for downstream processing

### Extensible Framework
- Easy to add new stage types (e.g., `stage4_validation`)
- Support for different execution strategies
- Future support for iterative and refinement workflows

## Benefits of Template Architecture

### Separation of Concerns
- **Templates**: Execution methodology
- **Personas**: Domain expertise
- **Router**: Strategy selection and orchestration

### Scalability
- Add new personas without touching execution logic
- Improve execution patterns without updating domain knowledge
- Support new domains instantly with existing templates

### Maintainability
- Single point of update for execution improvements
- Clear responsibility boundaries
- Consistent behavior across all personas

### Performance Optimization
- Templates can be optimized for SQL generation patterns
- Generic patterns enable better caching opportunities
- Standardized stage transitions improve predictability

## Future Enhancements

### Advanced Stage Types
- **Validation Stage**: Data quality checks and validation
- **Refinement Stage**: Iterative query improvement
- **Comparison Stage**: Side-by-side analysis patterns

### Conditional Execution
- Skip stages based on data quality or completeness
- Parallel stage execution for performance
- Dynamic stage sequencing based on results

### Template Versioning
- Version control for template evolution
- A/B testing for template effectiveness
- Rollback capabilities for template changes

This intent template system provides a robust, scalable foundation for multi-stage business intelligence workflows that can adapt to any domain while maintaining consistent execution patterns.