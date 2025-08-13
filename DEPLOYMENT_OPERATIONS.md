# Fabric MCP Agent - Deployment & Operations Guide

**Version**: 1.0 MVP  
**Status**: Production Ready  
**Target Environment**: Enterprise/Cloud Production

## 🚀 Production Deployment

### Prerequisites

**Infrastructure Requirements**:
- Python 3.8+ runtime environment
- Network access to Microsoft Fabric Data Warehouse
- Network access to Azure OpenAI service
- Minimum 2GB RAM, 2 CPU cores
- 10GB disk space for logs and application

**Service Dependencies**:
- Microsoft Fabric Data Warehouse (configured and accessible)
- Azure OpenAI Service (GPT-4o deployment recommended)
- Azure AD Service Principal (with Fabric DW permissions)

### Environment Setup

#### 1. Clone and Install
```bash
git clone <repository-url>
cd mcp_fabric_server
pip install -r requirements.txt
```

#### 2. Configure Secrets Management

**Local Development**: Create `.env` file in project root:
```env
# Fabric Data Warehouse Connection
FABRIC_SQL_SERVER=your-fabric-server.datawarehouse.fabric.microsoft.com
FABRIC_SQL_DATABASE=your_database_name

# Azure Authentication  
AZURE_CLIENT_ID=your-service-principal-id
AZURE_CLIENT_SECRET=your-service-principal-secret
AZURE_TENANT_ID=your-azure-tenant-id

# Azure OpenAI Service
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

**Azure Container Apps**: Uses Azure Key Vault with Managed Identity (see Container Deployment section below)

#### 3. Verify Configuration
```bash
python main.py
# Check startup logs for successful connections
```

#### 4. Test Deployment
```bash
# Test Web UI
curl http://localhost:8000

# Test MCP endpoints
curl http://localhost:8000/list_tools
curl -X POST http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"question": "test query"}'
```

### Production Deployment Options

#### Azure DevOps CI/CD (Recommended for Production)

**Prerequisites**:
- Azure DevOps project with repository
- Azure Container Registry: `itapacdataacr.azurecr.io`
- Azure Key Vault: `itapackeyvault` (pre-existing)
- Service Principal with appropriate permissions
- Variable Group `ServicePrincipal` with secrets: `AZURE_CLIENT_ID`, `AZURE_SECRET`, `AZURE_TENANT_ID`

**Deployment Steps**:
```bash
# 1. Push code to Azure DevOps
git add .
git commit -m "Deploy to Azure Container Apps"
git push origin main

# 2. Pipeline automatically handles:
#    - Docker image build and push to ACR
#    - Container App deployment with Managed Identity
#    - Key Vault access configuration
```

**Key Vault Integration**:
- Uses existing Key Vault: `https://itapackeyvault.vault.azure.net/`
- Creates Container App with Managed Identity
- Grants Key Vault access to Container App
- Zero secrets in environment variables

**Secret Name Mapping**:
| Environment Variable | Key Vault Secret |
|---------------------|------------------|
| `FABRIC_SQL_SERVER` | `fabric-sql-server` |
| `AZURE_CLIENT_ID` | `azure-client-id` |
| `AZURE_OPENAI_KEY` | `azure-openai-key` |

#### Using Docker (Local/VM Deployment)
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t fabric-mcp-agent .
docker run -p 8000:8000 --env-file .env fabric-mcp-agent
```

#### Using systemd Service
```ini
[Unit]
Description=Fabric MCP Agent
After=network.target

[Service]
Type=simple
User=mcpagent
WorkingDirectory=/opt/mcp_fabric_server
Environment=PATH=/opt/mcp_fabric_server/.venv/bin
ExecStart=/opt/mcp_fabric_server/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Using Process Manager (PM2)
```bash
npm install -g pm2
pm2 start ecosystem.config.js
```

`ecosystem.config.js`:
```javascript
module.exports = {
  apps: [{
    name: 'fabric-mcp-agent',
    script: 'python',
    args: 'main.py',
    cwd: '/opt/mcp_fabric_server',
    instances: 2,
    exec_mode: 'cluster',
    env: {
      NODE_ENV: 'production'
    },
    error_file: 'logs/pm2-error.log',
    out_file: 'logs/pm2-out.log',
    log_file: 'logs/pm2-combined.log'
  }]
}
```

## 📊 Operations & Monitoring

### Health Checks

#### Application Health Endpoint
```bash
# Add to main.py for production
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "dependencies": {
            "fabric_dw": "connected",
            "azure_openai": "connected"
        }
    }
```

#### Monitoring Script
```bash
#!/bin/bash
# health_check.sh
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ $response -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy: HTTP $response"
    exit 1
fi
```

### Performance Monitoring

#### Real-time Dashboard
```bash
# Run performance dashboard every 5 minutes
*/5 * * * * /opt/mcp_fabric_server/.venv/bin/python /opt/mcp_fabric_server/performance_dashboard.py
```

#### Key Metrics to Monitor
```bash
# Business Metrics
- Questions answered per hour
- Average response time
- Success rate
- User satisfaction (response quality)

# Technical Metrics  
- API call count and costs
- Database query performance
- Error rates by type
- Memory and CPU usage

# Infrastructure Metrics
- Network latency to Azure services
- SSL certificate expiration
- Disk space for logs
- Connection pool utilization
```

#### Alerting Rules
```yaml
# Example Prometheus alerting rules
groups:
  - name: fabric_mcp_agent
    rules:
      - alert: HighResponseTime
        expr: avg_response_time_ms > 30000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          
      - alert: HighErrorRate
        expr: error_rate > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Error rate above 5%"
          
      - alert: AzureOpenAICostSpike
        expr: hourly_api_cost > 100
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Azure OpenAI costs spiking"
```

### Log Management

#### Log Rotation Configuration
```bash
# /etc/logrotate.d/fabric-mcp-agent
/opt/mcp_fabric_server/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    sharedscripts
    postrotate
        systemctl reload fabric-mcp-agent
    endscript
}
```

#### Log Analysis Scripts
```python
# log_analyzer.py
def analyze_performance_trends():
    """Analyze 24h performance trends"""
    logs = parse_log_file('logs/performance.log')
    
    hourly_metrics = defaultdict(list)
    for log in logs:
        hour = log['timestamp'][:13]  # YYYY-MM-DDTHH
        hourly_metrics[hour].append(log['session_duration_ms'])
    
    # Detect performance degradation
    for hour, durations in hourly_metrics.items():
        avg_duration = statistics.mean(durations)
        if avg_duration > 20000:  # 20 second threshold
            alert_performance_issue(hour, avg_duration)

def analyze_error_patterns():
    """Identify recurring error patterns"""
    error_logs = parse_log_file('logs/errors.log')
    error_patterns = Counter()
    
    for log in error_logs:
        error_type = log.get('error_type', 'Unknown')
        error_patterns[error_type] += 1
    
    # Report top error patterns
    for error, count in error_patterns.most_common(5):
        print(f"Error: {error}, Count: {count}")
```

## 🔒 Security Operations

### Security Checklist

#### Pre-deployment Security Audit
```bash
# Check for secrets in code
rg -i "password|secret|key|token" --type py --exclude ".env"

# Verify environment variables
python -c "import os; print('✓ All required env vars present' if all(os.getenv(k) for k in ['FABRIC_SQL_SERVER', 'AZURE_CLIENT_ID', 'AZURE_OPENAI_KEY']) else '✗ Missing env vars')"

# Check file permissions
find . -name "*.py" -perm /o+w -exec echo "Warning: World-writable file {}" \;

# Verify SSL/TLS configuration
openssl s_client -connect your-fabric-server.datawarehouse.fabric.microsoft.com:1433 -servername your-fabric-server.datawarehouse.fabric.microsoft.com
```

#### Runtime Security Monitoring
```python
# security_monitor.py
def monitor_suspicious_queries():
    """Monitor for suspicious SQL patterns"""
    suspicious_patterns = [
        r'DROP\s+TABLE',
        r'DELETE\s+FROM',
        r'TRUNCATE\s+TABLE',
        r'INSERT\s+INTO',
        r'UPDATE\s+.*SET',
        r'CREATE\s+TABLE',
        r'ALTER\s+TABLE'
    ]
    
    sql_logs = parse_log_file('logs/performance.log')
    for log in sql_logs:
        sql_query = log.get('sql_query', '')
        for pattern in suspicious_patterns:
            if re.search(pattern, sql_query, re.IGNORECASE):
                alert_security_issue(log['request_id'], sql_query, pattern)

def verify_authentication_health():
    """Check Azure AD token validity"""
    try:
        from connectors.fabric_dw import get_access_token
        token = get_access_token()
        if token:
            print("✓ Azure AD authentication healthy")
        else:
            alert_auth_failure("Token acquisition failed")
    except Exception as e:
        alert_auth_failure(f"Authentication error: {str(e)}")
```

### Certificate and Token Management
```bash
# certificate_monitor.sh
#!/bin/bash

# Check Azure OpenAI certificate expiration
openssl s_client -servername your-resource.openai.azure.com -connect your-resource.openai.azure.com:443 2>/dev/null | openssl x509 -noout -dates

# Check Fabric DW certificate expiration  
openssl s_client -servername your-fabric-server.datawarehouse.fabric.microsoft.com -connect your-fabric-server.datawarehouse.fabric.microsoft.com:1433 2>/dev/null | openssl x509 -noout -dates

# Token refresh monitoring
python -c "
from connectors.fabric_dw import get_access_token
import jwt
import datetime

token = get_access_token()
decoded = jwt.decode(token, options={'verify_signature': False})
exp = datetime.datetime.fromtimestamp(decoded['exp'])
now = datetime.datetime.now()
hours_until_expiry = (exp - now).total_seconds() / 3600

if hours_until_expiry < 24:
    print(f'Warning: Token expires in {hours_until_expiry:.1f} hours')
else:
    print(f'Token healthy: {hours_until_expiry:.1f} hours until expiry')
"
```

## 🔄 Backup and Recovery

### Data Backup Strategy

#### Configuration Backup
```bash
#!/bin/bash
# backup_config.sh

BACKUP_DIR="/backup/mcp_fabric_server/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup configuration files
cp .env "$BACKUP_DIR/"
cp -r agentic_layer/prompts/ "$BACKUP_DIR/prompts/"

# Backup logs (last 7 days)
find logs/ -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/logs/" \;

# Create manifest
echo "Backup created: $(date)" > "$BACKUP_DIR/manifest.txt"
echo "Server: $(hostname)" >> "$BACKUP_DIR/manifest.txt"
echo "Version: 1.0.0" >> "$BACKUP_DIR/manifest.txt"

# Compress backup
tar -czf "${BACKUP_DIR}.tar.gz" -C /backup/mcp_fabric_server "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

echo "Backup completed: ${BACKUP_DIR}.tar.gz"
```

#### Disaster Recovery Procedures
```bash
#!/bin/bash
# disaster_recovery.sh

# 1. Stop service
systemctl stop fabric-mcp-agent

# 2. Restore from backup
BACKUP_FILE="$1"
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "Usage: $0 <backup_file.tar.gz>"
    exit 1
fi

# 3. Extract backup
tar -xzf "$BACKUP_FILE" -C /tmp/
BACKUP_DIR=$(tar -tzf "$BACKUP_FILE" | head -1 | cut -f1 -d"/")

# 4. Restore configuration
cp "/tmp/$BACKUP_DIR/.env" /opt/mcp_fabric_server/
cp -r "/tmp/$BACKUP_DIR/prompts/" /opt/mcp_fabric_server/agentic_layer/

# 5. Verify configuration
cd /opt/mcp_fabric_server
python -c "from main import app; print('Configuration valid')"

# 6. Restart service
systemctl start fabric-mcp-agent
systemctl status fabric-mcp-agent

echo "Disaster recovery completed"
```

## 📈 Performance Optimization

### Production Tuning

#### FastAPI Optimization
```python
# main.py production settings
from fastapi import FastAPI
from uvicorn import Config, Server

app = FastAPI(
    title="Fabric MCP Agent",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,
    redoc_url=None
)

# Production server configuration
if __name__ == "__main__":
    config = Config(
        app=app,
        host="0.0.0.0",
        port=8000,
        workers=4,  # Scale based on CPU cores
        worker_class="uvicorn.workers.UvicornWorker",
        access_log=False,  # Use custom logging instead
        server_header=False,  # Hide server header
        date_header=False,   # Reduce response size
    )
    server = Server(config)
    server.run()
```

#### Database Connection Optimization
```python
# connectors/fabric_dw.py optimizations
import pyodbc
from contextlib import contextmanager
import threading

# Connection pool
_connection_pool = threading.local()

@contextmanager
def get_fabric_conn():
    """Connection pool implementation"""
    if not hasattr(_connection_pool, 'conn') or _connection_pool.conn is None:
        conn_str = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={FABRIC_SQL_SERVER};"
            f"DATABASE={FABRIC_SQL_DATABASE};"
            "Authentication=ActiveDirectoryServicePrincipal;"
            f"UID={AZURE_CLIENT_ID};"
            f"PWD={AZURE_CLIENT_SECRET};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
            "Command Timeout=60;"
            "Mars_Connection=yes;"  # Multiple Active Result Sets
        )
        _connection_pool.conn = pyodbc.connect(conn_str)
    
    try:
        yield _connection_pool.conn
    except Exception as e:
        # Reset connection on error
        _connection_pool.conn = None
        raise e
```

### Scaling Considerations

#### Horizontal Scaling
```yaml
# kubernetes deployment example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fabric-mcp-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fabric-mcp-agent
  template:
    metadata:
      labels:
        app: fabric-mcp-agent
    spec:
      containers:
      - name: fabric-mcp-agent
        image: fabric-mcp-agent:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: FABRIC_SQL_SERVER
          valueFrom:
            secretKeyRef:
              name: fabric-secrets
              key: sql-server
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Load Balancing Configuration
```nginx
# nginx.conf
upstream fabric_mcp_backend {
    server 10.0.1.10:8000;
    server 10.0.1.11:8000;
    server 10.0.1.12:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://fabric_mcp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_timeout 60s;
    }
    
    location /health {
        proxy_pass http://fabric_mcp_backend/health;
        proxy_timeout 10s;
    }
}
```

## 🎯 Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Operations
```bash
#!/bin/bash
# daily_maintenance.sh

echo "=== Daily Maintenance $(date) ==="

# Check service health
systemctl status fabric-mcp-agent

# Review yesterday's performance
python performance_dashboard.py | tee /var/log/daily_performance.log

# Check log file sizes
du -sh logs/*.log

# Monitor Azure OpenAI costs
python -c "
from performance_dashboard import generate_performance_report
metrics = generate_performance_report()
daily_cost = metrics['api_call_costs']
if daily_cost > 50:  # Alert threshold
    print(f'⚠️ High daily cost: \${daily_cost:.2f}')
else:
    print(f'✓ Daily cost: \${daily_cost:.2f}')
"

echo "=== Daily Maintenance Complete ==="
```

#### Weekly Operations
```bash
#!/bin/bash
# weekly_maintenance.sh

echo "=== Weekly Maintenance $(date) ==="

# Rotate logs manually if needed
logrotate -f /etc/logrotate.d/fabric-mcp-agent

# Update performance baselines
python -c "
from performance_dashboard import generate_performance_report
import json

metrics = generate_performance_report()
baseline = {
    'avg_response_time': metrics['avg_response_time_ms'],
    'success_rate': metrics.get('success_rate', 0),
    'avg_cost_per_question': metrics['api_call_costs'] / max(metrics['total_requests'], 1),
    'week': '$(date +%Y-W%U)'
}

with open('baselines/week_$(date +%Y%U).json', 'w') as f:
    json.dump(baseline, f, indent=2)

print(f'Baseline saved: {baseline}')
"

# Check for prompt module updates
git log --since="1 week ago" --oneline agentic_layer/prompts/

echo "=== Weekly Maintenance Complete ==="
```

This operations guide provides comprehensive coverage for deploying, monitoring, and maintaining the Fabric MCP Agent in production environments.