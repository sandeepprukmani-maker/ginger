import os
import json
import uuid
from openai import OpenAI
from models import TestPlan, TestStep

class AIPromptConverter:
    def __init__(self):
        self.client = OpenAI(api_key='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')
    
    def convert_prompt_to_test_plan(self, prompt: str, browser: str = "chrome", headless: bool = False) -> TestPlan:
        """Convert natural language prompt to structured test plan"""
        
        system_prompt = """You are an expert in browser automation. Convert the user's request into a structured test plan.

The test plan should include:
1. A sequence of steps to accomplish the task
2. Each step should have: action, description, and appropriate parameters

Available actions (ONLY USE THESE):
- navigate: Go to a URL (use 'target' for the URL)
- click: Click an element (use 'target' for element description)
- type: Type text into an input (use 'target' for element, 'value' for text to type)
- wait: Wait for element or time (use 'target' for element or 'timeout' for milliseconds)
- snapshot: Take a screenshot (description only)
- handle_alert: Handle browser alerts (use 'alert_action' with 'accept' or 'dismiss')
- switch_tab: Switch to a different browser tab (use 'tab_index' for tab number)
- wait_for_new_tab: Wait for a new tab to open
- close_tab: Close the current tab
- get_alert_text: Get text from an alert

IMPORTANT: Do NOT use any other actions like 'assert', 'verify', 'check', etc. Only use the actions listed above.

For targets, use natural language descriptions like:
- "the search button"
- "the username input field"
- "https://google.com"

Return a JSON object with this exact structure:
{
  "name": "Brief name for the automation",
  "description": "What this automation does",
  "steps": [
    {
      "action": "navigate",
      "description": "Go to the website",
      "target": "https://example.com"
    },
    {
      "action": "type",
      "description": "Enter search term",
      "target": "the search input",
      "value": "search term"
    },
    {
      "action": "click",
      "description": "Click search button",
      "target": "the search button"
    }
  ]
}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                raise Exception("AI returned empty response")
            
            result = json.loads(content)
            
            # Create TestPlan from the result
            steps = []
            for step_data in result.get("steps", []):
                step = TestStep(
                    action=step_data.get("action", "wait"),
                    description=step_data.get("description", ""),
                    target=step_data.get("target"),
                    value=step_data.get("value"),
                    timeout=step_data.get("timeout", 5000)
                )
                steps.append(step)
            
            test_plan = TestPlan(
                id=str(uuid.uuid4()),
                name=result.get("name", "AI Generated Automation"),
                description=result.get("description", prompt),
                steps=steps,
                browser=browser,
                headless=headless
            )
            
            return test_plan
            
        except json.JSONDecodeError as e:
            raise Exception(f"AI returned invalid JSON: {str(e)}")
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            raise Exception(f"Failed to convert prompt to test plan: {str(e)}\nDetails: {error_detail}")
    
    def generate_playwright_code(self, test_plan: TestPlan, execution_report=None) -> str:
        """Generate standalone Playwright Python code from test plan"""
        
        code_lines = [
            "from playwright.sync_api import sync_playwright",
            "import time",
            "",
            "def run_automation():",
            "    with sync_playwright() as p:",
            f"        # Launch {test_plan.browser} browser",
            f"        browser = p.{test_plan.browser}.launch(headless={test_plan.headless})",
            "        page = browser.new_page()",
            "        ",
            f"        # {test_plan.description}",
            "        try:"
        ]
        
        for i, step in enumerate(test_plan.steps, 1):
            action = step.action
            target = step.target
            value = step.value
            desc = step.description
            
            code_lines.append(f"            # Step {i}: {desc}")
            
            if action == "navigate":
                code_lines.append(f'            page.goto("{target}")')
                code_lines.append("            page.wait_for_load_state('networkidle')")
                
            elif action == "click":
                code_lines.append(f'            # Click: {target}')
                code_lines.append(f'            page.get_by_text("{target}").first.click()')
                
            elif action == "type":
                code_lines.append(f'            # Type into: {target}')
                code_lines.append(f'            page.get_by_text("{target}").first.fill("{value}")')
                
            elif action == "wait":
                if target:
                    code_lines.append(f'            page.wait_for_selector("{target}")')
                else:
                    timeout_sec = (step.timeout or 1000) / 1000
                    code_lines.append(f"            time.sleep({timeout_sec})")
                    
            elif action == "snapshot":
                name = f"screenshot_{i}"
                code_lines.append(f'            page.screenshot(path="{name}.png")')
            
            code_lines.append("")
        
        code_lines.extend([
            "            print('Automation completed successfully!')",
            "            ",
            "        except Exception as e:",
            "            print(f'Error during automation: {e}')",
            "            page.screenshot(path='error_screenshot.png')",
            "            raise",
            "        finally:",
            "            browser.close()",
            "",
            "if __name__ == '__main__':",
            "    run_automation()"
        ])
        
        return "\n".join(code_lines)
