import os
from typing import Optional, Dict, Any
from browser_use import Agent, Browser, BrowserProfile, ChatOpenAI
from .playwright_code_generator import PlaywrightCodeGenerator

class BrowserAutomationEngine:
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        headless: bool = False,
        verbose: bool = False,
        generate_code: bool = False
    ):
        self.api_key = api_key
        self.model = model
        self.headless = headless
        self.verbose = verbose
        self.generate_code = generate_code

        self.llm = self._initialize_llm()
        self.browser = self._initialize_browser()
        self.code_generator = PlaywrightCodeGenerator(verbose=verbose) if generate_code else None

    def _initialize_llm(self) -> ChatOpenAI:
        # the newest OpenAI model is "gpt-4o-mini" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key
        )

        if self.verbose:
            print(f"✓ Initialized LLM: {self.model}")

        return llm

    def _initialize_browser(self) -> Browser:
        import shutil

        chromium_path = os.getenv("CHROMIUM_PATH")
        if not chromium_path:
            chromium_path = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("chrome")

        if chromium_path:
            if self.verbose:
                print(f"✓ Using Chromium at: {chromium_path}")
            profile = BrowserProfile(
                headless=self.headless,
                executable_path=chromium_path
            )
        else:
            profile = BrowserProfile(
                headless=self.headless
            )

        browser = Browser(
            browser_profile=profile
        )

        if self.verbose:
            print(f"✓ Initialized Browser (headless={self.headless})")

        return browser

    async def run_task(self, task: str, output_file: Optional[str] = None) -> Dict[str, Any]:
        if self.verbose:
            print(f"\n🎯 Creating agent for task: {task}\n")

        task_instruction = (
            f"{task}\n\n"
            "IMPORTANT INSTRUCTIONS:\n"
            "1. You may do necessary auxiliary actions (wait for page loads, dismiss popups, etc.) to complete those steps.\n"
            "2. After completing the user's specified steps, STOP IMMEDIATELY.\n"
            "4. Do NOT continue to what seems like the 'next logical step' or try to complete an entire workflow.\n"
            "5. When you finish the last step specified by the user, call 'done' immediately."
        )

        task = task_instruction

        agent = Agent(
            task=task,
            llm=self.llm,
            browser=self.browser,
        )

        if self.verbose:
            print("🔄 Agent created, starting execution...\n")

        history = await agent.run()

        if self.verbose:
            print(f"\n📊 Task execution completed")
            print(f"   Steps taken: {len(history.history) if hasattr(history, 'history') else 'N/A'}")

        result = self._extract_result(history)

        response = {
            'result': result,
            'history': history,
            'generated_code': None,
            'code_file': None
        }

        if self.generate_code and self.code_generator:
            if self.verbose:
                print("\n📝 Generating Playwright code from actions...")

            self.code_generator.parse_history(history)
            generated_code = self.code_generator.generate_code()
            response['generated_code'] = generated_code

            if output_file:
                self.code_generator.save_code(output_file)
                response['code_file'] = output_file
                if self.verbose:
                    print(f"✓ Code saved to: {output_file}")

        return response

    def _extract_result(self, history) -> Optional[str]:
        if not history:
            return None

        if hasattr(history, 'final_result'):
            return str(history.final_result())

        if hasattr(history, 'history') and history.history:
            last_action = history.history[-1]
            if hasattr(last_action, 'result'):
                return str(last_action.result)

        return "Task completed successfully"
