# Testing Guide - Fabric MCP Agent

This document provides comprehensive testing procedures for the direct-first architecture with AI fallback capabilities.

## 🧪 Test Cases Overview

### Architecture Validation Tests
- **Direct Tool Performance**: Fast exact-match queries
- **AI Fallback Logic**: Complex queries that require AI workflow
- **Entity Extraction**: AI-based competitor product identification
- **Evaluation Toggle**: Smart AI evaluation for single-stage queries

## 🖥️ Web UI Test Cases

### Test Button 1: "Complex AI Query (Fallback)"
**Query**: `Hogy quoted us a surgical kit with BD Luer-Lock Syringe 2.5mL. What's our equivalent?`

**Expected Flow**:
1. ✅ AI extracts entities: `{"competitor_product": "BD Luer-Lock Syringe 2.5mL"}`  
2. ✅ Direct tool attempts exact match → finds no results
3. ✅ **Fallback to AI workflow** (multi-stage: discovery → analysis → evaluation)
4. ✅ UI displays beautiful business analysis with findings and recommendations
5. ✅ **Validates**: Fallback logic + entity extraction + multi-stage AI evaluation

**Success Criteria**:
- Response includes `"execution_path": "ai_workflow_fallback"`
- UI shows business analysis section (not just raw table)
- Multiple syringe products found and analyzed
- Stage3 evaluation provides business recommendations

### Test Button 2: "Direct Tool Query"  
**Query**: `what's our product for hogy BR-56U10`

**Expected Flow**:
1. ✅ AI extracts entities: `{"competitor_product": "BR-56U10"}`
2. ✅ Direct tool finds exact match in mapping table  
3. ✅ **Direct execution** (sub-second response)
4. ✅ UI shows results with optional AI evaluation
5. ✅ **Validates**: Direct tool performance + AI evaluation toggle

**Success Criteria**:
- Response includes `"execution_path": "direct_first_with_ai_evaluation"`
- Fast execution time (<1 second)
- Exact product match returned
- Optional business analysis based on `enable_ai_evaluation` setting

## 📝 Manual Test Commands

### Test 1: Complex Fallback Scenario
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"question": "Hogy quoted us a surgical kit with BD Luer-Lock Syringe 2.5mL. What'\''s our equivalent"}'
```

**Expected Response Structure**:
```json
{
  "classification": {
    "persona": "spt_sales_rep",
    "execution_strategy": "multi_stage", 
    "extracted_entities": {
      "competitor_name": "BD",
      "competitor_product": "BD Luer-Lock Syringe 2.5mL"
    }
  },
  "tool_chain_results": {
    "execution_path": "ai_workflow_fallback",
    "stage1_query": {...},
    "stage2_query": {...}, 
    "stage3_evaluation": {
      "business_answer": "...",
      "key_findings": [...],
      "recommended_action": "..."
    }
  }
}
```

### Test 2: Direct Tool Performance
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"question": "what'\''s our product for hogy BR-56U10"}'
```

**Expected Response Structure**:
```json
{
  "classification": {
    "persona": "spt_sales_rep",
    "execution_strategy": "single_stage",
    "extracted_entities": {
      "competitor_name": "Hogy", 
      "competitor_product": "BR-56U10"
    },
    "enable_ai_evaluation": true
  },
  "tool_chain_results": {
    "execution_path": "direct_first_with_ai_evaluation",
    "direct_tool_execution": {
      "success": true,
      "tool_used": "competitor_mapping",
      "execution_time_ms": "<200"
    },
    "stage3_evaluation": {...}
  }
}
```

## 🔍 Performance Benchmarks

### Direct Tool Performance Targets
- **Execution time**: <200ms for exact matches
- **Success rate**: >85% for known competitor products  
- **Fallback rate**: <15% (only for unknown/complex products)

### AI Workflow Performance
- **Stage 1 (Discovery)**: <3 seconds
- **Stage 2 (Analysis)**: <4 seconds  
- **Stage 3 (Evaluation)**: <2 seconds
- **Total multi-stage**: <10 seconds end-to-end

## 🛠️ Debugging Test Failures

### Common Issues & Solutions

#### 1. Direct Tool Not Triggered
**Symptom**: Query goes to AI workflow instead of direct tool
**Check**: Pattern matcher in `direct_tools_registry.py`
```python
"pattern_matcher": lambda q: bool(re.search(r"Hogy\s+[\w\-\.\s]+", q, re.IGNORECASE))
```

#### 2. Entity Extraction Failure  
**Symptom**: `extracted_entities` field missing or incorrect
**Check**: AI classification in `stage0_intent.md` template
**Fix**: Improve entity extraction examples and rules

#### 3. Fallback Not Working
**Symptom**: Direct tool returns "no results" instead of falling back
**Check**: Logic in `execute_tool_chain()` around line 246
```python
if direct_data and len(direct_data) > 0:
    # Use direct results
else:
    # Should fallback to AI workflow
```

#### 4. UI Not Showing Business Analysis
**Symptom**: Only raw table displayed, no business insights
**Check**: Response contains `stage3_evaluation` field
**Check**: UI logic in `displayAgenticResults()` function

## 📊 Test Results Tracking

### Session Logging
All tests are automatically logged with session IDs. View logs:
```bash
python view_session.py                    # List recent sessions
python view_session.py <session_id>       # View detailed trace
ls logs/sessions/                          # Browse all session files
```

### Performance Monitoring
Monitor direct tool vs AI workflow usage:
- Check execution paths in session logs
- Track fallback rates and performance metrics
- Identify opportunities for new direct tools

## 🚀 Continuous Testing

### Pre-Deployment Checklist
- [ ] Both test buttons work in UI
- [ ] Manual curl commands return expected structure
- [ ] Performance benchmarks met
- [ ] No regression in existing functionality
- [ ] Session logging captures all test scenarios

### Regression Testing
Run these tests after any changes to:
- Intent classification logic
- Direct tool implementations  
- Entity extraction rules
- Fallback mechanisms