#!/usr/bin/env python3
"""
View session logs for easy debugging
"""
import os
import json
import sys
from datetime import datetime

def list_recent_sessions(limit=10):
    """List recent session files"""
    sessions_dir = "logs/sessions"
    if not os.path.exists(sessions_dir):
        print("No sessions directory found")
        return []
    
    session_files = [f for f in os.listdir(sessions_dir) if f.endswith('.log')]
    session_files.sort(reverse=True)  # Most recent first
    
    print(f"=== Recent Sessions (showing {min(limit, len(session_files))}) ===")
    
    recent_sessions = []
    for i, filename in enumerate(session_files[:limit]):
        filepath = os.path.join(sessions_dir, filename)
        try:
            with open(filepath, 'r') as f:
                first_line = f.readline()
                if first_line.strip():
                    session_data = json.loads(first_line)
                    user_question = session_data.get('data', {}).get('user_question', 'N/A')
                    timestamp = session_data.get('timestamp', 'N/A')
                    
                    print(f"{i+1:2d}. {filename}")
                    print(f"    Time: {timestamp}")
                    print(f"    Question: {user_question[:80]}..." if len(str(user_question)) > 80 else f"    Question: {user_question}")
                    print()
                    
                    recent_sessions.append({
                        'index': i+1,
                        'filename': filename,
                        'filepath': filepath,
                        'question': user_question
                    })
        except Exception as e:
            print(f"    Error reading {filename}: {e}")
    
    return recent_sessions

def view_session_trace(session_file):
    """View detailed session trace"""
    if not os.path.exists(session_file):
        print(f"Session file not found: {session_file}")
        return
    
    print(f"\n=== SESSION TRACE: {os.path.basename(session_file)} ===")
    
    events = []
    try:
        with open(session_file, 'r') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
    except Exception as e:
        print(f"Error reading session file: {e}")
        return
    
    if not events:
        print("No events found in session")
        return
    
    # Session overview
    start_event = events[0] if events else None
    end_event = events[-1] if events and events[-1].get('event_type') == 'SESSION_END' else None
    
    if start_event:
        user_question = start_event.get('data', {}).get('user_question', 'N/A')
        print(f"Question: {user_question}")
        print()
    
    # Event timeline
    for event in events:
        elapsed = event.get('elapsed_ms', 0)
        event_type = event.get('event_type', 'UNKNOWN')
        data = event.get('data', {})
        
        if event_type == "SESSION_START":
            print(f"[{elapsed:6.0f}ms] [START] SESSION START")
            
        elif event_type == "INTENT_CLASSIFICATION":
            persona = data.get('persona', 'unknown')
            strategy = data.get('execution_strategy', 'unknown')
            tokens = data.get('tokens_used', 0)
            confidence = data.get('confidence', 0)
            print(f"[{elapsed:6.0f}ms] [INTENT] {persona} ({strategy}) - {tokens} tokens (confidence: {confidence})")
            
        elif event_type == "SQL_EXECUTION":
            stage = data.get('stage', 'unknown')
            result_count = data.get('result_count', 0)
            exec_time = data.get('execution_time_ms', 0)
            print(f"[{elapsed:6.0f}ms] [SQL] {stage}: {result_count} results in {exec_time:.0f}ms")
            
        elif event_type == "DATA_COMPRESSION":
            stage = data.get('stage', 'unknown')
            ratio = data.get('compression_ratio', 0)
            savings = data.get('token_savings', 0)
            print(f"[{elapsed:6.0f}ms] [COMPRESS] {stage}: {ratio:.1%} ratio, saved {savings} chars")
            
        elif event_type == "API_CALL":
            purpose = data.get('purpose', 'unknown')
            total_tokens = data.get('total_tokens', 0)
            cost = data.get('estimated_cost', 0)
            print(f"[{elapsed:6.0f}ms] [API] {purpose}: {total_tokens} tokens (${cost:.4f})")
            
        elif event_type == "STAGE_TRANSITION":
            from_stage = data.get('from_stage', 'unknown')
            to_stage = data.get('to_stage', 'unknown')
            print(f"[{elapsed:6.0f}ms] [TRANSITION] {from_stage} -> {to_stage}")
            
        elif event_type == "ERROR":
            context = data.get('context', 'unknown')
            error_msg = data.get('error_message', 'unknown')
            print(f"[{elapsed:6.0f}ms] [ERROR] in {context}: {error_msg}")
            
        elif event_type == "SESSION_END":
            total_tokens = data.get('total_tokens', 0)
            cost = data.get('estimated_cost', 0)
            compression_savings = data.get('compression_savings', 0)
            success = data.get('success', False)
            status = "SUCCESS" if success else "FAILED"
            print(f"[{elapsed:6.0f}ms] [END] {status}: {total_tokens} tokens, ${cost:.4f}, saved {compression_savings} chars")
    
    # Session summary
    if end_event:
        print(f"\n=== SUMMARY ===")
        data = end_event.get('data', {})
        print(f"Duration: {data.get('total_duration_ms', 0):.0f}ms")
        print(f"API Calls: {data.get('api_calls', 0)}")
        print(f"Total Tokens: {data.get('total_tokens', 0):,}")
        print(f"Estimated Cost: ${data.get('estimated_cost', 0):.4f}")
        print(f"Compression Savings: {data.get('compression_savings', 0)} characters")

def main():
    if len(sys.argv) > 1:
        # View specific session by index or filename
        arg = sys.argv[1]
        
        if arg.isdigit():
            # View by index
            sessions = list_recent_sessions(20)
            index = int(arg) - 1
            if 0 <= index < len(sessions):
                view_session_trace(sessions[index]['filepath'])
            else:
                print(f"Invalid session index: {arg}")
        else:
            # View by filename
            session_file = f"logs/sessions/{arg}" if not arg.startswith('logs/') else arg
            view_session_trace(session_file)
    else:
        # List recent sessions
        sessions = list_recent_sessions()
        if sessions:
            print("Usage:")
            print("  python view_session.py <number>  - View session by index")
            print("  python view_session.py <filename> - View session by filename")

if __name__ == "__main__":
    main()