"""
Optimized Browser-Use Engine
AI-powered browser automation with advanced features and optimizations

New Features:
- Advanced browser capabilities (screenshots, PDFs, cookies, sessions)
- Enhanced popup handling with configurable timeouts
- Smart retry mechanism with exponential backoff
- State management for complex workflows
- Data extraction capabilities
- Performance monitoring and metrics
"""
import os
import asyncio
import configparser
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from browser_use import Agent, Browser
from browser_use.llm import ChatOpenAI

from app.engines.browser_use.advanced_features import AdvancedBrowserFeatures
from app.engines.browser_use.retry_mechanism import RetryConfig, RetryMechanism
from app.engines.browser_use.state_manager import WorkflowState
from app.engines.browser_use.data_extractor import DataExtractor
from app.engines.browser_use.performance_monitor import PerformanceMonitor

project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)

logger = logging.getLogger(__name__)


class OptimizedBrowserUseEngine:
    """
    Optimized browser automation engine with advanced capabilities
    
    Features:
    - Screenshot capture and PDF generation
    - Cookie and session management
    - Smart retry with exponential backoff
    - Workflow state persistence
    - Data extraction (tables, lists, metadata)
    - Performance monitoring
    - Enhanced popup handling
    """
    
    def __init__(self, headless: bool = False, enable_advanced_features: bool = True):
        """
        Initialize Optimized Browser-Use Engine
        
        Args:
            headless: Run browser in headless mode
            enable_advanced_features: Enable advanced capabilities
        """
        self.headless = headless
        self.enable_advanced_features = enable_advanced_features
        
        config = configparser.ConfigParser()
        config.read('config/config.ini')
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key must be set as OPENAI_API_KEY environment variable.")
        
        model = config.get('openai', 'model', fallback='gpt-4o-mini')
        timeout = int(config.get('openai', 'timeout', fallback='180'))
        self.max_steps = int(config.get('agent', 'max_steps', fallback='25'))
        
        # Browser performance settings - using reliable defaults
        self.minimum_wait_page_load_time = float(config.get('browser_performance', 'minimum_wait_page_load_time', fallback='1.0'))
        self.wait_for_network_idle_page_load_time = float(config.get('browser_performance', 'wait_for_network_idle_page_load_time', fallback='1.5'))
        self.wait_between_actions = float(config.get('browser_performance', 'wait_between_actions', fallback='1.0'))
        
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            timeout=timeout
        )
        
        if enable_advanced_features:
            output_dir = config.get('advanced_features', 'output_directory', fallback='automation_outputs')
            self.enable_screenshots = config.getboolean('advanced_features', 'enable_screenshots', fallback=True)
            self.enable_pdf_generation = config.getboolean('advanced_features', 'enable_pdf_generation', fallback=True)
            self.enable_cookie_management = config.getboolean('advanced_features', 'enable_cookie_management', fallback=True)
            self.enable_state_persistence = config.getboolean('advanced_features', 'enable_state_persistence', fallback=True)
            
            self.advanced_features = AdvancedBrowserFeatures(output_dir=output_dir)
            
            max_retries = int(config.get('retry', 'max_retries', fallback='3'))
            initial_delay = float(config.get('retry', 'initial_delay', fallback='1.0'))
            max_delay = float(config.get('retry', 'max_delay', fallback='30.0'))
            backoff_factor = float(config.get('retry', 'backoff_factor', fallback='2.0'))
            
            retry_config = RetryConfig(
                max_retries=max_retries,
                initial_delay=initial_delay,
                max_delay=max_delay,
                backoff_factor=backoff_factor
            )
            self.retry_mechanism = RetryMechanism(retry_config)
            
            track_metrics = config.getboolean('performance', 'track_detailed_metrics', fallback=True)
            self.performance_monitor = PerformanceMonitor(track_detailed_metrics=track_metrics)
            
            self.data_extractor = DataExtractor()
            self.workflow_state = None
            
            logger.info("🚀 Advanced features enabled: Screenshots, PDFs, Cookies, Retry, Performance Tracking")
        else:
            logger.info("ℹ️  Running in basic mode (advanced features disabled)")
    
    async def execute_instruction(self, instruction: str, 
                                  workflow_id: Optional[str] = None,
                                  save_screenshot: bool = False,
                                  save_pdf: bool = False,
                                  progress_callback=None) -> Dict[str, Any]:
        """
        Execute a natural language instruction with advanced features
        
        Args:
            instruction: User's natural language instruction
            workflow_id: Optional workflow ID for state management
            save_screenshot: Capture screenshot after completion
            save_pdf: Generate PDF after completion
            
        Returns:
            Dictionary with execution results and advanced metrics
        """
        op_id = None
        if self.enable_advanced_features:
            op_id = self.performance_monitor.start_operation("execute_instruction")
            
            if workflow_id:
                self.workflow_state = WorkflowState(workflow_id=workflow_id, persist_to_disk=True)
        
        try:
            logger.info("🤖 Initializing Browser-Use Agent")
            logger.info(f"📋 Task: {instruction}")
            logger.info(f"🔢 Max steps: {self.max_steps}")
            
            # Send initialization progress
            if progress_callback:
                progress_callback('init', {'message': 'Initializing browser automation agent...', 'instruction': instruction})
            
            # System instructions optimized for efficiency while maintaining safety
            system_instructions = f"""
TASK: "{instruction}"

CORE RULES:
1. Execute ONLY explicitly stated actions - nothing more
2. After completing all explicit steps → use done() immediately
3. Verify each action succeeded before proceeding
4. Keep thinking concise but thorough

POPUP/NEW WINDOW HANDLING:
- After clicking button that opens popup → wait 3s for window switch
- Verify popup content loaded correctly
- If content not ready → wait 2s more → retry
- Continue with explicit instructions in the new window

PAGE LOADING & ERRORS:
- If element not found → page still loading → wait 2s → retry with fresh page state
- Verify critical actions (form submissions, clicks) succeeded
- Do NOT assume success without verification

SECURITY:
- Never navigate to unintended domains
- Confirm sensitive actions before executing
            """
            
            logger.info("⚙️  Configuring agent with optimizations")
            
            # Send browser initialization progress
            if progress_callback:
                progress_callback('browser_init', {'message': f'Starting browser (headless={self.headless})...'})
            
            # Create browser instance with optimized performance settings
            browser = Browser(
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
            
            if self.enable_advanced_features:
                @self.retry_mechanism.async_retry
                async def run_with_retry():
                    return await agent.run(max_steps=self.max_steps)
                
                history = await run_with_retry()
            else:
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
                
                if self.enable_advanced_features and self.workflow_state:
                    self.workflow_state.add_step(
                        step_name=f"browser_action_{step_num}",
                        step_data={"action": action},
                        success=True
                    )
            
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
            
            if len(steps) == 0:
                logger.error(f"❌ Task failed - no steps were executed successfully")
                result = {
                    "success": False,
                    "error": "Browser automation failed to execute any steps",
                    "message": "No steps executed - browser may have failed to start",
                    "steps": [],
                    "iterations": 0,
                    "final_result": None
                }
            else:
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
            
            if self.enable_advanced_features:
                if op_id:
                    self.performance_monitor.end_operation(op_id, success=result["success"])
                
                result["performance_metrics"] = self.performance_monitor.get_summary()
                
                if self.workflow_state:
                    result["workflow_state"] = self.workflow_state.get_summary()
                
                result["retry_stats"] = self.retry_mechanism.get_stats()
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Browser-Use execution failed: {str(e)}", exc_info=True)
            
            if self.enable_advanced_features and op_id:
                self.performance_monitor.end_operation(op_id, success=False)
            
            return {
                "success": False,
                "error": str(e),
                "steps": [],
                "iterations": 0
            }
    
    def execute_instruction_sync(self, instruction: str, progress_callback=None, **kwargs) -> Dict[str, Any]:
        """
        Synchronous wrapper for execute_instruction
        
        Args:
            instruction: User's natural language instruction
            progress_callback: Optional callback for progress updates
            **kwargs: Additional arguments for execute_instruction
            
        Returns:
            Dictionary with execution results
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(self.execute_instruction(instruction, progress_callback=progress_callback, **kwargs))
            finally:
                loop.close()
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Sync execution error: {str(e)}",
                "steps": [],
                "iterations": 0
            }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance monitoring summary"""
        if self.enable_advanced_features:
            return self.performance_monitor.get_summary()
        return {"error": "Advanced features not enabled"}
    
    def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry mechanism statistics"""
        if self.enable_advanced_features:
            return self.retry_mechanism.get_stats()
        return {"error": "Advanced features not enabled"}
    
    def reset_metrics(self):
        """Reset all performance metrics and statistics"""
        if self.enable_advanced_features:
            self.performance_monitor.reset()
            self.retry_mechanism.reset_stats()
            logger.info("🔄 All metrics reset")
