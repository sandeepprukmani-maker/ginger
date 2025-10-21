#!/usr/bin/env python3
import sys
import os
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from src.code_generator import CodeGenerator
from src.executor import PlaywrightExecutor
from src.self_healing import SelfHealingEngine
from src.output_generator import OutputGenerator

console = Console()

def main():
    parser = argparse.ArgumentParser(
        description="Playwright MCP CLI - Convert natural language to self-healing Playwright code"
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
        "--show-browser",
        action="store_true",
        help="Show browser window during execution (default is headless)",
        default=False
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode - enter commands one by one"
    )
    
    args = parser.parse_args()
    
    console.print(Panel.fit(
        "[bold blue]Playwright MCP CLI[/bold blue]\n"
        "[dim]Natural Language → Self-Healing Playwright Code[/dim]",
        border_style="blue"
    ))
    
    headless = not args.show_browser
    
    if args.interactive:
        interactive_mode(headless)
    elif args.command:
        process_command(args.command, args.output, headless)
    else:
        console.print("[yellow]No command provided. Use --interactive mode or provide a command.[/yellow]")
        console.print("\nExample: python main.py 'Go to google.com and search for Playwright'")
        console.print("         python main.py --interactive")
        return

def interactive_mode(headless=True):
    console.print("\n[green]Interactive Mode[/green] - Type 'exit' to quit\n")
    
    while True:
        try:
            command = console.input("[bold cyan]Enter command:[/bold cyan] ")
            
            if command.lower() in ['exit', 'quit', 'q']:
                console.print("[yellow]Exiting...[/yellow]")
                break
            
            if not command.strip():
                continue
            
            process_command(command, None, headless)
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting...[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

def process_command(command: str, output_path: str | None = None, headless: bool = True):
    try:
        console.print(f"\n[bold]Processing:[/bold] {command}\n")
        
        console.print("[dim]Step 1/4: Generating Playwright code with AI...[/dim]")
        generator = CodeGenerator()
        generated_code, locator_info = generator.generate_code(command)
        
        console.print("[green]✓[/green] Code generated\n")
        console.print(Panel(
            generated_code,
            title="Generated Code",
            border_style="green",
            expand=False
        ))
        
        console.print("\n[dim]Step 2/4: Executing code...[/dim]")
        executor = PlaywrightExecutor(headless=headless)
        success, error_info = executor.execute(generated_code)
        
        if not success and error_info:
            console.print("[yellow]⚠[/yellow] Execution failed. Attempting self-healing...\n")
            console.print(f"[dim]Error: {error_info['message']}[/dim]\n")
            
            console.print("[dim]Step 3/4: Self-healing locators...[/dim]")
            healer = SelfHealingEngine()
            healed_code = healer.heal(generated_code, error_info, command)
            
            console.print("[green]✓[/green] Locators healed\n")
            console.print(Panel(
                healed_code,
                title="Healed Code",
                border_style="yellow",
                expand=False
            ))
            
            console.print("\n[dim]Re-executing healed code...[/dim]")
            success, error_info = executor.execute(healed_code)
            
            if success:
                console.print("[green]✓[/green] Execution successful after healing!\n")
                final_code = healed_code
            else:
                error_msg = error_info['message'] if error_info else "Unknown error"
                console.print(f"[red]✗[/red] Execution still failed: {error_msg}\n")
                return
        else:
            console.print("[green]✓[/green] Execution successful!\n")
            final_code = generated_code
        
        console.print("[dim]Step 4/4: Generating standalone script...[/dim]")
        output_gen = OutputGenerator()
        script_path = output_gen.save_script(final_code, output_path, command)
        
        console.print(f"[green]✓[/green] Standalone script saved to: [bold]{script_path}[/bold]\n")
        console.print("[dim]This script can be run independently without OpenAI/MCP![/dim]")
        
    except Exception as e:
        console.print(f"[red]Error processing command: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")

if __name__ == "__main__":
    main()
