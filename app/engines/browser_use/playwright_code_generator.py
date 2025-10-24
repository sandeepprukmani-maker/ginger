"""
Playwright Code Generator for Browser-Use
Converts browser-use automation history into CI/CD-ready Playwright code with stable selectors

Usage:
    history = await agent.run(...)
    generator = PlaywrightCodeGenerator(history)
    code = generator.generate_python_code()
    print(code)
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pydantic import BaseModel
from app.engines.playwright_mcp.selector_validator import (
    SelectorValidator,
    SelectorConfidence
)


@dataclass
class PlaywrightAction:
    """Represents a single Playwright action with confidence scoring"""
    action_type: str
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    comment: Optional[str] = None
    raw_action: Optional[str] = None
    confidence: Optional[SelectorConfidence] = None
    confidence_reason: Optional[str] = None


class Locator(BaseModel):
    """Represents a reusable locator"""
    name: str
    selector: str
    action_examples: List[str] = []


class PlaywrightCodeGenerator:
    """
    Generates Playwright Python code from browser-use agent history
    
    Features:
    - Extracts actions from AgentHistoryList
    - Generates clean, maintainable Playwright code
    - Creates reusable locators
    - Includes proper async/await patterns
    - Adds comments for clarity
    """
    
    def __init__(self, history=None, task_description: str = "Automated browser task"):
        """
        Initialize code generator
        
        Args:
            history: AgentHistoryList from browser-use agent.run()
            task_description: Description of what the automation does
        """
        self.history = history
        self.task_description = task_description
        self.actions: List[PlaywrightAction] = []
        self.locators: Dict[str, Locator] = {}
        
    def parse_history(self) -> List[PlaywrightAction]:
        """
        Parse browser-use history and extract Playwright actions
        
        Returns:
            List of PlaywrightAction objects
        """
        if not self.history:
            return []
        
        actions = []
        
        # Try to get model_actions if available
        if hasattr(self.history, 'model_actions'):
            try:
                model_actions = self.history.model_actions()
                for action in model_actions:
                    pw_action = self._convert_model_action(action)
                    if pw_action:
                        actions.append(pw_action)
            except Exception as e:
                print(f"Note: Could not extract model_actions: {e}")
        
        # Fallback: parse from history.history
        if not actions and hasattr(self.history, 'history'):
            for item in self.history.history:
                pw_action = self._parse_history_item(item)
                if pw_action:
                    actions.append(pw_action)
        
        self.actions = actions
        return actions
    
    def _convert_model_action(self, action: dict) -> Optional[PlaywrightAction]:
        """Convert browser-use model action to Playwright action"""
        action_name = action.get('name', '').lower()
        params = action.get('params', {}) or {}
        
        # Navigate action
        if 'navigate' in action_name or 'goto' in action_name:
            url = params.get('url') or params.get('target')
            if url:
                return PlaywrightAction(
                    action_type='navigate',
                    url=url,
                    comment=f"Navigate to {url}",
                    raw_action=str(action)
                )
        
        # Click action
        elif 'click' in action_name:
            selector = self._extract_selector(params)
            if selector:
                confidence, reason = SelectorValidator.validate_selector(selector)
                
                # Block rejected selectors - store original for debugging but mark as rejected
                if confidence == SelectorConfidence.REJECTED:
                    return PlaywrightAction(
                        action_type='click',
                        selector=None,  # No selector for rejected actions
                        comment=f"Click - REJECTED selector '{selector}' not used: {reason}",
                        raw_action=str(action),
                        confidence=confidence,
                        confidence_reason=f"REJECTED: {selector} - {reason}"
                    )
                
                return PlaywrightAction(
                    action_type='click',
                    selector=selector,
                    comment=f"Click {selector}",
                    raw_action=str(action),
                    confidence=confidence,
                    confidence_reason=reason
                )
        
        # Type/Input action
        elif 'type' in action_name or 'input' in action_name or 'fill' in action_name:
            selector = self._extract_selector(params)
            value = params.get('text') or params.get('value') or params.get('input')
            if selector and value:
                confidence, reason = SelectorValidator.validate_selector(selector)
                
                # Block rejected selectors - store original for debugging but mark as rejected
                if confidence == SelectorConfidence.REJECTED:
                    return PlaywrightAction(
                        action_type='fill',
                        selector=None,  # No selector for rejected actions
                        value=value,
                        comment=f"Fill '{value}' - REJECTED selector '{selector}' not used: {reason}",
                        raw_action=str(action),
                        confidence=confidence,
                        confidence_reason=f"REJECTED: {selector} - {reason}"
                    )
                
                return PlaywrightAction(
                    action_type='fill',
                    selector=selector,
                    value=value,
                    comment=f"Fill '{value}' into {selector}",
                    raw_action=str(action),
                    confidence=confidence,
                    confidence_reason=reason
                )
        
        # Wait action
        elif 'wait' in action_name:
            timeout = params.get('timeout') or params.get('duration', 1000)
            return PlaywrightAction(
                action_type='wait',
                value=str(timeout),
                comment=f"Wait {timeout}ms",
                raw_action=str(action)
            )
        
        # Generic action - store for analysis
        return PlaywrightAction(
            action_type='comment',
            comment=f"Action: {action_name} - {params}",
            raw_action=str(action)
        )
    
    def _parse_history_item(self, item) -> Optional[PlaywrightAction]:
        """Parse individual history item"""
        model_output = str(getattr(item, 'model_output', ''))
        
        if not model_output or model_output == 'None':
            return None
        
        # Simple heuristic parsing
        model_lower = model_output.lower()
        
        # Navigation
        if 'goto' in model_lower or 'navigate' in model_lower:
            # Try to extract URL
            url_match = re.search(r'https?://[^\s\'"]+', model_output)
            if url_match:
                return PlaywrightAction(
                    action_type='navigate',
                    url=url_match.group(0),
                    raw_action=model_output
                )
        
        # Click
        elif 'click' in model_lower:
            return PlaywrightAction(
                action_type='click',
                comment=f"Extracted from: {model_output[:100]}",
                raw_action=model_output
            )
        
        # Type/Fill
        elif any(word in model_lower for word in ['type', 'fill', 'input', 'enter']):
            return PlaywrightAction(
                action_type='fill',
                comment=f"Extracted from: {model_output[:100]}",
                raw_action=model_output
            )
        
        # Store as comment for manual review
        return PlaywrightAction(
            action_type='comment',
            comment=f"Step: {model_output[:150]}",
            raw_action=model_output
        )
    
    def _extract_selector(self, params: dict) -> Optional[str]:
        """Extract selector from action parameters"""
        keys_to_check = [
            'selector', 'index_selector', 'css', 'xpath', 
            'aria', 'text', 'query', 'target', 'element'
        ]
        
        for key in keys_to_check:
            value = params.get(key)
            if value and str(value).strip():
                return str(value).strip()
        
        return None
    
    def _normalize_locator_name(self, selector: str) -> str:
        """Create a valid Python variable name from selector"""
        # Remove special characters
        name = re.sub(r'[^0-9a-zA-Z_]+', '_', selector).strip('_')
        # Remove multiple underscores
        name = re.sub(r'__+', '_', name)
        # Truncate and ensure it's not empty
        name = (name[:50] or "locator").lower()
        # Ensure it doesn't start with a number
        if name[0].isdigit():
            name = f"loc_{name}"
        return name
    
    def extract_locators(self) -> Dict[str, Locator]:
        """Extract reusable locators from actions"""
        seen: Dict[str, Locator] = {}
        
        for action in self.actions:
            if not action.selector:
                continue
            
            sel = action.selector.strip()
            name_base = self._normalize_locator_name(sel)
            name = name_base
            idx = 1
            
            # Handle duplicates
            while name in seen:
                idx += 1
                name = f"{name_base}_{idx}"
            
            seen[name] = Locator(
                name=name,
                selector=sel,
                action_examples=[f"{action.action_type}({action.comment or sel})"]
            )
        
        self.locators = seen
        return seen
    
    def generate_python_code(self, 
                           use_locators: bool = True,
                           include_comments: bool = True,
                           async_style: bool = True,
                           test_framework: bool = True) -> str:
        """
        Generate CI/CD-ready Playwright Python code with explicit waits and confidence scoring
        
        Args:
            use_locators: Extract selectors into constants
            include_comments: Add explanatory comments
            async_style: Use async/await (recommended)
            test_framework: Use pytest-playwright framework (recommended for CI/CD)
            
        Returns:
            Complete Python script as string
        """
        if not self.actions:
            self.parse_history()
        
        if use_locators:
            self.extract_locators()
        
        code_lines = []
        
        # Header
        code_lines.append('"""')
        code_lines.append(f'{self.task_description}')
        code_lines.append('')
        code_lines.append('Generated from browser-use automation')
        code_lines.append('Uses stable selectors and explicit waits for CI/CD reliability')
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
        
        # Locators section
        if use_locators and self.locators:
            code_lines.append('# Locators extracted from automation')
            for name, locator in self.locators.items():
                examples = ', '.join(locator.action_examples)[:100]
                code_lines.append(f'{name.upper()} = r"{locator.selector}"  # {examples}')
            code_lines.append('')
            code_lines.append('')
        
        # Main function or pytest test
        if test_framework:
            code_lines.append('def test_automation(page: Page):')
            code_lines.append(f'    """Test: {self.task_description}"""')
            code_lines.append('')
            indent = '    '
        else:
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
        
        # Generate actions with CI/CD-ready error handling and waits
        if include_comments:
            code_lines.append(f'{indent}# Automation steps with explicit waits and error handling')
        code_lines.append('')
        
        for i, action in enumerate(self.actions, 1):
            if include_comments and action.comment:
                code_lines.append(f'{indent}# Step {i}: {action.comment}')
            
            # Add confidence warnings
            if action.confidence and action.confidence_reason and include_comments:
                if action.confidence == SelectorConfidence.HIGH:
                    code_lines.append(f'{indent}# ✅ Selector confidence: HIGH - {action.confidence_reason}')
                elif action.confidence == SelectorConfidence.MEDIUM:
                    code_lines.append(f'{indent}# ⚠️  Selector confidence: MEDIUM - {action.confidence_reason}')
                elif action.confidence == SelectorConfidence.LOW:
                    code_lines.append(f'{indent}# ⚠️  Selector confidence: LOW - {action.confidence_reason}')
                elif action.confidence == SelectorConfidence.REJECTED:
                    code_lines.append(f'{indent}# ❌ WARNING: REJECTED selector - {action.confidence_reason}')
            
            if action.action_type == 'navigate' and action.url:
                await_prefix = "" if test_framework else ("await " if async_style else "")
                code_lines.append(f'{indent}{await_prefix}page.goto("{action.url}", wait_until="domcontentloaded")')
                code_lines.append(f'{indent}{await_prefix}page.wait_for_load_state("networkidle")')
            
            elif action.action_type == 'click' and action.selector:
                # Skip executable code for rejected selectors
                if action.confidence == SelectorConfidence.REJECTED:
                    code_lines.append(f'{indent}# TODO: Replace rejected selector and implement click action')
                else:
                    await_prefix = "" if test_framework else ("await " if async_style else "")
                    selector = self._get_locator_or_selector(action.selector, use_locators)
                    locator_var = f'locator_{i}'
                    code_lines.append(f'{indent}{locator_var} = page.locator({selector})')
                    code_lines.append(f'{indent}{await_prefix}expect({locator_var}).to_be_visible()')
                    code_lines.append(f'{indent}{await_prefix}{locator_var}.click()')
            
            elif action.action_type == 'fill' and action.selector and action.value:
                # Skip executable code for rejected selectors
                if action.confidence == SelectorConfidence.REJECTED:
                    code_lines.append(f'{indent}# TODO: Replace rejected selector and implement fill action for: {action.value}')
                else:
                    await_prefix = "" if test_framework else ("await " if async_style else "")
                    selector = self._get_locator_or_selector(action.selector, use_locators)
                    locator_var = f'locator_{i}'
                    code_lines.append(f'{indent}{locator_var} = page.locator({selector})')
                    code_lines.append(f'{indent}{await_prefix}expect({locator_var}).to_be_visible()')
                    code_lines.append(f'{indent}{await_prefix}{locator_var}.fill("{action.value}")')
            
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
        if not use_locators:
            return f'"{selector}"'
        
        # Find matching locator
        for name, locator in self.locators.items():
            if locator.selector == selector:
                return name.upper()
        
        # Fallback to raw selector
        return f'"{selector}"'
    
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


# Convenience function
def generate_playwright_code_from_history(history, 
                                         task_description: str = "Automated task",
                                         output_file: Optional[str] = None) -> str:
    """
    Quick function to generate Playwright code from browser-use history
    
    Args:
        history: AgentHistoryList from browser-use
        task_description: What the automation does
        output_file: Optional file to save code to
        
    Returns:
        Generated Playwright Python code
        
    Example:
        history = await agent.run()
        code = generate_playwright_code_from_history(history, output_file="automation.py")
        print(code)
    """
    generator = PlaywrightCodeGenerator(history, task_description)
    
    if output_file:
        return generator.save_to_file(output_file)
    
    return generator.generate_python_code()
