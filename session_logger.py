"""
Session-based logging for easier debugging and tracing
"""
import json
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional

class SessionLogger:
    def __init__(self, request_id: str, user_question: str = None):
        self.request_id = request_id
        self.session_start = time.time()
        self.user_question = user_question
        self.events = []
        
        # Create logs/sessions directory
        os.makedirs('logs/sessions', exist_ok=True)
        
        # Log file per session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f"logs/sessions/session_{timestamp}_{request_id[:8]}.log"
        
        # Start session
        self.log_event("SESSION_START", {
            "user_question": user_question,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_event(self, event_type: str, data: Dict[str, Any] = None):
        """Log an event in the session"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_ms": (time.time() - self.session_start) * 1000,
            "event_type": event_type,
            "request_id": self.request_id,
            "data": data or {}
        }
        
        self.events.append(event)
        
        # Write to file immediately for real-time debugging
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    def log_intent_classification(self, classification: Dict[str, Any], tokens_used: int):
        """Log intent classification step"""
        self.log_event("INTENT_CLASSIFICATION", {
            "classification": classification,
            "tokens_used": tokens_used,
            "persona": classification.get("persona"),
            "execution_strategy": classification.get("execution_strategy"),
            "confidence": classification.get("confidence")
        })
    
    def log_sql_execution(self, stage: str, sql: str, execution_time_ms: float, result_count: int):
        """Log SQL execution"""
        self.log_event("SQL_EXECUTION", {
            "stage": stage,
            "sql": sql[:200] + "..." if len(sql) > 200 else sql,
            "execution_time_ms": execution_time_ms,
            "result_count": result_count
        })
    
    def log_data_compression(self, stage: str, original_size: int, compressed_size: int, compression_ratio: float):
        """Log data compression statistics"""
        self.log_event("DATA_COMPRESSION", {
            "stage": stage,
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio,
            "token_savings": original_size - compressed_size
        })
    
    def log_api_call(self, purpose: str, model: str, prompt_tokens: int, completion_tokens: int):
        """Log API call details"""
        total_tokens = prompt_tokens + completion_tokens
        self.log_event("API_CALL", {
            "purpose": purpose,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": self._estimate_cost(prompt_tokens, completion_tokens)
        })
    
    def log_stage_transition(self, from_stage: str, to_stage: str, intermediate_data: Any = None):
        """Log multi-stage transitions"""
        self.log_event("STAGE_TRANSITION", {
            "from_stage": from_stage,
            "to_stage": to_stage,
            "intermediate_summary": str(intermediate_data)[:100] + "..." if intermediate_data else None
        })
    
    def log_error(self, error: Exception, context: str):
        """Log errors with context"""
        self.log_event("ERROR", {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        })
    
    def log_session_end(self, success: bool, final_response: str = None):
        """Log session completion"""
        total_duration = (time.time() - self.session_start) * 1000
        
        # Calculate session statistics
        api_calls = len([e for e in self.events if e["event_type"] == "API_CALL"])
        total_tokens = sum([e["data"].get("total_tokens", 0) for e in self.events if e["event_type"] == "API_CALL"])
        total_cost = sum([e["data"].get("estimated_cost", 0) for e in self.events if e["event_type"] == "API_CALL"])
        compression_savings = sum([e["data"].get("token_savings", 0) for e in self.events if e["event_type"] == "DATA_COMPRESSION"])
        
        self.log_event("SESSION_END", {
            "success": success,
            "total_duration_ms": total_duration,
            "api_calls": api_calls,
            "total_tokens": total_tokens,
            "estimated_cost": total_cost,
            "compression_savings": compression_savings,
            "final_response_length": len(final_response) if final_response else 0
        })
        
        # Write session summary to main log for overview
        summary = {
            "session_id": self.request_id,
            "user_question": self.user_question,
            "duration_ms": total_duration,
            "tokens": total_tokens,
            "cost": total_cost,
            "compression_savings": compression_savings,
            "log_file": self.log_file,
            "success": success
        }
        
        with open('logs/session_summary.log', 'a') as f:
            f.write(json.dumps(summary) + '\n')
    
    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost based on GPT-4o pricing"""
        prompt_cost = (prompt_tokens / 1000) * 0.005  # $5 per 1M tokens
        completion_cost = (completion_tokens / 1000) * 0.015  # $15 per 1M tokens
        return prompt_cost + completion_cost
    
    def get_session_trace(self) -> str:
        """Get formatted session trace for debugging"""
        trace_lines = []
        trace_lines.append(f"=== SESSION TRACE: {self.request_id} ===")
        trace_lines.append(f"Question: {self.user_question}")
        trace_lines.append("")
        
        for event in self.events:
            elapsed = event["elapsed_ms"]
            event_type = event["event_type"]
            data = event["data"]
            
            if event_type == "INTENT_CLASSIFICATION":
                trace_lines.append(f"[{elapsed:6.0f}ms] INTENT: {data.get('persona')} ({data.get('execution_strategy')}) - {data.get('tokens_used')} tokens")
            elif event_type == "SQL_EXECUTION":
                trace_lines.append(f"[{elapsed:6.0f}ms] SQL {data.get('stage')}: {data.get('result_count')} results in {data.get('execution_time_ms'):.0f}ms")
            elif event_type == "DATA_COMPRESSION":
                trace_lines.append(f"[{elapsed:6.0f}ms] COMPRESSION {data.get('stage')}: {data.get('compression_ratio'):.1%} saved {data.get('token_savings')} chars")
            elif event_type == "API_CALL":
                trace_lines.append(f"[{elapsed:6.0f}ms] API {data.get('purpose')}: {data.get('total_tokens')} tokens (${data.get('estimated_cost'):.4f})")
            elif event_type == "STAGE_TRANSITION":
                trace_lines.append(f"[{elapsed:6.0f}ms] TRANSITION: {data.get('from_stage')} → {data.get('to_stage')}")
            elif event_type == "ERROR":
                trace_lines.append(f"[{elapsed:6.0f}ms] ERROR in {data.get('context')}: {data.get('error_message')}")
            elif event_type == "SESSION_END":
                trace_lines.append(f"[{elapsed:6.0f}ms] END: {data.get('total_tokens')} tokens, ${data.get('estimated_cost'):.4f}, {data.get('compression_savings')} chars saved")
        
        return "\n".join(trace_lines)

# Global session registry
_active_sessions = {}

def get_session_logger(request_id: str, user_question: str = None) -> SessionLogger:
    """Get or create session logger"""
    if request_id not in _active_sessions:
        _active_sessions[request_id] = SessionLogger(request_id, user_question)
    return _active_sessions[request_id]

def close_session(request_id: str):
    """Close and cleanup session"""
    if request_id in _active_sessions:
        del _active_sessions[request_id]