"""
🎮 Interactive Mode for Browser Automation
Provides a rich REPL interface with real-time feedback, command history, and autocomplete
"""

import asyncio
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from .logger import get_logger

logger = get_logger()


class InteractiveSession:
    """Interactive browser automation session with rich UI."""
    
    def __init__(self, automation):
        self.automation = automation
        self.console = Console()
        self.history: List[Dict[str, Any]] = []
        self.session_start = datetime.now()
        
        self.quick_commands = {
            "help": self._show_help,
            "h": self._show_help,
            "metrics": self._show_metrics,
            "m": self._show_metrics,
            "history": self._show_history,
            "clear": self._clear_screen,
            "cls": self._clear_screen,
            "quit": None,
            "exit": None,
            "q": None,
        }
    
    def _print_banner(self):
        """Display welcome banner."""
        banner = """
[bold cyan]╔═══════════════════════════════════════════════════════════╗
║   🚀 ULTRA-ENHANCED BROWSER AUTOMATION - INTERACTIVE MODE  ║
║                                                           ║
║   ⚡ Intelligent Caching    🧠 GPT-4o Vision             ║
║   🔄 Parallel Execution     🔍 Semantic Matching          ║
║   🔮 Predictive Loading     📊 Real-time Metrics          ║
╚═══════════════════════════════════════════════════════════╝[/bold cyan]
        """
        self.console.print(banner)
        
        config_info = f"""
[dim]Configuration:[/dim]
  • AI Model: [cyan]{'GPT-4o (Max Intelligence)' if self.automation.use_gpt4o else 'GPT-4o-mini (Fast)'}[/cyan]
  • Vision: [{'green' if self.automation.enable_vision else 'red'}]{'Enabled' if self.automation.enable_vision else 'Disabled'}[/]
  • Caching: [{'green' if self.automation.enable_caching else 'red'}]{'Enabled' if self.automation.enable_caching else 'Disabled'}[/]
  • Parallel: [{'green' if self.automation.enable_parallel else 'red'}]{'Enabled' if self.automation.enable_parallel else 'Disabled'}[/]
  • Max Retries: [cyan]{self.automation.max_retries}[/cyan]
        """
        self.console.print(Panel(config_info.strip(), title="🎮 Session Info", border_style="blue"))
    
    def _show_help(self):
        """Display help information."""
        help_table = Table(title="📖 Interactive Commands", show_header=True, header_style="bold magenta")
        help_table.add_column("Command", style="cyan", width=20)
        help_table.add_column("Aliases", style="dim", width=15)
        help_table.add_column("Description", style="green")
        
        commands = [
            ("Natural Language", "", "Just type what you want! e.g., 'go to google.com'"),
            ("help, h", "", "Show this help menu"),
            ("metrics, m", "", "Display performance metrics"),
            ("history", "", "Show command history"),
            ("clear, cls", "", "Clear the screen"),
            ("quit, exit, q", "", "Exit interactive mode"),
        ]
        
        for cmd, alias, desc in commands:
            help_table.add_row(cmd, alias, desc)
        
        self.console.print(help_table)
        
        self.console.print("\n[bold cyan]💡 Pro Tips:[/bold cyan]")
        tips = [
            "• Use natural language: 'click the login button', 'fill email field with test@example.com'",
            "• Chain actions: 'navigate to github.com and click sign in'",
            "• Extract data: 'get all links from the page'",
            "• Take screenshots: 'take a screenshot of the homepage'",
            "• Let AI figure it out: The system will find elements even with fuzzy descriptions",
        ]
        for tip in tips:
            self.console.print(f"  {tip}")
    
    def _show_metrics(self):
        """Display performance metrics."""
        metrics = self.automation.metrics
        
        metrics_table = Table(title="📊 Performance Metrics", show_header=True, header_style="bold yellow")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green", justify="right")
        
        data = [
            ("Total Commands", str(metrics.total_commands)),
            ("Cache Hit Rate", f"{metrics.cache_hit_rate():.1f}%"),
            ("Cache Hits", str(metrics.cache_hits)),
            ("Cache Misses", str(metrics.cache_misses)),
            ("Vision API Calls", str(metrics.vision_calls)),
            ("Total Retries", str(metrics.total_retries)),
            ("Avg Response Time", f"{metrics.avg_response_time:.2f}s"),
            ("Session Duration", str(datetime.now() - self.session_start).split('.')[0]),
        ]
        
        for metric, value in data:
            metrics_table.add_row(metric, value)
        
        self.console.print(metrics_table)
        
        if metrics.total_commands > 0:
            efficiency = "🔥 Excellent" if metrics.cache_hit_rate() > 50 else "✅ Good" if metrics.cache_hit_rate() > 20 else "📈 Building"
            self.console.print(f"\n[bold]Cache Efficiency:[/bold] {efficiency}")
    
    def _show_history(self):
        """Display command history."""
        if not self.history:
            self.console.print("[yellow]No command history yet[/yellow]")
            return
        
        history_table = Table(title="📜 Command History", show_header=True, header_style="bold blue")
        history_table.add_column("#", style="dim", width=5)
        history_table.add_column("Command", style="cyan")
        history_table.add_column("Status", style="green", width=12)
        history_table.add_column("Time", style="yellow", width=10)
        
        for i, entry in enumerate(self.history[-10:], 1):
            status = "✓ Success" if entry.get("status") == "success" else "⚠ Partial" if entry.get("status") == "partial_success" else "✗ Failed"
            history_table.add_row(
                str(i),
                entry["command"][:60] + "..." if len(entry["command"]) > 60 else entry["command"],
                status,
                f"{entry.get('execution_time', 0):.1f}s"
            )
        
        self.console.print(history_table)
    
    def _clear_screen(self):
        """Clear the console screen."""
        self.console.clear()
        self._print_banner()
    
    async def _execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a command with progress indicator."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task(f"⚡ Executing: {command[:50]}...", total=None)
            
            try:
                result = await self.automation.execute_command(command)
                progress.update(task, completed=True)
                return result
            except Exception as e:
                progress.update(task, completed=True)
                logger.error(f"Command execution failed: {e}")
                return {
                    "status": "error",
                    "summary": str(e),
                    "should_continue": True
                }
    
    def _display_result(self, command: str, result: Dict[str, Any]):
        """Display command result in a nice format."""
        status = result.get("status", "unknown")
        summary = result.get("summary", "No summary available")
        exec_time = result.get("execution_time", 0)
        
        status_color = "green" if status == "success" else "yellow" if status == "partial_success" else "red"
        status_icon = "✓" if status == "success" else "⚠" if status == "partial_success" else "✗"
        
        self.console.print(f"\n[{status_color}]{status_icon} Status:[/{status_color}] [{status_color}]{status}[/{status_color}]")
        
        if summary:
            self.console.print(Panel(
                summary,
                title="📋 Result",
                border_style=status_color,
                padding=(1, 2)
            ))
        
        if exec_time > 0:
            metrics_info = result.get("metrics", {})
            info_text = f"⏱️  Execution time: [cyan]{exec_time:.2f}s[/cyan]"
            if metrics_info:
                info_text += f" | Cache hit rate: [cyan]{metrics_info.get('cache_hit_rate', 0):.1f}%[/cyan]"
                if metrics_info.get('vision_calls', 0) > 0:
                    info_text += f" | 🧠 Vision calls: [cyan]{metrics_info.get('vision_calls')}[/cyan]"
            self.console.print(f"[dim]{info_text}[/dim]")
        
        self.history.append({
            "command": command,
            "status": status,
            "execution_time": exec_time,
            "timestamp": datetime.now()
        })
    
    async def run(self):
        """Run the interactive session."""
        self._clear_screen()
        self.console.print("\n[green]Type 'help' for commands, or just describe what you want to do![/green]\n")
        
        try:
            while True:
                try:
                    command = Prompt.ask(
                        "\n[bold cyan]🤖[/bold cyan]",
                        console=self.console
                    ).strip()
                    
                    if not command:
                        continue
                    
                    command_lower = command.lower()
                    
                    if command_lower in ["quit", "exit", "q"]:
                        if Confirm.ask("Are you sure you want to exit?", default=False):
                            break
                        continue
                    
                    if command_lower in self.quick_commands:
                        handler = self.quick_commands[command_lower]
                        if handler:
                            handler()
                        continue
                    
                    result = await self._execute_command(command)
                    self._display_result(command, result)
                    
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Command cancelled (Ctrl+C)[/yellow]")
                    continue
                except EOFError:
                    break
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    self.console.print(f"[red]Error: {e}[/red]")
        
        finally:
            self.console.print("\n[cyan]Session Summary:[/cyan]")
            self._show_metrics()
            self.console.print(f"\n[green]✓ Session completed. Total commands: {len(self.history)}[/green]")


async def start_interactive_mode(
    api_key: Optional[str] = None,
    use_gpt4o: bool = False,
    enable_vision: bool = True,
    browser: str = "chromium",
    headless: bool = True
):
    """
    Start an interactive browser automation session.
    
    Args:
        api_key: OpenAI API key (will prompt if not provided)
        use_gpt4o: Use GPT-4o for maximum intelligence (slower, more accurate)
        enable_vision: Enable GPT-4 Vision for element detection
        browser: Browser type (chromium, firefox, webkit)
        headless: Run browser in headless mode
    """
    console = Console()
    
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            api_key = Prompt.ask("Enter your OpenAI API key", password=True)
    
    automation = None
    try:
        from .mcp_client import PlaywrightMCPClient
        
        sys_path = Path(__file__).parent.parent.parent
        import sys
        if str(sys_path) not in sys.path:
            sys.path.insert(0, str(sys_path))
        
        from nl_automation_mcp import EnhancedMCPAutomation
        
        automation = EnhancedMCPAutomation(
            api_key=api_key,
            enable_vision=enable_vision,
            max_retries=5,
            enable_caching=True,
            enable_parallel=True,
            enable_predictions=True,
            use_gpt4o=use_gpt4o
        )
        
        with console.status("[bold cyan]Initializing browser automation...", spinner="dots"):
            await automation.initialize(browser=browser, headless=headless)
        
        session = InteractiveSession(automation)
        await session.run()
        
    except Exception as e:
        console.print(f"[red]Failed to start interactive mode: {e}[/red]")
        logger.exception("Interactive mode error")
    finally:
        if automation:
            try:
                await automation.close()
            except:
                pass


if __name__ == "__main__":
    import sys
    
    use_gpt4o = "--gpt4o" in sys.argv or "-4" in sys.argv
    no_vision = "--no-vision" in sys.argv
    visible = "--visible" in sys.argv or "-v" in sys.argv
    
    asyncio.run(start_interactive_mode(
        use_gpt4o=use_gpt4o,
        enable_vision=not no_vision,
        headless=not visible
    ))
