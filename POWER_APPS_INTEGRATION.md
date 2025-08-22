# Power Apps Integration with APIM-Protected MCP Agent

This guide explains how to configure Power Apps to consume the Fabric MCP Agent API through Azure API Management (APIM) with subscription key authentication.

## Overview

**Architecture:**
```
Power Apps → Azure API Management → Azure Container App (MCP Agent)
```

**Endpoint:** `https://m3apidwhsd1.azure-api.net/aca`  
**Authentication:** Subscription Key (`Ocp-Apim-Subscription-Key` header)

## Power Apps Configuration

### 1. Create Custom Connector

Power Apps can't directly call APIM with subscription keys, so create a custom connector:

#### Step 1: Navigate to Custom Connectors
1. Go to **Power Apps** → **Data** → **Custom Connectors**
2. Click **+ New custom connector** → **Create from blank**

#### Step 2: General Information
- **Connector name**: `FabricMCPAgent`
- **Description**: `AI-powered Microsoft Fabric Data Warehouse analysis`
- **Host**: `m3apidwhsd1.azure-api.net`
- **Base URL**: `/aca`

#### Step 3: Security Configuration
- **Authentication type**: `API Key`
- **Parameter label**: `Subscription Key`
- **Parameter name**: `Ocp-Apim-Subscription-Key`
- **Parameter location**: `Header`

### 2. Define API Operations

#### Operation 1: Agentic Intelligence (Primary)
- **Operation ID**: `AskQuestion`
- **Summary**: `Ask business question with AI reasoning`
- **Description**: `Submit natural language questions for intelligent analysis`
- **Verb**: `POST`
- **URL**: `/mcp`

**Request Body:**
```json
{
  "type": "object",
  "properties": {
    "question": {
      "type": "string",
      "description": "Natural language business question"
    }
  },
  "required": ["question"]
}
```

**Response Schema:**
```json
{
  "type": "object",
  "properties": {
    "question": {"type": "string"},
    "response": {"type": "string"},
    "classification": {"type": "string"},
    "tool_chain_results": {"type": "string"},
    "request_id": {"type": "string"}
  }
}
```

**Note:** `classification` and `tool_chain_results` are defined as strings because PowerApps Custom Connector UI doesn't support nested object types. These contain JSON strings that need to be parsed in PowerApps using `ParseJSON()`.

#### Operation 2: List Available Tools
- **Operation ID**: `ListTools`
- **Summary**: `Get available MCP tools`
- **Verb**: `GET`
- **URL**: `/list_tools`

#### Operation 3: Direct Tool Execution
- **Operation ID**: `ExecuteTool`
- **Summary**: `Execute specific MCP tool`
- **Verb**: `POST`
- **URL**: `/call_tool`

**Request Body:**
```json
{
  "type": "object",
  "properties": {
    "tool": {"type": "string"},
    "args": {"type": "object"}
  },
  "required": ["tool", "args"]
}
```

### 3. Test the Connector

#### Test Configuration
1. **Subscription Key**: `2c405c6d95ea493985aeda1985e91bf7`
2. **Test Request**:
   ```json
   {
     "question": "tell me the components in MRH-011C"
   }
   ```

#### Expected Response
```json
{
  "question": "tell me the components in MRH-011C",
  "response": "Product MRH-011C contains the following components...",
  "classification": {
    "persona": "product_planning",
    "execution_strategy": "multi_stage"
  },
  "tool_chain_results": {
    "stage3_evaluation": {
      "business_answer": "...",
      "key_findings": [...],
      "recommended_action": "..."
    }
  },
  "request_id": "req_123456789"
}
```

## Power Apps Implementation

### 1. Add Data Source
1. **Apps** → **Your App** → **Data** → **Add data**
2. Search for your custom connector: `FabricMCPAgent`
3. **Connect** → Enter subscription key when prompted

### 2. Create UI Components

#### Main Question Input
```powerfx
// Text Input Control
Name: txtQuestion
Default: "What are the components in MRH-011C?"
HintText: "Ask a business question about your data..."
```

#### Submit Button
```powerfx
// Button Control
Name: btnSubmit
Text: "Ask AI Assistant"
OnSelect: 
  UpdateContext({
    isLoading: true,
    errorMessage: ""
  });
  Set(
    aiResponse, 
    FabricMCPAgent.AskQuestion({question: txtQuestion.Text})
  );
  UpdateContext({isLoading: false})
```

#### Results Display
```powerfx
// HTML Text Control for Business Answer
Name: htmlBusinessAnswer
HtmlText: 
  If(
    IsEmpty(aiResponse),
    "Ask a question to see AI analysis...",
    "<h3>Business Analysis</h3><p>" & 
    aiResponse.response & 
    "</p>"
  )
```

#### Key Findings List
```powerfx
// Gallery Control
Name: galKeyFindings
Items: ParseJSON(aiResponse.tool_chain_results).stage3_evaluation.key_findings
Text: ThisItem.Value
```

### 3. Error Handling

```powerfx
// Error Display Control
Name: lblError
Text: 
  If(
    IsError(aiResponse),
    "Error: " & FirstError.Message,
    If(
      !IsEmpty(errorMessage),
      errorMessage,
      If(
        IsError(ParseJSON(aiResponse.classification)) Or IsError(ParseJSON(aiResponse.tool_chain_results)),
        "Error parsing response data. Please try again.",
        ""
      )
    )
  )
Visible: !IsEmpty(lblError.Text)
Color: Color.Red
```

### 4. JSON Parsing Helpers

Since PowerApps Custom Connector treats complex objects as strings, you need to parse them:

```powerfx
// Helper function to safely parse classification
Set(
  classificationData,
  If(
    IsError(ParseJSON(aiResponse.classification)),
    {persona: "unknown", execution_strategy: "single_stage"},
    ParseJSON(aiResponse.classification)
  )
);

// Helper function to safely parse tool results
Set(
  toolResultsData,
  If(
    IsError(ParseJSON(aiResponse.tool_chain_results)),
    {},
    ParseJSON(aiResponse.tool_chain_results)
  )
);

// Use parsed data in your controls
Text: classificationData.persona
Text: toolResultsData.stage3_evaluation.business_answer
Items: toolResultsData.stage3_evaluation.key_findings
```

### 5. Loading State

```powerfx
// Loading Spinner
Name: spinLoading
Visible: isLoading

// Disable submit while loading
btnSubmit.DisplayMode: 
  If(isLoading, DisplayMode.Disabled, DisplayMode.Edit)
```

## Business Use Cases

### 1. Product Analysis
**Question:** "What are the specifications for MRH-011C?"  
**Power Apps Context:** Product planning, inventory management

### 2. Competitive Replacement
**Question:** "Replace BD Luer-Lock Syringe 2.5mL with our equivalent"  
**Power Apps Context:** Sales quotation, competitive analysis

### 3. Component Discovery
**Question:** "Show me all surgical kit components"  
**Power Apps Context:** Kit configuration, product bundling

## Advanced Features

### 1. Multi-Stage Results Display
```powerfx
// Display different stages of AI reasoning
With(
  {
    classificationObj: ParseJSON(aiResponse.classification),
    toolResultsObj: ParseJSON(aiResponse.tool_chain_results)
  },
  If(
    classificationObj.execution_strategy = "multi_stage",
    // Show discovery → analysis → evaluation flow
    ShowMultiStageResults(toolResultsObj),
    // Show simple single-stage results
    ShowSimpleResults(toolResultsObj)
  )
)
```

### 2. Session Management
```powerfx
// Track conversation history
Set(
  conversationHistory,
  Collect(
    conversationHistory,
    {
      Question: txtQuestion.Text,
      Answer: aiResponse.response,
      SessionId: aiResponse.request_id,
      Timestamp: Now()
    }
  )
)
```

### 3. Export Capabilities
```powerfx
// Export results to Excel/SharePoint
Export(
  With(
    {toolResults: ParseJSON(aiResponse.tool_chain_results)},
    Table({
      Question: txtQuestion.Text,
      BusinessAnswer: aiResponse.response,
      KeyFindings: JSON(toolResults.stage3_evaluation.key_findings),
      Confidence: toolResults.stage3_evaluation.supporting_data.confidence
    })
  ),
  "MCP_Analysis_" & Text(Now(), "yyyymmdd_hhmmss") & ".xlsx"
)
```

## Security Considerations

1. **Subscription Key Protection**: Store in Power Apps environment variables
2. **User Access Control**: Implement Power Apps security roles
3. **Data Governance**: Follow organizational data access policies
4. **Audit Trail**: Log all API interactions for compliance

## Deployment Checklist

- [ ] Custom connector created and tested
- [ ] Subscription key configured securely
- [ ] Error handling implemented
- [ ] Loading states configured
- [ ] Business logic validated
- [ ] User training completed
- [ ] Security review passed

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check subscription key
2. **403 Forbidden**: Verify APIM CORS settings
3. **Timeout**: Increase Power Apps timeout settings
4. **Property type mismatch "Expected: object, Actual: string"**: 
   - This occurs when PowerApps expects object but receives string
   - **Solution**: Set `classification` and `tool_chain_results` as `string` type in Custom Connector schema
   - Use `ParseJSON()` in PowerApps formulas to access nested properties
5. **Schema Errors**: Validate request/response formats match documentation

### Debug Tips

1. Test custom connector independently
2. Use Power Apps Monitor for debugging
3. Check APIM analytics for request logs
4. Validate JSON schema compliance

---

This configuration enables Power Apps users to leverage the full power of the Fabric MCP Agent's AI-driven data analysis capabilities through an intuitive, low-code interface.