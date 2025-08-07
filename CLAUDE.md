# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**fabric-mcp-agent**: A two-layer system combining an MCP-compliant server with an agentic AI reasoning layer for Microsoft Fabric Data Warehouse access.

### 🔷 Layer 1: Fabric DW MCP Server
Standards-compliant MCP server that self-declares tools and provides clean abstractions over Fabric Data Warehouse operations.

### 🔷 Layer 2: Agentic Reasoning Layer  
Intelligent routing system that interprets business intent, selects appropriate prompt modules, and dynamically chains MCP tools to deliver enriched answers with tables, summaries, and visualizations.

## Target Architecture

```
fabric_mcp_project/
├── mcp_server/           # MCP tool declarations and FastAPI endpoints
│   ├── tools/           # Python logic for each MCP tool
├── agentic_layer/
│   ├── routing/         # Intent classifier and chain builder
│   ├── prompts/         # Modular prompt markdown files (*.md)
│   ├── memory/          # Session context management
├── connectors/
│   └── fabric_dw.py     # SQL access and metadata reader
├── tests/
└── main.py
```

## Development Commands

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

# Access Web UI for interactive testing
open http://localhost:8000
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

## Agentic Flow Architecture

### Prompting Flow & Hint System
1. **User Input** → "What's our top-selling product by margin this quarter?"
2. **Intent Classification** → Routes to appropriate prompt module (`agentic_layer/routing/intent_router.py:33`)
3. **Prompt Integration** → Loads domain context from `.md` files (`intent_router.py:94`)
4. **Enhanced SQL Generation** → Combines prompt context + user question (`intent_router.py:122-127`)
5. **MCP Tool Chain Execution**:
   - `get_metadata()` → Schema discovery with sample data
   - `run_sql_query(enhanced_question)` → Execute contextually-aware SQL  
   - `summarize_results(data)` → Business summary
   - `generate_visualization(data, 'bar')` → Chart creation
6. **Output** → Enriched response with summary, data table, and visualization

**Hint Flow Mechanism:**
```
User Question + Prompt Module Content → Enhanced Context → Better SQL Generation
```

The system automatically injects domain-specific hints through prompt modules, eliminating the need for users to provide schema details or query patterns.

### Key Components

#### Routing Agent (`agentic_layer/routing/`)
- Classifies business intent using LLM function-calling
- Selects appropriate prompt modules from `agentic_layer/prompts/*.md`
- Builds dynamic tool chains for complex queries
- Implements "pondering loop" for query refinement and retry logic

#### Prompt Modules (`agentic_layer/prompts/*.md`)
Task-specific instruction sets with built-in hints:
- `product_planning.md` - Product master data analysis (JPNPROdb_ps_mstr, JPNPROdb_pt_mstr)
  - Contains table schemas, query patterns, SQL guidelines, and business context
  - Automatically loaded when product-related questions are detected
- Additional domain-specific modules can be added as `.md` files

**Prompt Module Structure:**
- **Role & Context**: Domain expertise and table focus  
- **Query Patterns**: Common question templates with examples
- **SQL Guidelines**: Table-specific join patterns and filters
- **Business Context**: Key insights and use cases for domain experts

#### Memory Management (`agentic_layer/memory/`)
- Session context preservation
- Query history and refinement tracking
- Cross-query relationship mapping

## Current Implementation Status

**✅ PRODUCTION MVP COMPLETE**:
- FastAPI server with full MCP compliance (`/list_tools`, `/call_tool`, `/mcp`) 
- All 4 MCP tools fully implemented with error handling and logging
- Complete agentic reasoning layer with 95%+ intent classification accuracy
- Azure AD authentication with secure Fabric DW access
- Production-ready Web UI with interactive result tables
- Comprehensive performance monitoring and logging system
- Session-based business metrics tracking
- Azure OpenAI caching optimization

**🚀 Ready for Production Extension**:
- Scalable prompt module system (proven with `product_planning.md`)
- Extensible tool architecture for new business domains
- Performance monitoring foundation for enterprise scaling

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