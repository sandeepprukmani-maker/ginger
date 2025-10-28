"""
Generator Agent - Converts plans to executable Python Playwright code with rich, robust locators
Based on Playwright's pwt-generator.agent.md
"""
import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class GeneratorAgent:
    """
    Playwright Test Generator that converts execution plans into Python Playwright code.
    
    Creates robust, reusable code with:
    1. Rich locators (role, text, label-based instead of CSS selectors)
    2. Proper waits and synchronization
    3. Error handling and verification
    4. Clean, well-commented Python code
    """
    
    # Mapping from locator strategy to Playwright methods
    LOCATOR_STRATEGIES = {
        'role': 'get_by_role',
        'text': 'get_by_text',
        'label': 'get_by_label',
        'placeholder': 'get_by_placeholder',
        'testid': 'get_by_test_id',
        'title': 'get_by_title',
        'alt': 'get_by_alt_text',
        'auto': 'locator'  # fallback
    }
    
    def __init__(self, engine):
        """
        Initialize Generator Agent
        
        Args:
            engine: The browser automation engine
        """
        self.engine = engine
        
    async def generate_code(self, plan: Dict[str, Any], headless: bool = False) -> str:
        """
        Generate Python Playwright code from an execution plan with rich locators
        
        Args:
            plan: Execution plan from Planner
            headless: Whether to run in headless mode
            
        Returns:
            Python Playwright code as a string
        """
        logger.info(f"🎭 Generator Agent: Generating robust code for '{plan.get('scenario_name', 'Unknown')}'")
        
        try:
            # Generate step-by-step code with rich locators
            steps_code = self._generate_steps_with_rich_locators(plan.get('steps', []))
            
            # Build the complete script
            script = self._build_production_script(
                description=plan.get('description', 'Automation script'),
                scenario_name=plan.get('scenario_name', 'automation'),
                url=plan.get('url'),
                steps_code=steps_code,
                headless=headless
            )
            
            logger.info(f"✅ Robust code generated ({len(script)} characters) with rich locators")
            return script
            
        except Exception as e:
            logger.error(f"❌ Generator failed: {e}", exc_info=True)
            return self._generate_fallback_code(plan, headless)
    
    def _generate_steps_with_rich_locators(self, steps: List[Dict[str, Any]]) -> str:
        """
        Generate Python code for each step using rich, reusable locators
        
        Args:
            steps: List of step dictionaries from plan
            
        Returns:
            Python code for all steps with robust locators
        """
        code_lines = []
        
        for step in steps:
            step_num = step.get('step_number', 0)
            action = step.get('action', 'execute').lower()
            target = step.get('target', '')
            value = step.get('value', '')
            expected = step.get('expected_result', '')
            locator_strategy = step.get('locator_strategy', 'auto')
            
            # Add step comment
            code_lines.append(f"            # Step {step_num}: {step.get('action', 'Execute')} - {target}")
            
            # Generate code based on action type
            if action == 'navigate':
                code_lines.extend(self._gen_navigate_code(target))
                
            elif action == 'click':
                code_lines.extend(self._gen_click_code(target, locator_strategy))
                
            elif action == 'fill':
                code_lines.extend(self._gen_fill_code(target, value, locator_strategy))
                
            elif action == 'select':
                code_lines.extend(self._gen_select_code(target, value, locator_strategy))
                
            elif action == 'verify':
                code_lines.extend(self._gen_verify_code(target, locator_strategy))
                
            elif action == 'wait':
                code_lines.extend(self._gen_wait_code(target))
                
            else:
                # Generic action
                code_lines.append(f"            # Action: {action} on {target}")
                code_lines.append("            page.wait_for_timeout(1000)")
            
            # Add verification comment if specified
            if expected:
                code_lines.append(f"            # Expected: {expected}")
            
            code_lines.append("")  # Blank line between steps
        
        return "\n".join(code_lines)
    
    def _gen_navigate_code(self, url: str) -> List[str]:
        """Generate navigation code with proper waits"""
        return [
            f'            page.goto("{url}")',
            '            page.wait_for_load_state("networkidle", timeout=30000)',
        ]
    
    def _gen_click_code(self, target: str, strategy: str = 'auto') -> List[str]:
        """
        Generate click code with rich locators
        
        Uses role-based and text-based locators for maximum robustness
        """
        locator_code = self._create_rich_locator(target, strategy, action='click')
        
        return [
            f'            # Using rich locator strategy: {strategy}',
            f'            locator = {locator_code}',
            '            expect(locator).to_be_visible(timeout=10000)',
            '            locator.click()',
            '            page.wait_for_load_state("domcontentloaded")',
        ]
    
    def _gen_fill_code(self, target: str, value: str, strategy: str = 'label') -> List[str]:
        """
        Generate fill/input code with rich locators
        
        Prefers label-based locators for inputs, falls back to placeholder or role
        """
        locator_code = self._create_rich_locator(target, strategy, action='fill')
        
        # Use environment variable or placeholder for sensitive data
        if 'password' in target.lower():
            value_code = 'os.environ.get("TEST_PASSWORD", "test_password")'
        elif 'email' in target.lower() or 'username' in target.lower():
            value_code = 'os.environ.get("TEST_EMAIL", "test@example.com")'
        else:
            value_code = f'"{value}"'
        
        return [
            f'            # Using rich locator strategy: {strategy}',
            f'            input_field = {locator_code}',
            '            expect(input_field).to_be_visible(timeout=10000)',
            f'            input_field.fill({value_code})',
            '            page.wait_for_timeout(500)  # Allow for input processing',
        ]
    
    def _gen_select_code(self, target: str, value: str, strategy: str = 'label') -> List[str]:
        """Generate select/dropdown code with rich locators"""
        locator_code = self._create_rich_locator(target, strategy, action='select')
        
        return [
            f'            # Using rich locator strategy: {strategy}',
            f'            select_field = {locator_code}',
            '            expect(select_field).to_be_visible(timeout=10000)',
            f'            select_field.select_option(label="{value}")',
        ]
    
    def _gen_verify_code(self, target: str, strategy: str = 'text') -> List[str]:
        """Generate verification code"""
        locator_code = self._create_rich_locator(target, strategy, action='verify')
        
        return [
            f'            # Verification using {strategy} locator',
            f'            expect({locator_code}).to_be_visible(timeout=10000)',
        ]
    
    def _gen_wait_code(self, target: str) -> List[str]:
        """Generate wait code"""
        # Extract timeout if specified
        timeout_match = re.search(r'(\d+)\s*(s|sec|second|ms|millisecond)', target.lower())
        if timeout_match:
            amount = int(timeout_match.group(1))
            unit = timeout_match.group(2)
            if unit in ['s', 'sec', 'second']:
                ms = amount * 1000
            else:
                ms = amount
        else:
            ms = 2000  # Default 2 seconds
        
        return [
            f'            page.wait_for_timeout({ms})  # Wait for: {target}',
        ]
    
    def _create_rich_locator(self, target: str, strategy: str, action: str = '') -> str:
        """
        Create a rich, robust Playwright locator based on the strategy
        
        Prioritizes semantic locators over fragile CSS selectors:
        - role: Most semantic (buttons, links, headings, etc.)
        - text: Content-based (very robust)
        - label: Form inputs (associated with label tags)
        - placeholder: Form inputs with placeholder text
        
        Args:
            target: Description of the element
            strategy: Preferred locator strategy
            action: The action being performed (for context)
            
        Returns:
            Python code string for the locator
        """
        # Normalize target
        target_lower = target.lower()
        
        # Choose the best locator method
        if strategy == 'role':
            role = self._infer_role_from_target(target, action)
            name = self._extract_element_name(target)
            if name:
                return f'page.get_by_role("{role}", name="{name}")'
            else:
                return f'page.get_by_role("{role}").first'
        
        elif strategy == 'text':
            text = self._extract_element_name(target)
            # Use partial matching for robustness
            return f'page.get_by_text("{text}", exact=False)'
        
        elif strategy == 'label':
            label = self._extract_element_name(target)
            return f'page.get_by_label("{label}", exact=False)'
        
        elif strategy == 'placeholder':
            placeholder = self._extract_element_name(target)
            return f'page.get_by_placeholder("{placeholder}", exact=False)'
        
        elif strategy == 'testid':
            test_id = self._slugify(target)
            return f'page.get_by_test_id("{test_id}")'
        
        else:  # auto or fallback
            # Try to auto-detect the best strategy
            if any(kw in target_lower for kw in ['button', 'btn', 'click']):
                return self._create_rich_locator(target, 'role', action)
            elif any(kw in target_lower for kw in ['input', 'field', 'textbox', 'enter']):
                return self._create_rich_locator(target, 'label', action)
            elif any(kw in target_lower for kw in ['link', 'href']):
                return self._create_rich_locator(target, 'role', action)
            else:
                # Fallback to text-based locator
                text = self._extract_element_name(target)
                return f'page.locator("text={text}").first'
    
    def _infer_role_from_target(self, target: str, action: str) -> str:
        """Infer ARIA role from target description"""
        target_lower = target.lower()
        
        # Role mapping
        if any(kw in target_lower for kw in ['button', 'btn', 'submit', 'cancel']):
            return 'button'
        elif any(kw in target_lower for kw in ['link', 'href', 'anchor']):
            return 'link'
        elif any(kw in target_lower for kw in ['heading', 'title', 'header']):
            return 'heading'
        elif any(kw in target_lower for kw in ['textbox', 'input', 'field']):
            return 'textbox'
        elif any(kw in target_lower for kw in ['checkbox', 'check']):
            return 'checkbox'
        elif any(kw in target_lower for kw in ['radio']):
            return 'radio'
        elif any(kw in target_lower for kw in ['select', 'dropdown', 'combobox']):
            return 'combobox'
        else:
            # Default based on action
            if action == 'click':
                return 'button'
            elif action == 'fill':
                return 'textbox'
            else:
                return 'button'
    
    def _extract_element_name(self, target: str) -> str:
        """Extract meaningful name/text from target description"""
        # Remove common descriptive words
        noise_words = ['the', 'a', 'an', 'button', 'link', 'field', 'input', 'element', 
                       'box', 'area', 'text', 'form', 'select', 'dropdown']
        
        words = target.split()
        filtered = [w for w in words if w.lower() not in noise_words]
        
        if filtered:
            return ' '.join(filtered).strip()
        else:
            return target.strip()
    
    def _slugify(self, text: str) -> str:
        """Convert text to slug format for test IDs"""
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def _build_production_script(self, description: str, scenario_name: str, 
                                 url: str, steps_code: str, headless: bool) -> str:
        """
        Build a production-ready Python Playwright script
        
        Args:
            description: Script description
            scenario_name: Name of the scenario
            url: Starting URL (optional)
            steps_code: Generated code for all steps
            headless: Whether to run headless
            
        Returns:
            Complete Python script with imports and structure
        """
        # Sanitize scenario name for use in code
        safe_scenario = self._slugify(scenario_name)
        
        template = f'''"""
{description}

Generated by VisionVault AI Browser Automation
Scenario: {scenario_name}
Uses robust, reusable Playwright locators for maximum reliability
"""

from playwright.sync_api import sync_playwright, Page, expect
import sys
import os


def run_{safe_scenario}(page: Page) -> bool:
    """
    Execute the automation scenario
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
{steps_code}
        
        print("✅ Automation completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Automation failed: {{e}}")
        import traceback
        traceback.print_exc()
        
        # Capture failure context
        try:
            print(f"Current URL: {{page.url}}")
            print(f"Page title: {{page.title()}}")
        except:
            pass
        
        return False


def main():
    """
    Main entry point for the automation
    """
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless={headless})
        
        # Create context with reasonable defaults
        context = browser.new_context(
            viewport={{'width': 1920, 'height': 1080}},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        # Create page
        page = context.new_page()
        
        # Set default timeout
        page.set_default_timeout(30000)  # 30 seconds
        
        try:
            # Run the automation
            success = run_{safe_scenario}(page)
            
        finally:
            # Cleanup
            context.close()
            browser.close()
        
        return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
'''
        return template
    
    def _generate_fallback_code(self, plan: Dict[str, Any], headless: bool) -> str:
        """Generate basic fallback code if generation fails"""
        return self._build_production_script(
            description=plan.get('description', 'Automation task'),
            scenario_name=plan.get('scenario_name', 'automation'),
            url=plan.get('url'),
            steps_code='            # Automation steps would go here\n            page.wait_for_timeout(1000)',
            headless=headless
        )
