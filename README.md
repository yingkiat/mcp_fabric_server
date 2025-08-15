# fabric-mcp-agent

**🆕 Enhanced MVP with Multi-Stage Intelligence** - A complete two-layer system combining an MCP-compliant server with advanced multi-stage agentic AI reasoning for Microsoft Fabric Data Warehouse access.

## 🎯 MVP Status: **ENHANCED** ✅

**🆕 Major Update**: Now features intelligent multi-stage execution with discovery → analysis → evaluation workflows for complex business intelligence queries.

## 🔷 Architecture Overview

### Layer 1: Fabric DW MCP Server
Standards-compliant MCP server with 4 complete tools providing clean abstractions over Fabric Data Warehouse operations with full Azure AD authentication.

### Layer 2: **🆕 Multi-Stage Agentic Reasoning Engine**
Advanced intelligent system with **3 execution strategies**:
- **Single-Stage**: Simple queries → Standard tool chain
- **🆕 Multi-Stage**: Complex queries → Discovery → Analysis → Evaluation
- **🆕 Iterative**: Advanced queries → Refinement loops (future)

**🆕 Separation of Concerns Architecture**:
- **Intent Templates**: Domain-agnostic execution patterns (`agentic_layer/prompts/intent/`)
- **Persona Modules**: Business domain expertise (`agentic_layer/prompts/personas/`)  
- **Runtime Integration**: Dynamic combination for context-aware execution

## 🚀 Production Features

### ✅ Complete MCP Tools
- **`run_sql_query`**: Execute SQL from natural language questions or direct SQL with full error handling
- **`get_metadata`**: Retrieve comprehensive table schemas, sample data, and relationships  
- **`summarize_results`**: Generate business-friendly summaries with actionable insights
- **`generate_visualization`**: Create formatted data tables and chart configurations

### ✅ **🆕 Advanced Multi-Stage Intelligence**
- **Intelligent Execution Strategy**: Automatic selection between single-stage and multi-stage workflows
- **🆕 3-Stage Discovery Process**: Discovery → Analysis → Evaluation with AI-driven transitions
- **🆕 Domain-Agnostic Templates**: Reusable execution patterns that work across all business domains
- **🆕 Persona-Driven Context**: Business expertise modules for domain-specific knowledge
- **🆕 Pure Business Analysis**: Stage 3 provides structured insights without SQL execution
- **Enhanced JSON Parsing**: Robust handling of complex business responses with intelligent fallbacks
- **Azure OpenAI Caching**: Automatic response optimization for repeated queries

### ✅ Enterprise Features
- **Comprehensive Logging**: JSON-structured logs with request tracking and performance metrics
- **Performance Monitoring**: Real-time dashboard with session-based analytics
- **Error Tracking**: Full error context with automated recovery mechanisms
- **Security**: Azure AD authentication with read-only database access

## 🔄 **🆕 Multi-Stage Execution Flow**

**Enhanced intelligent query processing with adaptive execution strategies:**

### Single-Stage Flow (Simple Queries)
```
User: "Show me specifications for MRH-011C"
↓
Intent Classification → Single-Stage Strategy
↓
Load Persona: product_planning.md
↓
SQL Generation + Execution → Results
```

### **🆕 Multi-Stage Flow (Complex Queries)**
```
User: "Replace BD Luer-Lock Syringe 2.5mL with equivalent domestic product and pricing"
↓
Intent Classification → Multi-Stage Strategy + spt_sales_rep persona
↓
Stage 1: Discovery
  Template: stage1_discovery.md + Persona Context
  → Find candidate products matching criteria
↓
AI Intermediate Processing
  → Analyze Stage 1 results → Select best matches
↓
Stage 2: Analysis  
  Template: stage2_analysis.md + Selected Candidates
  → Get detailed pricing and specifications
↓
Stage 3: Evaluation
  Template: stage3_evaluation.md + All Previous Data
  → Pure business analysis (NO SQL) → Structured insights
```

**🆕 Key Innovation**: Domain-agnostic templates + business personas = context-aware execution

## 📋 API Endpoints

### MCP Standard Endpoints
- **`GET /list_tools`** - Returns all available MCP tools with schemas
- **`POST /call_tool`** - Execute specific MCP tool with arguments

### Agentic Intelligence Endpoint  
- **`POST /mcp`** - Full agentic reasoning with intent classification and tool chaining

## 🧪 Quick Start & Testing

### 1. Start the Server
```bash
python main.py
```
(Ensure `.env` is configured with Azure credentials)

### 2. Test MCP Tools Discovery
```bash
curl http://localhost:8000/list_tools
```

### 3. Test Individual MCP Tools
```bash
# Get table metadata
curl -X POST http://localhost:8000/call_tool -H "Content-Type: application/json" \
-d '{"tool": "get_metadata", "args": {"table_name": "JPNPROdb_ps_mstr"}}'

# Execute SQL query
curl -X POST http://localhost:8000/call_tool -H "Content-Type: application/json" \
-d '{"tool": "run_sql_query", "args": {"question": "Show me active products"}}'
```

### 4. **🆕 Test Multi-Stage Intelligence (Recommended)**
```bash
# Simple query (single-stage execution)
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" \
-d '{"question": "tell me the components in MRH-011C"}'

# 🆕 Complex query (multi-stage execution)
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" \
-d '{"question": "Replace BD Luer-Lock Syringe 2.5mL with equivalent domestic product and pricing"}'

# 🆕 Multi-stage product analysis
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" \
-d '{"question": "Analyze components and pricing for MRH-011C and recommend optimization opportunities"}'
```

### 5. Access the Web UI
```bash
# Open your browser and visit:
http://localhost:8000
```

## 🎯 **🆕 Enhanced Response Examples**

### Single-Stage Response (Simple Query)
```json
{
  "classification": {
    "intent": "product_specification_lookup",
    "persona": "product_planning", 
    "execution_strategy": "single_stage",
    "confidence": 0.95
  },
  "tool_chain_results": {
    "run_sql_query": {"results": [...]},
    "summarize_results": {...}
  },
  "final_response": "**Product MRH-011C specifications:**..."
}
```

### **🆕 Multi-Stage Response (Complex Query)**
```json
{
  "classification": {
    "intent": "competitive_replacement_analysis",
    "persona": "spt_sales_rep",
    "execution_strategy": "multi_stage",
    "confidence": 0.92
  },
  "tool_chain_results": {
    "stage1_query": {"results": [...]},
    "intermediate_analysis": {"selected_items": ["08-139-NPR"]},
    "stage2_query": {"results": [...]},
    "stage3_evaluation": {
      "business_answer": "Equivalent product identified: 08-139-NPR...",
      "key_findings": ["22-37% cost savings", "Multiple kit options"],
      "recommended_action": "Recommend 08-139-NPR as primary replacement...",
      "confidence": "high"
    }
  },
  "final_response": "**Equivalent products identified with 22-37% cost savings...**"
}
```

## 🌐 **🆕 Enhanced Production Web UI**

- **🆕 Multi-Stage Result Rendering**: Structured business analysis display with confidence indicators
- **🆕 Business Analysis Section**: Clear presentation of Stage 3 evaluation with findings and recommendations
- **🆕 Progressive Disclosure**: Primary insights first, detailed data on demand
- **🆕 Smart Result Detection**: Automatic detection of single-stage vs multi-stage responses
- **Enhanced Data Tables**: Interactive SQL results with sortable columns and hover effects
- **Prompt Management**: Live editing of persona modules with automatic backup
- **Real-time Testing**: All execution strategies accessible through responsive interface
- **Quick Test Buttons**: Pre-built queries for both simple and complex business scenarios

## Configuration

The server requires the following environment variables in a `.env` file located in the project root:

| Variable                | Description                                                      |
|-------------------------|------------------------------------------------------------------|
| FABRIC_SQL_SERVER       | Fully qualified Fabric Data Warehouse server hostname            |
| FABRIC_SQL_DATABASE     | Target database name in Fabric                                   |
| AZURE_CLIENT_ID         | Azure Service Principal client ID (for AAD authentication)       |
| AZURE_CLIENT_SECRET     | Azure Service Principal secret                                   |
| AZURE_TENANT_ID         | Azure tenant (directory) ID                                      |
| AZURE_OPENAI_KEY        | API key for your Azure OpenAI deployment                         |
| AZURE_OPENAI_ENDPOINT   | Endpoint URL for Azure OpenAI (e.g., https://xxxx.openai.azure.com) |
| AZURE_OPENAI_DEPLOYMENT | Deployment name (e.g., "gpt-4o")                                |

### Sample `.env`

```env
FABRIC_SQL_SERVER=jzd3bvvlcs5udln5rq47r4qvqi-qdrgdhglbgcezlr5igxskwv6ki.datawarehouse.fabric.microsoft.com
FABRIC_SQL_DATABASE=unified_data_warehouse
AZURE_CLIENT_ID=<your-azure-service-principal-client-id>
AZURE_CLIENT_SECRET=<your-azure-service-principal-secret>
AZURE_TENANT_ID=<your-azure-tenant-id>
AZURE_OPENAI_KEY=<your-azure-openai-key>
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

## 📊 **🆕 Enhanced Performance Monitoring**

### **🆕 Multi-Stage Performance Analysis**
**Current Baseline**: 40.7s total execution time

| Stage | Duration | Operations | Optimization Target |
|-------|----------|------------|-------------------|
| Intent Classification | 3.4s (8.3%) | LLM routing | Caching patterns |
| Stage 1: Discovery | 14.4s (35.4%) | SQL generation + execution | **50%+ reduction** |
| Stage 2: Analysis | 15.7s (38.5%) | SQL generation + execution | **50%+ reduction** |
| Stage 3: Evaluation | 7.1s (17.4%) | Pure LLM analysis | Prompt optimization |

### Real-time Dashboard
```bash
python performance_dashboard.py
```

### **🆕 Enhanced Metrics Output**
```
MCP AGENT PERFORMANCE DASHBOARD - MULTI-STAGE ANALYTICS
================================================================================

EXECUTION STRATEGY BREAKDOWN
Single-Stage Queries: 60% (avg 12.8s)
Multi-Stage Queries: 40% (avg 40.7s)

STAGE-LEVEL PERFORMANCE
Stage 1 Discovery: 14.4s avg
Stage 2 Analysis: 15.7s avg  
Stage 3 Evaluation: 7.1s avg
SQL Operations: 74% of total time

OPTIMIZATION OPPORTUNITIES
High Impact: SQL generation caching (60-70% reduction potential)
Medium Impact: Parallel processing (20-30% reduction)
```

## 🚀 **🆕 Enhanced Production Deployment**

This enhanced MVP is ready for production deployment with:
- ✅ **🆕 Multi-stage intelligent execution** with adaptive strategy selection
- ✅ **🆕 Structured business analysis** with confidence indicators and recommendations
- ✅ **🆕 Domain-agnostic architecture** for rapid business domain expansion
- ✅ **🆕 Enhanced UI rendering** with progressive disclosure and business insights
- ✅ Full error handling and recovery with intelligent JSON parsing fallbacks
- ✅ Comprehensive logging and monitoring with stage-level performance analytics
- ✅ Performance optimization with AI caching and clear optimization roadmap
- ✅ Security best practices implemented
- ✅ Scalable architecture for extension

## 📚 **🆕 Comprehensive Documentation**

- **[DESIGN_ARCHITECTURE.md](DESIGN_ARCHITECTURE.md)** - Complete system architecture with multi-stage workflow details
- **[CLAUDE.md](CLAUDE.md)** - Development guide with enhanced testing commands and prompt structure
- **[agentic_layer/prompts/intent/README.md](agentic_layer/prompts/intent/README.md)** - Intent template framework documentation
- **[UI_DOCUMENTATION.md](UI_DOCUMENTATION.md)** - Enhanced web interface with multi-stage result rendering
- **[API_RESPONSE_EXAMPLES.md](API_RESPONSE_EXAMPLES.md)** - Complete API response examples for all execution strategies
- **[PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md)** - Detailed optimization roadmap with specific targets and implementation phases

**🎯 Ready for Enterprise**: Complete documentation, performance analysis, and optimization roadmap for production scaling.