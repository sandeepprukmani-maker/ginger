import json
import subprocess
import asyncio
from typing import Any, Dict, Optional
import uuid


class MCPClient:
    """Client to communicate with the MCP server via stdio"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        
    async def start(self):
        """Start the MCP server process"""
        self.process = subprocess.Popen(
            ['node', 'mcp-server/build/index.js'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        await asyncio.sleep(1)
        print("MCP Server started")
    
    def _get_request_id(self) -> int:
        """Generate a unique request ID"""
        self.request_id += 1
        return self.request_id
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool and get the response"""
        if not self.process:
            raise RuntimeError("MCP server not started")
        
        request_id = self._get_request_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        request_json = json.dumps(request) + '\n'
        self.process.stdin.write(request_json)
        self.process.stdin.flush()
        
        response_line = self.process.stdout.readline()
        
        if not response_line:
            raise RuntimeError("No response from MCP server")
        
        response = json.loads(response_line)
        
        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")
        
        if "result" in response and "content" in response["result"]:
            content = response["result"]["content"][0]
            if content["type"] == "text":
                return json.loads(content["text"])
        
        return response
    
    async def list_tools(self) -> list:
        """List available tools"""
        if not self.process:
            raise RuntimeError("MCP server not started")
        
        request_id = self._get_request_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/list",
            "params": {}
        }
        
        request_json = json.dumps(request) + '\n'
        self.process.stdin.write(request_json)
        self.process.stdin.flush()
        
        response_line = self.process.stdout.readline()
        response = json.loads(response_line)
        
        if "result" in response and "tools" in response["result"]:
            return response["result"]["tools"]
        
        return []
    
    async def stop(self):
        """Stop the MCP server process"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            print("MCP Server stopped")
