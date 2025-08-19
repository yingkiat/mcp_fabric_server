# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**fabric-mcp-agent**: A two-layer system combining an MCP-compliant server with an agentic AI reasoning layer for Microsoft Fabric Data Warehouse access.

### 🔷 Layer 1: Fabric DW MCP Server
Standards-compliant MCP server that self-declares tools and provides clean abstractions over Fabric Data Warehouse operations.

### 🔷 Layer 2: Agentic Reasoning Layer  
Intelligent multi-stage execution system that interprets business intent, selects appropriate personas, and dynamically chains MCP tools through discovery → analysis → evaluation workflows for enriched business insights.

## Target Architecture

```
fabric_mcp_project/
├── mcp_server/           # MCP tool declarations and FastAPI endpoints
│   ├── tools/           # Python logic for each MCP tool
├── agentic_layer/
│   ├── routing/         # Intent classifier and multi-stage execution
│   ├── prompts/
│   │   ├── intent/      # Generic stage templates (discovery, analysis, evaluation)
│   │   └── personas/    # Domain-specific business contexts (*.md)
│   ├── memory/          # Session context management
├── connectors/
│   └── fabric_dw.py     # SQL access and metadata reader
├── config/
│   └── secrets_manager.py       # Key Vault integration
├── tests/
├── main.py
├── azure-pipelines.yml  # Azure DevOps CI/CD pipeline
├── Dockerfile           # Container image definition
├── docker-compose.yml   # Local development with Docker
└── .dockerignore        # Docker build exclusions
```

## Development Commands

### Local Development
```bash
# Start the combined MCP + Agentic server
python main.py

# Install dependencies
pip install -r requirements.txt

# Test MCP endpoints
curl http://localhost:8000/list_tools
curl -X POST http://localhost:8000/call_tool -H "Content-Type: application/json" -d '{"tool": "run_sql_query", "arguments": {"sql": "SELECT TOP 10 * FROM sales"}}'

# Test agentic layer endpoint (recommended - uses prompt hints)
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"question": "tell me the components in MRH-011C"}'

# Test individual MCP tools
curl -X POST http://localhost:8000/call_tool -H "Content-Type: application/json" -d '{"tool": "get_metadata", "args": {"table_name": "JPNPROdb_ps_mstr"}}'

# Test with component analysis context (uses prompt hints automatically)
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"question": "What are the specifications for MRH-011C?"}'

# Test competitive replacement (Japanese sales rep use case)
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"question": "Replace Terumo BD Luer-Lock Syringe 2.5mL with our equivalent product and give me pricing"}'

# Test surgical kit analysis
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"question": "Customer wants to replace competitor surgical kit with components: BD Luer-Lock Syringe 2.5mL, Sterile Gauze Pack, Disposable Scalpel. Find our equivalents with pricing."}'

# Access Web UI for interactive testing
open http://localhost:8000

# Test new multi-stage execution and prompt management
curl http://localhost:8000/prompts                                    # List available personas and intent templates
curl http://localhost:8000/prompts/personas/product_planning          # View specific persona content
curl -X PUT http://localhost:8000/prompts/personas/product_planning \ # Update persona with validation
  -H "Content-Type: application/json" \
  -d '{"module_name": "product_planning", "content": "# Updated Role..."}'

# Test multi-stage competitive replacement
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"question": "Replace BD Luer-Lock Syringe 2.5mL with equivalent domestic product and provide pricing comparison"}'

# Test multi-stage product analysis  
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"question": "Analyze the components and pricing structure for MRH-011C and recommend optimization opportunities"}'

# Debug and monitoring commands
python view_session.py                                                     # List recent session logs
python view_session.py 1                                                   # View detailed session trace
ls logs/sessions/                                                          # List all session files
```

### Docker Development
```bash
# Build and run with Docker Compose
docker-compose up --build

# Build Docker image manually
docker build -t fabric-mcp-agent .

# Run Docker container with environment variables
docker run -p 8000:8000 --env-file .env fabric-mcp-agent

# Test containerized endpoints
curl http://localhost:8000/list_tools
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"question": "tell me about products"}'
```

### Azure DevOps CI/CD Deployment
```bash
# Push to Azure DevOps to trigger pipeline
git add .
git commit -m "Deploy to Azure Container Apps"
git push origin main

# Pipeline automatically:
# 1. Builds Docker image and pushes to ACR
# 2. Deploys to Azure Container Apps with Key Vault integration
# 3. Tests deployment health

# Test deployed endpoints (after pipeline completes)
curl https://fabric-mcp-agent.azurecontainerapps.io/list_tools
curl -X POST https://fabric-mcp-agent.azurecontainerapps.io/mcp -H "Content-Type: application/json" -d '{"question": "tell me about products"}'
```

## MCP Tool Specifications

The server exposes 4 core MCP tools with complete input/output schemas:

### `run_sql_query`
- **Purpose**: Executes validated, parameterized SQL queries
- **Security**: Read-only access, SQL injection protection
- **Input**: SQL string, optional parameters
- **Output**: Result sets with column metadata

### `get_metadata` 
- **Purpose**: Returns comprehensive table schema information
- **Input**: `table_name` (string)
- **Output**: Column descriptions, data types, relationships, lineage

### `summarize_results`
- **Purpose**: Business-friendly summarization of query results  
- **Input**: Raw data array/JSON
- **Output**: Executive summary with key insights

### `generate_visualization`
- **Purpose**: Creates charts from structured data
- **Input**: Data + chart type (bar, line, pie)
- **Output**: Visualization configuration/embed code

## 🆕 Multi-Stage Agentic Flow Architecture

### 3-Stage Execution Strategy
The system intelligently determines execution strategy based on query complexity:

1. **Single-Stage**: Simple queries → Standard tool chain
2. **Multi-Stage**: Complex queries → Discovery → Analysis → Evaluation  
3. **Iterative**: Advanced queries → Refinement loops (future)

### Multi-Stage Flow Process
1. **User Input** → "Replace BD Luer-Lock Syringe 2.5mL with equivalent product and pricing"
2. **Intent Classification** → Routes to `spt_sales_rep` persona + determines `multi_stage` strategy
3. **Stage 1: Discovery** → Generic intent template + persona context → Find candidate products
4. **AI Intermediate Processing** → Analyze Stage 1 results → Select best matches
5. **Stage 2: Analysis** → Detailed query for selected candidates → Get comprehensive data  
6. **Stage 3: Evaluation** → Pure LLM business analysis → No SQL execution
7. **Output** → Structured business answer with findings, recommendations, and confidence

### Enhanced Context Integration
```
User Question + Persona Domain Knowledge + Generic Intent Templates → Multi-Stage Execution
```

**Key Innovation**: 
- **Domain-agnostic intent templates** work with any business context
- **Persona-specific knowledge** provides table schemas and business rules  
- **AI-driven stage transitions** optimize query complexity and results

### Key Components

#### 🆕 Multi-Stage Routing Agent (`agentic_layer/routing/`)
- Classifies business intent and determines execution strategy (`single_stage`, `multi_stage`, `iterative`)
- Selects appropriate personas from `agentic_layer/prompts/personas/*.md`
- Loads generic intent templates from `agentic_layer/prompts/intent/*.md`
- Executes 3-stage workflow with AI-driven stage transitions
- Implements robust JSON parsing with intelligent fallbacks

#### 🆕 Intent Templates (`agentic_layer/prompts/intent/`)
Domain-agnostic stage execution frameworks:

- `stage1_discovery.md` - **Discovery Query Patterns**
  - Generic approach to finding candidate records
  - Applicable to any domain (products, customers, orders, etc.)
  - Focuses on broad search patterns and initial filtering

- `stage2_analysis.md` - **Detailed Analysis Strategies**  
  - Deep-dive query patterns for comprehensive data gathering
  - Cross-reference and relationship analysis
  - Detailed attribute and metric collection

- `stage3_evaluation.md` - **Business Analysis Framework**
  - Pure evaluation and insight generation (no SQL execution)
  - Structured business answer format with findings and recommendations
  - Confidence assessment and data quality evaluation

#### Persona Modules (`agentic_layer/prompts/personas/*.md`)
Domain-specific business contexts and expertise:

- `product_planning.md` - **Product Master Data Analysis**
  - Tables: JPNPROdb_ps_mstr, JPNPROdb_pt_mstr
  - Use cases: Component analysis, product specifications, part relationships
  - Works with all execution strategies (single-stage or multi-stage)

- `spt_sales_rep.md` - **Competitive Replacement Specialist** (Japan Market)
  - **Multi-stage native**: Designed for discovery → analysis → evaluation workflow
  - **Core capability**: Replace competitor quotes with equivalent domestic products
  - **Real-world example**: "BD Luer-Lock Syringe 2.5mL" → "ｼﾘﾝｼﾞ2.5ML ﾛｯｸ" with competitive pricing
  - **Tables integrated**: JPNPROdb_pt_mstr, JPNPROdb_ps_mstr, JPNPROdb_nqpr_mstr, JPNPROdb_sod_det
  - **AI matching**: Semantic product matching with pricing analysis

**🆕 Separation of Concerns:**
- **Intent Templates**: Generic execution patterns (how to execute stages)
- **Personas**: Domain expertise and business knowledge (what to execute)
- **Runtime Integration**: Combined dynamically for context-aware multi-stage execution

#### Memory Management (`agentic_layer/memory/`)
- Session context preservation
- Query history and refinement tracking
- Cross-query relationship mapping

## Current Implementation Status

**✅ PRODUCTION MVP COMPLETE**:
- FastAPI server with full MCP compliance (`/list_tools`, `/call_tool`, `/mcp`) 
- All 4 MCP tools fully implemented with error handling and logging
- **🆕 Multi-stage agentic execution** with discovery → analysis → evaluation workflows
- **🆕 Intelligent execution strategy selection** (single-stage vs multi-stage)
- **🆕 Separation of concerns**: Generic intent templates + domain-specific personas
- Azure AD authentication with secure Fabric DW access
- **🆕 Enhanced Web UI** with multi-stage result rendering and business analysis display
- **🆕 Token Usage Optimization** with data compression (50-80% reduction in token usage)
- **🆕 Session-based logging system** - complete session traces for easy debugging
- Azure OpenAI caching optimization with robust JSON parsing

**🚀 Ready for Production Extension**:
- **🆕 Scalable intent template system** (domain-agnostic execution patterns)
- **🆕 Extensible persona architecture** (easy addition of new business domains)
- **🆕 Token optimization with data deduplication** (targeting 50-80% cost reduction)
- **🆕 Session-based debugging** with complete timeline traces in `logs/sessions/`

## Configuration

Environment variables required in `.env`:

```bash
# Fabric Data Warehouse Connection
FABRIC_SQL_SERVER=your-fabric-server.datawarehouse.fabric.microsoft.com
FABRIC_SQL_DATABASE=your_database_name

# Azure Authentication  
AZURE_CLIENT_ID=your-service-principal-id
AZURE_CLIENT_SECRET=your-service-principal-secret
AZURE_TENANT_ID=your-azure-tenant-id

# AI Layer (OpenAI/Claude)
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

## Security Architecture

- **SQL Validation**: Parameterized queries, injection protection
- **Access Control**: Read-only Fabric DW permissions
- **Authentication**: Azure AD Service Principal with token refresh
- **Scope Limitation**: Database-level access restrictions

## Development Workflow

1. **MCP Tool Development**: Implement tools in `mcp_server/tools/` with proper schemas
2. **Prompt Engineering**: Create domain-specific `.md` files in `agentic_layer/prompts/`
3. **Routing Logic**: Extend intent classification in `agentic_layer/routing/`
4. **Testing**: Use curl commands for individual tool testing, full flow validation via `/mcp` endpoint