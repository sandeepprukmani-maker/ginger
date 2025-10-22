import asyncio
import os
from typing import Optional, Dict, Any, List, Callable
from playwright.async_api import Page, Browser, Locator, async_playwright
from browser_use import Agent, Browser as BrowserUseWrapper, ChatOpenAI


class SelfHealingExecutor:
    """
    Executes Playwright code with AI-powered self-healing capabilities.
    When a locator fails, browser-use AI intervenes in the same session to fix it.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        verbose: bool = False
    ):
        self.api_key = api_key
        self.model = model
        self.verbose = verbose
        self.llm = None
        self.healed_locators: Dict[str, str] = {}
        self.healing_attempts = 0
        self.max_healing_attempts = 3
    
    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize OpenAI LLM for browser-use"""
        if not self.llm:
            self.llm = ChatOpenAI(
                model=self.model,
                api_key=self.api_key
            )
            if self.verbose:
                print(f"✓ Initialized healing LLM: {self.model}")
        return self.llm
    
    async def heal_locator(
        self,
        page: Page,
        failed_locator: str,
        action_description: str,
        element_description: str = "",
        playwright_context = None
    ) -> Optional[str]:
        """
        Use browser-use AI to find and fix a broken locator in the same session.
        
        Args:
            page: The Playwright page object
            failed_locator: The locator that failed
            action_description: What action we're trying to perform (e.g., "click login button")
            element_description: Additional context about the element
            playwright_context: The Playwright browser context to reuse
        
        Returns:
            New working locator string, or None if healing failed
        """
        if self.healing_attempts >= self.max_healing_attempts:
            if self.verbose:
                print(f"⚠️  Max healing attempts ({self.max_healing_attempts}) reached")
            return None
        
        self.healing_attempts += 1
        
        if self.verbose:
            print(f"\n🔧 Healing attempt {self.healing_attempts}/{self.max_healing_attempts}")
            print(f"   Failed locator: {failed_locator}")
            print(f"   Action: {action_description}")
        
        try:
            llm = self._initialize_llm()
            
            current_url = page.url
            page_title = await page.title()
            
            task = f"""On this page ({current_url}), locate the element for: {action_description}.

The previous locator failed: {failed_locator}
Element description: {element_description}

IMPORTANT: After finding the correct element:
1. Click or interact with it to confirm it's the right one
2. Report back its exact attributes: text content, role, id, class, aria-label, placeholder, or any other identifying attributes
3. Describe its location on the page for verification

Your response should include the element's attributes in detail."""
            
            if self.verbose:
                print(f"   🤖 AI analyzing page to find element...")
            
            cdp_url = await self._get_cdp_url(page)
            
            if not cdp_url:
                if self.verbose:
                    print(f"   ⚠️  Could not connect to existing browser session, fallback to heuristics")
                return await self._extract_locator_from_healing(page, action_description, element_description)
            
            if self.verbose:
                print(f"   🔗 Connecting to browser session: {cdp_url}")
            
            browser_wrapper = BrowserUseWrapper(
                browser_session={'cdp_url': cdp_url}
            )
            
            agent = Agent(
                task=task,
                llm=llm,
                browser=browser_wrapper,
            )
            
            result = await agent.run()
            
            if self.verbose:
                print(f"   🤖 AI task result: {str(result)[:100] if result else 'None'}...")
            
            history = agent.history if hasattr(agent, 'history') else None
            
            if not history:
                if self.verbose:
                    print(f"   ⚠️  No history found on agent object")
                return await self._extract_locator_from_healing(page, action_description, element_description)
            
            if self.verbose:
                print(f"   📋 Analyzing agent history with {len(history.model_actions) if hasattr(history, 'model_actions') else 0} actions")
            
            new_locator = await self._extract_locator_from_agent_history(
                page=page,
                history=history,
                action_desc=action_description,
                element_desc=element_description
            )
            
            if new_locator:
                self.healed_locators[failed_locator] = new_locator
                if self.verbose:
                    print(f"   ✅ Healing successful! New locator: {new_locator}")
                return new_locator
            else:
                if self.verbose:
                    print(f"   ⚠️  Could not extract locator from AI, trying heuristics...")
                new_locator = await self._extract_locator_from_healing(page, action_description, element_description)
                if new_locator:
                    self.healed_locators[failed_locator] = new_locator
                    if self.verbose:
                        print(f"   ✅ Heuristic healing successful! New locator: {new_locator}")
                    return new_locator
                
                if self.verbose:
                    print(f"   ❌ Healing failed - could not determine new locator")
                return None
                
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Healing error: {str(e)}")
                import traceback
                traceback.print_exc()
            return None
    
    async def _get_cdp_url(self, page: Page) -> Optional[str]:
        """
        Get CDP URL from the current Playwright browser session.
        Uses multiple strategies to ensure compatibility.
        """
        try:
            browser = page.context.browser
            
            if hasattr(browser, '_impl_obj'):
                impl_obj = browser._impl_obj
                
                if hasattr(impl_obj, '_connection') and hasattr(impl_obj._connection, 'url'):
                    return impl_obj._connection.url
                
                if hasattr(impl_obj, '_transport') and hasattr(impl_obj._transport, 'url'):
                    return impl_obj._transport.url
            
            if hasattr(browser, '_cdp_url'):
                return browser._cdp_url
            
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Could not extract CDP URL: {str(e)}")
        
        return None
    
    async def _extract_locator_from_agent_history(
        self,
        page: Page,
        history,
        action_desc: str,
        element_desc: str
    ) -> Optional[str]:
        """
        Extract a working locator from browser-use agent's action history.
        This parses what the AI actually found and interacted with.
        """
        if not history:
            if self.verbose:
                print(f"   ⚠️  History object is None")
            return None
        
        try:
            if hasattr(history, 'model_actions'):
                try:
                    actions = history.model_actions()
                    if self.verbose:
                        print(f"   📋 Found {len(actions) if actions else 0} model actions in history")
                except Exception as e:
                    if self.verbose:
                        print(f"   ⚠️  Could not call model_actions(): {str(e)}")
                    actions = []
                
                for i, action in enumerate(reversed(actions)):
                    if self.verbose:
                        print(f"   🔍 Analyzing action {len(actions) - i}: {type(action)}")
                    
                    if hasattr(action, '__dict__'):
                        action_dict = action.__dict__
                    elif isinstance(action, dict):
                        action_dict = action
                    else:
                        continue
                    
                    action_type = action_dict.get('action', {})
                    
                    if isinstance(action_type, dict):
                        if 'click_element' in action_type:
                            element = action_type['click_element'].get('element', {})
                            if self.verbose:
                                print(f"   ✓ Found click_element action with element: {element}")
                            locator = await self._build_locator_from_element(page, element)
                            if locator:
                                return locator
                        
                        if 'input_text' in action_type:
                            element = action_type['input_text'].get('element', {})
                            if self.verbose:
                                print(f"   ✓ Found input_text action with element: {element}")
                            locator = await self._build_locator_from_element(page, element)
                            if locator:
                                return locator
            else:
                if self.verbose:
                    print(f"   ⚠️  History has no model_actions attribute")
            
            if hasattr(history, 'history') and history.history:
                if self.verbose:
                    print(f"   🔍 Checking history.history list with {len(history.history)} items")
                for item in reversed(history.history):
                    if hasattr(item, 'result') and hasattr(item.result, 'extracted_content'):
                        if self.verbose:
                            print(f"   ✓ Found extracted content in history item")
                        element_data = item.result.extracted_content
                        if isinstance(element_data, dict) and 'attributes' in element_data:
                            locator = await self._build_locator_from_element(page, element_data)
                            if locator:
                                return locator
            
        except Exception as e:
            if self.verbose:
                print(f"   ❌ Error extracting from agent history: {str(e)}")
                import traceback
                traceback.print_exc()
        
        if self.verbose:
            print(f"   ⚠️  Could not extract locator from agent history - falling back to heuristics")
        return None
    
    async def _build_locator_from_element(self, page: Page, element: Dict) -> Optional[str]:
        """Build a Playwright locator string from element attributes found by browser-use"""
        if not element:
            return None
        
        text = element.get('text', '').strip()
        role = element.get('role', '').strip()
        attributes = element.get('attributes', {}) or {}
        
        strategies_to_try = []
        
        if attributes.get('data-testid'):
            strategies_to_try.append(f'page.get_by_test_id("{attributes["data-testid"]}")')
        
        if attributes.get('id'):
            strategies_to_try.append(f'page.locator("#{attributes["id"]}")')
        
        if attributes.get('aria-label'):
            strategies_to_try.append(f'page.get_by_label("{attributes["aria-label"]}")')
        
        if role and text:
            strategies_to_try.append(f'page.get_by_role("{role}", name="{text}")')
        elif role:
            strategies_to_try.append(f'page.get_by_role("{role}")')
        
        if text:
            strategies_to_try.append(f'page.get_by_text("{text}")')
        
        if attributes.get('placeholder'):
            strategies_to_try.append(f'page.get_by_placeholder("{attributes["placeholder"]}")')
        
        for strategy in strategies_to_try:
            try:
                locator = eval(strategy)
                count = await locator.count()
                if count > 0:
                    await locator.first.wait_for(timeout=2000, state="visible")
                    return strategy if count == 1 else f'{strategy}.first'
            except Exception:
                continue
        
        return None
    
    async def _extract_locator_from_healing(
        self,
        page: Page,
        action_desc: str,
        element_desc: str
    ) -> Optional[str]:
        """
        Try to intelligently find a working locator based on common patterns.
        This uses smart heuristics to locate elements after AI exploration.
        """
        desc_lower = (action_desc + " " + element_desc).lower()
        
        common_selectors = []
        
        if "login" in desc_lower or "sign in" in desc_lower:
            common_selectors.extend([
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                '[type="submit"]',
                'button[type="submit"]',
            ])
        
        if "search" in desc_lower:
            common_selectors.extend([
                'input[type="search"]',
                'input[name="q"]',
                'input[placeholder*="search" i]',
                '[aria-label*="search" i]',
            ])
        
        if "submit" in desc_lower or "button" in desc_lower:
            common_selectors.extend([
                'button[type="submit"]',
                'input[type="submit"]',
                'button',
            ])
        
        if "email" in desc_lower:
            common_selectors.extend([
                'input[type="email"]',
                'input[name="email"]',
                'input[autocomplete="email"]',
            ])
        
        if "password" in desc_lower:
            common_selectors.extend([
                'input[type="password"]',
                'input[name="password"]',
                'input[autocomplete="current-password"]',
            ])
        
        for selector in common_selectors:
            try:
                locator = page.locator(selector)
                count = await locator.count()
                if count > 0:
                    await locator.first.wait_for(timeout=2000, state="visible")
                    if self.verbose:
                        print(f"   🔍 Found working selector: {selector}")
                    return f'page.locator("{selector}").first'
            except Exception:
                continue
        
        text_elements = []
        if "click" in desc_lower:
            words = element_desc.split()
            for word in words:
                if len(word) > 3:
                    text_elements.append(word)
        
        for text in text_elements[:3]:
            try:
                selector = f'text={text}'
                locator = page.locator(selector)
                count = await locator.count()
                if count > 0:
                    if self.verbose:
                        print(f"   🔍 Found working text selector: {selector}")
                    return f'page.locator("{selector}").first'
            except Exception:
                continue
        
        return None
    
    async def safe_locator(
        self,
        page: Page,
        locator_str: str,
        action_description: str = "",
        element_description: str = "",
        timeout: int = 10000
    ) -> Optional[Locator]:
        """
        Get a locator with automatic self-healing if it fails.
        
        Args:
            page: Playwright page object
            locator_str: Locator string (e.g., 'page.get_by_text("Login")')
            action_description: Description of the action being performed
            element_description: Description of the element
            timeout: Timeout in milliseconds
        
        Returns:
            Working Locator object, or None if all attempts fail
        """
        if locator_str in self.healed_locators:
            locator_str = self.healed_locators[locator_str]
            if self.verbose:
                print(f"   📝 Using previously healed locator: {locator_str}")
        
        try:
            locator = eval(locator_str)
            await locator.wait_for(timeout=timeout)
            return locator
        except Exception as e:
            if self.verbose:
                print(f"   ⚠️  Locator failed: {locator_str}")
                print(f"      Error: {str(e)[:100]}")
            
            healed_locator_str = await self.heal_locator(
                page=page,
                failed_locator=locator_str,
                action_description=action_description,
                element_description=element_description
            )
            
            if healed_locator_str:
                try:
                    healed_locator = eval(healed_locator_str)
                    await healed_locator.wait_for(timeout=timeout)
                    return healed_locator
                except Exception as heal_error:
                    if self.verbose:
                        print(f"   ❌ Healed locator also failed: {str(heal_error)[:100]}")
            
            return None
    
    async def execute_with_healing(
        self,
        automation_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute an automation function with self-healing support.
        
        Args:
            automation_func: Async function to execute
            *args, **kwargs: Arguments to pass to the function
        
        Returns:
            Result of the automation function
        """
        self.healing_attempts = 0
        self.healed_locators.clear()
        
        if self.verbose:
            print("\n🚀 Starting execution with self-healing enabled")
            print(f"   Max healing attempts per locator: {self.max_healing_attempts}")
        
        try:
            result = await automation_func(*args, **kwargs)
            
            if self.verbose:
                print("\n✅ Execution completed successfully!")
                if self.healed_locators:
                    print(f"   Healed {len(self.healed_locators)} locator(s) during execution")
            
            return result
        except Exception as e:
            if self.verbose:
                print(f"\n❌ Execution failed: {str(e)}")
            raise


class HealingContext:
    """Context manager for self-healing Playwright automation"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        verbose: bool = False
    ):
        self.executor = SelfHealingExecutor(
            api_key=api_key,
            model=model,
            verbose=verbose
        )
        self.page: Optional[Page] = None
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    async def __aenter__(self):
        """Set up Playwright browser with healing support"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        context = await self.browser.new_context()
        self.page = await context.new_page()
        
        setattr(self.page, 'healing_locator', self._create_healing_locator_method())
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    def _create_healing_locator_method(self):
        """Create a healing locator method bound to the page"""
        async def healing_locator(
            locator_str: str,
            action_desc: str = "",
            element_desc: str = ""
        ) -> Optional[Locator]:
            return await self.executor.safe_locator(
                page=self.page,
                locator_str=locator_str,
                action_description=action_desc,
                element_description=element_desc
            )
        
        return healing_locator
