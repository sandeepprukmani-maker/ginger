import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from browser_use import Agent, Browser
from langchain_openai import ChatOpenAI
import os

logger = logging.getLogger(__name__)

class WrappedChatOpenAI:
    """Wrapper for ChatOpenAI to work with browser-use library
    
    browser-use v0.3.3+ tries to monkey-patch ainvoke, which fails with Pydantic v2.
    This wrapper exposes the required methods without Pydantic validation issues.
    """
    def __init__(self, model_name="gpt-4o", temperature=0.1, api_key=None):
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
            model_kwargs={}
        )
        self.model_name = model_name
        self.model = model_name
        self.provider = "openai"
    
    async def ainvoke(self, *args, **kwargs):
        """Async invoke method that browser-use expects"""
        return await self.llm.ainvoke(*args, **kwargs)
    
    def invoke(self, *args, **kwargs):
        """Sync invoke method"""
        return self.llm.invoke(*args, **kwargs)

class BrowserUseService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.browser = None
        self.context = None
        self.llm = None
        
    async def initialize(self):
        """Initialize the browser-use service"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            
            # Use wrapper class to avoid Pydantic v2 compatibility issues with browser-use
            self.llm = WrappedChatOpenAI(
                model_name="gpt-4o-mini",
                api_key=api_key,
                temperature=0.1
            )
            
            logger.info("Browser-use service initialized with wrapped ChatOpenAI")
            
            browser_config = self.config.get('browser', {})
            headless = browser_config.get('headless', True)
            
            logger.info(f"Initializing browser in {'headless' if headless else 'headful'} mode")
            
            # Configure browser with extended timeout for Windows compatibility
            browser_launch_timeout = browser_config.get('browser_launch_timeout', 120)
            
            self.browser = Browser(
                headless=headless,
                disable_security=False,
                config={
                    'new_context_config': {
                        'viewport': {
                            'width': browser_config.get('viewport_width', 1920),
                            'height': browser_config.get('viewport_height', 1080)
                        }
                    }
                }
            )
            
            logger.info(f"Browser-use service initialized successfully with {browser_launch_timeout}s timeout")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing browser-use service: {e}")
            return False
    
    async def execute_task(self, instruction: str) -> Dict[str, Any]:
        """Execute a natural language instruction using browser-use"""
        try:
            if not self.llm:
                await self.initialize()
            
            logger.info(f"Executing instruction: {instruction}")
            
            task_with_constraint = f"{instruction}\n\nIMPORTANT: Complete ONLY the instruction given above and then STOP immediately. Do not perform any additional actions like extracting data, scrolling further, or navigating to other pages unless explicitly requested in the instruction. You can make any auxiliary decisions needed to complete the instruction itself (like handling popups, accepting cookies, etc.), but do not go beyond what was asked."
            
            agent = Agent(
                task=task_with_constraint,
                llm=self.llm,
                browser=self.browser,
                max_actions_per_step=10
            )
            
            start_time = time.time()
            # Run with increased timeout for Windows compatibility
            result = await asyncio.wait_for(
                agent.run(max_steps=15),
                timeout=180.0  # 3 minute timeout
            )
            execution_time = time.time() - start_time
            
            logger.info(f"Instruction completed in {execution_time:.2f}s")
            
            return {
                'success': True,
                'result': result,
                'execution_time': execution_time,
                'error': None
            }
            
        except asyncio.TimeoutError:
            logger.error("Task execution timed out after 3 minutes")
            return {
                'success': False,
                'result': None,
                'execution_time': 0,
                'error': 'Task execution timed out. The browser may be slow to start on your system. Please ensure Playwright browsers are installed.'
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error executing task with browser-use: {error_msg}")
            
            # Provide helpful error messages for common issues
            if 'timed out' in error_msg.lower() or 'timeout' in error_msg.lower():
                error_msg = f"Browser launch timeout. On Windows, you may need to: 1) Run 'playwright install chromium' to install browsers, 2) Ensure no antivirus is blocking Playwright. Original error: {error_msg}"
            
            return {
                'success': False,
                'result': None,
                'execution_time': 0,
                'error': error_msg
            }
    
    async def execute_single_step(self, action_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action step for healing purposes"""
        try:
            if not self.browser:
                await self.initialize()
            
            logger.info(f"Executing single step - Action: {action_type}, Parameters: {parameters}")
            
            url = parameters.get('url')
            if url:
                task = f"Go to {url}"
                if action_type == 'click':
                    element_desc = parameters.get('element_description', '')
                    task += f" and click on {element_desc}"
                elif action_type == 'fill':
                    element_desc = parameters.get('element_description', '')
                    value = parameters.get('value', '')
                    task += f" and fill {element_desc} with {value}"
                elif action_type == 'select':
                    element_desc = parameters.get('element_description', '')
                    value = parameters.get('value', '')
                    task += f" and select {value} in {element_desc}"
            else:
                if action_type == 'click':
                    element_desc = parameters.get('element_description', '')
                    task = f"Click on {element_desc}"
                elif action_type == 'fill':
                    element_desc = parameters.get('element_description', '')
                    value = parameters.get('value', '')
                    task = f"Fill {element_desc} with {value}"
                elif action_type == 'select':
                    element_desc = parameters.get('element_description', '')
                    value = parameters.get('value', '')
                    task = f"Select {value} in {element_desc}"
                else:
                    task = parameters.get('task', action_type)
            
            agent = Agent(
                task=task,
                llm=self.llm,
                browser=self.browser
            )
            
            start_time = time.time()
            result = await agent.run()
            execution_time = time.time() - start_time
            
            logger.info(f"Single step completed successfully in {execution_time:.2f}s")
            
            return {
                'success': True,
                'result': result,
                'execution_time': execution_time,
                'healed_locator': self._extract_locator_from_result(result),
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error executing single step: {e}")
            return {
                'success': False,
                'result': None,
                'execution_time': 0,
                'healed_locator': None,
                'error': str(e)
            }
    
    def _extract_locator_from_result(self, result: Any) -> Optional[Dict[str, Any]]:
        """Extract locator information from browser-use result"""
        try:
            if hasattr(result, 'history') and result.history:
                last_action = result.history[-1]
                if hasattr(last_action, 'action'):
                    action_data = last_action.action
                    if hasattr(action_data, 'selector') or hasattr(action_data, 'xpath'):
                        return {
                            'type': 'css' if hasattr(action_data, 'selector') else 'xpath',
                            'value': getattr(action_data, 'selector', None) or getattr(action_data, 'xpath', None)
                        }
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not extract locator from result: {e}")
            return None
    
    async def get_page_context(self) -> Dict[str, Any]:
        """Get current page context information"""
        try:
            return {'url': None, 'title': None}
        except Exception as e:
            logger.error(f"Error getting page context: {e}")
            return {'url': None, 'title': None}
    
    async def close(self):
        """Close the browser and cleanup resources"""
        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
                logger.info("Browser-use service closed")
        except Exception as e:
            logger.error(f"Error closing browser-use service: {e}")
