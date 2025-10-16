#!/usr/bin/env python3
"""
Browser Automation Script using Playwright MCP Server
------------------------------------------------------
This script connects to the Playwright MCP server and allows you to automate
browser interactions using natural language prompts. The DOM is automatically
scanned - no need to provide locators.

Usage:
    python browser_automation.py "your prompt here"
    
Or run interactively:
    python browser_automation.py
"""

import asyncio
import json
import os
import sys
from typing import Any, List, Dict, Optional
import httpx
from openai import OpenAI

MCP_SERVER_URL = "http://localhost:8080/mcp"


class PlaywrightMCPClient:
    """Client for interacting with Playwright MCP Server"""
    
    def __init__(self, server_url: str = MCP_SERVER_URL):
        self.server_url = server_url
        self.session_id = None
        self.tools = []
        self.action_history = []
        
    async def initialize(self):
        """Initialize connection and get available tools"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.server_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "python-automation-client",
                            "version": "1.0.0"
                        }
                    }
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to initialize MCP connection: {response.status_code} - {response.text}")
            
            result = response.json()
            if "error" in result:
                raise Exception(f"MCP initialization error: {result['error']}")
            
            print(f"✓ Connected to MCP server: {result.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
            
            response = await client.post(
                self.server_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch tools list: {response.status_code} - {response.text}")
            
            result = response.json()
            if "error" in result:
                raise Exception(f"Tools list error: {result['error']}")
            
            self.tools = result.get("result", {}).get("tools", [])
            print(f"✓ Loaded {len(self.tools)} browser automation tools")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.server_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                tool_result = result.get("result", {})
                
                self.action_history.append({
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": tool_result
                })
                
                return tool_result
            else:
                raise Exception(f"Tool call failed: {response.text}")
    
    def get_tools_for_llm(self) -> List[Dict]:
        """Format tools for OpenAI function calling"""
        formatted_tools = []
        for tool in self.tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {})
                }
            })
        return formatted_tools
    
    def generate_rerunnable_code(self) -> str:
        """Generate Python code that can be rerun"""
        code_lines = [
            "#!/usr/bin/env python3",
            "# Auto-generated browser automation script",
            "# This script can be run independently",
            "",
            "import asyncio",
            "import httpx",
            "",
            'MCP_SERVER_URL = "http://localhost:8080/mcp"',
            "",
            "async def run_automation():",
            "    async with httpx.AsyncClient(timeout=60.0) as client:",
            "        # Initialize connection",
            "        await client.post(",
            "            MCP_SERVER_URL,",
            "            json={",
            '                "jsonrpc": "2.0",',
            '                "id": 1,',
            '                "method": "initialize",',
            "                \"params\": {",
            '                    "protocolVersion": "2024-11-05",',
            '                    "capabilities": {},',
            '                    "clientInfo": {"name": "automation", "version": "1.0.0"}',
            "                }",
            "            }",
            "        )",
            "",
        ]
        
        for i, action in enumerate(self.action_history, 1):
            code_lines.extend([
                f"        # Step {i}: {action['tool']}",
                "        response = await client.post(",
                "            MCP_SERVER_URL,",
                "            json={",
                '                "jsonrpc": "2.0",',
                f'                "id": {i + 1},',
                '                "method": "tools/call",',
                "                \"params\": {",
                f'                    "name": "{action["tool"]}",',
                f'                    "arguments": {json.dumps(action["arguments"])}',
                "                }",
                "            }",
                "        )",
                f"        print(f'Step {i} completed: {action['tool']}')",
                "",
            ])
        
        code_lines.extend([
            "if __name__ == '__main__':",
            "    asyncio.run(run_automation())",
        ])
        
        return "\n".join(code_lines)


class BrowserAutomationAgent:
    """Agent that converts prompts to browser automation using OpenAI"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set. Please set it first.")
        self.client = OpenAI(api_key=self.api_key)
        self.mcp_client = PlaywrightMCPClient()
        
    async def execute_prompt(self, prompt: str) -> str:
        """Execute a natural language prompt"""
        await self.mcp_client.initialize()
        
        tools = self.mcp_client.get_tools_for_llm()
        
        messages: List[Dict[str, Any]] = [{
            "role": "user",
            "content": prompt
        }]
        
        print(f"\n🤖 Processing prompt: {prompt}\n")
        
        while True:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,  # type: ignore
                tools=tools,  # type: ignore
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            if message.content:
                print(f"\n✓ {message.content}\n")
            
            if not message.tool_calls:
                break
            
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,  # type: ignore
                            "arguments": tc.function.arguments  # type: ignore
                        }
                    } for tc in message.tool_calls
                ]
            })
            
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name  # type: ignore
                function_args = json.loads(tool_call.function.arguments)  # type: ignore
                
                print(f"  → Executing: {function_name}")
                
                result = await self.mcp_client.call_tool(function_name, function_args)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
        
        rerunnable_code = self.mcp_client.generate_rerunnable_code()
        
        script_filename = "automation_script.py"
        with open(script_filename, "w") as f:
            f.write(rerunnable_code)
        
        print(f"✓ Rerunnable script saved to: {script_filename}\n")
        
        return rerunnable_code


async def main():
    """Main entry point"""
    
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        print("\n🌐 Browser Automation - Natural Language Interface")
        print("=" * 60)
        print("\nExamples:")
        print('  • "Go to google.com and search for Python"')
        print('  • "Navigate to github.com, click on search, and search for playwright"')
        print('  • "Fill out the login form with test@example.com and password123"')
        print("\n" + "=" * 60 + "\n")
        
        prompt = input("Enter your automation prompt: ").strip()
    
    if not prompt:
        print("Error: No prompt provided")
        sys.exit(1)
    
    try:
        agent = BrowserAutomationAgent()
        code = await agent.execute_prompt(prompt)
        
        print("\n" + "=" * 60)
        print("RERUNNABLE CODE:")
        print("=" * 60)
        print(code)
        print("=" * 60 + "\n")
        
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nTo use this script, you need to set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        print("\nGet your API key from: https://platform.openai.com/")
        print("\nOr provide it when creating the agent:")
        print("  agent = BrowserAutomationAgent(api_key='your-api-key')")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
