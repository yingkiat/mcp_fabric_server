# API Response Examples - Execution Strategies

## Overview

This document provides comprehensive examples of API responses for different execution strategies in the Fabric MCP Agent system.

## Single-Stage Execution

### Simple Product Query
**Request**:
```json
POST /mcp
{
    "question": "Show me the specifications for part MRH-011C"
}
```

**Response**:
```json
{
    "classification": {
        "intent": "product_specification_lookup",
        "persona": "product_planning",
        "confidence": 0.95,
        "execution_strategy": "single_stage",
        "metadata_strategy": "skip",
        "tool_chain": ["run_sql_query", "summarize_results"],
        "reasoning": "Simple product lookup requires single query execution"
    },
    "persona_used": "product_planning",
    "tool_chain_results": {
        "run_sql_query": {
            "sql_executed": "SELECT pt.pt_part, pt.pt_desc1, pt.pt_desc2, pt.pt_um FROM JPNPROdb_pt_mstr pt WHERE pt.pt_part = 'MRH-011C'",
            "results": [
                {
                    "pt_part": "MRH-011C",
                    "pt_desc1": "マイクロガイドワイヤー",
                    "pt_desc2": "0.014インチ 180cm",
                    "pt_um": "PC"
                }
            ],
            "row_count": 1,
            "execution_time_ms": 156
        },
        "summarize_results": {
            "summary": "Found 1 product record. Product MRH-011C is a micro guidewire with specifications: 0.014 inch diameter, 180cm length, sold per piece.",
            "row_count": 1,
            "columns": ["pt_part", "pt_desc1", "pt_desc2", "pt_um"],
            "context": "product_specification_lookup"
        }
    },
    "final_response": "**Product MRH-011C is a micro guidewire (マイクロガイドワイヤー) with the following specifications:**\n\n**Key Details:**\n• Part Number: MRH-011C\n• Description: マイクロガイドワイヤー 0.014インチ 180cm\n• Unit of Measure: PC (Per Piece)\n\n**Data Summary**: Found 1 product record",
    "request_id": "single-stage-abc123"
}
```

## Multi-Stage Execution

### Complex Competitive Replacement
**Request**:
```json
POST /mcp
{
    "question": "Replace BD Luer-Lock Syringe 2.5mL with equivalent domestic product and provide competitive pricing analysis"
}
```

**Response**:
```json
{
    "classification": {
        "intent": "competitive_replacement_analysis",
        "persona": "spt_sales_rep",
        "confidence": 0.92,
        "execution_strategy": "multi_stage",
        "metadata_strategy": "skip",
        "tool_chain": ["run_sql_query", "summarize_results"],
        "reasoning": "Competitive replacement requires discovery, analysis, and evaluation stages",
        "requires_intermediate_processing": true,
        "actual_tables": ["JPNPROdb_pt_mstr", "JPNPROdb_ps_mstr", "JPNPROdb_nqpr_mstr"]
    },
    "persona_used": "spt_sales_rep",
    "tool_chain_results": {
        "stage1_query": {
            "sql_executed": "SELECT pt.pt_part, pt.pt_desc1, pt.pt_desc2 FROM JPNPROdb_pt_mstr pt WHERE (pt.pt_desc1 LIKE '%シリンジ%' OR pt.pt_desc1 LIKE '%syringe%') AND (pt.pt_desc1 LIKE '%2.5%' OR pt.pt_desc2 LIKE '%2.5%') AND (pt.pt_desc1 LIKE '%ロック%' OR pt.pt_desc1 LIKE '%lock%' OR pt.pt_desc2 LIKE '%lock%')",
            "results": [
                {
                    "pt_part": "08-139-NPR",
                    "pt_desc1": "ｼﾘﾝｼﾞ2.5ML ﾙｱｰﾛｯｸ (ﾋﾟﾝｸ)",
                    "pt_desc2": ""
                },
                {
                    "pt_part": "08-140-NPR", 
                    "pt_desc1": "ｼﾘﾝｼﾞ2.5ML ﾙｱｰﾛｯｸ (ﾌﾞﾙｰ)",
                    "pt_desc2": ""
                }
            ],
            "row_count": 2,
            "execution_time_ms": 234
        },
        "intermediate_analysis": {
            "summary": "Found 2 potential equivalent products with matching syringe type, volume, and lock mechanism",
            "selected_items": ["08-139-NPR", "08-140-NPR"],
            "reasoning": "Both products match the 2.5mL Luer-Lock syringe specifications, differing only in color",
            "stage2_focus": "detailed pricing and kit inclusion analysis"
        },
        "stage2_query": {
            "sql_executed": "SELECT comp.pt_part AS ComponentPartNumber, comp.pt_desc1 AS ComponentDescription1, comp.pt_desc2 AS ComponentDescription2, kit.pt_part AS KitPartNumber, kit.pt_desc1 AS KitDescription1, kit.pt_desc2 AS KitDescription2, nqpr.nqpr_price AS UnitPrice, ps.ps_qty_per AS QuantityPerKit, CAST(nqpr.nqpr_price * ps.ps_qty_per AS DECIMAL(18, 2)) AS TotalPrice FROM JPNPROdb_pt_mstr comp INNER JOIN JPNPROdb_ps_mstr ps ON ps.ps_comp = comp.pt_part INNER JOIN JPNPROdb_pt_mstr kit ON ps.ps_par = kit.pt_part LEFT JOIN JPNPROdb_nqpr_mstr nqpr ON nqpr.nqpr_comp = comp.pt_part WHERE comp.pt_part IN ('08-139-NPR', '08-140-NPR') AND nqpr.nqpr_price IS NOT NULL ORDER BY kit.pt_part, comp.pt_part",
            "results": [
                {
                    "ComponentPartNumber": "08-139-NPR",
                    "ComponentDescription1": "ｼﾘﾝｼﾞ2.5ML ﾙｱｰﾛｯｸ (ﾋﾟﾝｸ)",
                    "ComponentDescription2": "",
                    "KitPartNumber": "M01ENT004A",
                    "KitDescription1": "ｼﾞｲﾝｷｯﾄ(ESS)",
                    "KitDescription2": "(SAPPOROKOSEI)2/CS",
                    "UnitPrice": "9.44000",
                    "QuantityPerKit": 2,
                    "TotalPrice": 18.88
                },
                {
                    "ComponentPartNumber": "08-140-NPR",
                    "ComponentDescription1": "ｼﾘﾝｼﾞ2.5ML ﾙｱｰﾛｯｸ (ﾌﾞﾙｰ)",
                    "ComponentDescription2": "",
                    "KitPartNumber": "M11OPH004A", 
                    "KitDescription1": "眼科キット",
                    "KitDescription2": "(SAPPOROKOSEI)1/CS",
                    "UnitPrice": "9.44000",
                    "QuantityPerKit": 1,
                    "TotalPrice": 9.44
                }
            ],
            "row_count": 2,
            "execution_time_ms": 187
        },
        "stage3_evaluation": {
            "business_answer": "The equivalent products for BD Luer-Lock Syringe 2.5mL are identified as '08-139-NPR' (Pink) and '08-140-NPR' (Blue). Both feature identical specifications and pricing at ¥9.44 per unit, providing significant cost savings compared to BD's premium pricing.",
            "key_findings": [
                "Two color variants (Pink and Blue) available with identical specifications to BD Luer-Lock 2.5mL",
                "Competitive unit price of ¥9.44 compared to BD's estimated ¥12-15 market price",
                "Products are included in multiple medical kits, providing flexibility for different procedures",
                "Consistent pricing across different kit configurations demonstrates stable supply chain"
            ],
            "recommended_action": "Recommend 08-139-NPR (Pink) as primary replacement due to broader kit inclusion. Highlight 22-37% cost savings compared to BD pricing. Prepare quote with both individual units and kit options for customer flexibility.",
            "supporting_data": {
                "primary_values": {
                    "best_match": "08-139-NPR",
                    "unit_price": "¥9.44",
                    "estimated_savings": "22-37%",
                    "kit_options": ["M01ENT004A", "M11OPH004A"]
                },
                "alternatives": "08-140-NPR available as blue variant with identical pricing",
                "confidence": "high"
            },
            "data_quality": "excellent - comprehensive pricing and kit data available",
            "sql_executed": null
        },
        "summarize_results": {
            "summary": "Found 2 equivalent products with comprehensive pricing analysis. Main recommendation: 08-139-NPR with ¥9.44 unit price, offering significant savings over BD competition.",
            "row_count": 2,
            "columns": ["ComponentPartNumber", "ComponentDescription1", "ComponentDescription2", "KitPartNumber", "KitDescription1", "KitDescription2", "UnitPrice", "QuantityPerKit", "TotalPrice"],
            "context": "competitive_replacement_analysis",
            "sample_record": {
                "ComponentPartNumber": "08-139-NPR",
                "ComponentDescription1": "ｼﾘﾝｼﾞ2.5ML ﾙｱｰﾛｯｸ (ﾋﾟﾝｸ)",
                "UnitPrice": "9.44000"
            }
        }
    },
    "final_response": "**The equivalent products for BD Luer-Lock Syringe 2.5mL are identified as '08-139-NPR' (Pink) and '08-140-NPR' (Blue). Both feature identical specifications and pricing at ¥9.44 per unit, providing significant cost savings compared to BD's premium pricing.**\n\n**Key Findings:**\n• Two color variants (Pink and Blue) available with identical specifications to BD Luer-Lock 2.5mL\n• Competitive unit price of ¥9.44 compared to BD's estimated ¥12-15 market price\n• Products are included in multiple medical kits, providing flexibility for different procedures\n• Consistent pricing across different kit configurations demonstrates stable supply chain\n\n**Recommended Action:** Recommend 08-139-NPR (Pink) as primary replacement due to broader kit inclusion. Highlight 22-37% cost savings compared to BD pricing. Prepare quote with both individual units and kit options for customer flexibility.",
    "request_id": "multi-stage-def456"
}
```

## Error Handling Examples

### Classification Fallback
**Request**:
```json
POST /mcp
{
    "question": "Show me the quantum flux capacitor inventory levels"
}
```

**Response**:
```json
{
    "classification": {
        "intent": "general_query",
        "persona": "product_planning",
        "confidence": 0.9,
        "execution_strategy": "single_stage",
        "metadata_strategy": "skip",
        "tool_chain": ["run_sql_query", "summarize_results"],
        "reasoning": "Fallback to product_planning persona (unknown product type)",
        "requires_intermediate_processing": false,
        "actual_tables": ["JPNPROdb_ps_mstr", "JPNPROdb_pt_mstr"]
    },
    "persona_used": "product_planning",
    "tool_chain_results": {
        "run_sql_query": {
            "sql_executed": "SELECT pt.pt_part, pt.pt_desc1 FROM JPNPROdb_pt_mstr pt WHERE pt.pt_desc1 LIKE '%quantum%' OR pt.pt_desc1 LIKE '%flux%' OR pt.pt_desc1 LIKE '%capacitor%'",
            "results": [],
            "row_count": 0,
            "execution_time_ms": 89,
            "message": "No products found matching the search criteria"
        },
        "summarize_results": {
            "summary": "No products found matching 'quantum flux capacitor'. This item may not exist in the current product catalog.",
            "row_count": 0,
            "columns": [],
            "context": "general_query"
        }
    },
    "final_response": "**No products found matching 'quantum flux capacitor'.**\n\n**Summary**: This item does not appear in the current product catalog.\n\n**Suggestions**: You can also ask about product comparisons, specifications, or part number relationships.",
    "request_id": "error-handling-ghi789"
}
```

### Stage 3 JSON Parsing Fallback
**Response Excerpt**:
```json
{
    "tool_chain_results": {
        "stage3_evaluation": {
            "business_answer": "Analysis completed successfully with extracted insights",
            "key_findings": [
                "Product analysis performed on available data",
                "Pricing information retrieved from multiple sources",
                "Competitive analysis shows favorable positioning"
            ],
            "recommended_action": "Review the detailed analysis results for business insights",
            "supporting_data": {
                "primary_values": "Analysis extracted from LLM response",
                "alternatives": "See raw response for additional details",
                "confidence": "medium"
            },
            "data_quality": "good - LLM analysis completed",
            "sql_executed": null,
            "raw_response": "{\n    \"business_answer\": \"The equivalent product for...",
            "parsing_note": "JSON parsing failed, extracted from raw text"
        }
    }
}
```

## Performance Metrics in Responses

### Timing Information
All responses include performance metadata:

```json
{
    "request_id": "timing-example-jkl012",
    "execution_metrics": {
        "total_duration_ms": 40700,
        "stage_breakdown": {
            "intent_classification": 3400,
            "stage1_execution": 14400, 
            "stage2_execution": 15700,
            "stage3_evaluation": 7100
        },
        "api_calls": 4,
        "sql_queries": 2,
        "tokens_used": 35240
    }
}
```

## Response Format Standards

### Consistent Structure
All responses follow this standard structure:

```json
{
    "classification": { /* Intent classification results */ },
    "persona_used": "string",
    "tool_chain_results": { /* Execution results */ },
    "final_response": "string", 
    "request_id": "string",
    "execution_metrics": { /* Performance data */ }
}
```

### Tool Chain Results Variants

**Single-Stage**:
- `run_sql_query`
- `summarize_results`
- `generate_visualization` (optional)

**Multi-Stage**:
- `stage1_query`
- `intermediate_analysis`
- `stage2_query`
- `stage3_evaluation`
- `summarize_results`

This standardized response format ensures consistent UI rendering and API client compatibility across all execution strategies.