"""
Direct Tools Registry - Performance optimization through pattern-matched fast execution
"""
import re
from typing import Dict, List, Callable, Any
from .direct_mapping_tools import execute_competitor_mapping

def get_direct_tools_for_persona(persona: str) -> List[Dict[str, Any]]:
    """Get applicable direct tools based on persona"""
    return DIRECT_TOOLS.get(persona, [])

def get_all_direct_tools() -> Dict[str, List[Dict[str, Any]]]:
    """Get complete direct tools registry"""
    return DIRECT_TOOLS

# Registry of direct tools organized by persona
DIRECT_TOOLS = {
    "spt_sales_rep": [
        {
            "name": "competitor_mapping",
            "pattern_matcher": lambda q: bool(re.search(r"Hogy\s+[\w\-\.\s]+", q, re.IGNORECASE)),
            "executor": execute_competitor_mapping,
            "description": "Direct competitor product mapping for Hogy products",
            "example_triggers": [
                "Replace Hogy BD Luer-Lock Syringe 2.5mL with our equivalent",
                "Hogy catheter equivalent",
                "Find our version of Hogy surgical kit"
            ],
            "expected_performance": {
                "avg_execution_time_ms": 200,
                "success_rate_target": 0.85,
                "fallback_acceptable": True
            }
        }
        # Future tools:
        # {
        #     "name": "simple_pricing", 
        #     "pattern_matcher": lambda q: re.match(r"price for \w+(-\w+)*$", q.lower()),
        #     "executor": execute_pricing_lookup,
        #     "description": "Direct single product pricing queries"
        # }
    ],
    
    "product_planning": [
        # Future tools for product planning persona:
        # {
        #     "name": "component_lookup",
        #     "pattern_matcher": lambda q: bool(re.search(r"components?\s+(?:in|for)\s+[\w\-]+$", q, re.I)),
        #     "executor": execute_component_lookup,
        #     "description": "Direct component relationship queries"
        # }
    ]
}

def validate_direct_tool_config(tool_config: Dict[str, Any]) -> List[str]:
    """Validate direct tool configuration for required fields"""
    errors = []
    
    required_fields = ["name", "pattern_matcher", "executor", "description"]
    for field in required_fields:
        if field not in tool_config:
            errors.append(f"Missing required field: {field}")
    
    # Validate pattern_matcher is callable
    if "pattern_matcher" in tool_config:
        if not callable(tool_config["pattern_matcher"]):
            errors.append("pattern_matcher must be callable")
    
    # Validate executor is callable
    if "executor" in tool_config:
        if not callable(tool_config["executor"]):
            errors.append("executor must be callable")
    
    return errors

def test_pattern_matcher(persona: str, tool_name: str, test_questions: List[str]) -> Dict[str, Any]:
    """Test pattern matcher against sample questions"""
    tools = get_direct_tools_for_persona(persona)
    tool = next((t for t in tools if t["name"] == tool_name), None)
    
    if not tool:
        return {"error": f"Tool {tool_name} not found for persona {persona}"}
    
    results = {}
    for question in test_questions:
        try:
            matches = tool["pattern_matcher"](question)
            results[question] = {"matches": matches, "error": None}
        except Exception as e:
            results[question] = {"matches": False, "error": str(e)}
    
    return {
        "tool_name": tool_name,
        "persona": persona, 
        "test_results": results,
        "success_rate": sum(1 for r in results.values() if r["matches"]) / len(results)
    }

def get_registry_stats() -> Dict[str, Any]:
    """Get statistics about the direct tools registry"""
    stats = {
        "total_personas": len(DIRECT_TOOLS),
        "total_tools": sum(len(tools) for tools in DIRECT_TOOLS.values()),
        "personas": {}
    }
    
    for persona, tools in DIRECT_TOOLS.items():
        stats["personas"][persona] = {
            "tool_count": len(tools),
            "tool_names": [tool["name"] for tool in tools]
        }
    
    return stats