# Stage 3: Result Evaluation & Business Answer

## Purpose
Critically analyze comprehensive results to extract clear business answers and actionable insights. **Database results are the authoritative source of truth** - always prioritize database findings over user claims when there are discrepancies.

## Generic Process
1. **Analyze result patterns** using database findings as authoritative source
2. **Identify discrepancies** between user statements and database findings
3. **Extract key insights** relevant to user question, correcting misconceptions where needed
4. **Synthesize accurate business answer** prioritizing database facts over user claims
5. **Provide actionable recommendations** based on verified data

## Evaluation Framework

### Data Quality Assessment
- **Completeness**: Are all expected fields populated?
- **Consistency**: Do values align across related records?
- **Accuracy**: Carefully verify if results match user's original claims and statements
- **Relevance**: Does data directly address user question?
- **Verification**: Cross-check database findings against user's original assumptions or claims

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
- **Direct response** to user question with factual accuracy
- **Clear conclusions** supported by verified data
- **Corrections** when user's original statements don't match database findings
- **Relevant context** utilizing appropriate data fields from database results
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