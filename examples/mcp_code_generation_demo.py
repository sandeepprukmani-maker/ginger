"""
Demo: Generate Playwright Code from Playwright MCP Automation

This script shows how Playwright MCP tool-based automation
automatically generates reusable Playwright Python code.

Usage:
    python examples/mcp_code_generation_demo.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import playwright_mcp_codebase
from dotenv import load_dotenv

load_dotenv()


def demo_mcp_code_generation():
    """
    Demonstrate Playwright MCP code generation
    """
    
    # Check for API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key to run this demo")
        return
    
    print("="*80)
    print("🎭 Playwright MCP Code Generator Demo")
    print("="*80)
    print()
    
    # Example task
    task = "Go to Google and search for 'Playwright MCP'"
    print(f"📋 Task: {task}")
    print()
    
    # Create Playwright MCP engine
    print("🔧 Creating Playwright MCP engine...")
    mcp_client, browser_agent = playwright_mcp_codebase.create_engine(headless=False)
    
    print("🤖 Running MCP automation...")
    print("   (This will open a browser window)")
    print()
    
    try:
        # Run automation
        result = browser_agent.execute_instruction(task)
        
        print("✅ Automation complete!")
        print(f"   Success: {result['success']}")
        print(f"   Steps taken: {len(result['steps'])}")
        print()
        
        # Check if Playwright code was generated
        if 'playwright_code' in result:
            playwright_code = result['playwright_code']
            
            print("✅ Playwright code generated!")
            print()
            print("="*80)
            print("📄 Generated Code:")
            print("="*80)
            print()
            print(playwright_code)
            print()
            print("="*80)
            
            # Save to file
            output_file = "generated_mcp_playwright_script.py"
            with open(output_file, 'w') as f:
                f.write(playwright_code)
            
            print(f"💾 Code saved to: {output_file}")
            print()
            print("To run the generated script:")
            print("  1. Install playwright: pip install playwright")
            print("  2. Install browsers: playwright install chromium")
            print(f"  3. Run: python {output_file}")
            print("="*80)
        else:
            print("⚠️  Playwright code was not generated (feature may need debugging)")
        
        # Cleanup
        if hasattr(mcp_client, 'cleanup'):
            mcp_client.cleanup()
        
    except Exception as e:
        print(f"❌ Error during automation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print()
    print("This demo will:")
    print("  1. Run a Playwright MCP automation task")
    print("  2. Capture the MCP tool calls")
    print("  3. Generate equivalent Playwright Python code")
    print("  4. Save the code to a file")
    print()
    input("Press Enter to continue...")
    print()
    
    demo_mcp_code_generation()
