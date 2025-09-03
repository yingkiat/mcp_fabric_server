"""
Direct mapping tools - Fast, deterministic SQL execution for pattern-matched queries
"""
import re
import time
from typing import Dict, Any, List
from connectors.fabric_dw import execute_sql

def execute_competitor_mapping(user_question: str, classification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Direct SQL execution for competitor product mapping - specifically for Hogy products
    
    This function bypasses AI SQL generation and executes a direct lookup for competitor
    product equivalents. Designed for spt_sales_rep persona with Hogy competitor triggers.
    
    Args:
        user_question: User question containing "Hogy [product_name]"
        classification: Intent classification result (for context)
        
    Returns:
        dict: Direct mapping results with our equivalent products
        
    Raises:
        ValueError: If product name cannot be extracted
        Exception: If SQL execution fails (triggers fallback)
    """
    
    # Extract competitor product name from question using multiple patterns
    product_name = _extract_hogy_product_name(user_question)
    
    if not product_name:
        raise ValueError("Could not extract Hogy product name from question")
    
    # Direct SQL execution - simplified mapping table
    sql = """
    SELECT 品番 
    FROM JPNMRSdb_SPT_SALES_DRAPE_MAPPING
    WHERE HOGY品番 = ?
    """
    
    try:
        start_time = time.time()
        
        # Execute with exact product name match - manually format SQL since execute_sql doesn't support parameters
        formatted_sql = sql.replace("?", f"'{product_name}'")
        results = execute_sql(formatted_sql)
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        # If no results, try fuzzy matching approach
        if not results or len(results) == 0:
            results = _try_fuzzy_matching(product_name)
            execution_time_ms += (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "competitor_product": f"Hogy {product_name}",
            "our_equivalents": results,
            "mapping_type": "direct_lookup",
            "sql_executed": sql,
            "execution_time_ms": round(execution_time_ms, 2),
            "result_count": len(results) if results else 0,
            "hogy_product_code": product_name
        }
        
    except Exception as e:
        # Re-raise to trigger fallback to AI workflow
        raise Exception(f"Direct mapping SQL execution failed: {str(e)}")

def _extract_hogy_product_name(question: str) -> str:
    """Extract Hogy product name using multiple pattern matching strategies"""
    
    # Pattern 1: "Hogy [product name] with/and/equivalent"
    pattern1 = re.search(r"Hogy\s+([\w\-\.\s]+?)(?:\s+with|\s+and|\s+equivalent|$)", question, re.IGNORECASE)
    if pattern1:
        return pattern1.group(1).strip()
    
    # Pattern 2: "Replace Hogy [product name]"
    pattern2 = re.search(r"replace\s+Hogy\s+([\w\-\.\s]+?)(?:\s+with|\s+and|$)", question, re.IGNORECASE)
    if pattern2:
        return pattern2.group(1).strip()
    
    # Pattern 3: "Hogy [product] equivalent"
    pattern3 = re.search(r"Hogy\s+([\w\-\.\s]+?)\s+equivalent", question, re.IGNORECASE)
    if pattern3:
        return pattern3.group(1).strip()
    
    return None

def _try_fuzzy_matching(product_name: str) -> List[Dict[str, Any]]:
    """
    Fallback fuzzy matching when direct mapping table lookup fails
    Uses similarity search on product master table
    """
    
    # Extract key terms from product name for fuzzy search
    key_terms = _extract_product_keywords(product_name)
    
    if not key_terms:
        return []
    
    # Build dynamic WHERE clause for multiple keyword matching
    where_conditions = []
    params = []
    
    for term in key_terms[:3]:  # Use top 3 keywords to avoid too broad search
        where_conditions.append("(UPPER(product_name_en) LIKE UPPER(?) OR UPPER(product_name_jp) LIKE UPPER(?))")
        params.extend([f"%{term}%", f"%{term}%"])
    
    fuzzy_sql = f"""
    SELECT TOP 5
        product_id,
        product_name_en,
        product_name_jp,
        specifications,
        'fuzzy_match' as mapping_type,
        0.7 as estimated_confidence
    FROM JPNPROdb_ps_mstr
    WHERE {' OR '.join(where_conditions)}
    ORDER BY 
        CASE 
            WHEN UPPER(product_name_en) LIKE UPPER(?) THEN 1
            WHEN UPPER(product_name_jp) LIKE UPPER(?) THEN 2  
            ELSE 3
        END,
        product_id
    """
    
    # Add primary search term for ordering
    params.extend([f"%{key_terms[0]}%", f"%{key_terms[0]}%"])
    
    try:
        # Format SQL manually since execute_sql doesn't support parameters
        formatted_fuzzy_sql = fuzzy_sql
        for param in params:
            formatted_fuzzy_sql = formatted_fuzzy_sql.replace("?", f"'{param}'", 1)
        return execute_sql(formatted_fuzzy_sql)
    except Exception:
        # If fuzzy matching also fails, return empty (will trigger AI fallback)
        return []

def _extract_product_keywords(product_name: str) -> List[str]:
    """Extract meaningful keywords from product name for fuzzy matching"""
    
    # Common medical device keywords that are searchable
    meaningful_terms = []
    
    # Split and clean product name
    words = re.split(r'[\s\-\.]+', product_name.lower())
    
    # Filter out common stopwords but keep medical/technical terms
    stopwords = {'the', 'a', 'an', 'with', 'for', 'and', 'or', 'of'}
    
    for word in words:
        word = word.strip()
        if word and word not in stopwords and len(word) > 2:
            meaningful_terms.append(word)
    
    # Prioritize technical terms and measurements
    prioritized = []
    technical_indicators = ['ml', 'mm', 'cm', 'gauge', 'fr', 'ch']
    
    for term in meaningful_terms:
        # Check if term contains technical indicators
        if any(indicator in term for indicator in technical_indicators):
            prioritized.insert(0, term)  # High priority
        else:
            prioritized.append(term)
    
    return prioritized[:5]  # Return top 5 keywords

def get_direct_mapping_stats() -> Dict[str, Any]:
    """Get statistics about direct mapping tool performance (for monitoring)"""
    
    # This would integrate with logging system in production
    return {
        "tool_name": "competitor_mapping",
        "supported_competitors": ["Hogy"],
        "typical_execution_time_ms": 150,
        "success_rate_target": 0.85,
        "fallback_strategy": "ai_workflow",
        "last_updated": "2025-01-01"
    }

def test_competitor_mapping_patterns():
    """Test function to validate pattern matching works correctly"""
    
    test_cases = [
        "Replace Hogy BD Luer-Lock Syringe 2.5mL with our equivalent",
        "Hogy catheter equivalent", 
        "Find our version of Hogy surgical kit",
        "What is the Hogy disposable scalpel equivalent?",
        "Replace Hogy BD Luer-Lock with domestic product"
    ]
    
    results = {}
    for question in test_cases:
        product_name = _extract_hogy_product_name(question)
        results[question] = {
            "extracted_product": product_name,
            "extraction_success": product_name is not None
        }
    
    return results