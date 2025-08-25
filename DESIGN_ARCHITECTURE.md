# Fabric MCP Agent - Design & Architecture

**Version**: 1.0 MVP Complete  
**Last Updated**: August 2025  
**Status**: Production Ready

## 🎯 System Overview

The Fabric MCP Agent is a production-ready two-layer system that bridges business users and Microsoft Fabric Data Warehouses through intelligent AI-powered query processing. It transforms natural language business questions into actionable insights with comprehensive logging and monitoring.

## 🏗️ Architecture Layers

### Layer 1: MCP-Compliant Server
**Purpose**: Standards-compliant interface providing clean abstractions over Fabric Data Warehouse operations.

**Components**:
- **FastAPI Application** (`main.py`)
- **MCP Tools** (`mcp_server/tools/`)
- **Database Connector** (`connectors/fabric_dw.py`)
- **Logging Middleware** (Request tracking and performance monitoring)

### Layer 2: Agentic Reasoning Engine
**Purpose**: Intelligent business context interpretation with multi-stage workflow execution.

**Components**:
- **Intent Router** (`agentic_layer/routing/intent_router.py`)
- **Intent Templates** (`agentic_layer/prompts/intent/`)
- **Persona Modules** (`agentic_layer/prompts/personas/`)
- **Session Management** (Request tracking and context preservation)

## 🔄 Request Flow Architecture

### 🆕 Multi-Stage Execution Strategy
The system now supports three execution strategies based on query complexity:

1. **Single-Stage**: Simple queries requiring one SQL execution
2. **Multi-Stage**: Complex queries requiring discovery → analysis → evaluation  
3. **Iterative**: Advanced queries with refinement loops (future)

### Multi-Stage Business Question Flow
```mermaid
graph TD
    A[User Question] --> B[Intent Classification]
    B --> C{Execution Strategy}
    
    C -->|Multi-Stage| D[Stage 1: Discovery]
    D --> E[SQL Generation + Execution]
    E --> F[AI Intermediate Processing]
    F --> G[Stage 2: Analysis]
    G --> H[SQL Generation + Execution]
    H --> I[Stage 3: Evaluation]
    I --> J[Pure AI Business Analysis]
    J --> K[Final Response]
    
    C -->|Single-Stage| L[Standard Tool Chain]
    L --> M[SQL + Summarize + Visualize]
    M --> K
    
    subgraph "Stage Breakdown"
        N["Stage 1: Find candidates<br/>🎯 Discovery Query"]
        O["Stage 2: Get details<br/>📊 Analysis Query"] 
        P["Stage 3: Business insights<br/>🧠 No SQL - Pure Analysis"]
    end
```

### 🆕 Competitive Replacement Flow (Two-Stage AI Matching)
```mermaid
graph TD
    A["User: Replace competitor kit"] --> B[Intent: spt_sales_rep]
    B --> C[Stage 1: AI Semantic Matching]
    C --> D[Extract Keywords from Competitor Description]
    D --> E[Query 1: Find Similar Products]
    E --> F[AI Evaluates Product Matches]
    F --> G[Select Best Equivalent Parts]
    G --> H[Stage 2: Pricing & Kit Analysis]
    H --> I[Query 2: Get Pricing & Components]
    I --> J[Generate Competitive Quote]
    J --> K[Business Response with Savings]
    
    subgraph "Example: BD Luer-Lock Syringe 2.5mL"
        L["Keywords: syringe, 2.5, ML, lock"] 
        M["SQL: LIKE '%シリンジ%' AND '%2.5%'"]
        N["Match: ｼﾘﾝｼﾞ2.5ML ﾛｯｸ"]
        O["Price: ¥850 vs Competitor ¥920"]
        P["Savings: ¥70 (7.6% better)"]
    end
```

### Detailed Session Phases

1. **Session Initialization**
   - Generate unique request ID
   - Extract user question from request body
   - Start session timing
   - Initialize phase tracking

2. **Intent Classification Phase**
   - Send question + available prompt modules to Azure OpenAI
   - Parse JSON response for intent, confidence, and tool chain
   - Log API call with token usage
   - Handle fallback for JSON parsing errors

3. **Tool Chain Execution Phase**
   - Load selected prompt module (`.md` file)
   - Execute tools in determined sequence:
     - `get_metadata` (optional - may be skipped by AI)
     - `run_sql_query` (with enhanced context)
     - `summarize_results` (business-friendly output)
     - `generate_visualization` (optional)

4. **SQL Generation & Execution**
   - Combine user question + prompt context + schema
   - Generate T-SQL via Azure OpenAI
   - Execute against Fabric Data Warehouse
   - Track execution time and result count

5. **Response Assembly**
   - Aggregate all tool results
   - Generate final business-friendly response
   - Include summary, key details, and suggestions

6. **Session Completion**
   - Calculate total session duration
   - Log comprehensive performance metrics
   - Return enriched response with request ID

## 🛠️ Component Deep Dive

### MCP Tools (`mcp_server/tools/`)

#### `run_sql_query` (Primary Tool)
- **Input**: Natural language question OR direct SQL
- **Process**: 
  1. Generate SQL from question using schema context
  2. Execute parameterized query against Fabric DW
  3. Track execution time and result count
- **Output**: SQL executed, results array, row count
- **Security**: Read-only access, parameterized queries

#### `get_metadata` (Schema Discovery)
- **Input**: Optional table name
- **Process**:
  1. Query INFORMATION_SCHEMA for column details
  2. Get row counts and sample data
  3. Return comprehensive table metadata
- **Output**: Column info, data types, sample records
- **Optimization**: May be skipped by AI if schema is known

#### `summarize_results` (Business Intelligence)
- **Input**: Query results array, business context
- **Process**: 
  1. Analyze result structure and patterns
  2. Generate business-friendly summary
  3. Add context-specific insights
- **Output**: Executive summary with key findings
- **Logic**: Pure Python processing (no AI calls)

#### `generate_visualization` (Data Presentation)
- **Input**: Data array, chart type, title
- **Process**:
  1. Analyze data structure for visualization suitability
  2. Create chart configuration or formatted table
  3. Optimize data for display (limit rows for performance)
- **Output**: Visualization config with data
- **Types**: Table, bar, line, pie charts

### Agentic Layer Components

#### Intent Router (`agentic_layer/routing/intent_router.py`)

**Classification Function**:
```python
def classify_intent(user_question: str, request_id: str = None) -> Dict[str, Any]
```

**🆕 Competitive Replacement Intent Detection**:
- **Trigger keywords**: "competitor quoted", "replace [Brand Name]", "equivalent to", "match this quote"
- **Special handling**: Routes to `spt_sales_rep.md` for two-stage processing
- **Japanese context**: Handles hiragana/katakana product descriptions
- **Auto-pricing**: Integrates QAD ERP pricing tables (JPNPROdb_nqpr_mstr, JPNPROdb_sod_det)

**Classification Logic**:
- Analyzes user question against available prompt modules
- Returns JSON with intent, confidence, tool chain, reasoning
- Uses system message to enforce JSON-only responses
- Implements robust error handling with fallback classification

**Tool Chain Execution**:
```python
def execute_tool_chain(user_question: str, classification: Dict[str, Any], request_id: str = None)
```

**Execution Logic**:
- Loads appropriate prompt module content
- Executes tools in determined sequence
- Passes enhanced context between tools
- Assembles final business response

#### 🆕 Intent Templates (`agentic_layer/prompts/intent/`)

**Generic Multi-Stage Templates**:
- **`stage1_discovery.md`**: Discovery query patterns and objectives
- **`stage2_analysis.md`**: Detailed analysis query strategies  
- **`stage3_evaluation.md`**: Business evaluation and insight generation

**Template Purpose**: Domain-agnostic frameworks that work with any persona context.

#### Persona Modules (`agentic_layer/prompts/personas/`)

**Current Personas**:
- **`product_planning.md`**: Product master data and component analysis
- **`spt_sales_rep.md`**: Competitive replacement and pricing analysis

**Persona Structure**:
```markdown
# Role & Context
## Key Tables & Schema
## Primary Use Cases  
## Query Patterns & Examples
## Business Logic & Rules
## SQL Guidelines & Joins
## Response Formatting
## Domain-Specific Context
```

**🆕 Multi-Stage Integration**: 
- Personas provide domain knowledge and table context
- Intent templates provide generic execution patterns
- Combined during runtime for context-aware multi-stage execution

### Database Connector (`connectors/fabric_dw.py`)

**Authentication Flow**:
1. Azure AD Service Principal authentication
2. Token acquisition for database access
3. ODBC connection with SSL/TLS encryption
4. Connection pooling and error handling

**Key Functions**:
- `get_access_token()`: Azure AD authentication
- `get_fabric_conn()`: Secure database connection
- `get_all_schema()`: Complete schema discovery
- `get_table_metadata()`: Detailed table information
- `execute_sql()`: Parameterized query execution

## 📊 Performance & Monitoring Architecture

### Logging System (`logging_config.py`)

**Multi-Channel Logging**:
- **Main Log**: Application events and request lifecycle
- **Performance Log**: Session metrics and timing
- **API Log**: Azure OpenAI usage and costs
- **Error Log**: Full error context with stack traces

**Session Tracking**:
- Unique request IDs for end-to-end traceability
- Phase-based timing (classification, SQL generation, execution)
- Token usage tracking per API call
- Business metrics (questions answered, results returned)

**Log Format**: Structured JSON with standardized fields
```json
{
  "timestamp": "2025-08-07T10:30:45",
  "request_id": "abc123ef",
  "user_question": "tell me the components in MRH-011C",
  "session_duration_ms": 15234,
  "api_calls": 2,
  "tokens_used": 26920,
  "classification": {"intent": "product_planning", "confidence": 0.95},
  "result_count": 27
}
```

### Performance Dashboard (`performance_dashboard.py`)

**Business Metrics**:
- Question-to-answer time (end-to-end session duration)
- Success rate for complete business sessions
- AI usage per business question (not per API call)
- Cost per business question analysis
- Tool usage patterns and optimization opportunities

**Real-time Analytics**:
- Hourly request distribution
- Top business questions
- Error analysis and categorization
- Performance percentiles (P95, P99)

## 🔒 Security Architecture

### Authentication & Authorization
- **Azure AD Service Principal**: Machine-to-machine authentication
- **Token-based Access**: JWT tokens with automatic refresh
- **Read-only Permissions**: Database access limited to SELECT operations
- **Connection Security**: TLS encryption for all connections

### Data Protection
- **Parameterized Queries**: SQL injection protection
- **Schema Validation**: Input validation and sanitization
- **Error Sanitization**: No sensitive data in logs or responses
- **Access Logging**: Complete audit trail for all operations

## 🚀 Scalability & Extension Points

### Horizontal Scaling
- **Stateless Design**: No server-side session storage
- **Connection Pooling**: Efficient database connection management
- **Caching Layer**: Azure OpenAI automatic response caching
- **Load Balancer Ready**: No sticky session requirements

### Vertical Extension
- **Prompt Module System**: Easy addition of new business domains
- **Tool Architecture**: Pluggable tool system for new capabilities
- **Connector Pattern**: Support for multiple data sources
- **API Versioning**: Backward compatibility for integrations

### Integration Points
- **MCP Standard**: Compatible with any MCP-compliant client
- **REST API**: Standard HTTP endpoints for web applications
- **WebSocket Support**: Ready for real-time implementations
- **Webhook Integration**: Event-driven architecture support

## 📈 Performance Characteristics

### 🆕 Multi-Stage Performance (Production Measurements)
**Total Execution Time**: 40.7 seconds average

| Stage | Duration | Operations | Percentage |
|-------|----------|------------|------------|
| **Intent Classification** | 3.4s | LLM routing decision | 8.3% |
| **Stage 1: Discovery** | 14.4s | SQL generation + execution | 35.4% |
| **Stage 2: Analysis** | 15.7s | SQL generation + execution | 38.5% |
| **Stage 3: Evaluation** | 7.1s | Pure LLM business analysis | 17.4% |

**Key Insights**:
- **SQL operations dominate**: 30.1s (74%) of total time
- **Database queries execute fast**: ~0.2s actual execution
- **LLM calls are efficient**: 10.5s combined (26%)
- **Stage 3 eliminates SQL**: Pure analysis phase

### Single-Stage Performance (Legacy)
- **Average Session**: 12-15 seconds end-to-end
- **95th Percentile**: 25-30 seconds
- **Database Queries**: 200ms-2s depending on complexity

### Resource Usage
- **Multi-Stage API Calls**: 4.0 average (classification + stage1 + stage2 + stage3)
- **Single-Stage API Calls**: 2.0 average (classification + SQL generation)
- **Token Usage**: 35,000+ average per multi-stage question
- **Cost per Multi-Stage Question**: ~$0.18 (GPT-4o pricing)
- **Memory Footprint**: <100MB base application

### 🚀 Optimization Opportunities
**High Impact**:
- **SQL Query Optimization**: Target 50% reduction in Stage 1 & 2 times
- **Database Indexing**: Add indexes for common query patterns
- **Parallel Processing**: Run summarize_results during Stage 3 evaluation

**Medium Impact**:
- **LLM Response Caching**: Cache persona contexts and patterns
- **Connection Pooling**: Reduce database connection overhead
- **Streaming Responses**: Return Stage 1 results immediately

## 🔄 Data Flow Patterns

### Typical Business Question Flow
1. **User Input**: "tell me the components in MRH-011C"
2. **Classification**: Routes to `product_planning.md` (0.5s)
3. **SQL Generation**: Creates component query with context (1.2s)
4. **Database Query**: Executes against Fabric DW (0.8s)
5. **Result Processing**: Formats 27 components (0.3s)
6. **Response Assembly**: Creates business summary (0.2s)
7. **Total Time**: ~3 seconds + network latency

### Error Handling Patterns
- **Classification Failures**: Fallback to generic product planning
- **SQL Generation Issues**: Retry with simplified context
- **Database Errors**: Graceful degradation with error context
- **API Timeouts**: Circuit breaker with user notification

## 🎛️ Configuration Management

### Environment Variables
- **Database Connection**: Fabric server, database, credentials
- **AI Service**: Azure OpenAI endpoint, key, deployment model
- **Logging**: Log levels, file paths, retention policies
- **Security**: Authentication parameters, token expiration

### Runtime Configuration
- **Prompt Modules**: Dynamic loading from file system
- **Tool Registration**: Automatic discovery and schema generation
- **Performance Thresholds**: Configurable alerting and monitoring
- **Feature Flags**: Enable/disable components for testing

This MVP architecture provides a solid foundation for enterprise deployment while maintaining flexibility for future enhancements and domain extensions.