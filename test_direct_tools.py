#!/usr/bin/env python3
"""
Test script for direct-first architecture implementation
"""
import requests
import json
import time

def test_direct_tools_endpoint():
    """Test the /list_tools endpoint includes direct tools"""
    
    print("🔧 Testing /list_tools endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/list_tools", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Total tools found: {len(data['tools'])}")
            print(f"📊 Tool categories: {data.get('tool_categories', {})}")
            
            # Look for direct tools
            direct_tools = [tool for tool in data['tools'] if tool.get('is_direct_tool', False)]
            
            if direct_tools:
                print(f"⚡ Direct tools found: {len(direct_tools)}")
                for tool in direct_tools:
                    print(f"   - {tool['name']}: {tool['description']}")
                    if tool.get('pattern_examples'):
                        print(f"     Examples: {tool['pattern_examples'][:2]}")
            else:
                print("⚠️ No direct tools found in registry")
                
            return True
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_direct_tool_call():
    """Test calling a direct tool via /call_tool"""
    
    print("\n🎯 Testing direct tool call...")
    
    # Test competitor mapping direct tool
    payload = {
        "tool": "direct_competitor_mapping", 
        "args": {
            "question": "Replace Hogy BD Luer-Lock Syringe 2.5mL with our equivalent"
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/call_tool",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Direct tool call successful!")
            print(f"🔍 Tool type: {data.get('tool_type')}")
            print(f"👤 Persona: {data.get('persona')}")
            print(f"🛤️ Execution path: {data.get('execution_path')}")
            
            result = data.get('result', {})
            print(f"⏱️ Execution time: {result.get('execution_time_ms', 'N/A')}ms")
            print(f"📝 Results found: {result.get('result_count', 0)}")
            
            return True
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_agentic_endpoint_with_direct_pattern():
    """Test /mcp endpoint with a pattern that should trigger direct tools"""
    
    print("\n🤖 Testing /mcp agentic endpoint with direct pattern...")
    
    payload = {
        "question": "Replace Hogy BD Luer-Lock Syringe 2.5mL with our equivalent"
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/mcp",
            json=payload,
            timeout=30
        )
        execution_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Agentic endpoint successful!")
            print(f"⏱️ Total execution time: {execution_time:.2f}s")
            print(f"🎯 Classification: {data.get('classification', {}).get('intent', 'N/A')}")
            print(f"👤 Persona: {data.get('classification', {}).get('persona', 'N/A')}")
            
            # Check if direct tools were used
            tool_results = data.get('tool_chain_results', {})
            
            if 'direct_tool_execution' in tool_results:
                print("⚡ Direct tool path taken!")
                direct_info = tool_results['direct_tool_execution']
                print(f"   Tool used: {direct_info.get('tool_used')}")
                print(f"   Execution time: {direct_info.get('execution_time_ms')}ms")
                print(f"   Pattern matched: {direct_info.get('pattern_matched')}")
                
                if 'stage3_evaluation' in tool_results:
                    print("🧠 AI evaluation completed")
                    eval_result = tool_results['stage3_evaluation']
                    print(f"   Business answer: {eval_result.get('business_answer', '')[:100]}...")
                
            elif 'execution_path' in tool_results:
                execution_path = tool_results.get('execution_path', 'unknown')
                print(f"🛤️ Execution path: {execution_path}")
                
                if execution_path == "ai_workflow_fallback":
                    print("🔄 Fallback to AI workflow occurred")
            
            # Show response preview
            response_preview = data.get('response', '')[:200]
            print(f"📝 Response preview: {response_preview}...")
            
            return True
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_agentic_endpoint_without_direct_pattern():
    """Test /mcp endpoint with a pattern that should NOT trigger direct tools (fallback test)"""
    
    print("\n🔄 Testing /mcp endpoint fallback (non-direct pattern)...")
    
    payload = {
        "question": "What are the components in MRH-011C?"
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/mcp",
            json=payload,
            timeout=30
        )
        execution_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Fallback test successful!")
            print(f"⏱️ Total execution time: {execution_time:.2f}s")
            print(f"🎯 Classification: {data.get('classification', {}).get('intent', 'N/A')}")
            
            # Should NOT have direct tool execution
            tool_results = data.get('tool_chain_results', {})
            
            if 'direct_tool_execution' in tool_results:
                print("⚠️ Unexpected: Direct tool was used for non-direct pattern")
            else:
                print("✅ Correct: No direct tool used, AI workflow executed")
                
                execution_path = tool_results.get('execution_path', 'unknown')
                print(f"🛤️ Execution path: {execution_path}")
            
            return True
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    """Run all tests"""
    
    print("🚀 Testing Direct-First Architecture Implementation")
    print("=" * 60)
    
    print("ℹ️ Make sure the server is running: python main.py")
    print("ℹ️ Server should be available at: http://localhost:8000")
    print()
    
    tests = [
        test_direct_tools_endpoint,
        test_direct_tool_call,
        test_agentic_endpoint_with_direct_pattern,
        test_agentic_endpoint_without_direct_pattern
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    print(f"📈 Success Rate: {(sum(results)/len(results)*100):.1f}%")
    
    if all(results):
        print("\n🎉 All tests passed! Direct-first architecture is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()