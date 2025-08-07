"""
Comprehensive logging and performance tracking for MCP Agent
"""
import logging
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
import inspect
import traceback

# Configure structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'user_question'):
            log_data['user_question'] = record.user_question
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms
        if hasattr(record, 'error_type'):
            log_data['error_type'] = record.error_type
        if hasattr(record, 'tool_name'):
            log_data['tool_name'] = record.tool_name
        if hasattr(record, 'classification'):
            log_data['classification'] = record.classification
        if hasattr(record, 'api_calls'):
            log_data['api_calls'] = record.api_calls
        if hasattr(record, 'tokens_used'):
            log_data['tokens_used'] = record.tokens_used
        if hasattr(record, 'sql_query'):
            log_data['sql_query'] = record.sql_query
        if hasattr(record, 'result_count'):
            log_data['result_count'] = record.result_count
            
        return json.dumps(log_data)

def setup_logging():
    """Setup comprehensive logging configuration"""
    
    # Ensure logs directory exists
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Main application logger
    main_logger = logging.getLogger("mcp_agent")
    main_logger.setLevel(logging.INFO)
    
    # Performance logger
    perf_logger = logging.getLogger("mcp_agent.performance")
    perf_logger.setLevel(logging.INFO)
    
    # Error logger
    error_logger = logging.getLogger("mcp_agent.errors")
    error_logger.setLevel(logging.ERROR)
    
    # API calls logger
    api_logger = logging.getLogger("mcp_agent.api")
    api_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    for logger in [main_logger, perf_logger, error_logger, api_logger]:
        logger.handlers.clear()
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    
    # File handlers
    main_file_handler = logging.FileHandler('logs/mcp_agent.log')
    main_file_handler.setFormatter(JSONFormatter())
    
    perf_file_handler = logging.FileHandler('logs/performance.log')
    perf_file_handler.setFormatter(JSONFormatter())
    
    error_file_handler = logging.FileHandler('logs/errors.log')
    error_file_handler.setFormatter(JSONFormatter())
    
    api_file_handler = logging.FileHandler('logs/api_calls.log')
    api_file_handler.setFormatter(JSONFormatter())
    
    # Add handlers
    main_logger.addHandler(console_handler)
    main_logger.addHandler(main_file_handler)
    
    perf_logger.addHandler(perf_file_handler)
    error_logger.addHandler(error_file_handler)
    api_logger.addHandler(api_file_handler)
    
    return {
        'main': main_logger,
        'performance': perf_logger,
        'errors': error_logger,
        'api': api_logger
    }

# Global performance tracker
class PerformanceTracker:
    def __init__(self):
        self.metrics = {}
        self.loggers = setup_logging()
    
    def start_request(self, request_id: str, endpoint: str, user_question: str = None):
        """Start tracking a new business question session"""
        self.metrics[request_id] = {
            'request_id': request_id,
            'endpoint': endpoint,
            'user_question': user_question,
            'session_start_time': time.time(),
            'api_calls': 0,
            'tokens_used': 0,
            'tools_executed': [],
            'errors': [],
            'classification': None,
            'sql_queries': [],
            'result_counts': [],
            'session_phases': {
                'intent_classification': {'start': None, 'end': None, 'tokens': 0},
                'sql_generation': {'start': None, 'end': None, 'tokens': 0},
                'sql_execution': {'start': None, 'end': None, 'duration_ms': 0},
                'result_processing': {'start': None, 'end': None}
            }
        }
        
        self.loggers['main'].info(
            f"Started request: {endpoint}",
            extra={
                'request_id': request_id,
                'user_question': user_question,
                'endpoint': endpoint
            }
        )
    
    def log_api_call(self, request_id: str, model: str, prompt_tokens: int, completion_tokens: int, purpose: str):
        """Log an API call with token usage and track session phases"""
        if request_id in self.metrics:
            self.metrics[request_id]['api_calls'] += 1
            self.metrics[request_id]['tokens_used'] += prompt_tokens + completion_tokens
            
            # Track phase timing and tokens
            phases = self.metrics[request_id]['session_phases']
            current_time = time.time()
            
            if purpose == 'intent_classification':
                if phases['intent_classification']['start'] is None:
                    phases['intent_classification']['start'] = current_time
                phases['intent_classification']['end'] = current_time
                phases['intent_classification']['tokens'] += prompt_tokens + completion_tokens
            elif purpose == 'sql_generation':
                if phases['sql_generation']['start'] is None:
                    phases['sql_generation']['start'] = current_time
                phases['sql_generation']['end'] = current_time
                phases['sql_generation']['tokens'] += prompt_tokens + completion_tokens
        
        self.loggers['api'].info(
            f"API call: {purpose}",
            extra={
                'request_id': request_id,
                'model': model,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': prompt_tokens + completion_tokens,
                'purpose': purpose
            }
        )
    
    def log_tool_execution(self, request_id: str, tool_name: str, duration_ms: float, success: bool, result_count: int = None):
        """Log tool execution metrics"""
        if request_id in self.metrics:
            self.metrics[request_id]['tools_executed'].append({
                'tool': tool_name,
                'duration_ms': duration_ms,
                'success': success,
                'result_count': result_count
            })
            if result_count is not None:
                self.metrics[request_id]['result_counts'].append(result_count)
        
        self.loggers['performance'].info(
            f"Tool executed: {tool_name}",
            extra={
                'request_id': request_id,
                'tool_name': tool_name,
                'duration_ms': duration_ms,
                'success': success,
                'result_count': result_count
            }
        )
    
    def log_classification(self, request_id: str, classification: Dict[str, Any]):
        """Log intent classification results"""
        if request_id in self.metrics:
            self.metrics[request_id]['classification'] = classification
        
        self.loggers['main'].info(
            f"Intent classified: {classification.get('intent', 'unknown')}",
            extra={
                'request_id': request_id,
                'classification': classification
            }
        )
    
    def log_sql_query(self, request_id: str, sql: str, execution_time_ms: float, result_count: int):
        """Log SQL query execution and track session phases"""
        if request_id in self.metrics:
            self.metrics[request_id]['sql_queries'].append({
                'sql': sql[:200] + '...' if len(sql) > 200 else sql,  # Truncate long queries
                'execution_time_ms': execution_time_ms,
                'result_count': result_count
            })
            
            # Track SQL execution phase
            phases = self.metrics[request_id]['session_phases']
            current_time = time.time()
            
            if phases['sql_execution']['start'] is None:
                phases['sql_execution']['start'] = current_time - (execution_time_ms / 1000)
            phases['sql_execution']['end'] = current_time
            phases['sql_execution']['duration_ms'] += execution_time_ms
        
        self.loggers['performance'].info(
            "SQL query executed",
            extra={
                'request_id': request_id,
                'sql_query': sql[:200] + '...' if len(sql) > 200 else sql,
                'duration_ms': execution_time_ms,
                'result_count': result_count
            }
        )
    
    def log_error(self, request_id: str, error: Exception, context: str):
        """Log errors with full context"""
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'traceback': traceback.format_exc()
        }
        
        if request_id in self.metrics:
            self.metrics[request_id]['errors'].append(error_data)
        
        self.loggers['errors'].error(
            f"Error in {context}: {str(error)}",
            extra={
                'request_id': request_id,
                'error_type': type(error).__name__,
                'context': context,
                'traceback': traceback.format_exc()
            }
        )
    
    def end_request(self, request_id: str, success: bool = True):
        """Finish tracking business question session and log final metrics"""
        if request_id not in self.metrics:
            return
        
        metrics = self.metrics[request_id]
        session_end_time = time.time()
        total_session_duration = (session_end_time - metrics['session_start_time']) * 1000  # Convert to ms
        
        # Calculate phase durations
        phases = metrics['session_phases']
        phase_durations = {}
        
        for phase_name, phase_data in phases.items():
            if phase_data['start'] and phase_data['end']:
                phase_durations[f'{phase_name}_duration_ms'] = (phase_data['end'] - phase_data['start']) * 1000
            elif phase_name == 'sql_execution' and phase_data['duration_ms'] > 0:
                phase_durations[f'{phase_name}_duration_ms'] = phase_data['duration_ms']
        
        # Log business question session summary
        self.loggers['performance'].info(
            f"Business Question Session Completed: {metrics['endpoint']}",
            extra={
                'request_id': request_id,
                'session_duration_ms': total_session_duration,
                'api_calls': metrics['api_calls'],
                'tokens_used': metrics['tokens_used'],
                'tools_count': len(metrics['tools_executed']),
                'errors_count': len(metrics['errors']),
                'success': success,
                'user_question': metrics.get('user_question'),
                'classification': metrics.get('classification'),
                'total_results': sum(metrics['result_counts']) if metrics['result_counts'] else 0,
                'phase_breakdown': phase_durations,
                'intent_classification_tokens': phases['intent_classification']['tokens'],
                'sql_generation_tokens': phases['sql_generation']['tokens']
            }
        )
        
        # Clean up
        del self.metrics[request_id]

# Global tracker instance
tracker = PerformanceTracker()

def track_performance(tool_name: str):
    """Decorator to track function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to extract request_id from arguments
            request_id = kwargs.get('request_id') or getattr(args[0] if args else None, 'request_id', None)
            if not request_id:
                request_id = str(uuid.uuid4())[:8]
            
            start_time = time.time()
            success = True
            result = None
            
            try:
                result = func(*args, **kwargs)
                
                # Try to count results if it's a list or dict with results
                result_count = None
                if isinstance(result, dict) and 'results' in result:
                    if isinstance(result['results'], list):
                        result_count = len(result['results'])
                elif isinstance(result, list):
                    result_count = len(result)
                
                return result
                
            except Exception as e:
                success = False
                tracker.log_error(request_id, e, f"{tool_name}_execution")
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                result_count = None
                
                if result and isinstance(result, dict) and 'results' in result:
                    if isinstance(result['results'], list):
                        result_count = len(result['results'])
                
                tracker.log_tool_execution(request_id, tool_name, duration_ms, success, result_count)
        
        return wrapper
    return decorator

def generate_request_id():
    """Generate unique request ID"""
    return str(uuid.uuid4())

# Create logs directory if it doesn't exist
import os
if not os.path.exists('logs'):
    os.makedirs('logs')