import os
from typing import Optional
try:
    from openai import AsyncOpenAI, OpenAIError
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .logger import get_logger
from .config import AutomationConfig

logger = get_logger()


class AITaskGenerator:
    
    def __init__(self, automation_config: Optional[AutomationConfig] = None):
        self.config = automation_config or AutomationConfig()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI package not available. Install with: pip install openai")
        elif not self.api_key:
            logger.warning("OPENAI_API_KEY not set. AI code generation will not be available.")
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def generate_playwright_code(self, task_description: str) -> Optional[str]:
        if not OPENAI_AVAILABLE:
            logger.error("Cannot generate code: OpenAI package not installed")
            return None
        
        if not self.client:
            logger.error("Cannot generate code: OPENAI_API_KEY not set")
            return None
        
        logger.info(f"Generating Playwright code for: {task_description}")
        
        try:
            system_prompt = """You are an expert Python developer and Playwright automation engineer.
Generate complete, runnable Python scripts using Playwright.
Use realistic and working CSS or XPath selectors.
Provide only valid code with proper imports, async functions, and browser handling.
Make the code robust with error handling and logging.
Use best practices for browser automation.
Return ONLY the Python code, no explanations or markdown formatting."""

            user_prompt = f"""Generate a complete Python Playwright script for this task:

{task_description}

Requirements:
- Use async/await with Playwright
- Include proper imports
- Add error handling
- Use realistic selectors
- Make it production-ready
- Add logging where appropriate"""

            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            code = response.choices[0].message.content
            logger.success("Code generation completed")
            return code
            
        except Exception as e:
            logger.error(f"Error during code generation: {e}")
            return None
    
    async def generate_scraping_code(self, url: str, data_description: str) -> Optional[str]:
        task = (
            f"Generate Python Playwright code to scrape data from {url}. "
            f"Extract the following data: {data_description}. "
            f"Return the data as a list of dictionaries and print it in JSON format."
        )
        return await self.generate_playwright_code(task)
    
    async def generate_form_filling_code(self, url: str, form_fields: str) -> Optional[str]:
        task = (
            f"Generate Python Playwright code to fill out a form at {url}. "
            f"The form has these fields: {form_fields}. "
            f"Fill the form with appropriate test data and submit it."
        )
        return await self.generate_playwright_code(task)
    
    async def generate_login_code(self, url: str, username_field: str, password_field: str) -> Optional[str]:
        task = (
            f"Generate Python Playwright code to log in to {url}. "
            f"Username field selector: {username_field}, Password field selector: {password_field}. "
            f"Include error handling and session management."
        )
        return await self.generate_playwright_code(task)
