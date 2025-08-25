# Stage 2: Detailed Analysis

## Purpose
Execute detailed analysis queries using selected items from Stage 1 to gather comprehensive information.

## Generic Process
1. **Use selected items** from intermediate AI processing
2. **Generate detailed queries** to extract complete information
3. **Join related data** from multiple tables as needed
4. **Return comprehensive dataset** for final evaluation

## SQL Generation Guidelines
- Use **specific identifiers** from Stage 1 selections
- **Join multiple tables** to gather related information
- Include **quantitative data** (prices, quantities, metrics)
- **Aggregate or group** data as appropriate for analysis
- **Order results** logically for evaluation

## Context Integration
The persona context provides:
- **Table relationships** and join patterns
- **Key metrics** and fields to retrieve
- **Business calculations** and derived fields
- **Filtering rules** for data quality

## Input Requirements
- **Selected items** from Stage 1 (identifiers, descriptions)
- **Selection reasoning** from intermediate processing
- **User question context** for focused analysis

## Output Requirements
Return comprehensive data with:
- **Primary entity information** (products, customers, transactions)
- **Related entity data** (components, pricing, relationships)
- **Quantitative metrics** (prices, quantities, totals)
- **Categorical information** (types, statuses, classifications)

## Common Patterns
- **Pricing analysis**: Get costs, margins, competitive pricing
- **Component analysis**: Expand BOMs, kit contents, specifications
- **Relationship analysis**: Find related items, alternatives, substitutes
- **Performance analysis**: Metrics, trends, comparisons