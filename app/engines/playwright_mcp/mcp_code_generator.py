"""
Playwright Code Generator for MCP Tool Calls
Converts Playwright MCP tool calls into reusable Playwright Python code

Usage:
    steps = [{"tool": "browser_navigate_to", "arguments": {"url": "..."}, ...}]
    generator = MCPCodeGenerator(steps, task_description="My task")
    code = generator.generate_python_code()
"""

import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class PlaywrightAction:
    """Represents a single Playwright action"""
    action_type: str
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    comment: Optional[str] = None
    ref: Optional[str] = None


class MCPCodeGenerator:
    """
    Generates Playwright Python code from MCP tool call steps
    
    Converts tool calls like:
    - browser_navigate_to → page.goto()
    - browser_click → page.locator().click()
    - browser_fill → page.locator().fill()
    - browser_snapshot → page content inspection
    """
    
    def __init__(self, steps: List[Dict[str, Any]], task_description: str = "MCP Automation"):
        """
        Initialize code generator
        
        Args:
            steps: List of MCP tool call steps from agent execution
            task_description: Description of what the automation does
        """
        self.steps = steps
        self.task_description = task_description
        self.actions: List[PlaywrightAction] = []
        self.locators: Dict[str, str] = {}
        
    def parse_steps(self) -> List[PlaywrightAction]:
        """
        Parse MCP tool call steps and convert to Playwright actions
        
        Returns:
            List of PlaywrightAction objects
        """
        actions = []
        
        for step in self.steps:
            tool_name = step.get('tool', '')
            arguments = step.get('arguments', {})
            success = step.get('success', False)
            
            if not success:
                # Include failed steps as comments for debugging
                actions.append(PlaywrightAction(
                    action_type='comment',
                    comment=f"Failed: {tool_name} - {step.get('error', 'Unknown error')}"
                ))
                continue
            
            # Convert MCP tool calls to Playwright actions
            if 'navigate' in tool_name.lower():
                url = arguments.get('url', '')
                if url:
                    actions.append(PlaywrightAction(
                        action_type='navigate',
                        url=url,
                        comment=f"Navigate to {url}"
                    ))
            
            elif 'click' in tool_name.lower():
                ref = arguments.get('ref')
                selector = arguments.get('selector')
                
                if ref:
                    # MCP uses element references like "e1", "e2"
                    actions.append(PlaywrightAction(
                        action_type='click',
                        ref=ref,
                        comment=f"Click element [ref={ref}]"
                    ))
                elif selector:
                    actions.append(PlaywrightAction(
                        action_type='click',
                        selector=selector,
                        comment=f"Click {selector}"
                    ))
                else:
                    actions.append(PlaywrightAction(
                        action_type='comment',
                        comment=f"Click action (selector not captured)"
                    ))
            
            elif 'fill' in tool_name.lower() or 'type' in tool_name.lower():
                ref = arguments.get('ref')
                selector = arguments.get('selector')
                value = arguments.get('value') or arguments.get('text', '')
                
                if (ref or selector) and value:
                    actions.append(PlaywrightAction(
                        action_type='fill',
                        selector=selector,
                        ref=ref,
                        value=value,
                        comment=f"Fill '{value}' into {selector or f'[ref={ref}]'}"
                    ))
                else:
                    actions.append(PlaywrightAction(
                        action_type='comment',
                        comment=f"Fill action: {value}"
                    ))
            
            elif 'snapshot' in tool_name.lower():
                # Snapshot is used for page inspection, convert to wait
                actions.append(PlaywrightAction(
                    action_type='wait',
                    value='1000',
                    comment='Wait for page state (snapshot taken)'
                ))
            
            elif 'press' in tool_name.lower():
                key = arguments.get('key', '')
                actions.append(PlaywrightAction(
                    action_type='press',
                    value=key,
                    comment=f"Press key: {key}"
                ))
            
            elif 'scroll' in tool_name.lower():
                actions.append(PlaywrightAction(
                    action_type='comment',
                    comment='Scroll action (implement page.evaluate for scrolling)'
                ))
            
            else:
                # Generic tool call - add as comment
                actions.append(PlaywrightAction(
                    action_type='comment',
                    comment=f"Tool: {tool_name} - {arguments}"
                ))
        
        self.actions = actions
        return actions
    
    def extract_locators(self) -> Dict[str, str]:
        """
        Extract reusable locators from actions
        
        Returns:
            Dictionary mapping locator names to selectors
        """
        seen_selectors = {}
        counter = 1
        
        for action in self.actions:
            if action.selector:
                sel = action.selector.strip()
                if sel and sel not in seen_selectors:
                    # Create a meaningful locator name
                    name = self._create_locator_name(sel, action.action_type, counter)
                    seen_selectors[sel] = name
                    counter += 1
        
        self.locators = seen_selectors
        return seen_selectors
    
    def _create_locator_name(self, selector: str, action_type: str, counter: int) -> str:
        """Create a valid Python variable name from selector"""
        # Extract meaningful parts
        if 'button' in selector.lower():
            base = 'button'
        elif 'input' in selector.lower():
            base = 'input'
        elif 'text' in selector.lower():
            base = 'link'
        elif selector.startswith('#'):
            base = selector[1:].split('[')[0]
        elif selector.startswith('.'):
            base = selector[1:].split('[')[0]
        else:
            base = action_type
        
        # Clean and format
        name = re.sub(r'[^0-9a-zA-Z_]+', '_', base).strip('_')
        name = re.sub(r'__+', '_', name)
        name = (name[:30] or f"element_{counter}").lower()
        
        if name[0].isdigit():
            name = f"loc_{name}"
        
        return name.upper()
    
    def generate_python_code(self,
                            use_locators: bool = True,
                            include_comments: bool = True,
                            async_style: bool = True) -> str:
        """
        Generate complete Playwright Python code
        
        Args:
            use_locators: Extract selectors into constants
            include_comments: Add explanatory comments
            async_style: Use async/await (recommended)
            
        Returns:
            Complete Python script as string
        """
        if not self.actions:
            self.parse_steps()
        
        if use_locators:
            self.extract_locators()
        
        code_lines = []
        
        # Header
        code_lines.append('"""')
        code_lines.append(f'{self.task_description}')
        code_lines.append('')
        code_lines.append('Generated from Playwright MCP automation')
        code_lines.append('To run: python script.py')
        code_lines.append('"""')
        code_lines.append('')
        
        # Imports
        if async_style:
            code_lines.append('import asyncio')
        code_lines.append('from playwright.async_api import async_playwright' if async_style else 'from playwright.sync_api import sync_playwright')
        code_lines.append('')
        code_lines.append('')
        
        # Locators section
        if use_locators and self.locators:
            code_lines.append('# Locators extracted from MCP automation')
            for selector, name in self.locators.items():
                code_lines.append(f'{name} = r"{selector}"')
            code_lines.append('')
            code_lines.append('')
        
        # Main function
        if async_style:
            code_lines.append('async def main():')
        else:
            code_lines.append('def main():')
        
        code_lines.append('    """Main automation function"""')
        
        # Browser setup
        if async_style:
            code_lines.append('    async with async_playwright() as p:')
            code_lines.append('        browser = await p.chromium.launch(headless=False)')
            code_lines.append('        page = await browser.new_page()')
            code_lines.append('')
        else:
            code_lines.append('    with sync_playwright() as p:')
            code_lines.append('        browser = p.chromium.launch(headless=False)')
            code_lines.append('        page = browser.new_page()')
            code_lines.append('')
        
        # Generate actions
        indent = '        '
        
        if include_comments:
            code_lines.append(f'{indent}# Automation steps')
        
        for i, action in enumerate(self.actions, 1):
            if include_comments and action.comment:
                code_lines.append(f'{indent}# Step {i}: {action.comment}')
            
            if action.action_type == 'navigate' and action.url:
                code_lines.append(f'{indent}{"await " if async_style else ""}page.goto("{action.url}")')
            
            elif action.action_type == 'click':
                if action.selector:
                    selector = self._get_locator_or_selector(action.selector, use_locators)
                    code_lines.append(f'{indent}{"await " if async_style else ""}page.locator({selector}).click()')
                elif action.ref:
                    code_lines.append(f'{indent}# Click element by reference (convert to specific selector)')
                    code_lines.append(f'{indent}# Original ref: {action.ref}')
            
            elif action.action_type == 'fill':
                if action.selector:
                    selector = self._get_locator_or_selector(action.selector, use_locators)
                    code_lines.append(f'{indent}{"await " if async_style else ""}page.locator({selector}).fill("{action.value}")')
                elif action.ref:
                    code_lines.append(f'{indent}# Fill element by reference (convert to specific selector)')
                    code_lines.append(f'{indent}# Value: {action.value}, ref: {action.ref}')
            
            elif action.action_type == 'press' and action.value:
                code_lines.append(f'{indent}{"await " if async_style else ""}page.keyboard.press("{action.value}")')
            
            elif action.action_type == 'wait' and action.value:
                code_lines.append(f'{indent}{"await " if async_style else ""}page.wait_for_timeout({action.value})')
            
            elif action.action_type == 'comment':
                code_lines.append(f'{indent}# {action.comment}')
            
            code_lines.append('')
        
        # Pause before closing
        if include_comments:
            code_lines.append(f'{indent}# Pause to review results')
        code_lines.append(f'{indent}{"await " if async_style else ""}page.wait_for_timeout(3000)')
        code_lines.append('')
        
        # Cleanup
        code_lines.append(f'{indent}{"await " if async_style else ""}browser.close()')
        code_lines.append('')
        code_lines.append('')
        
        # Runner
        code_lines.append('if __name__ == "__main__":')
        if async_style:
            code_lines.append('    asyncio.run(main())')
        else:
            code_lines.append('    main()')
        
        return '\n'.join(code_lines)
    
    def _get_locator_or_selector(self, selector: str, use_locators: bool) -> str:
        """Get locator constant name or raw selector"""
        if not use_locators or selector not in self.locators:
            return f'"{selector}"'
        
        return self.locators[selector]
    
    def save_to_file(self, filename: str, **kwargs) -> str:
        """
        Generate code and save to file
        
        Args:
            filename: Output filename
            **kwargs: Arguments passed to generate_python_code()
            
        Returns:
            Generated code
        """
        code = self.generate_python_code(**kwargs)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)
        
        return code


def generate_playwright_code_from_mcp_steps(
    steps: List[Dict[str, Any]],
    task_description: str = "MCP Automation",
    output_file: Optional[str] = None
) -> str:
    """
    Quick function to generate Playwright code from MCP steps
    
    Args:
        steps: List of MCP tool call steps
        task_description: What the automation does
        output_file: Optional file to save code to
        
    Returns:
        Generated Playwright Python code
        
    Example:
        result = agent.execute_instruction("Go to Google")
        code = generate_playwright_code_from_mcp_steps(
            result['steps'],
            task_description="Google navigation",
            output_file="google_nav.py"
        )
    """
    generator = MCPCodeGenerator(steps, task_description)
    
    if output_file:
        return generator.save_to_file(output_file)
    
    return generator.generate_python_code()
