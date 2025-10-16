import asyncio
import json
import subprocess
from typing import Any, Dict, List, Optional
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


class PlaywrightMCPClient:
    """Client for communicating with Playwright MCP server"""
    
    def __init__(self, mcp_server_command: List[str] = None):
        if mcp_server_command is None:
            # Default: connect to local MCP server via stdio
            mcp_server_command = ["node", "cli.js", "--headless", "--browser", "chromium", "--no-sandbox"]
        self.server_command = mcp_server_command
        self.session: Optional[ClientSession] = None
        self.available_tools: List[Dict[str, Any]] = []
        self.exit_stack = None
        
    async def connect(self):
        """Connect to the MCP server via stdio"""
        from contextlib import AsyncExitStack
        self.exit_stack = AsyncExitStack()
        
        server_params = StdioServerParameters(
            command=self.server_command[0],
            args=self.server_command[1:],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()
        
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get available tools from MCP server"""
        try:
            if not self.session:
                return []
                
            response = await self.session.list_tools()
            self.available_tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in response.tools
            ]
            return self.available_tools
        except Exception as e:
            print(f"Error listing tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        try:
            if not self.session:
                return {"error": "Not connected"}
                
            result = await self.session.call_tool(tool_name, arguments=arguments)
            return {
                "content": result.content,
                "isError": result.isError if hasattr(result, 'isError') else False
            }
        except Exception as e:
            print(f"Error calling tool {tool_name}: {e}")
            return {"error": str(e)}
    
    async def execute_automation_sequence(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a sequence of automation steps"""
        results = []
        
        for step in steps:
            tool_name = step.get("tool")
            if not tool_name:
                continue
                
            arguments = step.get("arguments", {})
            
            print(f"Executing: {tool_name} with {arguments}")
            result = await self.call_tool(tool_name, arguments)
            results.append({
                "step": step,
                "result": result
            })
            
            await asyncio.sleep(0.5)
            
        return results
    
    async def close(self):
        """Close the connection"""
        if self.exit_stack:
            await self.exit_stack.aclose()
