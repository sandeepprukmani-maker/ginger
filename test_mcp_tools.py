#!/usr/bin/env python3
"""Test MCP connection and available tools"""

import asyncio
from src.automation.mcp_client import PlaywrightMCPClient
from src.automation.logger import get_logger

logger = get_logger()

async def test_mcp_tools():
    client = PlaywrightMCPClient()
    
    try:
        logger.info("Connecting to MCP server...")
        await client.connect(browser="chromium", headless=True)
        
        logger.info("Available MCP tools:")
        tools = client.get_available_tools()
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Check if browser_snapshot is available
        has_snapshot = any(t['name'] == 'browser_snapshot' for t in tools)
        logger.info(f"\nbrowser_snapshot available: {has_snapshot}")
        
        if has_snapshot:
            # Test navigation and DOM snapshot
            logger.info("\nTesting DOM analysis...")
            await client.navigate("https://example.com")
            await asyncio.sleep(2)
            
            logger.info("Getting page snapshot...")
            snapshot = await client.call_tool("browser_snapshot", {})
            
            if snapshot:
                logger.success(f"✓ DOM snapshot retrieved! Length: {len(snapshot) if isinstance(snapshot, str) else 'N/A'}")
                logger.info(f"First 500 chars: {str(snapshot)[:500]}")
            else:
                logger.error("✗ DOM snapshot returned empty")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
