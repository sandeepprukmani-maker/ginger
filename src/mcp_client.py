"""
MCP Client to interact with Playwright MCP Server
"""

import asyncio
import subprocess
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import logging
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaywrightMCPClient:
    def __init__(self):
        self.session: ClientSession | None = None
        self.exit_stack = None
        self.recorded_actions = []
    
    async def connect(self):
        """Connect to the Playwright MCP server"""
        server_params = StdioServerParameters(
            command="python",
            args=["src/mcp_server.py"],
            env=None
        )
        
        stdio_transport = await stdio_client(server_params)
        self.stdio, self.write = stdio_transport
        self.session = ClientSession(self.stdio, self.write)
        
        await self.session.initialize()
        logger.info("Connected to Playwright MCP server")
    
    async def list_tools(self) -> list:
        """List available MCP tools"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        result = await self.session.list_tools()
        return result.tools
    
    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Call a tool and record the action"""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        logger.info(f"Calling tool: {tool_name} with args: {arguments}")
        
        result = await self.session.call_tool(tool_name, arguments)
        
        response_text = ""
        for content in result.content:
            if hasattr(content, 'text'):
                response_text += content.text
        
        locator = self._extract_locator(response_text)
        
        self.recorded_actions.append({
            "tool": tool_name,
            "arguments": arguments,
            "locator": locator,
            "success": "error" not in response_text.lower()
        })
        
        logger.info(f"Tool result: {response_text[:200]}")
        
        return response_text
    
    def _extract_locator(self, response_text: str) -> str:
        """Extract Playwright locator from response (first line only)"""
        if "Locator:" in response_text:
            locator_part = response_text.split("Locator:")[1].strip()
            locator_line = locator_part.split("\n")[0].strip()
            return locator_line
        return ""
    
    def get_recorded_actions(self) -> list:
        """Get all successfully recorded actions"""
        return [a for a in self.recorded_actions if a["success"]]
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.session:
            await self.session.close()
            logger.info("Disconnected from MCP server")
