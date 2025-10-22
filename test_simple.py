#!/usr/bin/env python3
import asyncio
import sys
from automation_engine import BrowserAutomationEngine
import os

async def test():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found")
        sys.exit(1)
    
    print("Testing AI Browser Automation CLI")
    print("Task: Go to example.com and get the page title")
    
    engine = BrowserAutomationEngine(
        api_key=api_key,
        model="gpt-4o-mini",
        headless=True,
        verbose=True
    )
    
    result = await engine.run_task("Go to example.com and tell me the page title")
    print(f"\n\nFinal Result: {result}")

if __name__ == "__main__":
    asyncio.run(test())
