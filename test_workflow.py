#!/usr/bin/env python3
"""
Test script to verify the complete workflow:
1. Run browser-use automation
2. Generate Playwright code
3. Execute with self-healing
"""

import asyncio
import os
from automation_engine import BrowserAutomationEngine


async def test_code_generation():
    """Test generating code from browser-use automation"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    print("="*60)
    print("TEST: Code Generation from Browser-Use Automation")
    print("="*60)
    
    engine = BrowserAutomationEngine(
        api_key=api_key,
        model="gpt-4o-mini",
        headless=False,
        verbose=True,
        generate_code=True
    )
    
    task = "go to example.com and tell me the page title"
    
    try:
        print(f"\n🎯 Running task: {task}")
        response = await engine.run_task(task, output_file="test_generated.py")
        
        print("\n" + "="*60)
        print("RESULTS:")
        print("="*60)
        print(f"Task Result: {response.get('result')}")
        print(f"Code Generated: {'Yes' if response.get('generated_code') else 'No'}")
        print(f"Code File: {response.get('code_file')}")
        
        if response.get('generated_code'):
            print("\n" + "-"*60)
            print("GENERATED CODE PREVIEW:")
            print("-"*60)
            lines = response['generated_code'].split('\n')[:30]
            print('\n'.join(lines))
            if len(response['generated_code'].split('\n')) > 30:
                print("... (truncated)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    success = await test_code_generation()
    
    print("\n" + "="*60)
    if success:
        print("✅ Test completed successfully!")
        print("\nNext steps:")
        print("1. Check test_generated.py for the generated code")
        print("2. Run: python main.py --execute-code test_generated.py")
        print("   (This will execute with self-healing enabled)")
    else:
        print("❌ Test failed - check errors above")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
