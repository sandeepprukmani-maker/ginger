#!/usr/bin/env python3
"""
Browser Automation Script using Playwright MCP Server
------------------------------------------------------
This script connects to the Playwright MCP server and allows you to automate
browser interactions using natural language prompts.

Before running:
1. Set your OpenAI API key: export OPENAI_API_KEY='your-api-key-here'
2. Start the MCP server: npx @modelcontextprotocol/server-playwright

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

# Get API key from environment variable
OPENAI_API_KEY = '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'
MCP_SERVER_URL = "http://127.0.0.1:8760/mcp"


class PlaywrightMCPClient:
    """Client for interacting with Playwright MCP Server"""

    def __init__(self, server_url: str = MCP_SERVER_URL):
        self.server_url = server_url
        self.session_id = None
        self.tools = []
        self.action_history = []

    async def initialize(self):
        """Initialize connection and get available tools"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Initialize MCP connection
                init_response = await client.post(
                    self.server_url,
                    headers=headers,
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

                if init_response.status_code != 200:
                    raise Exception(f"MCP server returned status {init_response.status_code}")

                init_result = init_response.json()
                if "error" in init_result:
                    raise Exception(f"MCP initialization error: {init_result['error']}")

                print(
                    f"✓ Connected to MCP server: {init_result.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")

                # Get available tools
                tools_response = await client.post(
                    self.server_url,
                    headers=headers,
                    json={
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list",
                        "params": {}
                    }
                )

                if tools_response.status_code != 200:
                    raise Exception(f"Failed to fetch tools: {tools_response.status_code}")

                tools_result = tools_response.json()
                if "error" in tools_result:
                    raise Exception(f"Tools list error: {tools_result['error']}")

                self.tools = tools_result.get("result", {}).get("tools", [])
                print(f"✓ Loaded {len(self.tools)} browser automation tools")

        except httpx.ConnectError:
            raise Exception(f"Cannot connect to MCP server at {self.server_url}. Make sure the server is running.")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from MCP server: {e}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.server_url,
                headers=headers,
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
                if "error" in result:
                    raise Exception(f"Tool error: {result['error']}")

                tool_result = result.get("result", {})
                self.action_history.append({
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": tool_result
                })
                return tool_result
            else:
                raise Exception(f"Tool call failed with status {response.status_code}: {response.text}")


class SimpleBrowserAutomation:
    """Simplified browser automation without OpenAI dependency"""

    def __init__(self):
        self.mcp_client = PlaywrightMCPClient()

    async def execute_simple_command(self, prompt: str):
        """Execute simple browser commands based on prompt"""
        await self.mcp_client.initialize()

        # Simple command mapping - you can expand this
        prompt_lower = prompt.lower()

        if "google" in prompt_lower and "search" in prompt_lower:
            # Extract search query
            if "search for" in prompt_lower:
                search_query = prompt_lower.split("search for")[1].strip()
            elif "search" in prompt_lower:
                search_query = prompt_lower.split("search")[1].strip()
            else:
                search_query = "test"

            print(f"🔍 Executing: Navigate to Google and search for '{search_query}'")

            # Navigate to Google
            result1 = await self.mcp_client.call_tool("navigate", {"url": "https://www.google.com"})
            print(f"✓ Navigated to Google: {result1}")

            # Wait for page to load
            await asyncio.sleep(2)

            # Find search box and type (this would need more sophisticated DOM analysis)
            # For now, let's just navigate to the search URL directly
            search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            result2 = await self.mcp_client.call_tool("navigate", {"url": search_url})
            print(f"✓ Searched for '{search_query}': {result2}")

        elif "open" in prompt_lower:
            # Extract URL
            if "http" in prompt:
                url = prompt.split("open")[1].strip()
            else:
                url = f"https://{prompt.split('open')[1].strip()}"

            print(f"🌐 Opening: {url}")
            result = await self.mcp_client.call_tool("navigate", {"url": url})
            print(f"✓ Navigation result: {result}")

        else:
            print("❓ Unknown command. Try:")
            print("  • 'open google.com'")
            print("  • 'open google search for dogs'")
            print("  • 'navigate to github.com'")
            return

        # Generate rerunnable code
        code = self.generate_rerunnable_code()
        self.save_script(code)

        return code

    def generate_rerunnable_code(self) -> str:
        """Generate Python code that can be rerun"""
        code_lines = [
            "#!/usr/bin/env python3",
            "# Auto-generated browser automation script",
            "",
            "import asyncio",
            "import httpx",
            "",
            'MCP_SERVER_URL = "http://127.0.0.1:5000/mcp"',
            "",
            "async def run_automation():",
            '    headers = {',
            '        "Accept": "application/json",',
            '        "Content-Type": "application/json"',
            '    }',
            "",
            "    async with httpx.AsyncClient(timeout=60.0) as client:",
            "        # Initialize connection",
            "        await client.post(",
            "            MCP_SERVER_URL,",
            "            headers=headers,",
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

        for i, action in enumerate(self.mcp_client.action_history, 1):
            code_lines.extend([
                f"        # Step {i}: {action['tool']}",
                "        response = await client.post(",
                "            MCP_SERVER_URL,",
                "            headers=headers,",
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
                "        result = response.json()",
                f'        print(f"Step {i} result: {{result}}")',
                "",
            ])

        code_lines.extend([
            "if __name__ == '__main__':",
            "    asyncio.run(run_automation())",
        ])

        return "\n".join(code_lines)

    def save_script(self, code: str):
        """Save the generated script"""
        script_filename = "automation_script.py"
        with open(script_filename, "w") as f:
            f.write(code)
        print(f"✓ Rerunnable script saved to: {script_filename}")


async def main():
    """Main entry point"""

    # Check if MCP server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:5000", timeout=5.0)
    except:
        print("❌ MCP server is not running!")
        print("\nTo start the MCP server, run:")
        print("  npx @modelcontextprotocol/server-playwright")
        print("\nOr install and run it:")
        print("  npm install -g @modelcontextprotocol/server-playwright")
        print("  npx @modelcontextprotocol/server-playwright")
        sys.exit(1)

    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        print("\n🌐 Browser Automation - Simple Interface")
        print("=" * 50)
        print("\nExamples:")
        print('  • "open google.com"')
        print('  • "open google search for python programming"')
        print('  • "navigate to github.com"')
        print("\n" + "=" * 50 + "\n")
        prompt = input("Enter your automation command: ").strip()

    if not prompt:
        print("Error: No command provided")
        sys.exit(1)

    try:
        automator = SimpleBrowserAutomation()
        await automator.execute_simple_command(prompt)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure MCP server is running: npx @modelcontextprotocol/server-playwright")
        print("2. Check if port 5000 is available")
        print("3. Verify your network connection")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())