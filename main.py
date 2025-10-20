import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.automation import BrowserEngine, TaskExecutor, AITaskGenerator, AI_AVAILABLE
from src.automation.config import BrowserConfig, AutomationConfig
from src.automation.logger import get_logger, console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

logger = get_logger()


async def run_web_automation_demo():
    console.print(Panel.fit("Web Automation Demo", style="bold cyan"))
    
    url = Prompt.ask("Enter URL to automate")
    
    browser_config = BrowserConfig(headless=True, screenshot_on_error=True)
    automation_config = AutomationConfig(log_level="INFO")
    
    browser = BrowserEngine(browser_config, automation_config)
    executor = TaskExecutor(browser)
    
    try:
        await browser.start()
        
        logger.info(f"Navigating to {url}")
        await browser.navigate(url)
        await browser.wait_for_load()
        
        page_title = await browser.get_text("h1")
        if page_title:
            logger.success(f"Page heading: {page_title}")
        
        links = await browser.get_all_text("a")
        if links:
            console.print(f"\n[cyan]Found {len(links)} links on the page[/cyan]")
            
            table = Table(title="First 10 Links", show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=3)
            table.add_column("Link Text", style="cyan")
            
            for i, link_text in enumerate(links[:10], 1):
                if link_text.strip():
                    table.add_row(str(i), link_text.strip()[:80])
            
            console.print(table)
        
        screenshot_path = await browser.screenshot("web_automation_demo")
        logger.success(f"Screenshot saved to {screenshot_path}")
            
    except Exception as e:
        logger.exception(f"Error during automation: {e}")
    finally:
        await browser.stop()


async def run_ai_code_generation():
    console.print(Panel.fit("AI Code Generation Demo", style="bold cyan"))
    
    if not AI_AVAILABLE:
        console.print("[red]AI code generation is not available due to package compatibility issues.[/red]")
        console.print("[yellow]The core automation framework works without AI features.[/yellow]")
        return
    
    task_description = Prompt.ask(
        "Describe the automation task"
    )
    
    config = AutomationConfig(openai_model="gpt-4o-mini", mcp_timeout=300)
    generator = AITaskGenerator(config)
    
    console.print("\n[yellow]Generating code... This may take a moment.[/yellow]\n")
    
    code = await generator.generate_playwright_code(task_description)
    
    if code:
        console.print(Panel(code, title="Generated Code", border_style="green"))
        
        if Confirm.ask("Save to file?", default=True):
            filename = Prompt.ask("Filename", default="generated_automation.py")
            with open(filename, 'w') as f:
                f.write(code)
            logger.success(f"Code saved to {filename}")
    else:
        logger.error("Failed to generate code. Make sure OPENAI_API_KEY is set.")


async def run_form_automation_demo():
    console.print(Panel.fit("Form Automation Demo", style="bold cyan"))
    
    url = Prompt.ask("Enter form URL")
    
    browser_config = BrowserConfig(headless=True, screenshot_on_error=True)
    automation_config = AutomationConfig(log_level="INFO")
    
    browser = BrowserEngine(browser_config, automation_config)
    executor = TaskExecutor(browser)
    
    try:
        await browser.start()
        
        logger.info(f"Navigating to {url}")
        await browser.navigate(url)
        await browser.wait_for_load()
        
        console.print("\n[yellow]You can now define form fields to fill[/yellow]")
        console.print("[dim]Example: input[name='email'] = test@example.com[/dim]\n")
        
        form_data = {}
        
        while True:
            selector = Prompt.ask("Enter CSS selector (or press Enter to finish)", default="")
            if not selector:
                break
            
            value = Prompt.ask(f"Enter value for '{selector}'")
            form_data[selector] = value
        
        if form_data:
            success = await executor.fill_form(form_data)
            if success:
                logger.success("Form filled successfully!")
                
                screenshot_path = await browser.screenshot("form_filled")
                logger.success(f"Screenshot saved to {screenshot_path}")
        else:
            logger.info("No form data provided")
            
    except Exception as e:
        logger.exception(f"Error during automation: {e}")
    finally:
        await browser.stop()


async def run_data_extraction_demo():
    console.print(Panel.fit("Data Extraction Demo", style="bold cyan"))
    
    url = Prompt.ask("Enter URL to extract data from")
    selector = Prompt.ask("Enter CSS selector for elements to extract")
    
    browser_config = BrowserConfig(headless=True, screenshot_on_error=True)
    automation_config = AutomationConfig(log_level="INFO")
    
    browser = BrowserEngine(browser_config, automation_config)
    
    try:
        await browser.start()
        
        logger.info(f"Navigating to {url}")
        await browser.navigate(url)
        await browser.wait_for_load()
        
        texts = await browser.get_all_text(selector)
        
        if texts:
            console.print(f"\n[cyan]Found {len(texts)} elements matching '{selector}'[/cyan]\n")
            
            table = Table(title="Extracted Data", show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=5)
            table.add_column("Content", style="green")
            
            for i, text in enumerate(texts[:20], 1):
                if text.strip():
                    table.add_row(str(i), text.strip()[:100])
            
            console.print(table)
            
            if Confirm.ask("\nSave to file?", default=False):
                filename = Prompt.ask("Filename", default="extracted_data.txt")
                with open(filename, 'w') as f:
                    for text in texts:
                        f.write(f"{text}\n")
                logger.success(f"Data saved to {filename}")
        else:
            logger.warning(f"No elements found matching selector: {selector}")
            
    except Exception as e:
        logger.exception(f"Error during automation: {e}")
    finally:
        await browser.stop()


async def main():
    console.print(Panel.fit(
        "[bold cyan]Browser Automation Framework[/bold cyan]\n"
        "[dim]Universal web automation for any site[/dim]",
        border_style="cyan"
    ))
    
    options = {
        "1": ("Web Automation Demo", run_web_automation_demo),
        "2": ("Form Automation Demo", run_form_automation_demo),
        "3": ("Data Extraction Demo", run_data_extraction_demo),
        "4": (f"AI Code Generation {'[dim](unavailable)[/dim]' if not AI_AVAILABLE else ''}", run_ai_code_generation),
        "5": ("Exit", None)
    }
    
    while True:
        console.print("\n[bold]Available Demos:[/bold]")
        for key, (name, _) in options.items():
            console.print(f"  {key}. {name}")
        
        choice = Prompt.ask("\nSelect an option", choices=list(options.keys()), default="1")
        
        if choice == "5":
            console.print("\n[cyan]Goodbye![/cyan]")
            break
        
        _, func = options[choice]
        if func:
            try:
                await func()
            except KeyboardInterrupt:
                console.print("\n[yellow]Operation cancelled[/yellow]")
            except Exception as e:
                logger.exception(f"Unexpected error: {e}")
        
        console.print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Program terminated[/yellow]")
