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
from browser_use import Agent
from browser_use.llm import ChatOpenAI

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
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key must be set as OPENAI_API_KEY environment variable. Never store API keys in config files for security reasons.")
        
        model = config.get('openai', 'model', fallback='gpt-4o-mini')
        timeout = int(config.get('openai', 'timeout', fallback='180'))
        
        self.max_steps = int(config.get('agent', 'max_steps', fallback='50'))
        
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            timeout=timeout
        )
    
    async def execute_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        Execute a natural language instruction
        
        Args:
            instruction: User's natural language instruction
            
        Returns:
            Dictionary with execution results and steps taken
        """
        try:
            logger.info("🤖 Initializing Browser-Use Agent")
            logger.info(f"📋 Task: {instruction}")
            logger.info(f"🔢 Max steps: {self.max_steps}")
            
            # Enhanced system message for smart and powerful automation
            system_instructions = """
You are an advanced browser automation agent with sophisticated reasoning capabilities.

CORE CAPABILITIES:
1. **Navigation & Exploration**: Navigate to any URL, explore page structures, understand page context
2. **Form Interaction**: Fill complex forms, handle dropdowns, checkboxes, radio buttons, file uploads
3. **Element Interaction**: Click buttons, links, images; scroll to elements; hover for tooltips
4. **Data Extraction**: Extract text, tables, lists, images, links, structured data from pages
5. **Multi-Step Workflows**: Handle authentication, shopping carts, data entry, search & filter operations
6. **Dynamic Content**: Wait for AJAX/dynamic content, handle loading states, infinite scroll
7. **Error Recovery**: Retry failed operations, handle unexpected popups, deal with CAPTCHAs gracefully
8. **Session Management**: Maintain cookies, local storage, handle multi-page workflows

ADVANCED FEATURES:
- Handle complex authentication flows (login, 2FA, OAuth)
- Work with SPAs and frameworks (React, Angular, Vue)
- Extract and process data from tables, charts, and dashboards
- Fill multi-step forms with validation
- Handle file downloads and uploads
- Work with iframes and shadow DOM
- Manage browser tabs and windows

POPUP & WINDOW HANDLING:
- Automatically detect and switch to new windows/popups
- Handle OAuth popups (Google, Facebook, GitHub sign-in)
- Manage alert, confirm, and prompt dialogs
- Continue workflow seamlessly across window switches

SMART EXECUTION:
- Analyze page structure before acting
- Use precise selectors for reliable element targeting
- Verify actions succeeded before proceeding
- Adapt to page changes and dynamic content
- Provide detailed feedback on what was accomplished

STOPPING BEHAVIOR:
- Execute ALL requested actions in the instruction
- STOP when the complete task is finished
- If instruction says "and extract the data", ensure data is extracted before stopping
- For multi-step tasks, complete ALL steps mentioned
            """
            
            logger.info("⚙️  Configuring agent with literal execution instructions")
            
            agent = Agent(
                task=instruction,
                llm=self.llm,
                extend_system_message=system_instructions.strip(),
            )
            
            logger.info("▶️  Starting agent execution...")
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
            
            final_result = history.final_result() if hasattr(history, 'final_result') else None
            
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
            
            return {
                "success": True,
                "message": f"Task completed successfully. Executed {len(steps)} steps.",
                "steps": steps,
                "iterations": len(steps),
                "final_result": final_result
            }
            
        except Exception as e:
            logger.error(f"❌ Browser-Use execution failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "steps": [],
                "iterations": 0
            }
    
    def execute_instruction_sync(self, instruction: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for execute_instruction
        Each call creates a new event loop to ensure thread safety
        
        Args:
            instruction: User's natural language instruction
            
        Returns:
            Dictionary with execution results
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self.execute_instruction(instruction))
            finally:
                loop.close()
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Sync execution error: {str(e)}",
                "steps": [],
                "iterations": 0
            }
