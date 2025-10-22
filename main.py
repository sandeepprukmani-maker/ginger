"""Main entry point for NL2Playwright converter."""
import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax

# Load environment variables
load_dotenv()

# Import converter
from converter import NL2PlaywrightConverter


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()


def get_llm():
    """Get LLM instance based on available API keys."""
    # Try OpenAI first
    if os.getenv('OPENAI_API_KEY'):
        from browser_use import ChatOpenAI
        console.print("[green]Using OpenAI (GPT-4.1-mini)[/green]")
        return ChatOpenAI(model='gpt-4.1-mini', temperature=0.0)
    
    # Try Anthropic
    elif os.getenv('ANTHROPIC_API_KEY'):
        from browser_use import ChatAnthropic
        console.print("[green]Using Anthropic (Claude Sonnet 4)[/green]")
        return ChatAnthropic(model='claude-sonnet-4-0', temperature=0.0)
    
    # Try Google Gemini
    elif os.getenv('GEMINI_API_KEY'):
        from browser_use import ChatGoogle
        console.print("[green]Using Google Gemini (Flash)[/green]")
        return ChatGoogle(model='gemini-2.0-flash-exp', temperature=0.0)
    
    # Try Browser Use Cloud
    elif os.getenv('BROWSER_USE_API_KEY'):
        from browser_use import ChatBrowserUse
        console.print("[green]Using Browser Use Cloud LLM[/green]")
        return ChatBrowserUse()
    
    else:
        console.print("[red]Error: No LLM API key found![/red]")
        console.print("\nPlease set one of the following environment variables:")
        console.print("  - OPENAI_API_KEY")
        console.print("  - ANTHROPIC_API_KEY")
        console.print("  - GEMINI_API_KEY")
        console.print("  - BROWSER_USE_API_KEY")
        console.print("\nYou can add it to a .env file in the nl2playwright directory.")
        sys.exit(1)


def display_banner():
    """Display welcome banner."""
    banner = """
 ███╗   ██╗██╗     ██████╗ ██████╗ ██╗      █████╗ ██╗   ██╗██╗    ██╗██████╗ ██╗ ██████╗ ██╗  ██╗████████╗
 ████╗  ██║██║     ╚════██╗██╔══██╗██║     ██╔══██╗╚██╗ ██╔╝██║    ██║██╔══██╗██║██╔════╝ ██║  ██║╚══██╔══╝
 ██╔██╗ ██║██║      █████╔╝██████╔╝██║     ███████║ ╚████╔╝ ██║ █╗ ██║██████╔╝██║██║  ███╗███████║   ██║   
 ██║╚██╗██║██║     ██╔═══╝ ██╔═══╝ ██║     ██╔══██║  ╚██╔╝  ██║███╗██║██╔══██╗██║██║   ██║██╔══██║   ██║   
 ██║ ╚████║███████╗███████╗██║     ███████╗██║  ██║   ██║   ╚███╔███╔╝██║  ██║██║╚██████╔╝██║  ██║   ██║   
 ╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝    ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
    """
    console.print(Panel(f"[cyan]{banner}[/cyan]", title="[bold]Natural Language to Playwright[/bold]", border_style="cyan"))
    console.print("[dim]Convert natural language commands into executable Playwright scripts[/dim]\n")


async def main():
    """Main application loop."""
    display_banner()
    
    # Get LLM
    try:
        llm = get_llm()
    except Exception as e:
        console.print(f"[red]Error initializing LLM: {e}[/red]")
        return
    
    # Create converter
    headless = os.getenv('HEADLESS', 'false').lower() == 'true'
    output_dir = os.getenv('OUTPUT_DIR', 'generated_scripts')
    
    converter = NL2PlaywrightConverter(
        llm=llm,
        headless=headless,
        output_dir=output_dir
    )
    
    console.print(f"[green]✓[/green] Browser mode: {'Headless' if headless else 'Visible'}")
    console.print(f"[green]✓[/green] Output directory: {output_dir}\n")
    
    # Main loop
    while True:
        try:
            # Get user input
            console.print("[bold cyan]Enter your task[/bold cyan] (or 'quit' to exit):")
            task = Prompt.ask("[yellow]>[/yellow]")
            
            if task.lower() in ('quit', 'exit', 'q'):
                console.print("\n[cyan]Goodbye! 👋[/cyan]")
                break
            
            if not task.strip():
                continue
            
            # Convert to Playwright script
            console.print(f"\n[dim]Processing task...[/dim]")
            
            script, output_path = await converter.convert(task)
            
            # Display results
            console.print("\n" + "="*80)
            console.print(Panel(
                f"[green]✓ Script generated successfully![/green]\n\nSaved to: [cyan]{output_path}[/cyan]",
                title="[bold]Success[/bold]",
                border_style="green"
            ))
            
            # Show preview
            console.print("\n[bold]Script Preview:[/bold]")
            syntax = Syntax(script, "python", theme="monokai", line_numbers=True)
            console.print(syntax)
            console.print("="*80 + "\n")
            
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted by user[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            logger.exception("Conversion error")
            console.print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[cyan]Goodbye! 👋[/cyan]")
