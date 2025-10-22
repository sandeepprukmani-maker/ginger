"""Main converter that uses browser-use agent to execute tasks and capture actions."""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict

from browser_use import Agent, Browser, Controller
from browser_use.agent.views import AgentHistoryList, ActionResult
from browser_use.dom.views import DOMInteractedElement

from action_capture import ActionCapture
from playwright_generator import PlaywrightScriptGenerator


class NL2PlaywrightConverter:
    """Converts natural language to Playwright scripts using browser-use."""
    
    def __init__(self, llm, headless: bool = False, output_dir: str = "generated_scripts"):
        self.llm = llm
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.action_capture = ActionCapture()
        
    async def convert(self, natural_language_task: str) -> tuple[str, str]:
        """
        Convert natural language to Playwright script.
        
        Returns:
            tuple: (script_content, output_path)
        """
        self.logger.info(f"Converting task: {natural_language_task}")
        self.action_capture.clear()
        
        # Create custom controller to capture actions
        controller = self._create_capturing_controller()
        
        # Create browser instance
        browser = Browser(
            headless=self.headless,
            keep_alive=False
        )
        
        try:
            # Create and run agent
            agent = Agent(
                task=natural_language_task,
                llm=self.llm,
                browser=browser,
                controller=controller,
                use_vision=True,  # Enable vision for better element detection
            )
            
            self.logger.info("Starting browser-use agent...")
            history: AgentHistoryList = await agent.run(max_steps=30)
            
            # Extract actions from history
            self._extract_actions_from_history(history)
            
            # Generate Playwright script
            generator = PlaywrightScriptGenerator(async_mode=False)
            script = generator.generate(
                actions=self.action_capture.get_actions(),
                task_description=natural_language_task
            )
            
            # Save script
            output_path = self._save_script(script, natural_language_task)
            
            self.logger.info(f"✅ Playwright script generated: {output_path}")
            return script, str(output_path)
            
        except Exception as e:
            self.logger.error(f"Error during conversion: {e}", exc_info=True)
            raise
        finally:
            # Cleanup is handled by agent
            pass
    
    def _create_capturing_controller(self) -> Controller:
        """Create a custom controller that captures actions."""
        controller = Controller()
        
        # Hook into the controller's action execution
        # We'll capture actions by monitoring the agent's history
        return controller
    
    def _extract_actions_from_history(self, history: AgentHistoryList):
        """Extract and convert actions from agent history."""
        for step in history.history:
            if not step.action_results:
                continue
                
            for action_result in step.action_results:
                self._process_action_result(action_result)
    
    def _process_action_result(self, action_result: ActionResult):
        """Process a single action result and capture it."""
        action = action_result.action
        
        if not action:
            return
        
        # Navigate action
        if 'go_to_url' in action:
            url = action['go_to_url'].get('url', '')
            self.action_capture.capture_navigation(url)
        
        # Click action
        elif 'click_element' in action:
            index = action['click_element'].get('index')
            if index is not None and action_result.interacted_element:
                element_info = self._extract_element_info(action_result.interacted_element)
                self.action_capture.capture_click(element_info)
        
        # Input action
        elif 'input_text' in action:
            index = action['input_text'].get('index')
            text = action['input_text'].get('text', '')
            if index is not None and action_result.interacted_element:
                element_info = self._extract_element_info(action_result.interacted_element)
                self.action_capture.capture_fill(element_info, text)
        
        # Send keys action
        elif 'send_keys' in action:
            keys = action['send_keys'].get('keys', '')
            # Parse keys and convert to individual presses
            for key in keys.split():
                self.action_capture.capture_press(key)
        
        # Scroll action
        elif 'scroll' in action:
            direction = action['scroll'].get('direction', 'down')
            amount = action['scroll'].get('amount', 100)
            self.action_capture.capture_scroll(direction, amount)
        
        # Switch tab action
        elif 'switch_tab' in action:
            page_id = action['switch_tab'].get('page_id', 0)
            self.action_capture.capture_switch_tab(page_id)
        
        # Open tab action
        elif 'open_tab' in action:
            self.action_capture.capture_new_tab()
        
        # Wait action
        elif 'wait' in action:
            duration = action['wait'].get('seconds', 1) * 1000
            self.action_capture.capture_wait(int(duration))
    
    def _extract_element_info(self, element: DOMInteractedElement) -> Dict[str, Any]:
        """Extract element information for selector generation."""
        return {
            'tag_name': element.tag_name if hasattr(element, 'tag_name') else None,
            'id': element.element_id if hasattr(element, 'element_id') else None,
            'class': element.class_name if hasattr(element, 'class_name') else None,
            'text': element.text if hasattr(element, 'text') else None,
            'attributes': element.attributes if hasattr(element, 'attributes') else {},
            'xpath': element.xpath if hasattr(element, 'xpath') else None,
            'role': element.role if hasattr(element, 'role') else None,
        }
    
    def _save_script(self, script: str, task: str) -> Path:
        """Save the generated script to a file."""
        # Create a safe filename from the task
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in task)
        safe_name = safe_name[:50]  # Limit length
        safe_name = safe_name.strip().replace(' ', '_')
        
        # Add timestamp to avoid conflicts
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.py"
        
        output_path = self.output_dir / filename
        output_path.write_text(script, encoding='utf-8')
        
        return output_path
