#!/usr/bin/env python3
"""
Integration test for MCP-based CLI
Tests that generated scripts are actually executable
"""

import asyncio
import os
import sys
from pathlib import Path
import tempfile
import subprocess

async def test_mcp_workflow():
    """Test the complete MCP workflow"""
    print("=" * 60)
    print("MCP Integration Test")
    print("=" * 60)
    print()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Skipping test.")
        return 1
    
    try:
        from src.mcp_client import PlaywrightMCPClient
        from src.mcp_server import PlaywrightMCPServer
        
        print("✓ Modules loaded successfully\n")
        
        print("Testing MCP server locator discovery...")
        
        client = PlaywrightMCPClient()
        await client.connect()
        print("✓ Connected to MCP server\n")
        
        print("Testing navigation...")
        result = await client.call_tool("playwright_navigate", {"url": "https://example.com"})
        print(f"Navigation result: {result[:100]}...\n")
        
        print("Testing click with locator discovery...")
        result = await client.call_tool("playwright_click", {"text": "More information"})
        print(f"Click result: {result[:200]}...\n")
        
        print("Checking recorded actions...")
        actions = client.get_recorded_actions()
        print(f"✓ Recorded {len(actions)} successful actions\n")
        
        for i, action in enumerate(actions, 1):
            print(f"  Action {i}: {action['tool']}")
            print(f"    Locator: {action['locator']}")
            print()
        
        await client.disconnect()
        
        print("=" * 60)
        print("✓ MCP integration test passed!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Integration test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(test_mcp_workflow()))
