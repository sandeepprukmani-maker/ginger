import asyncio
import json
import os
from openai import OpenAI
import time
from playwright.async_api import async_playwright


class PlaywrightAutomationEngine:
    """Real Playwright automation engine - executes actual browser automation"""

    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.openai_client = OpenAI(
            api_key=self.openai_api_key) if self.openai_api_key else None
        self.playwright = None
        self.browser = None
        self.page = None

    async def start_browser(self):
        """Start Playwright browser"""
        try:
            print("🚀 Starting Playwright browser...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.page = await self.browser.new_page()
            print("✅ Browser started successfully")
            return True
        except Exception as e:
            print(f"❌ Error starting browser: {e}")
            return False

    async def execute_action(self, tool_name, parameters):
        """Execute real Playwright actions"""
        print(f"🛠️ Executing: {tool_name}")
        print(f"📋 Parameters: {parameters}")

        try:
            if tool_name == "navigate":
                url = parameters.get("url")
                await self.page.goto(url, wait_until="networkidle")
                title = await self.page.title()
                return {
                    "status": "success",
                    "action": "navigate",
                    "url": url,
                    "title": title
                }

            elif tool_name == "click":
                selector = parameters.get("selector")
                await self.page.click(selector)
                await self.page.wait_for_timeout(500)
                return {
                    "status": "success",
                    "action": "click",
                    "selector": selector
                }

            elif tool_name == "fill":
                selector = parameters.get("selector")
                text = parameters.get("text")
                await self.page.fill(selector, text)
                return {
                    "status": "success",
                    "action": "fill",
                    "selector": selector,
                    "text": text
                }

            elif tool_name == "screenshot":
                path = f"screenshot_{int(time.time())}.png"
                await self.page.screenshot(path=path)
                return {
                    "status": "success",
                    "action": "screenshot",
                    "path": path
                }

            elif tool_name == "get_text":
                selector = parameters.get("selector")
                text = await self.page.inner_text(selector)
                return {
                    "status": "success",
                    "action": "get_text",
                    "selector": selector,
                    "text": text
                }

            elif tool_name == "get_all_text":
                selector = parameters.get("selector")
                elements = await self.page.query_selector_all(selector)
                texts = []
                for elem in elements:
                    text = await elem.inner_text()
                    texts.append(text)
                return {
                    "status": "success",
                    "action": "get_all_text",
                    "selector": selector,
                    "texts": texts
                }

            else:
                return {
                    "status": "error",
                    "error": f"Unknown action: {tool_name}"
                }

        except Exception as e:
            return {
                "status": "error",
                "action": tool_name,
                "error": str(e)
            }

    async def analyze_and_generate_actions(self, url, user_prompt):
        """Use OpenAI to analyze and generate automation actions"""

        if not self.openai_client:
            return await self.fallback_analysis(url, user_prompt)

        try:
            system_prompt = """You are a web automation expert using Playwright.
Analyze the user request and generate a sequence of Playwright actions.

Available actions:
- navigate: Go to a URL
- click: Click an element (use CSS selectors, text selectors like 'text=Button', or role selectors)
- fill: Fill an input field
- screenshot: Take a screenshot
- get_text: Get text from an element
- get_all_text: Get text from multiple elements

Return JSON array format:
[
  {
    "tool": "navigate|click|fill|screenshot|get_text|get_all_text",
    "parameters": {
      "url": "for navigate",
      "selector": "CSS selector or text=Button or [role=button]",
      "text": "for fill actions"
    },
    "description": "what this step accomplishes"
  }
]

For selectors, prefer:
- Text selectors: "text=Login" or "text=Submit"
- Role selectors: "[role='button']", "[role='link']"
- CSS selectors: "button.submit", "input[name='email']"
- Common patterns: "h1", "a", "button", "input[type='text']"

IMPORTANT: Always start with navigate action to the URL."""

            context = f"""
URL: {url}
User Request: {user_prompt}

Generate the sequence of Playwright actions needed."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "system",
                    "content": system_prompt
                }, {
                    "role": "user",
                    "content": context
                }],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2000)

            actions_text = response.choices[0].message.content
            data = json.loads(actions_text)
            
            # Handle both direct array and wrapped in "actions" key
            if isinstance(data, list):
                return data
            elif "actions" in data:
                return data["actions"]
            else:
                return await self.fallback_analysis(url, user_prompt)

        except Exception as e:
            print(f"OpenAI analysis failed: {e}")
            return await self.fallback_analysis(url, user_prompt)

    async def fallback_analysis(self, url, user_prompt):
        """Fallback analysis when OpenAI is not available"""
        prompt_lower = user_prompt.lower()
        actions = []

        # Always start with navigation
        actions.append({
            "tool": "navigate",
            "parameters": {
                "url": url
            },
            "description": f"Navigate to {url}"
        })

        # Parse common patterns
        if "click" in prompt_lower:
            if "button" in prompt_lower:
                actions.append({
                    "tool": "click",
                    "parameters": {"selector": "button"},
                    "description": "Click the first button"
                })
            else:
                actions.append({
                    "tool": "click",
                    "parameters": {"selector": "a"},
                    "description": "Click the first link"
                })

        if any(word in prompt_lower for word in ['type', 'fill', 'enter']):
            actions.append({
                "tool": "fill",
                "parameters": {
                    "selector": "input",
                    "text": "example text"
                },
                "description": "Fill text input"
            })

        if "screenshot" in prompt_lower:
            actions.append({
                "tool": "screenshot",
                "parameters": {},
                "description": "Take screenshot"
            })

        if any(word in prompt_lower for word in ['get', 'scrape', 'extract']):
            if "title" in prompt_lower:
                actions.append({
                    "tool": "get_text",
                    "parameters": {"selector": "h1"},
                    "description": "Get page title"
                })
            else:
                actions.append({
                    "tool": "get_all_text",
                    "parameters": {"selector": "a"},
                    "description": "Get all link texts"
                })

        return actions

    async def execute_automation_plan(self, actions):
        """Execute the generated automation actions"""
        results = []

        for action in actions:
            try:
                tool_name = action["tool"]
                parameters = action["parameters"]
                description = action["description"]

                print(f"🔧 {description}")

                result = await self.execute_action(tool_name, parameters)
                
                results.append({
                    "action": description,
                    "tool": tool_name,
                    "result": result,
                    "success": result.get("status") == "success"
                })

                await asyncio.sleep(0.5)

            except Exception as e:
                results.append({
                    "action": action.get("description", "Unknown"),
                    "tool": tool_name,
                    "result": {"error": str(e)},
                    "success": False
                })

        return results

    def generate_playwright_code(self, actions, url):
        """Generate executable Playwright Python code from actions"""
        
        code_lines = [
            "import asyncio",
            "from playwright.async_api import async_playwright",
            "",
            "async def automate():",
            "    async with async_playwright() as p:",
            "        browser = await p.chromium.launch(headless=False)",
            "        page = await browser.new_page()",
            "        ",
            "        try:"
        ]

        for action in actions:
            tool = action["tool"]
            params = action["parameters"]
            desc = action["description"]

            code_lines.append(f"            # {desc}")

            if tool == "navigate":
                code_lines.append(
                    f"            await page.goto('{params.get('url', url)}', wait_until='networkidle')")

            elif tool == "click":
                code_lines.append(
                    f"            await page.click('{params.get('selector', 'button')}')")

            elif tool == "fill":
                code_lines.append(
                    f"            await page.fill('{params.get('selector', 'input')}', '{params.get('text', '')}')")

            elif tool == "screenshot":
                code_lines.append(
                    f"            await page.screenshot(path='automation_screenshot.png')")

            elif tool == "get_text":
                code_lines.append(
                    f"            text = await page.inner_text('{params.get('selector', 'h1')}')")
                code_lines.append(
                    f"            print(f'Text: {{text}}')")

            elif tool == "get_all_text":
                code_lines.append(
                    f"            elements = await page.query_selector_all('{params.get('selector', 'a')}')")
                code_lines.append(
                    f"            for elem in elements:")
                code_lines.append(
                    f"                text = await elem.inner_text()")
                code_lines.append(
                    f"                print(f'- {{text}}')")

            code_lines.append("")

        code_lines.extend([
            "            print('✅ Automation completed!')",
            "            ",
            "        except Exception as e:",
            "            print(f'❌ Error: {e}')",
            "            ",
            "        finally:",
            "            await browser.close()",
            "",
            "if __name__ == '__main__':",
            "    asyncio.run(automate())"
        ])

        return "\n".join(code_lines)

    async def stop_browser(self):
        """Stop the browser"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("🛑 Browser stopped")


class MCPAutomationApp:
    """Main automation application"""

    def __init__(self):
        self.engine = None

    async def initialize(self, openai_key=None):
        """Initialize the automation engine"""
        self.engine = PlaywrightAutomationEngine(openai_key)
        return await self.engine.start_browser()

    async def process_automation_request(self, url, prompt, generate_code=True):
        """Process a complete automation request"""
        print(f"\n🎯 Processing: {prompt}")
        print(f"🌐 Target URL: {url}")

        # Step 1: Generate actions using OpenAI
        print("🤖 Analyzing with OpenAI...")
        actions = await self.engine.analyze_and_generate_actions(url, prompt)

        print(f"📋 Generated {len(actions)} actions:")
        for i, action in enumerate(actions, 1):
            print(f"  {i}. {action['description']}")

        # Step 2: Execute the automation
        print("\n⚡ Executing automation...")
        results = await self.engine.execute_automation_plan(actions)

        # Step 3: Generate code
        code = ""
        filename = ""
        if generate_code:
            print("\n💻 Generating Playwright code...")
            code = self.engine.generate_playwright_code(actions, url)
            filename = f"automation_{int(time.time())}.py"
            with open(filename, 'w') as f:
                f.write(code)
            print(f"📁 Code saved: {filename}")

        return {
            "success": any(r["success"] for r in results),
            "actions": actions,
            "results": results,
            "generated_code": code,
            "code_file": filename
        }

    async def cleanup(self):
        """Cleanup resources"""
        if self.engine:
            await self.engine.stop_browser()


async def main():
    """CLI interface"""
    app = MCPAutomationApp()

    print("🚀 Playwright Real Automation System")
    print("=" * 50)

    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        openai_key = input("Enter OpenAI API key (or press Enter to skip): ").strip()
        if openai_key:
            os.environ['OPENAI_API_KEY'] = openai_key

    if not await app.initialize(openai_key):
        print("❌ Failed to initialize browser")
        return

    print("\n✅ System ready!")
    print("Examples:")
    print("• URL: https://example.com, Prompt: get the page title")
    print("• URL: https://news.ycombinator.com, Prompt: get top 5 story titles")
    print("Type 'quit' to exit\n")

    try:
        while True:
            url = input("🔗 Enter URL: ").strip()
            if url.lower() == 'quit':
                break

            prompt = input("💡 Enter prompt: ").strip()
            if prompt.lower() == 'quit':
                break

            result = await app.process_automation_request(url, prompt)

            if result["success"]:
                print("\n✅ Automation completed!")
                print(f"📊 Executed {len(result['actions'])} actions")
                if result["code_file"]:
                    print(f"💾 Code: {result['code_file']}")
            else:
                print("❌ Automation failed")

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    finally:
        await app.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
