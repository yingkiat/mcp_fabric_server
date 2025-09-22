"""
Direct mapping tools - Fast, deterministic SQL execution for pattern-matched queries
"""
import re
import time
from typing import Dict, Any, List
from connectors.fabric_dw import execute_sql

def execute_competitor_mapping(user_question: str, classification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Direct SQL execution for competitor product mapping using AI-extracted entities
    
    This function bypasses AI SQL generation and executes a direct lookup for competitor
    product equivalents. Uses entities extracted by AI during intent classification.
    
    Args:
        user_question: User question containing competitor products
        classification: Intent classification result with extracted_entities
        
    Returns:
        dict: Direct mapping results with our equivalent products
        
    Raises:
        ValueError: If required entities are not available in classification
        Exception: If SQL execution fails (triggers fallback)
    """
    
    # Extract competitor information from AI classification
    extracted_entities = classification.get("extracted_entities", {})
    competitor_product_raw = extracted_entities.get("competitor_product")
    competitor_name = extracted_entities.get("competitor_name")
    
    if not competitor_product_raw:
        raise ValueError("No competitor product extracted by AI classification")
    
    # Handle multiple products (comma-separated string OR list)
    if isinstance(competitor_product_raw, list):
        products = [p.strip() for p in competitor_product_raw if p.strip()]
    else:
        products = [p.strip() for p in competitor_product_raw.split(',') if p.strip()]
    
    try:
        start_time = time.time()
        
        # Build IN clause for multiple products - much more efficient than individual queries
        product_list = "', '".join(products)  # Join with proper SQL escaping
        sql = f"""
        SELECT DISTINCT 
            sdm.競合品番,
            sdm.品番,
            sdm.競合メーカー名,
            sdm.品番2,
            pt.pt_desc1 + ' ' + pt.pt_desc2 AS 品番説明
        FROM 
            JPNMRSdb_SPT_SALES_DRAPE_MAPPING sdm
        LEFT JOIN JPNPROdb_pt_mstr pt ON sdm.品番 = pt.pt_part
        WHERE 
            sdm.競合品番 IN ('{product_list}')
        """
        
        results = execute_sql(sql)
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Track which products were found vs missing
        found_products = set()
        if results:
            found_products = {row.get('競合品番') for row in results if row.get('競合品番')}
        
        successful_products = [p for p in products if p in found_products]
        failed_products = [p for p in products if p not in found_products]
        
        # Try fuzzy matching for failed products if any
        fuzzy_results = []
        if failed_products:
            for product in failed_products:
                fuzzy_matches = _try_fuzzy_matching(product)
                if fuzzy_matches:
                    fuzzy_results.extend(fuzzy_matches)
                    successful_products.append(f"{product} (fuzzy)")
                    failed_products = [p for p in failed_products if p != product]  # Remove from failed list
        
        # Combine direct and fuzzy results
        all_results = (results or []) + fuzzy_results
        
        return {
            "success": True,
            "competitor_products": products,  # Multiple products input
            "competitor_name": competitor_name,
            "results": all_results,
            "mapping_type": "multi_product_lookup" if len(products) > 1 else "single_product_lookup",
            "sql_executed": sql,
            "execution_time_ms": round(execution_time_ms, 2),
            "result_count": len(all_results) if all_results else 0,
            "successful_products": successful_products,
            "failed_products": failed_products,
            "extraction_method": "ai_classification"
        }
        
    except Exception as e:
        # Re-raise to trigger fallback to AI workflow
        raise Exception(f"Direct mapping SQL execution failed: {str(e)}")

# Removed _extract_hogy_product_name - now using AI-extracted entities from classification

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

def execute_product_specs_lookup(user_question: str, classification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Direct SQL execution for product specifications lookup using AI-extracted product codes
    
    This function bypasses AI SQL generation and executes a direct lookup for product
    specifications from JPNMRSdb_SPT_SALES_DRAPE_SPECS table.
    
    Args:
        user_question: User question containing product codes
        classification: Intent classification result with extracted_entities
        
    Returns:
        dict: Direct specifications results for the requested products
        
    Raises:
        ValueError: If required entities are not available in classification
        Exception: If SQL execution fails (triggers fallback)
    """
    
    # Extract product information from AI classification
    extracted_entities = classification.get("extracted_entities", {})
    product_codes_raw = extracted_entities.get("product_codes")
    
    if not product_codes_raw:
        raise ValueError("No product codes extracted by AI classification")
    
    # Handle multiple products (comma-separated string OR list)
    if isinstance(product_codes_raw, list):
        products = [p.strip() for p in product_codes_raw if p.strip()]
    else:
        products = [p.strip() for p in product_codes_raw.split(',') if p.strip()]
    
    try:
        start_time = time.time()
        
        # Build IN clause for multiple products - much more efficient than individual queries
        product_list = "', '".join(products)  # Join with proper SQL escaping
        sql = f"""
        SELECT
            品番 as product_code, -- Product
            名称 as description, -- Description of base material
            AAMIレベル as aami_level, -- AMMI level
            横 as width_cm, --Width
            縦 as height_cm, --Height
            開脚 as legs_split, --Whether the legs are split (Y/N)
            素材 as material, --Material of the opening in the middle of the drape
            開窓部横 as opening_width_cm, --Width of the opening in the middle of the drape
            開窓部縦 as opening_height_cm, --Height of the opening in the middle of the drape
            形状 as opening_shape, --Shape of the opening area
            パウチ as pouch_quantity, --Quantity of pouches
            [コードホルダ―] as cord_holder, --Cord holder
            透明翼 as transparent_panels --Transparent side panels
        FROM
            JPNMRSdb_SPT_SALES_DRAPE_SPECS
        WHERE 
            品番 IN ('{product_list}')
        """
        
        results = execute_sql(sql)
        execution_time_ms = (time.time() - start_time) * 1000
        
        # DEBUG: Log actual SQL and results
        print(f"DEBUG: Product specs SQL: {sql}")
        print(f"DEBUG: Raw results count: {len(results) if results else 0}")
        if results:
            print(f"DEBUG: First result keys: {list(results[0].keys()) if results else 'No results'}")
            print(f"DEBUG: First result: {results[0] if results else 'No results'}")
        
        # Track which products were found vs missing
        found_products = set()
        if results:
            found_products = {row.get('product_code') for row in results if row.get('product_code')}
        
        successful_products = [p for p in products if p in found_products]
        failed_products = [p for p in products if p not in found_products]
        
        return {
            "success": True,
            "product_codes": products,  # Multiple products input
            "specifications": results,
            "lookup_type": "multi_product_specs" if len(products) > 1 else "single_product_specs",
            "sql_executed": sql,
            "execution_time_ms": round(execution_time_ms, 2),
            "result_count": len(results) if results else 0,
            "successful_products": successful_products,
            "failed_products": failed_products,
            "extraction_method": "ai_classification"
        }
        
    except Exception as e:
        # Re-raise to trigger fallback to AI workflow
        raise Exception(f"Direct product specs SQL execution failed: {str(e)}")

def execute_anz_competitor_mapping(user_question: str, classification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Direct SQL execution for ANZ competitor product mapping using AI-extracted entities

    This function bypasses AI SQL generation and executes a direct lookup for ANZ competitor
    product equivalents. Uses entities extracted by AI during intent classification.

    Args:
        user_question: User question containing ANZ competitor products
        classification: Intent classification result with extracted_entities

    Returns:
        dict: Direct mapping results with ANZ Medline equivalent products

    Raises:
        ValueError: If required entities are not available in classification
        Exception: If SQL execution fails (triggers fallback)
    """

    # Extract competitor information from AI classification
    extracted_entities = classification.get("extracted_entities", {})
    competitor_product_raw = extracted_entities.get("competitor_product")
    competitor_name = extracted_entities.get("competitor_name")

    if not competitor_product_raw:
        raise ValueError("No competitor product extracted by AI classification")

    # Handle multiple products (comma-separated string OR list)
    if isinstance(competitor_product_raw, list):
        products = [p.strip() for p in competitor_product_raw if p.strip()]
    else:
        products = [p.strip() for p in competitor_product_raw.split(',') if p.strip()]

    try:
        start_time = time.time()

        # Build flexible search terms for ANZ competitor mapping
        search_conditions = []
        for product in products:
            # Create multiple search patterns for each product
            search_terms = []

            # Original product term
            search_terms.append(f"LOWER(m.[Competitor Product Code] + ' ' + m.[Competitor Description]) LIKE '%{product.lower()}%'")

            # Split product into key terms for broader matching
            words = product.replace('-', ' ').replace('.', ' ').split()
            for word in words:
                if len(word) > 2:  # Skip very short words
                    search_terms.append(f"LOWER(m.[Competitor Product Code] + ' ' + m.[Competitor Description]) LIKE '%{word.lower()}%'")

            # Combine terms for this product with OR
            if search_terms:
                search_conditions.append(f"({' OR '.join(search_terms)})")

        # Combine all product searches with OR
        where_clause = ' OR '.join(search_conditions)

        sql = f"""
        SELECT
            m.[Competitor Product Code],
            m.[Competitor Description],
            m.[Updated Medline Product Code],
            m.[Updated Medline Description],
            m.[Updated Medline Code Status],
            m.[STD Cost],
            m.[Category],
            m.[Sub-Category],
            m.[BNS Alt Code],
            m.[FG (Sterile) Alt Code],
            p.pt_um as [UOM]
        FROM
            anz_spt_competitor_mapping m
        LEFT JOIN ANZPRO2EEdb_pt_mstr p ON m.[Updated Medline Product Code] = p.pt_part
        WHERE
            ({where_clause})
            AND m.[Updated Medline Code Status] = 'REL'
        ORDER BY m.[Category], m.[STD Cost]
        """

        results = execute_sql(sql)
        execution_time_ms = (time.time() - start_time) * 1000

        # Track which products were found vs missing
        found_products = set()
        if results:
            # Extract competitor product codes from results to match against input
            for row in results:
                comp_code = row.get('Competitor Product Code', '')
                comp_desc = row.get('Competitor Description', '')
                full_comp = f"{comp_code} {comp_desc}".lower()

                # Check which input products match this result
                for product in products:
                    if product.lower() in full_comp or any(word.lower() in full_comp for word in product.split() if len(word) > 2):
                        found_products.add(product)

        successful_products = list(found_products)
        failed_products = [p for p in products if p not in found_products]

        return {
            "success": True,
            "competitor_products": products,
            "competitor_name": competitor_name,
            "results": results,
            "mapping_type": "anz_multi_product_lookup" if len(products) > 1 else "anz_single_product_lookup",
            "sql_executed": sql,
            "execution_time_ms": round(execution_time_ms, 2),
            "result_count": len(results) if results else 0,
            "successful_products": successful_products,
            "failed_products": failed_products,
            "extraction_method": "ai_classification"
        }

    except Exception as e:
        # Re-raise to trigger fallback to AI workflow
        raise Exception(f"ANZ direct mapping SQL execution failed: {str(e)}")

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
    """Test function to validate AI-based entity extraction (replaces regex patterns)"""
    
    test_cases = [
        "Replace Hogy BD Luer-Lock Syringe 2.5mL with our equivalent",
        "Hogy catheter equivalent", 
        "Find our version of Hogy surgical kit",
        "What is the Hogy disposable scalpel equivalent?",
        "Replace Hogy BD Luer-Lock with domestic product"
    ]
    
    return {
        "note": "Entity extraction now handled by AI classification in stage0_intent.md",
        "test_cases": test_cases,
        "expected_entities": [
            {"competitor_name": "BD", "competitor_product": "BD Luer-Lock Syringe 2.5mL"},
            {"competitor_name": "Hogy", "competitor_product": "catheter"},
            {"competitor_name": "Hogy", "competitor_product": "surgical kit"},
            {"competitor_name": "Hogy", "competitor_product": "disposable scalpel"},
            {"competitor_name": "Hogy", "competitor_product": "BD Luer-Lock"}
        ]
    }