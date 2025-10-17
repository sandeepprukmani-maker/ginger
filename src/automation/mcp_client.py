import asyncio
import os
from contextlib import AsyncExitStack
from typing import Optional, Dict, Any, List
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .logger import get_logger

logger = get_logger()


class PlaywrightMCPClient:
    """
    Client for communicating with Playwright MCP server.
    Provides browser automation capabilities via Model Context Protocol.
    """
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.tools: List[Dict[str, Any]] = []
        
    async def connect(self, browser: str = "chromium", headless: bool = True):
        """
        Connect to Playwright MCP server.
        
        Args:
            browser: Browser type (chromium, firefox, webkit)
            headless: Whether to run in headless mode
        """
        try:
            logger.info(f"Connecting to Playwright MCP server (browser={browser}, headless={headless})")
            
            # Set up environment for npx command (fix NixOS env issues)
            env = os.environ.copy()
            env.setdefault("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
            env.setdefault("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
            env.setdefault("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
            
            # Build args (only add --headless if headless mode is enabled)
            args = ["@playwright/mcp@latest", "--browser", browser]
            if headless:
                args.append("--headless")
            
            server_params = StdioServerParameters(
                command="npx",
                args=args,
                env=env
            )
            
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read_stream, write_stream = stdio_transport
            
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            await self.session.initialize()
            
            response = await self.session.list_tools()
            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                }
                for tool in response.tools
            ]
            
            logger.success(f"Connected to Playwright MCP! Available tools: {[t['name'] for t in self.tools]}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Playwright MCP: {e}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a Playwright MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        if not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")
        
        try:
            logger.info(f"Calling MCP tool: {tool_name} with args: {arguments}")
            
            result = await self.session.call_tool(tool_name, arguments)
            
            if result.content:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return_value = content.text
                    try:
                        return_value = json.loads(return_value)
                    except json.JSONDecodeError:
                        pass
                    logger.success(f"Tool {tool_name} completed successfully")
                    return return_value
            
            return None
            
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            raise
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL."""
        return await self.call_tool("browser_navigate", {"url": url})
    
    async def click(self, selector: str) -> Dict[str, Any]:
        """Click an element."""
        return await self.call_tool("browser_click", {"selector": selector})
    
    async def fill(self, selector: str, value: str) -> Dict[str, Any]:
        """Fill an input field."""
        return await self.call_tool("browser_fill_form", {
            "selector": selector,
            "value": value
        })
    
    async def screenshot(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Take a screenshot."""
        args = {}
        if path:
            args["path"] = path
        return await self.call_tool("browser_take_screenshot", args)
    
    async def evaluate(self, expression: str) -> Any:
        """Execute JavaScript in the browser."""
        return await self.call_tool("browser_evaluate", {"expression": expression})
    
    async def get_page_content(self) -> str:
        """Get the current page HTML content."""
        result = await self.call_tool("browser_snapshot", {})
        return result if isinstance(result, str) else ""
    
    async def close(self):
        """Close the MCP client connection."""
        try:
            await self.exit_stack.aclose()
            logger.info("MCP client connection closed")
        except Exception as e:
            logger.error(f"Error closing MCP client: {e}")
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools."""
        return self.tools
