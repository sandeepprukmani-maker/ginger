#!/usr/bin/env python3
"""
Example automation commands
Run these to see the automation system in action
"""

import asyncio
from automation import AutomationEngine


async def example_1_simple_navigation():
    """Example 1: Simple navigation"""
    print("\n" + "="*60)
    print("Example 1: Simple Navigation")
    print("="*60)
    
    engine = AutomationEngine()
    await engine.initialize()
    
    await engine.execute_automation("navigate to example.com")
    
    await engine.close()


async def example_2_search():
    """Example 2: Search automation"""
    print("\n" + "="*60)
    print("Example 2: Search Automation")
    print("="*60)
    
    engine = AutomationEngine()
    await engine.initialize()
    
    await engine.execute_automation(
        "go to google.com and search for 'Playwright automation'"
    )
    
    await engine.close()


async def example_3_complex():
    """Example 3: Complex multi-step automation"""
    print("\n" + "="*60)
    print("Example 3: Complex Automation")
    print("="*60)
    
    engine = AutomationEngine()
    await engine.initialize()
    
    await engine.execute_automation(
        "navigate to github.com, click on the explore button, and take a snapshot"
    )
    
    await engine.close()


async def example_4_data_extraction():
    """Example 4: Data extraction"""
    print("\n" + "="*60)
    print("Example 4: Data Extraction")
    print("="*60)
    
    engine = AutomationEngine()
    await engine.initialize()
    
    await engine.execute_automation(
        "go to hacker news homepage and get the titles of top stories"
    )
    
    await engine.close()


async def run_all_examples():
    """Run all examples"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║   🎯 Browser Automation Examples                            ║
║   Powered by Playwright MCP + LLM                           ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    examples = [
        example_1_simple_navigation,
        example_2_search,
        example_3_complex,
        example_4_data_extraction
    ]
    
    for i, example in enumerate(examples, 1):
        try:
            await example()
            print(f"\n✅ Example {i} completed")
        except Exception as e:
            print(f"\n❌ Example {i} failed: {e}")
        
        if i < len(examples):
            print("\nPress Enter to continue to next example...")
            input()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        example_num = int(sys.argv[1])
        examples = [
            example_1_simple_navigation,
            example_2_search,
            example_3_complex,
            example_4_data_extraction
        ]
        
        if 1 <= example_num <= len(examples):
            asyncio.run(examples[example_num - 1]())
        else:
            print(f"Invalid example number. Choose 1-{len(examples)}")
    else:
        asyncio.run(run_all_examples())
