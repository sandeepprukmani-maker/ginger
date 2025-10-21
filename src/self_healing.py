import os
import re
from openai import OpenAI
from rich.console import Console

console = Console()

class SelfHealingEngine:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self.client = OpenAI(api_key=api_key)
    
    def heal(self, original_code: str, error_info: dict, original_command: str) -> str:
        system_prompt = """You are a Playwright code debugging expert specializing in fixing locator issues.

When a Playwright script fails due to a locator not finding an element, your job is to:
1. Identify the problematic locator in the code
2. Suggest alternative locator strategies that are more robust
3. Fix the code by replacing the failed locator with a better one

Locator priority (most to least stable):
1. get_by_role() - Best for semantic elements
2. get_by_label() - Good for form fields
3. get_by_placeholder() - Good for inputs
4. get_by_text() - Good for links/buttons
5. locator() with data-testid - Stable if available
6. CSS selectors - Less stable, use as last resort

Return ONLY the fixed function code, no explanations."""
        
        user_prompt = f"""The following Playwright code failed to execute:

```python
{original_code}
```

Error information:
- Type: {error_info['type']}
- Message: {error_info['message']}
- Failed locator: {error_info.get('failed_locator', 'Unknown')}

Original automation task: "{original_command}"

Fix the code by replacing the failed locator with a more robust alternative.
Try multiple locator strategies if possible. Return only the fixed run_automation(page) function."""
        
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
            
            healed_code = response.choices[0].message.content
            if healed_code is None:
                raise ValueError("OpenAI returned empty response")
            healed_code = healed_code.strip()
            
            if "```python" in healed_code:
                healed_code = healed_code.split("```python")[1].split("```")[0].strip()
            elif "```" in healed_code:
                healed_code = healed_code.split("```")[1].split("```")[0].strip()
            
            return healed_code
            
        except Exception as e:
            console.print(f"[red]Error during self-healing: {e}[/red]")
            raise
