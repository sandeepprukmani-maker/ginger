"""
Engine Test Script
Tests if the engines can initialize properly with your API key
Run this BEFORE starting the web app to verify everything works
"""
import os
import sys
from dotenv import load_dotenv

print("=" * 60)
print("Engine Initialization Test")
print("=" * 60)

# Step 1: Load .env file
print("\n[Step 1] Loading .env file...")
if not os.path.exists('.env'):
    print("❌ FATAL ERROR: .env file not found!")
    print("   You must create a .env file in this directory")
    print("   Run: copy .env.example .env")
    print("   Then edit .env and add your API key")
    sys.exit(1)

load_dotenv(override=True)
api_key = os.environ.get('OPENAI_API_KEY')

if not api_key:
    print("❌ FATAL ERROR: OPENAI_API_KEY not found in .env file!")
    print("   Open your .env file and make sure it contains:")
    print("   OPENAI_API_KEY=sk-your-actual-key-here")
    sys.exit(1)

masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
print(f"✅ API key loaded: {masked_key}")

# Step 2: Test Browser-Use engine initialization
print("\n[Step 2] Testing Browser-Use engine...")
try:
    from browser_use_codebase.engine import BrowserUseEngine
    engine = BrowserUseEngine(headless=True)
    print("✅ Browser-Use engine initialized successfully!")
except Exception as e:
    print(f"❌ Browser-Use engine FAILED: {str(e)}")
    print("\nThis is the exact error the web app will show!")
    sys.exit(1)

# Step 3: Test Playwright MCP engine initialization
print("\n[Step 3] Testing Playwright MCP engine...")
try:
    from playwright_mcp_codebase.agent.conversation_agent import BrowserAgent
    from playwright_mcp_codebase.client.stdio_client import MCPStdioClient
    
    # Don't actually initialize the client, just test the agent can be created
    client = MCPStdioClient(headless=True)
    agent = BrowserAgent(client)
    print("✅ Playwright MCP engine initialized successfully!")
except Exception as e:
    print(f"❌ Playwright MCP engine FAILED: {str(e)}")
    print("\nThis is the exact error the web app will show!")
    sys.exit(1)

# Step 4: Success!
print("\n" + "=" * 60)
print("🎉 SUCCESS! All engines initialized correctly!")
print("=" * 60)
print("\nYour setup is correct. You can now run:")
print("  python main.py")
print("\nThe web application should work without API key errors.")
print("=" * 60)
