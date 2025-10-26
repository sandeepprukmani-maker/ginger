"""
Browser-Use Engine
AI-powered browser automation using browser-use library

Thread Safety Notes:
- This engine creates a fresh Browser instance per request
- Each request runs on its own event loop to ensure thread safety
- Browser instances are NOT cached to prevent asyncio loop affinity issues
- Memory is cleaned up after each request via finally block
"""
import os
import asyncio
import configparser
import logging
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv
from browser_use import Agent, Browser
from browser_use.llm import ChatOpenAI
from auth.oauth_handler import get_oauth_token_with_retry

# Import ChatBrowserUse for optimized browser automation (3-5x faster)
try:
    from browser_use.llm import ChatBrowserUse
    CHAT_BROWSER_USE_AVAILABLE = True
except ImportError:
    CHAT_BROWSER_USE_AVAILABLE = False

# Load .env file from project root with explicit path
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)

logger = logging.getLogger(__name__)


class BrowserUseEngine:
    """
    Browser automation engine using browser-use library
    
    Thread Safety: This engine is designed for Flask's multi-threaded environment.
    Each request creates its own event loop and browser instance, which are
    properly cleaned up after execution.
    """
    
    def __init__(self, headless: bool = False):
        """
        Initialize Browser-Use Engine
        
        Args:
            headless: Run browser in headless mode
        """
        self.headless = headless
        
        config = configparser.ConfigParser()
        config.read('config/config.ini')
        
        gateway_base_url = os.environ.get('GW_BASE_URL')
        if not gateway_base_url:
            raise ValueError("GW_BASE_URL must be set as environment variable to connect to the gateway endpoint.")
        
        try:
            oauth_token = get_oauth_token_with_retry(max_retries=3)
        except Exception as e:
            raise ValueError(f"Failed to obtain OAuth token: {str(e)}. Please check your OAuth configuration.")
        
        model = config.get('openai', 'model', fallback='gpt-4.1-2025-04-14-eastus-dz')
        timeout = int(config.get('openai', 'timeout', fallback='180'))
        
        self.max_steps = int(config.get('agent', 'max_steps', fallback='25'))
        
        # Browser performance settings - using reliable defaults
        self.minimum_wait_page_load_time = float(config.get('browser_performance', 'minimum_wait_page_load_time', fallback='1.0'))
        self.wait_for_network_idle_page_load_time = float(config.get('browser_performance', 'wait_for_network_idle_page_load_time', fallback='1.5'))
        self.wait_between_actions = float(config.get('browser_performance', 'wait_between_actions', fallback='1.0'))
        
        # Use ChatBrowserUse model if enabled (3-5x faster for browser automation)
        use_chat_browser_use = config.getboolean('openai', 'use_chat_browser_use', fallback=False)
        
        if use_chat_browser_use and CHAT_BROWSER_USE_AVAILABLE:
            logger.info("🚀 Using ChatBrowserUse optimized model (3-5x faster)")
            self.llm = ChatBrowserUse()
        else:
            if use_chat_browser_use and not CHAT_BROWSER_USE_AVAILABLE:
                logger.warning("⚠️  ChatBrowserUse not available, falling back to standard OpenAI model")
            logger.info(f"Using gateway model: {model} via {gateway_base_url}")
            self.llm = ChatOpenAI(
                model=model,
                base_url=gateway_base_url,
                api_key=oauth_token,
                default_headers={
                    "Authorization": f"Bearer {oauth_token}"
                },
                timeout=timeout
            )
    
    async def execute_instruction(self, instruction: str, progress_callback=None) -> Dict[str, Any]:
        """
        Execute a natural language instruction
        
        Args:
            instruction: User's natural language instruction
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with execution results and steps taken
        """
        # Input validation
        if not instruction or not instruction.strip():
            logger.error("❌ Empty instruction provided")
            return {
                "success": False,
                "error": "Instruction cannot be empty",
                "error_type": "ValidationError",
                "steps": [],
                "iterations": 0
            }
        
        instruction = instruction.strip()
        browser = None
        try:
            logger.info("🤖 Initializing Browser-Use Agent")
            logger.info(f"📋 Task: {instruction}")
            logger.info(f"🔢 Max steps: {self.max_steps}")
            
            # Send initialization progress
            if progress_callback:
                progress_callback('init', {'message': 'Initializing browser automation agent...', 'instruction': instruction})
            
            # System instructions optimized for efficiency while maintaining safety
            # Fix from https://github.com/browser-use/browser-use/pull/235 to prevent going beyond task
            system_instructions = f"""
YOUR ULTIMATE TASK: "{instruction}"

⚠️ CRITICAL - GOAL-BASED EXECUTION ⚠️
Identify the GOAL of the task, then stop immediately once that goal is achieved.
You MAY make auxiliary decisions to achieve the goal (wait for pages, handle popups, retry actions).
You MUST NOT perform actions beyond achieving the stated goal.

EXECUTION APPROACH:
1. Parse the task to identify the GOAL (the end state to achieve)
2. Make necessary auxiliary decisions to reach that goal:
   ✅ Wait for pages to load
   ✅ Handle popups or dialog boxes that block progress
   ✅ Retry failed actions (element not found, slow page load)
   ✅ Navigate through necessary intermediate steps
3. Once the GOAL is achieved → IMMEDIATELY use done()
4. Do NOT perform additional "helpful" actions beyond the goal

EXAMPLES OF GOAL-BASED EXECUTION:

Task: "open linkedin.com click join now"
→ GOAL: Click the "join now" button on LinkedIn
→ ✅ Correct: Navigate to linkedin.com → Wait for page → Click "join now" → Verify click succeeded → done()
→ ❌ Wrong: Navigate → Click "join now" → Fill email → Fill password (GOAL was already achieved after clicking!)

Task: "go to amazon.com and search for laptop"
→ GOAL: Execute a search for "laptop" on Amazon
→ ✅ Correct: Navigate → Wait for page → Type "laptop" in search → Click search button → done()
→ ❌ Wrong: Navigate → Search → Click first result → View product details (GOAL was achieved after search!)

Task: "fill in the email field with test@example.com and submit the form"
→ GOAL: Submit form with email filled
→ ✅ Correct: Fill email → Click submit → Wait for submission → done()
→ ❌ Wrong: Stop after filling email (GOAL requires submitting!)

CRITICAL: STOP IMMEDIATELY AFTER GOAL IS ACHIEVED
→ Do NOT fill forms unless required to achieve the goal
→ Do NOT click buttons unless required to achieve the goal
→ Do NOT navigate to pages unless required to achieve the goal
→ Ask yourself: "Have I achieved the stated goal?" If yes → done()

AUXILIARY DECISIONS (ALLOWED):
- Waiting for pages/elements to load
- Handling popups that block the goal
- Retrying actions that fail due to timing
- Navigating to intermediate pages to reach the goal
- Verifying that actions succeeded

PAGE LOADING & ERRORS:
- If element not found → page still loading → wait 2s → retry with fresh page state
- Verify critical actions succeeded before done()
- If action fails after retries → report failure and use done()

SECURITY:
- Never navigate to unintended domains
- Confirm sensitive actions before executing
            """
            
            logger.info("⚙️  Configuring agent with literal execution instructions")
            
            # Send browser initialization progress
            if progress_callback:
                progress_callback('browser_init', {'message': f'Starting browser (headless={self.headless})...'})
            
            # Create browser instance with optimized performance settings
            # Browser accepts **data kwargs, type stubs might not reflect all parameters
            browser = Browser(  # type: ignore
                headless=self.headless,
                disable_security=False,  # Keep security enabled for production
                minimum_wait_page_load_time=self.minimum_wait_page_load_time,
                wait_for_network_idle_page_load_time=self.wait_for_network_idle_page_load_time,
                wait_between_actions=self.wait_between_actions
            )
            logger.info(f"🌐 Browser initialized (headless={self.headless})")
            
            # Send agent creation progress
            if progress_callback:
                progress_callback('agent_create', {'message': 'Creating AI agent...'})
            
            agent = Agent(
                task=instruction,
                llm=self.llm,
                browser=browser,  # Pass browser for proper popup/multi-window handling
                extend_system_message=system_instructions.strip(),
            )
            
            logger.info("▶️  Starting agent execution...")
            
            # Send execution start progress
            if progress_callback:
                progress_callback('execution_start', {'message': 'Agent is now executing automation steps...'})
            
            history = await agent.run(max_steps=self.max_steps)
            logger.info(f"⏹️  Agent execution completed")
            
            logger.info("📊 Processing execution history...")
            steps = []
            for i, item in enumerate(history.history):
                step_num = i + 1
                action = str(getattr(item, 'model_output', ''))
                state = str(getattr(item, 'state', ''))
                
                logger.info(f"  Step {step_num}: {action[:100]}...")
                
                step = {
                    "tool": "browser_use_action",
                    "arguments": {"action": action},
                    "success": True,
                    "result": {
                        "state": state,
                        "step_number": step_num
                    }
                }
                steps.append(step)
                
                # Send step progress update
                if progress_callback:
                    progress_callback('step', {
                        'step_number': step_num,
                        'action': action[:150],
                        'total_steps': len(history.history)
                    })
            
            final_result = history.final_result() if hasattr(history, 'final_result') else None
            
            # Generate Playwright code from automation (optional feature)
            playwright_code = None
            try:
                from app.engines.browser_use.playwright_code_generator import generate_playwright_code_from_history
                playwright_code = generate_playwright_code_from_history(
                    history,
                    task_description=instruction
                )
                logger.info("🎭 Playwright code generated successfully")
            except Exception as e:
                logger.debug(f"Could not generate Playwright code: {e}")
            
            # Check if task actually succeeded - if 0 steps executed, it likely failed
            if len(steps) == 0:
                logger.error(f"❌ Task failed - no steps were executed successfully")
                return {
                    "success": False,
                    "error": "Browser automation failed to execute any steps. This usually means the browser could not launch.",
                    "message": "No steps executed - browser may have failed to start",
                    "steps": [],
                    "iterations": 0,
                    "final_result": None
                }
            
            logger.info(f"✅ Task completed successfully!")
            logger.info(f"📈 Total steps executed: {len(steps)}")
            if final_result:
                logger.info(f"🎯 Final result: {str(final_result)[:200]}")
            
            result = {
                "success": True,
                "message": f"Task completed successfully. Executed {len(steps)} steps.",
                "steps": steps,
                "iterations": len(steps),
                "final_result": final_result
            }
            
            # Add Playwright code if generated
            if playwright_code:
                result["playwright_code"] = playwright_code
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Browser-Use execution failed: {error_msg}", exc_info=True)
            
            # Provide helpful error context
            error_context = {
                "success": False,
                "error": error_msg,
                "error_type": type(e).__name__,
                "steps": [],
                "iterations": 0
            }
            
            # Add helpful hints based on error type
            if "timeout" in error_msg.lower():
                error_context["hint"] = "The operation timed out. Consider increasing the timeout or simplifying the task."
            elif "api" in error_msg.lower() or "key" in error_msg.lower():
                error_context["hint"] = "API key error. Please check your OPENAI_API_KEY environment variable."
            elif "playwright" in error_msg.lower() or "browser" in error_msg.lower():
                error_context["hint"] = "Browser initialization failed. Ensure Playwright is properly installed."
            
            return error_context
        finally:
            # Clean up browser resources
            if browser is not None:
                try:
                    await browser.close()
                    logger.debug("🧹 Browser instance closed successfully")
                except Exception as cleanup_error:
                    logger.warning(f"⚠️  Error closing browser: {cleanup_error}")
    
    def execute_instruction_sync(self, instruction: str, progress_callback=None) -> Dict[str, Any]:
        """
        Synchronous wrapper for execute_instruction
        Each call creates a new event loop to ensure thread safety
        
        Args:
            instruction: User's natural language instruction
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with execution results
        """
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self.execute_instruction(instruction, progress_callback=progress_callback))
            finally:
                # Clean up pending tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                # Wait for cancelled tasks to finish
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                
        except Exception as e:
            logger.error(f"Sync execution error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Sync execution error: {str(e)}",
                "steps": [],
                "iterations": 0
            }
        finally:
            # Always close the event loop
            if loop is not None:
                try:
                    loop.close()
                    logger.debug("🧹 Event loop closed successfully")
                except Exception as loop_error:
                    logger.warning(f"⚠️  Error closing event loop: {loop_error}")
