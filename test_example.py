#!/usr/bin/env python3

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_health():
    print("🔍 Checking API health...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"✅ API Status: {response.json()}")
    print()

def execute_simple_test():
    print("🚀 Executing a simple test plan...")
    print("   (This will start the MCP server automatically)")
    print()
    
    test_plan = {
        "id": "simple_test",
        "name": "Simple Navigation Test",
        "description": "Test MCP server startup",
        "browser": "chrome",
        "headless": True,
        "steps": [
            {
                "action": "navigate",
                "description": "Open example.com",
                "target": "https://www.example.com",
                "timeout": 10000
            },
            {
                "action": "snapshot",
                "description": "Capture page state",
                "timeout": 3000
            },
            {
                "action": "wait",
                "description": "Wait 2 seconds",
                "timeout": 2000
            }
        ]
    }
    
    print("📋 Test Plan:")
    print(json.dumps(test_plan, indent=2))
    print()
    print("⏳ Sending request to API...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/execute",
            json=test_plan,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Execution Complete!")
            print(f"   Execution ID: {result['execution_id']}")
            print(f"   Status: {result['status']}")
            print(f"   Total Steps: {result['total_steps']}")
            print(f"   Successful Steps: {result['successful_steps']}")
            print(f"   Failed Steps: {result['failed_steps']}")
            print(f"\n📊 MCP Statistics:")
            print(f"   Tool Calls: {result['mcp_tool_calls']}")
            print(f"   DOM Elements Analyzed: {result['dom_elements_analyzed']}")
            print(f"   Locators Corrected: {result['locators_corrected']}")
            print(f"   Total Retries: {result['total_retries']}")
            print(f"   Screenshots Captured: {result['screenshots_captured']}")
            
            return result['execution_id']
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Error executing test: {str(e)}")
        return None

def get_execution_details(execution_id):
    if not execution_id:
        return
    
    print(f"\n📄 Fetching execution details...")
    response = requests.get(f"{BASE_URL}/api/executions/{execution_id}")
    
    if response.status_code == 200:
        details = response.json()
        print(f"\n✨ Execution Details:")
        print(f"   Test Name: {details['test_plan_name']}")
        print(f"   Status: {details['status']}")
        print(f"   Start Time: {details['start_time']}")
        print(f"   End Time: {details.get('end_time', 'N/A')}")
        
        if details.get('steps'):
            print(f"\n📝 Steps Executed:")
            for step in details['steps']:
                status_emoji = "✅" if step['status'] == "success" else "❌"
                print(f"   {status_emoji} Step {step['step_number']}: {step['description']}")
                if step.get('locator_used'):
                    print(f"      Locator: {step['locator_used']} (confidence: {step.get('locator_confidence', 0):.2f})")

if __name__ == "__main__":
    print("=" * 60)
    print("AI Automation Runner - MCP Integration Test")
    print("=" * 60)
    print()
    
    test_health()
    execution_id = execute_simple_test()
    get_execution_details(execution_id)
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
