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
        """Generate the actual Python script content"""
        
        script_lines = [
            "#!/usr/bin/env python3",
            '"""',
            f'Auto-generated Playwright script from Task #{task_id}',
            f'Generated at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            'This script uses healed locators from the self-healing automation system.',
            '"""',
            '',
            'import asyncio',
            'from playwright.async_api import async_playwright, Page',
            'import sys',
            '',
            '',
            'async def run_automation(page: Page):',
            '    """Execute the automated workflow"""',
            '    try:',
        ]
        
        for log in action_logs:
            if log.status in ['success', 'healed']:
                script_lines.extend(self._generate_step_code(log))
        
        script_lines.extend([
            '',
            '        print("✓ Automation completed successfully")',
            '        return True',
            '',
            '    except Exception as e:',
            '        print(f"✗ Error during automation: {e}")',
            '        return False',
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
            '',
            '        success = await run_automation(page)',
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
    
    def _generate_step_code(self, log: ActionLog) -> List[str]:
        """Generate code for a single step"""
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
