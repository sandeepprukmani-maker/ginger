#!/usr/bin/env python3
"""Install Playwright browser"""

import asyncio
from src.automation.mcp_client import PlaywrightMCPClient
from src.automation.logger import get_logger

logger = get_logger()

async def install_browser():
    client = PlaywrightMCPClient()
    
    try:
        logger.info("Connecting to MCP server...")
        await client.connect(browser="chromium", headless=True)
        
        logger.info("Installing Chromium browser...")
        result = await client.call_tool("browser_install", {})
        logger.success(f"Browser installation result: {result}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(install_browser())
