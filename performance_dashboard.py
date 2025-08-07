"""
Performance Dashboard for MCP Agent
Generates real-time analytics from log files
"""
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

def parse_log_file(file_path: str):
    """Parse JSON log file and return records"""
    if not os.path.exists(file_path):
        return []
    
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                records.append(record)
            except json.JSONDecodeError:
                continue
    return records

def generate_performance_report():
    """Generate comprehensive performance report"""
    
    # Parse all log files
    main_logs = parse_log_file('logs/mcp_agent.log')
    perf_logs = parse_log_file('logs/performance.log')
    api_logs = parse_log_file('logs/api_calls.log')
    error_logs = parse_log_file('logs/errors.log')
    
    # Initialize metrics
    metrics = {
        'total_requests': 0,
        'successful_requests': 0,
        'failed_requests': 0,
        'avg_response_time_ms': 0,
        'total_api_calls': 0,
        'total_tokens_used': 0,
        'avg_tokens_per_request': 0,
        'classification_accuracy': 0,
        'tool_usage': Counter(),
        'error_types': Counter(),
        'hourly_request_count': defaultdict(int),
        'endpoint_usage': Counter(),
        'top_questions': Counter(),
        'response_times': [],
        'sql_execution_times': [],
        'api_call_costs': 0
    }
    
    # Analyze performance logs - focus on business question sessions
    for record in perf_logs:
        if 'Business Question Session Completed' in record.get('message', ''):
            metrics['total_requests'] += 1
            
            # If no explicit success field, assume success if no errors
            success = record.get('success')
            if success is None:
                request_id = record.get('request_id')
                has_errors = any(err_record.get('request_id') == request_id for err_record in error_logs)
                success = not has_errors
            
            if success:
                metrics['successful_requests'] += 1
            else:
                metrics['failed_requests'] += 1
            
            # Session duration (end-to-end business question experience)
            session_duration = record.get('session_duration_ms', 0)
            metrics['response_times'].append(session_duration)
            
            # API calls and tokens
            api_calls = record.get('api_calls', 0)
            tokens = record.get('tokens_used', 0)
            metrics['total_api_calls'] += api_calls
            metrics['total_tokens_used'] += tokens
            
            # Hourly distribution
            timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
            hour_key = timestamp.strftime('%Y-%m-%d %H:00')
            metrics['hourly_request_count'][hour_key] += 1
            
            # User questions
            question = record.get('user_question', '')
            if question:
                metrics['top_questions'][question[:50] + '...' if len(question) > 50 else question] += 1
        
        # Tool usage
        tool_name = record.get('tool_name')
        if tool_name:
            metrics['tool_usage'][tool_name] += 1
            
            # SQL execution times
            if tool_name == 'run_sql_query' and 'duration_ms' in record:
                metrics['sql_execution_times'].append(record['duration_ms'])
    
    # Analyze API logs
    for record in api_logs:
        total_tokens = record.get('total_tokens', 0)
        # Estimate cost (GPT-4o pricing: ~$0.005 per 1K tokens)
        metrics['api_call_costs'] += total_tokens * 0.005 / 1000
    
    # Analyze error logs
    for record in error_logs:
        error_type = record.get('error_type', 'Unknown')
        metrics['error_types'][error_type] += 1
    
    # Analyze main logs for endpoints
    for record in main_logs:
        if 'Started request' in record.get('message', ''):
            endpoint = record.get('message', '').split(': ')[-1]
            metrics['endpoint_usage'][endpoint] += 1
    
    # Calculate averages
    if metrics['response_times']:
        metrics['avg_response_time_ms'] = statistics.mean(metrics['response_times'])
        metrics['p95_response_time_ms'] = statistics.quantiles(metrics['response_times'], n=20)[18]  # 95th percentile
        metrics['p99_response_time_ms'] = statistics.quantiles(metrics['response_times'], n=100)[98]  # 99th percentile
    
    if metrics['sql_execution_times']:
        metrics['avg_sql_execution_ms'] = statistics.mean(metrics['sql_execution_times'])
    
    if metrics['total_requests'] > 0:
        metrics['avg_tokens_per_request'] = metrics['total_tokens_used'] / metrics['total_requests']
        metrics['success_rate'] = (metrics['successful_requests'] / metrics['total_requests']) * 100
    
    return metrics

def print_dashboard():
    """Print formatted performance dashboard"""
    metrics = generate_performance_report()
    
    print("=" * 80)
    print("MCP AGENT PERFORMANCE DASHBOARD")
    print("=" * 80)
    
    print("\nREQUEST METRICS")
    print(f"Total Requests: {metrics['total_requests']}")
    print(f"Successful: {metrics['successful_requests']} ({metrics.get('success_rate', 0):.1f}%)")
    print(f"Failed: {metrics['failed_requests']}")
    
    print("\nBUSINESS SESSION PERFORMANCE")
    print(f"Avg Question-to-Answer Time: {metrics['avg_response_time_ms']:.1f}ms ({metrics['avg_response_time_ms']/1000:.1f}s)")
    if 'p95_response_time_ms' in metrics:
        print(f"95th Percentile: {metrics['p95_response_time_ms']:.1f}ms ({metrics['p95_response_time_ms']/1000:.1f}s)")
        print(f"99th Percentile: {metrics['p99_response_time_ms']:.1f}ms ({metrics['p99_response_time_ms']/1000:.1f}s)")
    if 'avg_sql_execution_ms' in metrics:
        print(f"Avg SQL Execution: {metrics['avg_sql_execution_ms']:.1f}ms")
    
    print("\nAI USAGE PER BUSINESS QUESTION")
    print(f"Avg API Calls per Question: {metrics['total_api_calls'] / max(metrics['total_requests'], 1):.1f}")
    print(f"Total Tokens Used: {metrics['total_tokens_used']:,}")
    print(f"Avg Tokens per Question: {metrics['avg_tokens_per_request']:.0f}")
    print(f"Estimated Cost per Question: ${metrics['api_call_costs'] / max(metrics['total_requests'], 1):.4f}")
    print(f"Total Estimated Cost: ${metrics['api_call_costs']:.4f}")
    
    print("\nTOOL USAGE")
    for tool, count in metrics['tool_usage'].most_common(10):
        print(f"  {tool}: {count}")
    
    print("\nENDPOINT USAGE")
    for endpoint, count in metrics['endpoint_usage'].most_common():
        print(f"  {endpoint}: {count}")
    
    print("\nERROR ANALYSIS")
    if metrics['error_types']:
        for error, count in metrics['error_types'].most_common():
            print(f"  {error}: {count}")
    else:
        print("  No errors recorded")
    
    print("\nTOP QUESTIONS")
    for question, count in metrics['top_questions'].most_common(5):
        print(f"  ({count}x) {question}")
    
    print("\nHOURLY REQUEST DISTRIBUTION")
    sorted_hours = sorted(metrics['hourly_request_count'].items())
    for hour, count in sorted_hours[-10:]:  # Last 10 hours
        print(f"  {hour}: {count} requests")
    
    print("=" * 80)

def export_metrics_json():
    """Export metrics as JSON for external monitoring"""
    metrics = generate_performance_report()
    
    with open('logs/metrics_summary.json', 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    
    print("Metrics exported to logs/metrics_summary.json")

if __name__ == "__main__":
    print_dashboard()
    export_metrics_json()