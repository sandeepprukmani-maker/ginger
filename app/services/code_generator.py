import os
import logging
from typing import List, Dict, Any
from datetime import datetime
from app.models.database import DatabaseManager, ActionLog

logger = logging.getLogger(__name__)

class PlaywrightCodeGenerator:
    def __init__(self, db_manager: DatabaseManager, output_dir: str = 'data/generated_scripts'):
        self.db_manager = db_manager
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_script(self, task_id: int, headless: bool = False) -> str:
        """Generate a Playwright Python script from action logs"""
        try:
            session = self.db_manager.get_session()
            
            action_logs = session.query(ActionLog).filter_by(task_id=task_id).order_by(ActionLog.step_number).all()
            
            if not action_logs:
                logger.warning(f"No action logs found for task {task_id}")
                return None
            
            script_content = self._generate_script_content(action_logs, task_id, headless)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'task_{task_id}_{timestamp}.py'
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(script_content)
            
            logger.info(f"Generated Playwright script: {filepath} (headless={headless})")
            
            self.db_manager.close_session()
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return None
    
    def _generate_script_content(self, action_logs: List[ActionLog], task_id: int, headless: bool = False) -> str:
        """Generate the actual Python script content with self-healing capabilities"""
        
        script_lines = [
            "#!/usr/bin/env python3",
            '"""',
            f'Auto-generated Self-Healing Playwright script from Task #{task_id}',
            f'Generated at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            'This script includes self-healing capabilities using browser-use and MCP.',
            '"""',
            '',
            'import asyncio',
            'import os',
            'import sys',
            'import json',
            'import re',
            'from playwright.async_api import async_playwright, Page',
            'from typing import Dict, Any, Optional',
            '',
            '# Add parent directory to path to import healing services',
            'sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))',
            '',
            'try:',
            '    from app.services.browser_use_service import BrowserUseService',
            '    from app.services.mcp_service import MCPServerService',
            '    import yaml',
            '    HEALING_AVAILABLE = True',
            'except ImportError:',
            '    HEALING_AVAILABLE = False',
            '    print("Warning: Healing services not available. Script will run without self-healing.")',
            '',
            '',
            'class SelfHealingScript:',
            '    """Self-healing automation script"""',
            '    ',
            '    def __init__(self, page: Page, script_path: str):',
            '        self.page = page',
            '        self.script_path = script_path',
            '        self.browser_use = None',
            '        self.mcp_service = None',
            '        self.healing_enabled = HEALING_AVAILABLE',
            '        ',
            '    async def initialize_healing(self):',
            '        """Initialize healing services"""',
            '        if not self.healing_enabled:',
            '            return',
            '        ',
            '        try:',
            '            config_path = os.path.join(os.path.dirname(self.script_path), "..", "..", "config", "config.yaml")',
            '            if os.path.exists(config_path):',
            '                with open(config_path, "r") as f:',
            '                    config = yaml.safe_load(f)',
            '            else:',
            '                config = {"browser": {"headless": True}, "mcp": {}}',
            '            ',
            '            self.browser_use = BrowserUseService(config.get("browser", {}))',
            '            self.mcp_service = MCPServerService(config.get("mcp", {}))',
            '            print("✓ Healing services initialized")',
            '        except Exception as e:',
            '            print(f"Warning: Could not initialize healing services: {e}")',
            '            self.healing_enabled = False',
            '    ',
            '    async def heal_step(self, step_num: int, action: str, selector: str, error: str, value: str = "") -> Optional[str]:',
            '        """Attempt to heal a failed step and return new selector"""',
            '        if not self.healing_enabled:',
            '            return None',
            '        ',
            '        print(f"\\n🔧 Attempting to heal step {step_num}: {action}")',
            '        ',
            '        # Try browser-use healing',
            '        for retry in range(2):',
            '            try:',
            '                print(f"  → Browser-use healing attempt {retry + 1}/2")',
            '                ',
            '                if action == "click":',
            '                    instruction = f"Click on the element that was previously at {selector}"',
            '                elif action == "fill":',
            '                    instruction = f"Find and focus the input field that was previously at {selector}"',
            '                else:',
            '                    instruction = f"Interact with element at {selector}"',
            '                ',
            '                await self.browser_use.initialize()',
            '                result = await self.browser_use.execute_task(instruction)',
            '                ',
            '                if result.get("success"):',
            '                    print(f"  ✓ Healed via browser-use, re-executing action on page")',
            '                    # The action was performed by browser-use, now perform it on our page too',
            '                    try:',
            '                        if action == "click":',
            '                            await self.page.click(selector)',
            '                        elif action == "fill":',
            '                            await self.page.fill(selector, value)',
            '                        print(f"  ✓ Action re-executed successfully on page")',
            '                        self.update_script(step_num, selector, selector, "browser-use")',
            '                        return selector',
            '                    except Exception as page_error:',
            '                        print(f"  ✗ Failed to re-execute on page: {page_error}")',
            '                    ',
            '            except Exception as e:',
            '                print(f"  ✗ Browser-use attempt {retry + 1} failed: {e}")',
            '            ',
            '            await asyncio.sleep(1)',
            '        ',
            '        # Try MCP healing with selector discovery',
            '        try:',
            '            print(f"  → MCP healing attempt")',
            '            if self.mcp_service.start_server():',
            '                current_url = self.page.url',
            '                if self.mcp_service.navigate(current_url):',
            '                    # Try to find a better selector',
            '                    description = f"element for {action} action"',
            '                    if action == "fill" and value:',
            '                        description = f"input field for entering {value}"',
            '                    ',
            '                    new_selector = self.mcp_service.get_element_locator(description, None)',
            '                    ',
            '                    if new_selector and new_selector != selector:',
            '                        print(f"  → MCP found new selector: {new_selector}")',
            '                        # Try the new selector on our page',
            '                        try:',
            '                            if action == "click":',
            '                                await self.page.click(new_selector)',
            '                            elif action == "fill":',
            '                                await self.page.fill(new_selector, value)',
            '                            print(f"  ✓ Healed via MCP with new selector and action re-executed")',
            '                            self.update_script(step_num, selector, new_selector, "mcp")',
            '                            self.mcp_service.stop_server()',
            '                            return new_selector',
            '                        except Exception as page_error:',
            '                            print(f"  ✗ New selector failed on page: {page_error}")',
            '                    ',
            '                    # Fallback: try original selector with retry',
            '                    try:',
            '                        if action == "click":',
            '                            await self.page.click(selector)',
            '                        elif action == "fill":',
            '                            await self.page.fill(selector, value)',
            '                        print(f"  ✓ Healed via MCP retry with original selector")',
            '                        self.update_script(step_num, selector, selector, "mcp")',
            '                        self.mcp_service.stop_server()',
            '                        return selector',
            '                    except Exception as page_error:',
            '                        print(f"  ✗ Original selector retry failed: {page_error}")',
            '                        ',
            '                self.mcp_service.stop_server()',
            '        except Exception as e:',
            '            print(f"  ✗ MCP healing failed: {e}")',
            '        ',
            '        print(f"  ✗ All healing attempts failed")',
            '        return None',
            '    ',
            '    def update_script(self, step_num: int, old_selector: str, new_selector: str, healing_source: str):',
            '        """Update this script file with healed selector"""',
            '        try:',
            '            with open(self.script_path, "r") as f:',
            '                lines = f.readlines()',
            '            ',
            '            # Find and update the step',
            '            step_comment = f"# Step {step_num}:"',
            '            in_step = False',
            '            updated_lines = []',
            '            ',
            '            for line in lines:',
            '                if step_comment in line:',
            '                    # Update comment to show it was healed',
            '                    updated_lines.append(line.replace(step_comment, f"# Step {step_num}: (Healed via {healing_source})"))',
            '                    in_step = True',
            '                elif in_step and old_selector in line:',
            '                    # Replace old selector with new one in the actual code',
            '                    updated_lines.append(line.replace(old_selector, new_selector))',
            '                    in_step = False',
            '                else:',
            '                    updated_lines.append(line)',
            '            ',
            '            with open(self.script_path, "w") as f:',
            '                f.writelines(updated_lines)',
            '            ',
            '            print(f"  ✓ Script updated: {old_selector} → {new_selector}")',
            '        except Exception as e:',
            '            print(f"  Warning: Could not update script: {e}")',
            '    ',
            '    async def run(self):',
            '        """Execute the automated workflow with self-healing"""',
            '        await self.initialize_healing()',
            '        ',
            '        failed_steps = []',
            '        total_steps = 0',
            '        ',
        ]
        
        # Generate steps with healing logic
        for log in action_logs:
            if log.status in ['success', 'healed']:
                total_steps += 1
                script_lines.extend(self._generate_self_healing_step_code(log))
        
        script_lines.extend([
            '        ',
            '        if failed_steps:',
            '            print(f"\\n⚠ Automation completed with {len(failed_steps)} failed step(s)")',
            '            print(f"Failed steps: {failed_steps}")',
            '            return False',
            '        else:',
            '            print("\\n✓ Automation completed successfully")',
            '            return True',
            '',
            '',
            'async def main():',
            '    """Main entry point"""',
            '    async with async_playwright() as p:',
            f'        browser = await p.chromium.launch(headless={headless})',
            '        context = await browser.new_context(',
            '            viewport={"width": 1920, "height": 1080}',
            '        )',
            '        page = await context.new_page()',
            '        ',
            '        script_path = os.path.abspath(__file__)',
            '        healer = SelfHealingScript(page, script_path)',
            '        success = await healer.run()',
            '',
            '        await page.wait_for_timeout(2000)',
            '        await browser.close()',
            '',
            '        return 0 if success else 1',
            '',
            '',
            'if __name__ == "__main__":',
            '    exit_code = asyncio.run(main())',
            '    sys.exit(exit_code)',
        ])
        
        return '\n'.join(script_lines)
    
    def _generate_self_healing_step_code(self, log: ActionLog) -> List[str]:
        """Generate code for a single step with self-healing capability"""
        lines = []
        step_num = log.step_number
        action_type = log.action_type
        locator = log.healed_locator or log.locator
        selector = self._extract_selector(locator)
        
        lines.append(f'        # Step {step_num}: {action_type}')
        if log.healing_source:
            lines.append(f'        # Previously healed via: {log.healing_source}')
        
        lines.append(f'        try:')
        
        # Generate the actual step code with try-except
        if log.url:
            lines.append(f'            print("Step {step_num}: Navigating to {log.url}")')
            lines.append(f'            await self.page.goto("{log.url}")')
            lines.append('            await self.page.wait_for_load_state("networkidle")')
        
        if action_type == 'click':
            if locator:
                lines.append(f'            print("Step {step_num}: Clicking element: {selector}")')
                lines.append(f'            await self.page.click("{selector}")')
                lines.append('            await self.page.wait_for_timeout(500)')
        
        elif action_type == 'fill':
            if locator:
                value = locator.get('value', '') if isinstance(locator, dict) else ''
                lines.append(f'            print("Step {step_num}: Filling field: {selector}")')
                lines.append(f'            await self.page.fill("{selector}", "{value}")')
                lines.append('            await self.page.wait_for_timeout(300)')
        
        elif action_type == 'select':
            if locator:
                value = locator.get('value', '') if isinstance(locator, dict) else ''
                lines.append(f'            print("Step {step_num}: Selecting option: {value}")')
                lines.append(f'            await self.page.select_option("{selector}", "{value}")')
                lines.append('            await self.page.wait_for_timeout(300)')
        
        elif action_type == 'wait':
            timeout = log.execution_time * 1000 if log.execution_time else 5000
            lines.append(f'            await self.page.wait_for_timeout({int(timeout)})')
        
        # Add healing logic with value parameter for fill/select actions
        lines.append(f'            total_steps += 1')
        lines.append(f'        except Exception as e:')
        lines.append(f'            print(f"✗ Step {step_num} failed: {{e}}")')
        lines.append(f'            ')
        lines.append(f'            # Attempt healing')
        
        # Extract value for fill/select actions to pass to heal_step
        if action_type in ['fill', 'select']:
            value_str = locator.get('value', '') if isinstance(locator, dict) else ''
            lines.append(f'            healed_selector = await self.heal_step({step_num}, "{action_type}", "{selector}", str(e), "{value_str}")')
        else:
            lines.append(f'            healed_selector = await self.heal_step({step_num}, "{action_type}", "{selector}", str(e))')
        
        lines.append(f'            ')
        lines.append(f'            if healed_selector:')
        lines.append(f'                print(f"✓ Step {step_num} healed successfully, continuing...")')
        lines.append(f'                total_steps += 1')
        lines.append(f'            else:')
        lines.append(f'                print(f"✗ Step {step_num} could not be healed, marking as failed")')
        lines.append(f'                failed_steps.append({step_num})')
        lines.append(f'                # Continue to next step despite failure')
        lines.append('')
        
        return lines
    
    def _generate_step_code(self, log: ActionLog) -> List[str]:
        """Generate code for a single step (legacy method for compatibility)"""
        lines = []
        
        lines.append(f'        # Step {log.step_number}: {log.action_type}')
        
        if log.healing_source:
            lines.append(f'        # Healed via: {log.healing_source}')
        
        locator = log.healed_locator or log.locator
        
        if log.url:
            lines.append(f'        print("Navigating to: {log.url}")')
            lines.append(f'        await page.goto("{log.url}")')
            lines.append('        await page.wait_for_load_state("networkidle")')
        
        if log.action_type == 'click':
            if locator:
                selector = self._extract_selector(locator)
                lines.append(f'        print("Clicking element: {selector}")')
                lines.append(f'        await page.click("{selector}")')
                lines.append('        await page.wait_for_timeout(500)')
        
        elif log.action_type == 'fill':
            if locator:
                selector = self._extract_selector(locator)
                value = locator.get('value', '') if isinstance(locator, dict) else ''
                lines.append(f'        print("Filling field: {selector}")')
                lines.append(f'        await page.fill("{selector}", "{value}")')
                lines.append('        await page.wait_for_timeout(300)')
        
        elif log.action_type == 'select':
            if locator:
                selector = self._extract_selector(locator)
                value = locator.get('value', '') if isinstance(locator, dict) else ''
                lines.append(f'        print("Selecting option: {value}")')
                lines.append(f'        await page.select_option("{selector}", "{value}")')
                lines.append('        await page.wait_for_timeout(300)')
        
        elif log.action_type == 'wait':
            timeout = log.execution_time * 1000 if log.execution_time else 5000
            lines.append(f'        await page.wait_for_timeout({int(timeout)})')
        
        lines.append('')
        
        return lines
    
    def _extract_selector(self, locator: Any) -> str:
        """Extract a CSS selector from locator data"""
        if isinstance(locator, dict):
            if 'value' in locator:
                return locator['value']
            if 'selector' in locator:
                return locator['selector']
            if 'css' in locator:
                return locator['css']
            if 'xpath' in locator:
                return f"xpath={locator['xpath']}"
        
        if isinstance(locator, str):
            return locator
        
        return 'body'
    
    def get_script_path(self, task_id: int) -> str:
        """Get the path to a generated script for a task"""
        try:
            files = os.listdir(self.output_dir)
            task_files = [f for f in files if f.startswith(f'task_{task_id}_')]
            
            if task_files:
                task_files.sort(reverse=True)
                return os.path.join(self.output_dir, task_files[0])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting script path: {e}")
            return None
