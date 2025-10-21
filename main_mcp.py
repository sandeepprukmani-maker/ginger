#!/usr/bin/env python3
"""
Playwright MCP CLI - Proper MCP Integration
Converts natural language to browser automation using Playwright MCP Server
"""

import asyncio
import os
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from src.mcp_client import PlaywrightMCPClient
from src.output_generator import OutputGenerator
import argparse
import json

console = Console()

class MCPAutomationCLI:
    def __init__(self):
        self.client = PlaywrightMCPClient()
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.output_gen = OutputGenerator()
    
    async def init(self):
        """Initialize MCP connection"""
        await self.client.connect()
    
    async def process_command(self, natural_language: str, output_path: str | None = None):
        """Process natural language command using MCP"""
        console.print(f"\n[bold]Processing:[/bold] {natural_language}\n")
        
        console.print("[dim]Step 1/4: Analyzing command with AI...[/dim]")
        
        tools = await self.client.list_tools()
        
        tool_calls = await self._convert_nl_to_mcp_calls(natural_language, tools)
        
        console.print(f"[green]✓[/green] Planned {len(tool_calls)} actions\n")
        
        console.print("[dim]Step 2/4: Executing actions via MCP server...[/dim]")
        
        for i, call in enumerate(tool_calls, 1):
            console.print(f"  [{i}/{len(tool_calls)}] {call['name']}...")
            try:
                result = await self.client.call_tool(call['name'], call['arguments'])
                console.print(f"  [green]✓[/green] {call['name']} completed")
            except Exception as e:
                console.print(f"  [red]✗[/red] {call['name']} failed: {e}")
        
        console.print("\n[dim]Step 3/4: Recording successful actions...[/dim]")
        
        recorded_actions = self.client.get_recorded_actions()
        console.print(f"[green]✓[/green] Recorded {len(recorded_actions)} successful actions\n")
        
        console.print("[dim]Step 4/4: Generating standalone Playwright code...[/dim]")
        
        standalone_code = self._generate_code_from_actions(recorded_actions)
        
        console.print(Panel(
            standalone_code,
            title="Generated Standalone Code",
            border_style="green",
            expand=False
        ))
        
        script_path = self.output_gen.save_script(standalone_code, output_path, natural_language)
        
        console.print(f"\n[green]✓[/green] Standalone script saved to: [bold]{script_path}[/bold]")
        console.print("[dim]This script works without OpenAI/MCP![/dim]\n")
    
    async def _convert_nl_to_mcp_calls(self, command: str, available_tools: list) -> list[dict]:
        """Use OpenAI to convert natural language to MCP tool calls"""
        
        tool_descriptions = "\n".join([
            f"- {tool.name}: {tool.description}\n  Args: {json.dumps(tool.inputSchema.get('properties', {}), indent=2)}"
            for tool in available_tools
        ])
        
        system_prompt = f"""You are a browser automation expert. Convert natural language commands into a sequence of Playwright MCP tool calls.

Available tools:
{tool_descriptions}

Return ONLY a JSON array of tool calls in this format:
[
  {{"name": "playwright_navigate", "arguments": {{"url": "https://example.com"}}}},
  {{"name": "playwright_click", "arguments": {{"role": "link", "text": "More information"}}}}
]

Use the most robust locator strategies:
1. role + text (best for buttons/links)
2. label (for form inputs)
3. text content (for general elements)
4. selector (last resort)

Return ONLY valid JSON, no explanations."""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Convert this to MCP tool calls: {command}"}
            ],
            temperature=0.2
        )
        
        content = response.choices[0].message.content
        if not content:
            return []
        
        content = content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        tool_calls = json.loads(content)
        return tool_calls
    
    def _generate_code_from_actions(self, actions: list[dict]) -> str:
        """Generate standalone Playwright Python code from recorded MCP actions"""
        
        code_lines = []
        
        for action in actions:
            if action["locator"]:
                locator = action["locator"].strip()
                if locator and not locator.startswith("#"):
                    code_lines.append(f"    {locator}")
        
        function_code = "def run_automation(page):\n"
        if code_lines:
            function_code += "\n".join(code_lines)
        else:
            function_code += "    pass"
        
        return function_code
    
    async def cleanup(self):
        """Cleanup MCP connection"""
        await self.client.disconnect()

async def main():
    parser = argparse.ArgumentParser(
        description="Playwright MCP CLI - Convert natural language to Playwright code via MCP"
    )
    parser.add_argument(
        "command",
        nargs="?",
        help="Natural language command for browser automation"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path for generated Python script",
        default=None
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode"
    )
    
    args = parser.parse_args()
    
    console.print(Panel.fit(
        "[bold blue]Playwright MCP CLI (MCP-Powered)[/bold blue]\n"
        "[dim]Natural Language → MCP → Self-Healing Playwright Code[/dim]",
        border_style="blue"
    ))
    
    cli = MCPAutomationCLI()
    
    try:
        await cli.init()
        
        if args.interactive:
            console.print("\n[green]Interactive Mode[/green] - Type 'exit' to quit\n")
            
            while True:
                try:
                    command = console.input("[bold cyan]Enter command:[/bold cyan] ")
                    
                    if command.lower() in ['exit', 'quit', 'q']:
                        console.print("[yellow]Exiting...[/yellow]")
                        break
                    
                    if not command.strip():
                        continue
                    
                    await cli.process_command(command, None)
                    console.print()
                    
                except KeyboardInterrupt:
                    console.print("\n[yellow]Exiting...[/yellow]")
                    break
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    import traceback
                    traceback.print_exc()
        
        elif args.command:
            await cli.process_command(args.command, args.output)
        else:
            console.print("[yellow]No command provided. Use --interactive mode or provide a command.[/yellow]")
            console.print("\nExample: python main_mcp.py 'Go to example.com and click More Information'")
            return
    
    finally:
        await cli.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
