import os
from openai import OpenAI
from rich.console import Console

console = Console()

class CodeGenerator:
    def __init__(self):
        api_key = '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'
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Please set it before running the CLI."
            )
        self.client = OpenAI(api_key=api_key)
    
    def generate_code(self, natural_language_command: str) -> tuple[str, dict]:
        system_prompt = """You are an expert Playwright automation code generator. 
        
Convert natural language commands into robust Playwright Python code.

CRITICAL REQUIREMENTS:
1. Use MULTIPLE locator strategies for resilience (role, text, CSS, data-testid)
2. Generate code that uses Playwright's native locator methods
3. Include proper error handling
4. Add waits and assertions where appropriate
5. The code should be a complete function named 'run_automation' that takes a 'page' parameter
6. Use the most stable locators (prefer role and text over CSS selectors)
7. Return ONLY the function code, no explanations

Example locator strategies to use:
- page.get_by_role("button", name="Submit")
- page.get_by_text("Login")
- page.get_by_label("Email")
- page.get_by_placeholder("Enter your name")
- page.locator("[data-testid='submit-btn']")
- page.locator("css=.button.primary")

Generate the code inside a function called run_automation(page).
"""
        
        user_prompt = f"""Generate Playwright Python code for this automation task:

"{natural_language_command}"

Return only the run_automation(page) function with proper Playwright locators.
Use multiple locator strategies for robustness."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            generated_code = response.choices[0].message.content
            if generated_code is None:
                raise ValueError("OpenAI returned empty response")
            generated_code = generated_code.strip()
            
            if "```python" in generated_code:
                generated_code = generated_code.split("```python")[1].split("```")[0].strip()
            elif "```" in generated_code:
                generated_code = generated_code.split("```")[1].split("```")[0].strip()
            
            locator_info = self._extract_locator_info(generated_code)
            
            return generated_code, locator_info
            
        except Exception as e:
            console.print(f"[red]Error generating code: {e}[/red]")
            raise
    
    def _extract_locator_info(self, code: str) -> dict:
        locator_patterns = {
            'get_by_role': code.count('get_by_role'),
            'get_by_text': code.count('get_by_text'),
            'get_by_label': code.count('get_by_label'),
            'get_by_placeholder': code.count('get_by_placeholder'),
            'locator': code.count('locator('),
        }
        
        return {
            'strategies_used': [k for k, v in locator_patterns.items() if v > 0],
            'counts': locator_patterns,
            'total_locators': sum(locator_patterns.values())
        }
