"""
Helper utilities for robust locator strategies and self-healing.
These are used when executing GENERATED Playwright code, not during initial browser-use automation.
"""

from typing import List, Dict, Optional
from playwright.async_api import Page, Locator


class LocatorBuilder:
    """Build robust locators with multiple fallback strategies"""
    
    @staticmethod
    def by_text(text: str, exact: bool = False) -> List[str]:
        """Generate text-based locator strategies"""
        escaped = text.replace('"', '\\"')
        strategies = [
            f'page.get_by_text("{escaped}", exact={exact})',
            f'page.locator(\'text={escaped}\')',
        ]
        if not exact:
            strategies.append(f'page.locator(\'//*[contains(text(), "{escaped}")]\')')
        return strategies
    
    @staticmethod
    def by_role(role: str, name: Optional[str] = None) -> List[str]:
        """Generate role-based locator strategies"""
        if name:
            name_escaped = name.replace('"', '\\"')
            return [
                f'page.get_by_role("{role}", name="{name_escaped}")',
                f'page.locator(\'[role="{role}"][aria-label="{name_escaped}"]\')',
                f'page.locator(\'[role="{role}"]\')',
            ]
        return [
            f'page.get_by_role("{role}")',
            f'page.locator(\'[role="{role}"]\')',
        ]
    
    @staticmethod
    def by_label(label: str) -> List[str]:
        """Generate label-based locator strategies"""
        escaped = label.replace('"', '\\"')
        return [
            f'page.get_by_label("{escaped}")',
            f'page.locator(\'[aria-label="{escaped}"]\')',
            f'page.locator(\'label:has-text("{escaped}")\')',
        ]
    
    @staticmethod
    def by_placeholder(placeholder: str) -> List[str]:
        """Generate placeholder-based locator strategies"""
        escaped = placeholder.replace('"', '\\"')
        return [
            f'page.get_by_placeholder("{escaped}")',
            f'page.locator(\'[placeholder="{escaped}"]\')',
        ]
    
    @staticmethod
    def by_test_id(test_id: str) -> List[str]:
        """Generate test-id based locator strategies"""
        return [
            f'page.get_by_test_id("{test_id}")',
            f'page.locator(\'[data-testid="{test_id}"]\')',
            f'page.locator(\'[data-test-id="{test_id}"]\')',
        ]
    
    @staticmethod
    def by_id(element_id: str) -> List[str]:
        """Generate id-based locator strategies"""
        return [
            f'page.locator("#{element_id}")',
            f'page.locator(\'[id="{element_id}"]\')',
        ]
    
    @staticmethod
    def by_css(selector: str) -> List[str]:
        """Generate CSS selector locator"""
        return [f'page.locator("{selector}")']
    
    @staticmethod
    def by_xpath(xpath: str) -> List[str]:
        """Generate XPath locator"""
        return [f'page.locator(\'{xpath}\')']


async def try_locator_strategies(
    page: Page,
    strategies: List[str],
    timeout: int = 5000,
    verbose: bool = False
) -> Optional[Locator]:
    """
    Try multiple locator strategies until one works.
    Used in generated code for fallback locator support.
    
    Args:
        page: Playwright page object
        strategies: List of locator strategy strings
        timeout: Timeout in milliseconds per strategy
        verbose: Print debug information
    
    Returns:
        Working Locator object, or None if all fail
    """
    for i, strategy in enumerate(strategies):
        try:
            locator = eval(strategy)
            await locator.wait_for(timeout=timeout)
            if verbose and i > 0:
                print(f"   ✓ Fallback strategy {i} worked: {strategy}")
            return locator
        except Exception:
            if verbose:
                print(f"   ⚠️  Strategy {i} failed: {strategy}")
            continue
    
    return None


class LocatorHealer:
    """
    Context information for self-healing locators.
    This is used ONLY when executing generated Playwright code.
    """
    
    @staticmethod
    def extract_element_info(locator_str: str) -> Dict[str, str]:
        """Extract information from a locator string for healing context"""
        info = {
            'type': 'unknown',
            'value': '',
            'description': ''
        }
        
        if 'get_by_text' in locator_str:
            info['type'] = 'text'
            info['description'] = 'element with text'
        elif 'get_by_role' in locator_str:
            info['type'] = 'role'
            info['description'] = 'element with role'
        elif 'get_by_label' in locator_str:
            info['type'] = 'label'
            info['description'] = 'element with label'
        elif 'get_by_placeholder' in locator_str:
            info['type'] = 'placeholder'
            info['description'] = 'input with placeholder'
        elif 'get_by_test_id' in locator_str:
            info['type'] = 'test_id'
            info['description'] = 'element with test ID'
        elif 'locator' in locator_str:
            if 'text=' in locator_str:
                info['type'] = 'text'
                info['description'] = 'element with text'
            elif '[role=' in locator_str:
                info['type'] = 'role'
                info['description'] = 'element with role'
            elif '#' in locator_str:
                info['type'] = 'id'
                info['description'] = 'element with ID'
            else:
                info['type'] = 'css'
                info['description'] = 'element matching CSS selector'
        
        return info
    
    @staticmethod
    def build_healing_task(
        locator_str: str,
        action: str,
        url: str,
        title: str
    ) -> str:
        """Build a task description for browser-use to heal a broken locator"""
        element_info = LocatorHealer.extract_element_info(locator_str)
        
        task = f"""On the current page (URL: {url}, Title: {title}), find the {element_info['description']} that we need to {action}.

The previous locator ({locator_str}) no longer works. Analyze the page and locate the correct element, then provide information about its attributes so we can create a new working locator."""
        
        return task
