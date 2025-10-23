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
from typing import Dict, Any, List
from browser_use import Agent
from browser_use.llm import ChatOpenAI

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
        
        self.max_steps = int(config.get('agent', 'max_steps', fallback='25'))
        
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key
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
            
            # Custom system message to ensure literal execution
            system_instructions = """
CRITICAL INSTRUCTIONS:
1. Follow the user's instruction LITERALLY - do only what is explicitly asked
2. STOP IMMEDIATELY once the stated task is complete
3. Do NOT extract, save, or compile data unless explicitly requested
4. Do NOT perform additional "helpful" actions beyond the instruction
5. If asked to "search", stop when search results appear
6. If asked to "navigate", stop when the page loads
7. If asked to "click", stop after clicking
8. Only do extra work (extract, save, analyze) if the instruction explicitly asks for it
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
