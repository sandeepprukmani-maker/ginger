import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.automation import BrowserEngine, EnhancedNaturalLanguageExecutor, AI_AVAILABLE
from src.automation.config import BrowserConfig, AutomationConfig
from src.automation.logger import get_logger, console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

logger = get_logger()


async def run_natural_language_automation():
    """
    Run browser automation using natural language instructions.
    """
    console.print(Panel.fit(
        "[bold cyan]Natural Language Browser Automation[/bold cyan]\n"
        "[dim]Describe what you want to automate, and AI will do it[/dim]",
        border_style="cyan"
    ))
    
    if not AI_AVAILABLE:
        console.print("[red]AI features not available. Please ensure OpenAI package is installed.[/red]")
        return
    
    import os
    if not os.getenv("OPENAI_API_KEY"):
        console.print("[red]OPENAI_API_KEY not set. Please set your OpenAI API key.[/red]")
        console.print("[yellow]You can set it with: export OPENAI_API_KEY='your-api-key'[/yellow]")
        return
    
    browser_config = BrowserConfig(
        headless=True,
        screenshot_on_error=True,
        timeout=30000
    )
    automation_config = AutomationConfig(
        log_level="INFO",
        max_retries=3,
        retry_delay=2
    )
    
    browser = BrowserEngine(browser_config, automation_config)
    nl_executor = EnhancedNaturalLanguageExecutor(browser, automation_config)
    
    try:
        await browser.start()
        logger.success("Browser started successfully")
        
        console.print("\n[bold cyan]Enhanced Natural Language Automation Mode[/bold cyan]")
        console.print("[green]✨ Powered by vision-based intelligence and advanced automation[/green]\n")
        console.print("[dim]Examples:[/dim]")
        console.print("  • Go to google.com and search for 'browser automation'")
        console.print("  • Navigate to example.com and extract all headings")
        console.print("  • Open github.com and click the login button")
        console.print("  • Visit news.ycombinator.com and get the top 5 story titles")
        console.print("  • Find all product prices on this page and save them")
        console.print("  • Fill in the contact form and submit it\n")
        
        stats = nl_executor.get_memory_stats()
        if stats["total_executions"] > 0:
            console.print(f"[dim]Memory: {stats['total_executions']} executions, "
                        f"{stats['success_rate']:.1f}% success rate[/dim]\n")
        
        while True:
            instruction = Prompt.ask("\n[bold green]What would you like to automate?[/bold green]", default="")
            
            if not instruction:
                if Confirm.ask("No instruction provided. Exit?", default=True):
                    break
                continue
            
            if instruction.lower() in ["exit", "quit", "q"]:
                console.print("[cyan]Goodbye![/cyan]")
                break
            
            if instruction.lower() == "stats":
                show_stats(nl_executor)
                continue
            
            starting_url = Prompt.ask("Starting URL (optional, press Enter to skip)", default="")
            url = starting_url if starting_url else None
            
            use_vision = Confirm.ask("Use vision-based analysis? (slower but more intelligent)", default=False)
            
            console.print(f"\n[yellow]Executing: {instruction}[/yellow]")
            if use_vision:
                console.print("[cyan]✨ Vision mode enabled - AI will analyze page structure[/cyan]")
            console.print("[dim]The AI will convert this to browser actions and execute them...[/dim]\n")
            
            try:
                result = await nl_executor.execute_instruction(instruction, url, use_vision=use_vision)
                
                if result.success:
                    console.print(f"\n[bold green]✓ Success![/bold green] "
                                f"Completed {result.steps_completed}/{result.total_steps} steps")
                    
                    if result.data:
                        console.print("\n[bold]Extracted Data:[/bold]")
                        if isinstance(result.data, list):
                            if len(result.data) > 10:
                                console.print(f"[dim]Showing first 10 of {len(result.data)} items[/dim]")
                            for i, item in enumerate(result.data[:10], 1):
                                console.print(f"  {i}. {str(item)[:100]}")
                        else:
                            console.print(f"  {result.data}")
                    
                    if Confirm.ask("\nTake a screenshot?", default=False):
                        screenshot_path = await browser.screenshot("nl_automation")
                        logger.success(f"Screenshot saved to {screenshot_path}")
                
                else:
                    console.print(f"\n[bold red]✗ Failed[/bold red] after {result.steps_completed}/{result.total_steps} steps")
                    console.print(f"[red]Error: {result.error}[/red]")
                    
                    if Confirm.ask("Take error screenshot for debugging?", default=True):
                        screenshot_path = await browser.screenshot("nl_automation_error")
                        logger.info(f"Error screenshot saved to {screenshot_path}")
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Execution cancelled[/yellow]")
            except Exception as e:
                logger.exception(f"Error during execution: {e}")
            
            if not Confirm.ask("\nRun another automation?", default=True):
                break
    
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
    
    finally:
        await browser.stop()
        logger.info("Browser stopped")
        
        final_stats = nl_executor.get_memory_stats()
        console.print(f"\n[dim]Session complete. Total executions: {final_stats['total_executions']}, "
                    f"Success rate: {final_stats['success_rate']:.1f}%[/dim]")


def show_stats(nl_executor: EnhancedNaturalLanguageExecutor):
    """Display execution statistics."""
    stats = nl_executor.get_memory_stats()
    
    table = Table(title="Execution Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Executions", str(stats["total_executions"]))
    table.add_row("Successes", str(stats["successes"]))
    table.add_row("Failures", str(stats["failures"]))
    table.add_row("Success Rate", f"{stats['success_rate']:.1f}%")
    table.add_row("Learned Patterns", str(stats["learned_patterns"]))
    
    console.print(table)


async def main():
    try:
        await run_natural_language_automation()
    except KeyboardInterrupt:
        console.print("\n[yellow]Program terminated[/yellow]")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
