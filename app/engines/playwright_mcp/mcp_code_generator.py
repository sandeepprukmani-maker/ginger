"""
Playwright Code Generator for MCP Tool Calls
Converts Playwright MCP tool calls into reusable Playwright Python code with role-based locators

Usage:
    steps = [{"tool": "browser_navigate_to", "arguments": {"url": "..."}, ...}]
    generator = MCPCodeGenerator(steps, task_description="My task")
    code = generator.generate_python_code()
"""

import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ElementMetadata:
    """Metadata about an element from MCP snapshot"""
    ref: str
    role: Optional[str] = None
    name: Optional[str] = None
    text: Optional[str] = None
    tag: Optional[str] = None
    aria_label: Optional[str] = None
    placeholder: Optional[str] = None
    type_attr: Optional[str] = None
    
    def to_playwright_locator(self, fallback_selector: Optional[str] = None) -> str:
        """Convert element metadata to best-practice Playwright locator"""
        # Prioritize role-based locators (best practice)
        if self.role and self.name:
            return f'page.get_by_role("{self.role}", name="{self._escape(self.name)}")'
        elif self.role and self.text:
            return f'page.get_by_role("{self.role}", name="{self._escape(self.text)}")'
        elif self.role:
            return f'page.get_by_role("{self.role}")'
        
        # Use semantic locators
        if self.aria_label:
            return f'page.get_by_label("{self._escape(self.aria_label)}")'
        if self.placeholder:
            return f'page.get_by_placeholder("{self._escape(self.placeholder)}")'
        if self.text and len(self.text) < 100:
            return f'page.get_by_text("{self._escape(self.text)}")'
        
        # Fallback to provided selector or generic locator
        if fallback_selector:
            return f'page.locator("{self._escape(fallback_selector)}")'
        
        # Last resort: use ref as comment
        return None
    
    def _escape(self, text: str) -> str:
        """Escape quotes in text"""
        if not text:
            return ""
        return text.replace('"', '\\"').replace('\n', ' ').strip()


@dataclass
class PlaywrightAction:
    """Represents a single Playwright action with enhanced metadata"""
    action_type: str
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    comment: Optional[str] = None
    ref: Optional[str] = None
    element_meta: Optional[ElementMetadata] = None
    locator_code: Optional[str] = None


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
        self.element_metadata: Dict[str, ElementMetadata] = {}
        self.snapshot_cache: Dict[str, Any] = {}
        
    def _extract_element_metadata_from_snapshot(self, snapshot_result: Any) -> None:
        """Extract element metadata from MCP snapshot result"""
        if not snapshot_result or not isinstance(snapshot_result, dict):
            return
        
        content = snapshot_result.get('content', [])
        if not content:
            return
        
        # MCP snapshots can have text content with YAML-like element references
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                text = item.get('text', '')
                # Parse element references from snapshot text
                # Format: [ref=e1] role=button name="Submit"
                self._parse_snapshot_elements(text)
    
    def _parse_snapshot_elements(self, snapshot_text: str) -> None:
        """Parse element references from snapshot text"""
        if not snapshot_text:
            return
        
        # Look for element patterns like [ref=e1] role=button name="Submit" aria-label="..." placeholder="..."
        lines = snapshot_text.split('\n')
        for line in lines:
            ref_match = re.search(r'\[ref=([^\]]+)\]', line)
            if ref_match:
                ref = ref_match.group(1)
                
                # Extract various attributes from the snapshot line
                role_match = re.search(r'\brole[=:](\w+)', line, re.IGNORECASE)
                name_match = re.search(r'\bname[=:]"([^"]*)"', line, re.IGNORECASE)
                text_match = re.search(r'\btext[=:]"([^"]*)"', line, re.IGNORECASE)
                aria_label_match = re.search(r'\baria-label[=:]"([^"]*)"', line, re.IGNORECASE)
                placeholder_match = re.search(r'\bplaceholder[=:]"([^"]*)"', line, re.IGNORECASE)
                tag_match = re.search(r'\btag[=:](\w+)', line, re.IGNORECASE)
                type_match = re.search(r'\btype[=:]"?(\w+)"?', line, re.IGNORECASE)
                
                meta = ElementMetadata(
                    ref=ref,
                    role=role_match.group(1) if role_match else None,
                    name=name_match.group(1) if name_match else None,
                    text=text_match.group(1) if text_match else None,
                    aria_label=aria_label_match.group(1) if aria_label_match else None,
                    placeholder=placeholder_match.group(1) if placeholder_match else None,
                    tag=tag_match.group(1) if tag_match else None,
                    type_attr=type_match.group(1) if type_match else None
                )
                
                self.element_metadata[ref] = meta
    
    def parse_steps(self) -> List[PlaywrightAction]:
        """
        Parse MCP tool call steps and convert to Playwright actions with element metadata
        
        Returns:
            List of PlaywrightAction objects
        """
        actions = []
        
        # First pass: extract element metadata from snapshots
        for step in self.steps:
            if 'snapshot' in step.get('tool', '').lower():
                result = step.get('result')
                if result:
                    self._extract_element_metadata_from_snapshot(result)
        
        # Second pass: convert steps to actions
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
                
                element_meta = None
                locator_code = None
                comment = "Click action"
                
                if ref and ref in self.element_metadata:
                    element_meta = self.element_metadata[ref]
                    locator_code = element_meta.to_playwright_locator(fallback_selector=selector)
                    comment = f"Click {element_meta.role or 'element'}"
                    if element_meta.name:
                        comment += f" '{element_meta.name}'"
                    # If metadata didn't produce a locator, use placeholder
                    if not locator_code:
                        locator_code = f'page.locator("[data-testid=\\"{ref}\\"]")'
                        comment += " - TODO: Replace placeholder selector"
                elif selector:
                    # Use the MCP-provided selector directly
                    comment = f"Click element: {selector}"
                    locator_code = f'page.locator("{selector}")'
                elif ref:
                    # No metadata and no selector - create a placeholder that will run but needs replacement
                    comment = f"Click element [ref={ref}] - TODO: Replace placeholder selector"
                    locator_code = f'page.locator("[data-testid=\\"{ref}\\"]")'
                else:
                    # Absolute fallback - should rarely happen
                    comment = "Click action - TODO: Update this generic selector"
                    locator_code = 'page.locator("body")'
                
                actions.append(PlaywrightAction(
                    action_type='click',
                    ref=ref,
                    selector=selector,
                    element_meta=element_meta,
                    locator_code=locator_code,
                    comment=comment
                ))
            
            elif 'fill' in tool_name.lower() or 'type' in tool_name.lower():
                ref = arguments.get('ref')
                selector = arguments.get('selector')
                value = arguments.get('value') or arguments.get('text', '')
                
                element_meta = None
                locator_code = None
                comment = "Fill action"
                
                if ref and ref in self.element_metadata:
                    element_meta = self.element_metadata[ref]
                    locator_code = element_meta.to_playwright_locator(fallback_selector=selector)
                    comment = f"Fill '{value}' into {element_meta.role or 'element'}"
                    if element_meta.name:
                        comment += f" '{element_meta.name}'"
                    # If metadata didn't produce a locator, use placeholder
                    if not locator_code:
                        locator_code = f'page.locator("[data-testid=\\"{ref}\\"]")'
                        comment += " - TODO: Replace placeholder selector"
                elif selector:
                    # Use the MCP-provided selector directly
                    comment = f"Fill '{value}' into element: {selector}"
                    locator_code = f'page.locator("{selector}")'
                elif ref:
                    # No metadata and no selector - create a placeholder that will run but needs replacement
                    comment = f"Fill '{value}' into [ref={ref}] - TODO: Replace placeholder selector"
                    locator_code = f'page.locator("[data-testid=\\"{ref}\\"]")'
                else:
                    # Absolute fallback - should rarely happen
                    comment = f"Fill '{value}' - TODO: Update this generic selector"
                    locator_code = 'page.locator("input")'
                
                # Always create a fill action, even if we need a TODO locator
                actions.append(PlaywrightAction(
                    action_type='fill',
                    selector=selector,
                    ref=ref,
                    value=value,
                    element_meta=element_meta,
                    locator_code=locator_code,
                    comment=comment
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
                            test_framework: bool = True,
                            include_comments: bool = True,
                            async_style: bool = True) -> str:
        """
        Generate complete Playwright Python code with proper test structure
        
        Args:
            test_framework: Use pytest-playwright framework (recommended)
            include_comments: Add explanatory comments
            async_style: Use async/await (recommended)
            
        Returns:
            Complete Python script as string
        """
        if not self.actions:
            self.parse_steps()
        
        code_lines = []
        
        # Header
        code_lines.append('"""')
        code_lines.append(f'{self.task_description}')
        code_lines.append('')
        code_lines.append('Generated from Playwright MCP automation')
        code_lines.append('Uses role-based locators following Playwright best practices')
        code_lines.append('')
        if test_framework:
            code_lines.append('To run: pytest test_automation.py')
            code_lines.append('To run headed: pytest test_automation.py --headed')
        else:
            code_lines.append('To run: python script.py')
        code_lines.append('"""')
        code_lines.append('')
        
        # Imports
        if test_framework:
            code_lines.append('import pytest')
            code_lines.append('from playwright.sync_api import Page, expect')
            code_lines.append('')
            code_lines.append('')
        else:
            if async_style:
                code_lines.append('import asyncio')
            code_lines.append('from playwright.async_api import async_playwright' if async_style else 'from playwright.sync_api import sync_playwright')
            code_lines.append('')
            code_lines.append('')
        
        if test_framework:
            # Generate pytest test function
            code_lines.append('def test_automation(page: Page):')
            code_lines.append(f'    """Test: {self.task_description}"""')
            code_lines.append('')
            indent = '    '
        else:
            # Generate standalone script
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
            
            indent = '        '
        
        # Generate actions
        
        if include_comments:
            code_lines.append(f'{indent}# Automation steps')
        
        for i, action in enumerate(self.actions, 1):
            if include_comments and action.comment:
                code_lines.append(f'{indent}# Step {i}: {action.comment}')
            
            if action.action_type == 'navigate' and action.url:
                await_prefix = "" if test_framework else ("await " if async_style else "")
                code_lines.append(f'{indent}{await_prefix}page.goto("{action.url}")')
            
            elif action.action_type == 'click':
                await_prefix = "" if test_framework else ("await " if async_style else "")
                if action.locator_code:
                    # Use the pre-generated locator code with role-based selectors
                    code_lines.append(f'{indent}{await_prefix}{action.locator_code}.click()')
                else:
                    code_lines.append(f'{indent}# TODO: Click action - add proper selector')
            
            elif action.action_type == 'fill':
                await_prefix = "" if test_framework else ("await " if async_style else "")
                if action.locator_code and action.value is not None:
                    # Use the pre-generated locator code with role-based selectors
                    escaped_value = action.value.replace('"', '\\"').replace('\n', '\\n')
                    code_lines.append(f'{indent}{await_prefix}{action.locator_code}.fill("{escaped_value}")')
                else:
                    code_lines.append(f'{indent}# TODO: Fill action - add proper selector')
            
            elif action.action_type == 'press' and action.value:
                await_prefix = "" if test_framework else ("await " if async_style else "")
                code_lines.append(f'{indent}{await_prefix}page.keyboard.press("{action.value}")')
            
            elif action.action_type == 'wait' and action.value:
                await_prefix = "" if test_framework else ("await " if async_style else "")
                code_lines.append(f'{indent}{await_prefix}page.wait_for_timeout({action.value})')
            
            elif action.action_type == 'comment':
                code_lines.append(f'{indent}# {action.comment}')
            
            code_lines.append('')
        
        if not test_framework:
            # Pause before closing (only for standalone scripts)
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
