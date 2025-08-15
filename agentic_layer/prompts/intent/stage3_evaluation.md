# Stage 3: Result Evaluation & Business Answer

## Purpose
Analyze comprehensive results from Stage 2 to extract clear business answers and actionable insights.

## Generic Process
1. **Analyze result patterns** (duplicates, variations, trends)
2. **Extract key insights** relevant to user question
3. **Synthesize business answer** in domain-appropriate format
4. **Provide actionable recommendations** based on data

## Evaluation Framework

### Data Quality Assessment
- **Completeness**: Are all expected fields populated?
- **Consistency**: Do values align across related records?
- **Accuracy**: Do results match expected patterns?
- **Relevance**: Does data directly address user question?

### Pattern Recognition
- **Duplicates**: Identify and consolidate repeated information
- **Variations**: Understand ranges, alternatives, options
- **Outliers**: Flag unusual values or patterns
- **Trends**: Identify patterns in pricing, quantities, relationships

### Business Logic Application
- **Domain rules**: Apply persona-specific business logic
- **Calculations**: Perform necessary computations (totals, averages, margins)
- **Comparisons**: Evaluate options against criteria
- **Recommendations**: Suggest best choices based on analysis

## Output Requirements

### Business Answer
- **Direct response** to user question
- **Clear conclusions** supported by data
- **Specific values** (prices, quantities, identifiers)
- **Confidence indicators** for recommendations

### Supporting Evidence
- **Key data points** that support conclusions
- **Alternative options** where applicable
- **Limitations or caveats** in the analysis
- **Next steps** or follow-up actions

### Structured Format
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

## Common Evaluation Patterns
- **Competitive analysis**: Best match, pricing comparison, value proposition
- **Product selection**: Optimal choice, trade-offs, specifications
- **Financial analysis**: Costs, margins, ROI, budget impact
- **Operational analysis**: Efficiency, capacity, performance metrics