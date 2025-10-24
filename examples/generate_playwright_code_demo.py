"""
Demo: Generate Playwright Code from Browser-Use Automation

This script shows how to use browser-use to perform automation,
then automatically generate reusable Playwright code from it.

Usage:
    python examples/generate_playwright_code_demo.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from browser_use import Agent
from browser_use.llm import ChatOpenAI
from browser_use_codebase.playwright_code_generator import generate_playwright_code_from_history
from dotenv import load_dotenv

load_dotenv()


async def demo_code_generation():
    """
    Demonstrate converting browser-use automation to Playwright code
    """
    
    # Check for API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key to run this demo")
        return
    
    print("="*80)
    print("🎭 Browser-Use to Playwright Code Generator Demo")
    print("="*80)
    print()
    
    # Example task
    task = "Go to Google and search for 'Playwright testing'"
    print(f"📋 Task: {task}")
    print()
    
    # Create browser-use agent
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=api_key,
        timeout=60
    )
    
    agent = Agent(
        task=task,
        llm=llm
    )
    
    print("🤖 Running browser automation...")
    print("   (This will open a browser window)")
    print()
    
    try:
        # Run automation and capture history
        history = await agent.run(max_steps=10)
        
        print("✅ Automation complete!")
        print(f"   Steps taken: {len(history.history)}")
        print(f"   Task completed: {history.is_done()}")
        print()
        
        # Generate Playwright code
        print("🔄 Converting to Playwright code...")
        print()
        
        playwright_code = generate_playwright_code_from_history(
            history,
            task_description=f"Automation: {task}",
            output_file="generated_playwright_script.py"
        )
        
        print("✅ Playwright code generated!")
        print()
        print("="*80)
        print("📄 Generated Code:")
        print("="*80)
        print()
        print(playwright_code)
        print()
        print("="*80)
        print("💾 Code saved to: generated_playwright_script.py")
        print()
        print("To run the generated script:")
        print("  1. Install playwright: pip install playwright")
        print("  2. Install browsers: playwright install chromium")
        print("  3. Run: python generated_playwright_script.py")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Error during automation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print()
    print("This demo will:")
    print("  1. Run a browser automation task using browser-use")
    print("  2. Extract the automation steps")
    print("  3. Generate equivalent Playwright Python code")
    print("  4. Save the code to a file")
    print()
    input("Press Enter to continue...")
    print()
    
    asyncio.run(demo_code_generation())
