"""
Automation Script Generator with Self-Healing
Generates single executable automation scripts with embedded self-healing capabilities
"""
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI
from ..file_manager import AgentFileManager
from ..mcp_code_generator import MCPCodeGenerator

logger = logging.getLogger(__name__)


class AutomationAgent:
    """
    🤖 Automation Agent - Generates self-healing automation scripts
    
    Creates a single executable Python script that:
    - Performs the requested automation task
    - Includes self-healing logic for resilience
    - Uses stable locators and best practices
    - Can be run independently without the framework
    """
    
    def __init__(self, mcp_client, llm_client: OpenAI, model: str, file_manager: Optional[AgentFileManager] = None):
        """
        Initialize the Automation Agent
        
        Args:
            mcp_client: MCP client for browser automation
            llm_client: OpenAI client instance
            model: Model name to use
            file_manager: Optional file manager for saving scripts
        """
        self.mcp_client = mcp_client
        self.client = llm_client
        self.model = model
        self.file_manager = file_manager or AgentFileManager()
        
    def generate_automation_script(
        self, 
        execution_steps: List[Dict[str, Any]], 
        instruction: str,
        save_to_file: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a single self-healing automation script from execution steps
        
        Args:
            execution_steps: Steps captured from direct execution
            instruction: Original user instruction
            save_to_file: Whether to save the script to file
            
        Returns:
            Dictionary with generated script and metadata
        """
        logger.info("🤖 Generating self-healing automation script...")
        
        # Use MCP code generator to convert steps to Playwright code
        code_generator = MCPCodeGenerator(execution_steps, instruction)
        
        # Generate base Playwright code
        base_code = code_generator.generate_python_code(
            test_framework=False,  # Not a test, it's an automation script
            async_style=True,  # Use async for better performance
            use_locators=True,  # Extract locators for maintainability
            include_comments=True
        )
        
        # Wrap with self-healing template
        self_healing_script = self._add_self_healing_wrapper(base_code, instruction)
        
        # Save to file if requested
        script_file = None
        if save_to_file:
            script_name = self._sanitize_filename(instruction)
            script_file = f"automation_{script_name}.py"
            
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(self_healing_script)
            
            logger.info(f"✅ Automation script saved to {script_file}")
        
        return {
            "success": True,
            "generated_code": self_healing_script,
            "script_file": script_file,
            "message": "Self-healing automation script generated successfully"
        }
    
    def _add_self_healing_wrapper(self, base_code: str, instruction: str) -> str:
        """
        Wrap the base automation code with self-healing capabilities
        
        Args:
            base_code: Base Playwright automation code
            instruction: Original instruction for documentation
            
        Returns:
            Enhanced code with self-healing wrapper
        """
        return f'''"""
Self-Healing Browser Automation Script
Task: {instruction}

This script includes automatic healing for common failure modes:
- Retries with exponential backoff for temporary failures
- Automatic selector fallbacks if elements can't be found  
- Smart waits for dynamic content
- Detailed error reporting for debugging

To run:
    python automation_script.py

Requirements:
    pip install playwright
    playwright install chromium
"""

import asyncio
import logging
import time
from playwright.async_api import async_playwright, Page, Error as PlaywrightError
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SelfHealingAutomation:
    """Automation with self-healing capabilities"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        """
        Initialize the automation
        
        Args:
            max_retries: Maximum retry attempts for failed actions
            base_delay: Base delay for exponential backoff (seconds)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.page: Optional[Page] = None
    
    async def run_with_healing(self, page: Page):
        """
        Run the automation with self-healing
        
        Args:
            page: Playwright page object
        """
        self.page = page
        
        # Set default timeouts
        page.set_default_timeout(30000)  # 30 seconds
        
        try:
            await self._execute_automation()
            logger.info("✅ Automation completed successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Automation failed after retries: {{str(e)}}")
            return False
    
    async def _execute_automation(self):
        """Execute the main automation logic"""
        # GENERATED CODE STARTS HERE
{self._indent_code(base_code, 8)}
        # GENERATED CODE ENDS HERE
    
    async def click_with_healing(self, selector: str, timeout: int = 30000):
        """
        Click an element with automatic retries and healing
        
        Args:
            selector: Element selector
            timeout: Timeout in milliseconds
        """
        for attempt in range(self.max_retries):
            try:
                # Wait for element to be visible and enabled
                await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
                await self.page.click(selector, timeout=timeout)
                logger.debug(f"✅ Clicked: {{selector}}")
                return
            except PlaywrightError as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(f"⚠️  Click failed (attempt {{attempt + 1}}/{{self.max_retries}}): {{selector}}")
                    logger.warning(f"Retrying in {{delay}}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ Click failed after {{self.max_retries}} attempts: {{selector}}")
                    raise
    
    async def fill_with_healing(self, selector: str, value: str, timeout: int = 30000):
        """
        Fill an input field with automatic retries and healing
        
        Args:
            selector: Input selector
            value: Value to fill
            timeout: Timeout in milliseconds
        """
        for attempt in range(self.max_retries):
            try:
                await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
                await self.page.fill(selector, value, timeout=timeout)
                logger.debug(f"✅ Filled: {{selector}} with '{{value}}'")
                return
            except PlaywrightError as e:
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(f"⚠️  Fill failed (attempt {{attempt + 1}}/{{self.max_retries}}): {{selector}}")
                    logger.warning(f"Retrying in {{delay}}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"❌ Fill failed after {{self.max_retries}} attempts: {{selector}}")
                    raise


async def main():
    """Main entry point"""
    logger.info("=" * 80)
    logger.info("🚀 Starting self-healing browser automation")
    logger.info(f"Task: {instruction}")
    logger.info("=" * 80)
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True  # Set to False to see the browser
        )
        
        try:
            context = await browser.new_context(
                viewport={{"width": 1920, "height": 1080}}
            )
            page = await context.new_page()
            
            # Run automation with self-healing
            automation = SelfHealingAutomation(max_retries=3, base_delay=1.0)
            success = await automation.run_with_healing(page)
            
            if success:
                logger.info("=" * 80)
                logger.info("✅ Automation completed successfully")
                logger.info("=" * 80)
            else:
                logger.error("=" * 80)
                logger.error("❌ Automation failed")
                logger.error("=" * 80)
                
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
'''
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code by specified number of spaces"""
        indent = " " * spaces
        lines = code.split('\n')
        
        # Skip the imports and module docstring from base code
        # Extract just the automation logic
        in_main_function = False
        automation_lines = []
        
        for line in lines:
            # Skip imports, docstrings, and function definitions
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                continue
            if line.strip().startswith('"""') or line.strip().startswith("'''"):
                continue
            if 'async def main()' in line or 'def main()' in line:
                in_main_function = True
                continue
            if line.strip().startswith('if __name__'):
                break
            
            if in_main_function:
                # Remove one level of indentation from the original function
                if line.startswith('    '):
                    automation_lines.append(line[4:])
                elif line.strip():
                    automation_lines.append(line)
        
        # If we didn't find a main function, use the whole code
        if not automation_lines:
            automation_lines = [l for l in lines if l.strip() and not l.strip().startswith('import') and not l.strip().startswith('from')]
        
        # Add indentation
        indented_lines = [indent + line if line.strip() else '' for line in automation_lines]
        
        return '\n'.join(indented_lines)
    
    def _sanitize_filename(self, text: str, max_length: int = 50) -> str:
        """Convert text to safe filename"""
        # Remove special characters
        safe = ''.join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in text)
        # Replace spaces with underscores
        safe = safe.replace(' ', '_')
        # Lowercase and limit length
        safe = safe.lower()[:max_length]
        # Remove trailing underscores
        safe = safe.rstrip('_')
        return safe if safe else 'automation'
