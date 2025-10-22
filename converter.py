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
        self.logger.info(f"Processing {len(history.history)} history steps")

        for step_idx, step in enumerate(history.history):
            self.logger.debug(f"Step {step_idx}: model_output={step.model_output is not None}")

            if not step.model_output or not step.model_output.action:
                self.logger.debug(f"Step {step_idx}: Skipping - no model_output or actions")
                continue

            # Get interacted elements from state
            interacted_elements = step.state.interacted_element if hasattr(step.state, 'interacted_element') else []
            self.logger.debug(
                f"Step {step_idx}: Found {len(step.model_output.action)} actions, {len(interacted_elements)} interacted elements")

            # Process each action in this step
            for i, action_model in enumerate(step.model_output.action):
                self.logger.debug(f"Step {step_idx}, Action {i}: {type(action_model).__name__}")
                # Get corresponding interacted element if available
                interacted_elem = interacted_elements[i] if i < len(interacted_elements) else None
                self._process_action(action_model, interacted_elem,
                                     step.state.url if hasattr(step.state, 'url') else None)

        captured_count = len(self.action_capture.get_actions())
        self.logger.info(f"Captured {captured_count} actions total")

    def _process_action(self, action_model, interacted_element, current_url: str = None):
        """Process a single action model and capture it."""
        # Log action model attributes for debugging
        action_attrs = [attr for attr in dir(action_model) if not attr.startswith('_')]
        self.logger.debug(f"Action model attributes: {action_attrs}")

        # Get action dict from the action model
        action_dict = action_model.model_dump() if hasattr(action_model, 'model_dump') else {}
        self.logger.debug(f"Action dict keys: {list(action_dict.keys())}")

        # Navigate action
        if hasattr(action_model, 'go_to_url') and action_model.go_to_url:
            url = action_model.go_to_url.url if hasattr(action_model.go_to_url, 'url') else str(action_model.go_to_url)
            self.logger.info(f"Capturing navigation to: {url}")
            self.action_capture.capture_navigation(url)

        # Click action
        elif hasattr(action_model, 'click_element') and action_model.click_element:
            self.logger.info(f"Capturing click, interacted_element: {interacted_element is not None}")
            if interacted_element:
                element_info = self._extract_element_info(interacted_element)
                self.logger.debug(f"Element info: {element_info}")
                self.action_capture.capture_click(element_info)
            else:
                # Even without element, capture with minimal info
                self.logger.warning("Click action without interacted element, using fallback")
                self.action_capture.capture_click({'tag_name': 'button', 'text': 'element'})

        # Input action
        elif hasattr(action_model, 'input_text') and action_model.input_text:
            text = action_model.input_text.text if hasattr(action_model.input_text, 'text') else ''
            self.logger.info(f"Capturing input: {text}")
            if interacted_element:
                element_info = self._extract_element_info(interacted_element)
                self.action_capture.capture_fill(element_info, text)
            else:
                self.logger.warning("Input action without interacted element, using fallback")
                self.action_capture.capture_fill({'tag_name': 'input', 'text': 'input'}, text)

        # Send keys action
        elif hasattr(action_model, 'send_keys') and action_model.send_keys:
            keys = action_model.send_keys.keys if hasattr(action_model.send_keys, 'keys') else ''
            self.logger.info(f"Capturing send keys: {keys}")
            # Parse keys and convert to individual presses
            for key in str(keys).split():
                self.action_capture.capture_press(key)

        # Scroll action
        elif hasattr(action_model, 'scroll') and action_model.scroll:
            direction = action_model.scroll.direction if hasattr(action_model.scroll, 'direction') else 'down'
            amount = action_model.scroll.amount if hasattr(action_model.scroll, 'amount') else 100
            self.logger.info(f"Capturing scroll: {direction} {amount}")
            self.action_capture.capture_scroll(str(direction), amount)

        # Switch tab action
        elif hasattr(action_model, 'switch_tab') and action_model.switch_tab:
            page_id = action_model.switch_tab.page_id if hasattr(action_model.switch_tab, 'page_id') else 0
            self.logger.info(f"Capturing switch tab: {page_id}")
            self.action_capture.capture_switch_tab(page_id)

        # Open tab action
        elif hasattr(action_model, 'open_tab') and action_model.open_tab:
            self.logger.info("Capturing new tab")
            self.action_capture.capture_new_tab()

        # Wait action
        elif hasattr(action_model, 'wait') and action_model.wait:
            duration = action_model.wait.seconds if hasattr(action_model.wait, 'seconds') else 1
            self.logger.info(f"Capturing wait: {duration}s")
            self.action_capture.capture_wait(int(duration * 1000))

        # Done action (task complete)
        elif hasattr(action_model, 'done') and action_model.done:
            self.logger.info("Task marked as done")

        else:
            self.logger.warning(f"Unknown action type, dict: {action_dict}")

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
