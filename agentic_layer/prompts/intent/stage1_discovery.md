# Stage 1: Discovery & Matching

## Purpose
Execute initial discovery queries to find potential matches or candidates based on user criteria.

## Generic Process
1. **Extract key search criteria** from user question using persona context
2. **Generate focused discovery query** to find relevant items
3. **Return candidates** for intermediate AI selection

## SQL Generation Guidelines
- Focus on **broad matching** to capture potential candidates
- Use **flexible search criteria** (LIKE patterns, multiple alternatives)
- **Limit results** (TOP 10-20) for efficient processing
- **Include key identifiers** and descriptive fields for AI evaluation

## Context Integration
The persona context provides:
- **Domain-specific terminology** and search patterns
- **Table schemas** and column mappings
- **Business rules** for filtering and matching

## Output Requirements
Return structured data with:
- **Primary identifiers** (part numbers, IDs, codes)
- **Descriptive information** for AI evaluation
- **Key attributes** relevant to the matching criteria

## Error Handling
- If no matches found, broaden search criteria
- Include alternative search terms from persona context
- Ensure query syntax matches available table schema