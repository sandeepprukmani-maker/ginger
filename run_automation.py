#!/usr/bin/env python3
"""
Single-Shot Browser Automation - Execute ONE command and complete ALL steps automatically
Usage: python run_automation.py "your full command here"
"""

import asyncio
import sys
import os
from nl_automation_mcp import EnhancedMCPAutomation
from rich.console import Console

console = Console()

async def run_single_command(command: str):
    """Execute a single automation command with all steps completed automatically."""
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[red]❌ Error: OPENAI_API_KEY environment variable not set[/red]")
        console.print("[yellow]Set it with: export OPENAI_API_KEY='your-key-here'[/yellow]")
        return
    
    # Initialize automation with fast settings
    automation = EnhancedMCPAutomation(
        api_key=api_key,
        enable_vision=True,
        max_retries=5,
        enable_caching=True,
        enable_parallel=True,
        enable_predictions=True,
        use_gpt4o=False  # Use GPT-4o-mini for speed (change to True for max accuracy)
    )
    
    try:
        console.print("[cyan]🚀 Initializing browser automation...[/cyan]")
        await automation.initialize(browser="chromium", headless=True)
        
        console.print(f"\n[bold green]📋 Command:[/bold green] {command}\n")
        console.print("[yellow]⚡ Executing all steps automatically...[/yellow]\n")
        
        # Execute the FULL command - all steps done automatically
        result = await automation.execute_command(command)
        
        # Show results
        console.print(f"\n[bold]{'✅ SUCCESS' if result['status'] == 'success' else '⚠️  PARTIAL SUCCESS'}[/bold]")
        console.print(f"\n[cyan]Summary:[/cyan]")
        console.print(result['summary'])
        
        if 'execution_time' in result:
            console.print(f"\n[dim]⚡ Execution time: {result['execution_time']:.2f}s[/dim]")
            console.print(f"[dim]📊 Cache hit rate: {result['metrics']['cache_hit_rate']:.1f}%[/dim]")
            console.print(f"[dim]🔄 Total retries: {result['metrics']['total_retries']}[/dim]")
        
        console.print("\n[green]✓ Automation complete![/green]")
        
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        await automation.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print("[bold cyan]Single-Shot Browser Automation[/bold cyan]")
        console.print("\n[yellow]Usage:[/yellow]")
        console.print('  python run_automation.py "Your full command here"')
        console.print("\n[yellow]Example:[/yellow]")
        console.print('  python run_automation.py "Go to Google, search for Python tutorials, and take a screenshot"')
        console.print("\n[yellow]Complex Example:[/yellow]")
        console.print('  python run_automation.py "Open page https://example.com, Type username admin into Username field, Type password pass123 into Password field, Click Submit button, Verify page contains Welcome text"')
        sys.exit(1)
    
    # Get the full command from arguments
    command = " ".join(sys.argv[1:])
    
    # Run it
    asyncio.run(run_single_command(command))
