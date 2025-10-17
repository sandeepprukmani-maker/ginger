import json
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .browser_engine import BrowserEngine
from .task_executor import TaskExecutor, TaskType, TaskResult
from .advanced_tools import AdvancedPlaywrightTools, PageContext
from .vision_analyzer import VisionPageAnalyzer, ElementLocation
from .session_memory import SessionMemory
from .logger import get_logger
from .config import AutomationConfig

logger = get_logger()


@dataclass
class ExecutionStep:
    action: str
    params: Dict[str, Any]
    description: str
    use_vision: bool = False


@dataclass
class ExecutionResult:
    success: bool
    steps_completed: int
    total_steps: int
    error: Optional[str] = None
    data: Any = None


class EnhancedNaturalLanguageExecutor:
    """
    Highly intelligent executor with advanced capabilities:
    - Vision-based element detection
    - Smart selector fallback strategies  
    - Dynamic content handling
    - iframe/popup support
    - Intelligent error recovery
    - Learning from execution patterns
    """
    
    def __init__(self, browser_engine: BrowserEngine, automation_config: Optional[AutomationConfig] = None):
        self.browser = browser_engine
        self.task_executor = TaskExecutor(browser_engine)
        self.config = automation_config or AutomationConfig()
        self.client = None
        self.memory = SessionMemory(session_dir=self.config.session_dir)
        self.advanced_tools: Optional[AdvancedPlaywrightTools] = None
        self.vision_analyzer = VisionPageAnalyzer()
        
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI package not available. Natural language execution requires OpenAI.")
        elif not api_key:
            logger.warning("OPENAI_API_KEY not set. Natural language execution will not be available.")
        else:
            self.client = AsyncOpenAI(api_key=api_key)
    
    async def execute_instruction(self, instruction: str, url: Optional[str] = None,
                                 use_vision: bool = False) -> ExecutionResult:
        """
        Execute a natural language instruction with advanced capabilities.
        
        Args:
            instruction: Natural language instruction
            url: Optional starting URL
            use_vision: Whether to use vision-based analysis
            
        Returns:
            ExecutionResult with success status and any extracted data
        """
        if not self.client:
            logger.error("Cannot execute instruction: OpenAI client not initialized")
            return ExecutionResult(success=False, steps_completed=0, total_steps=0, 
                                 error="OpenAI API not available")
        
        if self.browser.page and not self.advanced_tools:
            self.advanced_tools = AdvancedPlaywrightTools(self.browser.page)
        
        logger.info(f"Processing instruction with enhanced capabilities: {instruction}")
        
        max_retries = self.config.max_retries
        attempt = 0
        page_context = None
        
        while attempt < max_retries:
            try:
                if use_vision and self.advanced_tools:
                    page_context = await self.advanced_tools.get_page_context(
                        include_screenshot=True,
                        include_dom=True
                    )
                
                steps = await self._convert_instruction_to_steps(instruction, url, page_context)
                
                if not steps:
                    return ExecutionResult(success=False, steps_completed=0, total_steps=0,
                                         error="Could not convert instruction to actions")
                
                logger.info(f"Generated {len(steps)} steps (vision-enhanced: {use_vision})")
                
                result = await self._execute_steps_with_intelligence(steps, page_context)
                
                if result.success:
                    self._record_execution(instruction, steps, True)
                    return result
                
                logger.warning(f"Execution failed on attempt {attempt + 1}: {result.error}")
                
                if attempt < max_retries - 1:
                    logger.info("Analyzing error with vision and retrying...")
                    
                    corrected_steps = await self._intelligent_error_correction(
                        instruction, steps, result.error, attempt, page_context
                    )
                    
                    if corrected_steps:
                        attempt += 1
                        logger.info(f"Retrying with corrected steps (attempt {attempt + 1})...")
                        steps = corrected_steps
                        result = await self._execute_steps_with_intelligence(steps, page_context)
                        
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
    
    async def _convert_instruction_to_steps(self, instruction: str, url: Optional[str] = None,
                                           context: Optional[PageContext] = None) -> List[ExecutionStep]:
        """
        Convert instruction to steps with enhanced context awareness.
        """
        memory_context = self.memory.get_context_for_instruction(instruction)
        
        page_info = ""
        if context:
            page_info = f"""
Current page context:
- URL: {context.url}
- Title: {context.title}
- Has iframes: {context.has_iframes}
- Has popups: {context.has_popups}
- Visible elements: {len(context.visible_elements)}
"""
            if context.visible_elements:
                page_info += "\nKey visible elements:\n" + "\n".join(context.visible_elements[:15])
        
        system_prompt = """You are an expert browser automation assistant with advanced capabilities.

Available actions:
- navigate: Go to a URL {"action": "navigate", "params": {"url": "https://example.com"}}
- click: Click an element {"action": "click", "params": {"selector": "button.submit", "description": "submit button"}}
- fill: Fill input {"action": "fill", "params": {"selector": "input[name='q']", "value": "search term", "description": "search box"}}
- extract_text: Extract text {"action": "extract_text", "params": {"selector": "h1", "all": false, "description": "page title"}}
- wait: Wait {"action": "wait", "params": {"type": "time", "duration": 2000}}
- wait_dynamic: Wait for dynamic content {"action": "wait_dynamic", "params": {}}
- scroll_to: Scroll to element {"action": "scroll_to", "params": {"selector": "div.content"}}
- handle_iframe: Switch to iframe {"action": "handle_iframe", "params": {"selector": "iframe#content"}}
- screenshot: Screenshot {"action": "screenshot", "params": {"name": "screenshot"}}
- extract_links: Get all links {"action": "extract_links", "params": {"filter_text": "optional filter"}}
- extract_table: Get table data {"action": "extract_table", "params": {"selector": "table.data"}}

IMPORTANT SELECTOR GUIDELINES:
1. Always include a human-readable "description" in params for click/fill/extract actions
2. Use generic, flexible selectors (prefer classes over ids)
3. Consider multiple fallback strategies
4. For buttons/links, include descriptive text when possible
5. Account for dynamic content - add wait_dynamic when needed
6. If iframe detected, add handle_iframe step before interacting with iframe content

Return ONLY a JSON array of steps. Be specific but flexible with selectors."""

        user_prompt = f"""Instruction: {instruction}

{page_info}
"""
        
        if url:
            user_prompt += f"\nStarting URL: {url}"
        
        if memory_context:
            user_prompt += f"\n\n{memory_context}"
        
        user_prompt += "\n\nGenerate the automation steps as a JSON array:"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2500
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
                    description=step.get("description", step["action"]),
                    use_vision=step.get("use_vision", False)
                )
                for step in steps_data
            ]
            
            return steps
            
        except Exception as e:
            logger.error(f"Error converting instruction to steps: {e}")
            return []
    
    async def _execute_steps_with_intelligence(self, steps: List[ExecutionStep],
                                               context: Optional[PageContext] = None) -> ExecutionResult:
        """
        Execute steps with intelligent element finding and error handling.
        """
        total_steps = len(steps)
        completed = 0
        last_data = None
        current_context = context
        
        for i, step in enumerate(steps):
            logger.info(f"Step {i+1}/{total_steps}: {step.description}")
            
            try:
                if step.action in ["click", "fill", "extract_text", "scroll_to"]:
                    if "selector" in step.params and "description" in step.params:
                        original_selector = step.params["selector"]
                        description = step.params["description"]
                        
                        selector = await self._intelligent_find_selector(
                            description, original_selector, step.use_vision, current_context
                        )
                        
                        if selector:
                            step.params["selector"] = selector
                        else:
                            logger.warning(f"Could not find element for: {description}, using original")
                
                if step.action == "wait_dynamic":
                    if self.advanced_tools:
                        await self.advanced_tools.wait_for_dynamic_content()
                        completed += 1
                        continue
                
                if step.action == "handle_iframe":
                    if self.advanced_tools:
                        frame = await self.advanced_tools.handle_iframe(step.params.get("selector"))
                        if frame:
                            logger.info("Successfully switched to iframe")
                        completed += 1
                        continue
                
                if step.action == "extract_links":
                    if self.advanced_tools:
                        links = await self.advanced_tools.extract_links(step.params.get("filter_text"))
                        last_data = links
                        completed += 1
                        continue
                
                if step.action == "extract_table":
                    if self.advanced_tools:
                        table_data = await self.advanced_tools.extract_table_data(step.params.get("selector", "table"))
                        last_data = table_data
                        completed += 1
                        continue
                
                if step.action == "scroll_to":
                    if self.advanced_tools:
                        await self.advanced_tools.scroll_to_element(step.params["selector"])
                        completed += 1
                        continue
                
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
                
                # Refresh page context after successful navigation for DOM analysis
                if step.action == "navigate" and result.success and self.advanced_tools and step.use_vision:
                    await asyncio.sleep(1)  # Give page time to load
                    current_context = await self.advanced_tools.get_page_context(
                        include_screenshot=True,
                        include_dom=True
                    )
                    logger.info(f"📊 Refreshed DOM context after navigation to {current_context.url}")
                
                if result.data is not None:
                    last_data = result.data
                    if isinstance(result.data, list) and len(result.data) <= 10:
                        logger.info(f"Step result: {result.data}")
                    else:
                        logger.info(f"Step result: {str(result.data)[:100]}...")
                
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
    
    async def _intelligent_find_selector(self, description: str, fallback_selector: str,
                                        use_vision: bool, context: Optional[PageContext]) -> str:
        """
        Intelligently find the best selector using multiple strategies.
        """
        if self.advanced_tools:
            smart_selector = await self.advanced_tools.smart_find_element(description)
            if smart_selector:
                return smart_selector
        
        if use_vision and context and self.vision_analyzer.client:
            location = await self.vision_analyzer.find_element_by_description(context, description)
            if location and location.confidence > 0.7:
                logger.info(f"Vision found selector: {location.suggested_selector}")
                return location.suggested_selector
        
        return fallback_selector
    
    async def _intelligent_error_correction(self, instruction: str, failed_steps: List[ExecutionStep],
                                           error: str, attempt: int,
                                           context: Optional[PageContext]) -> Optional[List[ExecutionStep]]:
        """
        Use vision and AI to correct errors intelligently.
        """
        logger.info("Performing intelligent error correction...")
        
        if context and self.vision_analyzer.client:
            failed_step = None
            for step in failed_steps:
                if "selector" in step.params:
                    failed_step = step
                    break
            
            if failed_step:
                diagnosis = await self.vision_analyzer.diagnose_error(
                    context, error, failed_step.params.get("selector", "")
                )
                if diagnosis:
                    logger.info(f"Vision diagnosis: {diagnosis}")
        
        system_prompt = """You are an expert at debugging and correcting browser automation failures.
Analyze the error and generate corrected steps using better selectors and strategies.

Common fixes:
- Use more flexible selectors
- Add wait_dynamic for dynamic content
- Add scroll_to before clicking elements
- Use text-based selectors when CSS fails
- Handle iframes if present
- Try alternative element descriptions

Return ONLY corrected JSON array of steps."""

        failed_steps_json = json.dumps([
            {"action": s.action, "params": s.params, "description": s.description}
            for s in failed_steps
        ], indent=2)
        
        context_info = ""
        if context:
            context_info = f"""
Page context:
- URL: {context.url}
- Title: {context.title}
- Has iframes: {context.has_iframes}
- Visible elements: {len(context.visible_elements)}
"""
        
        user_prompt = f"""Original instruction: {instruction}

Failed steps:
{failed_steps_json}

Error: {error}

{context_info}

Generate corrected steps with better selectors and strategies:"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,
                max_tokens=2500
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
                    description=step.get("description", step["action"]),
                    use_vision=step.get("use_vision", False)
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
        """Record execution in persistent memory."""
        steps_data = [
            {"action": s.action, "params": s.params, "description": s.description}
            for s in steps
        ]
        self.memory.record_execution(instruction, success, steps_data, error)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about execution memory."""
        return self.memory.get_stats()
