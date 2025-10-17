#!/usr/bin/env python3
"""
Natural Language Browser Automation using Playwright MCP Server
Uses Model Context Protocol for AI-powered browser automation
"""

import asyncio
import json
import sys
from pathlib import Path

from src.automation.mcp_client import PlaywrightMCPClient
from src.automation.logger import get_logger
from openai import AsyncOpenAI

logger = get_logger()


class MCPNaturalLanguageAutomation:
    """Natural language automation using Playwright MCP server."""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.mcp = PlaywrightMCPClient()
        self.conversation_history = []
    
    async def initialize(self, browser: str = "chromium", headless: bool = True):
        """Initialize MCP connection."""
        await self.mcp.connect(browser=browser, headless=headless)
        logger.success("MCP automation initialized!")
    
    async def execute_command(self, command: str) -> str:
        """
        Execute a natural language command using AI + MCP.
        
        Args:
            command: Natural language instruction (e.g., "search for Python tutorials on Google")
            
        Returns:
            Result description
        """
        logger.info(f"Processing command: {command}")
        
        # Get available MCP tools
        tools = self.mcp.get_available_tools()
        
        # Format tools for OpenAI (type: ignore for dynamic tool schema)
        openai_tools: list = [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            }
            for tool in tools
        ]
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": command
        })
        
        # Call OpenAI to determine which tools to use
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a browser automation assistant using Playwright MCP tools. "
                        "Execute user commands by calling the appropriate Playwright tools. "
                        "Break down complex tasks into multiple tool calls. "
                        "Always provide clear feedback about what you're doing."
                    )
                },
                *self.conversation_history
            ],
            tools=openai_tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        results = []
        
        # Execute tool calls
        if message.tool_calls:
            for tool_call in message.tool_calls:
                # Handle both function and custom tool calls
                if hasattr(tool_call, 'function'):
                    tool_name = tool_call.function.name  # type: ignore
                    # SECURITY: Use json.loads() instead of eval() to prevent RCE
                    try:
                        tool_args = json.loads(tool_call.function.arguments)  # type: ignore
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse tool arguments: {e}")
                        continue
                else:
                    continue
                
                logger.info(f"Executing: {tool_name}({tool_args})")
                
                try:
                    result = await self.mcp.call_tool(tool_name, tool_args)
                    results.append(f"✓ {tool_name}: {result}")
                    
                    # Add tool result to conversation
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call]
                    })
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
                    
                except Exception as e:
                    error_msg = f"✗ {tool_name} failed: {e}"
                    results.append(error_msg)
                    logger.error(error_msg)
        
        # Get final response
        if results:
            final_response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Summarize what was accomplished in a friendly way."
                    },
                    *self.conversation_history
                ]
            )
            summary = final_response.choices[0].message.content or "Task completed"
            logger.success(summary)
            return summary
        else:
            return message.content or "Command executed"
    
    async def cleanup(self):
        """Clean up resources."""
        await self.mcp.close()


async def main():
    """Main entry point for MCP automation."""
    import os
    
    # Get OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set!")
        sys.exit(1)
    
    # Create automation instance
    automation = MCPNaturalLanguageAutomation(api_key)
    
    try:
        # Initialize MCP
        logger.info("Initializing Playwright MCP server...")
        await automation.initialize(browser="chromium", headless=False)
        
        print("\n" + "="*60)
        print("🎭 Playwright MCP Natural Language Automation")
        print("="*60)
        print("\nType natural language commands to automate the browser.")
        print("Examples:")
        print("  - Go to google.com and search for Python tutorials")
        print("  - Navigate to github.com")
        print("  - Click the login button")
        print("\nType 'quit' or 'exit' to stop.\n")
        
        # Interactive mode
        while True:
            try:
                command = input("💬 Command: ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break
                
                if not command:
                    continue
                
                result = await automation.execute_command(command)
                print(f"\n✅ {result}\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"\n❌ Error: {e}\n")
    
    finally:
        await automation.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
