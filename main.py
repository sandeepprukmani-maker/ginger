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

    # ❌ Incorrect: os.getenv is a function, not a dictionary
    # os.getenv['OPENAI_API_KEY'] = 'sk-...'

    # ✅ Correct way to set environment variable
    os.environ['OPENAI_API_KEY'] = (
        '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'
    )

    api_key = os.getenv('OPENAI_API_KEY')

    if api_key:
        try:
            from browser_use import ChatOpenAI
            console.print("[green]Using OpenAI (GPT-4.1-mini)[/green]")
            return ChatOpenAI(model='gpt-4.1-mini', temperature=0.0)
        except ImportError:
            console.print("[red]Error: 'browser_use' module not found.[/red]")
            sys.exit(1)
    else:
        console.print("[red]Error: No LLM API key found![/red]")
        console.print("\nPlease set one of the following environment variables:")
        console.print("  - OPENAI_API_KEY")
        console.print("\nYou can add it to a .env file in the nl2playwright directory.")
        sys.exit(1)


def display_banner():
    """Display welcome banner."""
    banner = r"""
 ███╗   ██╗██╗     ██████╗ ██████╗ ██╗      █████╗ ██╗   ██╗██╗    ██╗██████╗ ██╗ ██████╗ ██╗  ██╗████████╗
 ████╗  ██║██║     ╚════██╗██╔══██╗██║     ██╔══██╗╚██╗ ██╔╝██║    ██║██╔══██╗██║██╔════╝ ██║  ██║╚══██╔══╝
 ██╔██╗ ██║██║      █████╔╝██████╔╝██║     ███████║ ╚████╔╝ ██║ █╗ ██║██████╔╝██║██║  ███╗███████║   ██║   
 ██║╚██╗██║██║     ██╔═══╝ ██╔═══╝ ██║     ██╔══██║  ╚██╔╝  ██║███╗██║██╔══██╗██║██║   ██║██╔══██║   ██║   
 ██║ ╚████║███████╗███████╗██║     ███████╗██║  ██║   ██║   ╚███╔███╔╝██║  ██║██║╚██████╔╝██║  ██║   ██║   
 ╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝   ╚═╝    ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
    """
    console.print(
        Panel(
            f"[cyan]{banner}[/cyan]",
            title="[bold]Natural Language to Playwright[/bold]",
            border_style="cyan",
        )
    )
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
            console.print("[bold cyan]Enter your task[/bold cyan] (or 'quit' to exit):")
            task = Prompt.ask("[yellow]>[/yellow]")

            if task.lower() in ('quit', 'exit', 'q'):
                console.print("\n[cyan]Goodbye! 👋[/cyan]")
                break

            if not task.strip():
                continue

            console.print(f"\n[dim]Processing task...[/dim]")

            script, output_path = await converter.convert(task)

            console.print("\n" + "=" * 80)
            console.print(
                Panel(
                    f"[green]✓ Script generated successfully![/green]\n\nSaved to: [cyan]{output_path}[/cyan]",
                    title="[bold]Success[/bold]",
                    border_style="green",
                )
            )

            console.print("\n[bold]Script Preview:[/bold]")
            syntax = Syntax(script, "python", theme="monokai", line_numbers=True)
            console.print(syntax)
            console.print("=" * 80 + "\n")

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
