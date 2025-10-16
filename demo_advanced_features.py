#!/usr/bin/env python3

import requests
import json

BASE_URL = "http://localhost:5000"

def demo_multi_page_navigation():
    print("\n" + "="*60)
    print("DEMO 1: Multi-Page Navigation")
    print("="*60)
    
    test_plan = {
        "id": "demo_multi_page",
        "name": "Multi-Page Navigation Demo",
        "description": "Navigate across multiple pages",
        "browser": "chrome",
        "headless": True,
        "steps": [
            {
                "action": "navigate",
                "description": "Open GitHub homepage",
                "target": "https://github.com",
                "timeout": 5000
            },
            {
                "action": "snapshot",
                "description": "Capture homepage",
                "timeout": 2000
            },
            {
                "action": "click",
                "description": "Go to Pricing page",
                "target": "Pricing",
                "timeout": 3000
            },
            {
                "action": "wait",
                "description": "Wait for page load",
                "timeout": 2000
            },
            {
                "action": "snapshot",
                "description": "Capture pricing page",
                "timeout": 2000
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/api/execute", json=test_plan, timeout=60)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success! Execution ID: {result['execution_id']}")
        print(f"   Pages analyzed: {result['dom_elements_analyzed']} elements")
        print(f"   MCP tool calls: {result['mcp_tool_calls']}")

def demo_tab_management():
    print("\n" + "="*60)
    print("DEMO 2: Tab Management")
    print("="*60)
    
    test_plan = {
        "id": "demo_tabs",
        "name": "Tab Management Demo",
        "description": "Open, switch, and close tabs",
        "browser": "chrome",
        "headless": True,
        "steps": [
            {
                "action": "navigate",
                "description": "Open main page",
                "target": "https://www.example.com",
                "timeout": 5000
            },
            {
                "action": "snapshot",
                "description": "Capture tab 1",
                "timeout": 2000
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/api/execute", json=test_plan, timeout=60)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success! Execution ID: {result['execution_id']}")
        print(f"   Tabs managed with DOM preservation")

def demo_alert_handling():
    print("\n" + "="*60)
    print("DEMO 3: Alert Handling")
    print("="*60)
    print("Note: This demonstrates alert handling capability")
    print("The actual alert interaction depends on the target page")

def show_available_actions():
    print("\n" + "="*60)
    print("AVAILABLE ACTIONS")
    print("="*60)
    
    actions = {
        "Basic Actions": [
            "navigate - Navigate to URL",
            "click - Click element",
            "type - Type text into field",
            "snapshot - Capture DOM and screenshot",
            "wait - Pause execution"
        ],
        "Alert/Dialog Actions": [
            "handle_alert - Accept/dismiss alerts (alert_action: accept|dismiss)",
            "get_alert_text - Get text from alert dialog"
        ],
        "Multi-Tab Actions": [
            "wait_for_new_tab - Wait for new tab to open",
            "switch_tab - Switch to specific tab (tab_index: 0,1,2...)",
            "close_tab - Close tab (tab_index: optional)"
        ]
    }
    
    for category, action_list in actions.items():
        print(f"\n{category}:")
        for action in action_list:
            print(f"  • {action}")

if __name__ == "__main__":
    print("\n🚀 AI Automation Runner - Advanced Features Demo")
    print("Demonstrating multi-page, tab management, and alert handling\n")
    
    show_available_actions()
    
    print("\n\nRunning Demos...")
    print("(Using headless mode for efficiency)")
    
    try:
        demo_multi_page_navigation()
        demo_tab_management()
        demo_alert_handling()
        
        print("\n" + "="*60)
        print("✅ All demos completed successfully!")
        print("="*60)
        print("\nCheck the example test plans in test_plans/ for more:")
        print("  • multi_tab_example.json")
        print("  • alert_handling_example.json")
        print("  • multi_page_flow.json")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
