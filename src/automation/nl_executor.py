import json
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .browser_engine import BrowserEngine
from .task_executor import TaskExecutor, TaskType, TaskResult
from .logger import get_logger
from .config import AutomationConfig
from .session_memory import SessionMemory

logger = get_logger()


@dataclass
class ExecutionStep:
    action: str
    params: Dict[str, Any]
    description: str


@dataclass
class ExecutionResult:
    success: bool
    steps_completed: int
    total_steps: int
    error: Optional[str] = None
    data: Any = None


class NaturalLanguageExecutor:
    """
    Intelligent executor that converts natural language instructions into browser automation.
    Learns from errors and retries with corrections.
    """
    
    def __init__(self, browser_engine: BrowserEngine, automation_config: Optional[AutomationConfig] = None):
        self.browser = browser_engine
        self.task_executor = TaskExecutor(browser_engine)
        self.config = automation_config or AutomationConfig()
        self.client = None
        self.memory = SessionMemory(session_dir=self.config.session_dir)
        
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI package not available. Natural language execution requires OpenAI.")
        elif not api_key:
            logger.warning("OPENAI_API_KEY not set. Natural language execution will not be available.")
        else:
            self.client = AsyncOpenAI(api_key=api_key)
    
    async def execute_instruction(self, instruction: str, url: Optional[str] = None) -> ExecutionResult:
        """
        Execute a natural language instruction by converting it to browser actions.
        
        Args:
            instruction: Natural language instruction (e.g., "go to google and search for playwright")
            url: Optional starting URL
            
        Returns:
            ExecutionResult with success status and any extracted data
        """
        if not self.client:
            logger.error("Cannot execute instruction: OpenAI client not initialized")
            return ExecutionResult(success=False, steps_completed=0, total_steps=0, 
                                 error="OpenAI API not available")
        
        logger.info(f"Processing instruction: {instruction}")
        
        max_retries = self.config.max_retries
        attempt = 0
        
        while attempt < max_retries:
            try:
                steps = await self._convert_instruction_to_steps(instruction, url)
                
                if not steps:
                    return ExecutionResult(success=False, steps_completed=0, total_steps=0,
                                         error="Could not convert instruction to actions")
                
                logger.info(f"Generated {len(steps)} steps to execute")
                
                result = await self._execute_steps(steps)
                
                if result.success:
                    self._record_execution(instruction, steps, True)
                    return result
                
                logger.warning(f"Execution failed on attempt {attempt + 1}: {result.error}")
                
                if attempt < max_retries - 1:
                    logger.info("Analyzing error and retrying with corrections...")
                    
                    corrected_steps = await self._analyze_and_correct(
                        instruction, steps, result.error, attempt
                    )
                    
                    if corrected_steps:
                        attempt += 1
                        logger.info(f"Retrying with corrected steps (attempt {attempt + 1})...")
                        steps = corrected_steps
                        result = await self._execute_steps(steps)
                        
                        if result.success:
                            self._record_execution(instruction, steps, True)
                            return result
                        
                        logger.warning(f"Corrected execution also failed: {result.error}")
                
                attempt += 1
            
            except Exception as e:
                logger.error(f"Unexpected error during execution: {e}")
                attempt += 1
                await asyncio.sleep(self.config.retry_delay)
        
        error_msg = "Max retries exceeded"
        if 'steps' in locals() and steps:
            self._record_execution(instruction, steps, False, error_msg)
        
        return ExecutionResult(success=False, steps_completed=0, total_steps=len(steps) if steps else 0,
                             error=error_msg)
    
    async def _convert_instruction_to_steps(self, instruction: str, url: Optional[str] = None) -> List[ExecutionStep]:
        """
        Use AI to convert natural language instruction into actionable steps.
        """
        context = self.memory.get_context_for_instruction(instruction)
        
        system_prompt = """You are an expert browser automation assistant. Convert natural language instructions into a sequence of browser automation actions.

Available actions:
- navigate: Go to a URL {"action": "navigate", "params": {"url": "https://example.com"}}
- click: Click an element {"action": "click", "params": {"selector": "button.submit"}}
- fill: Fill an input field {"action": "fill", "params": {"selector": "input[name='search']", "value": "search term"}}
- extract_text: Extract text from elements {"action": "extract_text", "params": {"selector": "h1", "all": false}}
- wait: Wait for something {"action": "wait", "params": {"type": "time", "duration": 2000}}
- scroll: Scroll the page {"action": "scroll", "params": {"direction": "down", "amount": 500}}
- screenshot: Take a screenshot {"action": "screenshot", "params": {"name": "screenshot"}}

Return ONLY a JSON array of steps. Each step must have:
- action: The action type
- params: Parameters for the action
- description: Human-readable description of what this step does

Use realistic CSS selectors. Be specific and practical.
Consider common web patterns (forms use input/button, links use a, etc.)"""

        user_prompt = f"""Instruction: {instruction}"""
        
        if url:
            user_prompt += f"\nStarting URL: {url}"
        
        if context:
            user_prompt += f"\n\nContext from previous executions:\n{context}"
        
        user_prompt += "\n\nGenerate the steps as a JSON array:"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            steps_data = json.loads(content)
            
            steps = [
                ExecutionStep(
                    action=step["action"],
                    params=step["params"],
                    description=step.get("description", step["action"])
                )
                for step in steps_data
            ]
            
            return steps
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Response content: {content}")
            return []
        except Exception as e:
            logger.error(f"Error converting instruction to steps: {e}")
            return []
    
    async def _execute_steps(self, steps: List[ExecutionStep]) -> ExecutionResult:
        """
        Execute a sequence of steps.
        """
        total_steps = len(steps)
        completed = 0
        last_data = None
        
        for i, step in enumerate(steps):
            logger.info(f"Step {i+1}/{total_steps}: {step.description}")
            
            try:
                task_type = TaskType(step.action)
                result = await self.task_executor.execute_task(task_type, step.params)
                
                if not result.success:
                    error_msg = f"Step {i+1} failed: {result.error or 'Unknown error'}"
                    logger.error(error_msg)
                    return ExecutionResult(
                        success=False,
                        steps_completed=completed,
                        total_steps=total_steps,
                        error=error_msg
                    )
                
                if result.data is not None:
                    last_data = result.data
                    logger.info(f"Step result: {str(result.data)[:100]}")
                
                completed += 1
                await asyncio.sleep(0.5)
                
            except ValueError:
                error_msg = f"Invalid action type: {step.action}"
                logger.error(error_msg)
                return ExecutionResult(
                    success=False,
                    steps_completed=completed,
                    total_steps=total_steps,
                    error=error_msg
                )
            except Exception as e:
                error_msg = f"Step {i+1} error: {str(e)}"
                logger.error(error_msg)
                return ExecutionResult(
                    success=False,
                    steps_completed=completed,
                    total_steps=total_steps,
                    error=error_msg
                )
        
        logger.success(f"Successfully completed all {total_steps} steps")
        return ExecutionResult(
            success=True,
            steps_completed=completed,
            total_steps=total_steps,
            data=last_data
        )
    
    async def _analyze_and_correct(self, instruction: str, failed_steps: List[ExecutionStep], 
                                   error: str, attempt: int) -> Optional[List[ExecutionStep]]:
        """
        Analyze the error and generate corrected steps.
        """
        logger.info(f"Analyzing error and generating corrections (attempt {attempt + 1})...")
        
        system_prompt = """You are an expert at debugging browser automation scripts. 
Given a failed automation sequence, analyze the error and generate corrected steps.

Common issues:
- Wrong selectors: Try more generic selectors, text-based selectors, or ARIA labels
- Timing: Add wait steps before interactions
- Page navigation: Ensure page is loaded before interactions
- Dynamic content: Wait for elements to appear

Return ONLY a JSON array of corrected steps."""

        failed_steps_json = json.dumps([
            {"action": s.action, "params": s.params, "description": s.description}
            for s in failed_steps
        ], indent=2)
        
        user_prompt = f"""Original instruction: {instruction}

Failed steps:
{failed_steps_json}

Error: {error}

Generate corrected steps that will work:"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            steps_data = json.loads(content)
            
            corrected_steps = [
                ExecutionStep(
                    action=step["action"],
                    params=step["params"],
                    description=step.get("description", step["action"])
                )
                for step in steps_data
            ]
            
            logger.info(f"Generated {len(corrected_steps)} corrected steps")
            return corrected_steps
            
        except Exception as e:
            logger.error(f"Error generating corrections: {e}")
            return None
    
    def _record_execution(self, instruction: str, steps: List[ExecutionStep], 
                         success: bool, error: Optional[str] = None):
        """
        Record execution in persistent memory.
        """
        steps_data = [
            {"action": s.action, "params": s.params, "description": s.description}
            for s in steps
        ]
        self.memory.record_execution(instruction, success, steps_data, error)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about execution memory."""
        return self.memory.get_stats()
