"""
Analysis and visualization tools for MCP server
"""
import json
from typing import List, Dict, Any

def summarize_results(data: List[Dict[str, Any]], context: str = ""):
    """
    MCP Tool: Generate business-friendly summary of query results
    """
    try:
        if not data or not isinstance(data, list):
            return {"summary": "No data to summarize", "context": context}
        
        # Basic statistics
        row_count = len(data)
        
        if row_count == 0:
            return {"summary": "Query returned no results", "context": context}
        
        # Get column names and types
        columns = list(data[0].keys()) if data else []
        
        # Generate summary
        summary_parts = [
            f"Found {row_count} record{'s' if row_count != 1 else ''}",
            f"Columns: {', '.join(columns)}"
        ]
        
        # Add context-specific insights
        if "product" in context.lower():
            summary_parts.append("Use this data for product planning and inventory decisions")
        elif "sales" in context.lower():
            summary_parts.append("Review for sales trends and performance analysis")
        
        return {
            "summary": ". ".join(summary_parts),
            "row_count": row_count,
            "columns": columns,
            "context": context,
            "sample_record": data[0] if data else None
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "context": context
        }

def generate_visualization(data: List[Dict[str, Any]], chart_type: str = "table", title: str = ""):
    """
    MCP Tool: Generate visualization configuration from data
    """
    try:
        if not data or not isinstance(data, list):
            return {"error": "No data provided for visualization"}
        
        columns = list(data[0].keys()) if data else []
        
        if chart_type.lower() == "table":
            return {
                "type": "table",
                "title": title or "Data Table",
                "config": {
                    "columns": columns,
                    "rows": data[:20],  # Limit to first 20 rows for display
                    "total_rows": len(data)
                }
            }
        
        elif chart_type.lower() in ["bar", "line", "pie"]:
            # For charts, we need to identify numeric columns
            numeric_columns = []
            text_columns = []
            
            if data:
                for col in columns:
                    sample_value = data[0].get(col)
                    if isinstance(sample_value, (int, float)):
                        numeric_columns.append(col)
                    else:
                        text_columns.append(col)
            
            return {
                "type": chart_type.lower(),
                "title": title or f"{chart_type.title()} Chart",
                "config": {
                    "data": data[:10],  # Limit for chart performance
                    "x_axis": text_columns[0] if text_columns else columns[0],
                    "y_axis": numeric_columns[0] if numeric_columns else columns[1] if len(columns) > 1 else columns[0],
                    "available_columns": {
                        "numeric": numeric_columns,
                        "text": text_columns
                    }
                }
            }
        
        else:
            return {"error": f"Unsupported chart type: {chart_type}. Supported types: table, bar, line, pie"}
            
    except Exception as e:
        return {
            "error": str(e),
            "chart_type": chart_type
        }