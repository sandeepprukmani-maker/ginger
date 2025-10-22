"""Capture and convert browser-use actions to Playwright code."""
import logging
from typing import Any, Dict, List
from dataclasses import dataclass, field


@dataclass
class PlaywrightAction:
    """Represents a single Playwright action."""
    action_type: str
    selector: str | None = None
    value: str | None = None
    url: str | None = None
    comment: str | None = None
    tab_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ActionCapture:
    """Captures browser-use actions and converts them to Playwright format."""
    
    def __init__(self):
        self.actions: List[PlaywrightAction] = []
        self.logger = logging.getLogger(__name__)
        self.current_tab = 0
        self.tab_count = 1
        
    def capture_navigation(self, url: str, comment: str = None):
        """Capture page navigation."""
        self.actions.append(PlaywrightAction(
            action_type="goto",
            url=url,
            comment=comment or f"Navigate to {url}",
            tab_index=self.current_tab
        ))
        
    def capture_click(self, element_info: Dict[str, Any], comment: str = None):
        """Capture click action with Playwright selector."""
        selector = self._extract_playwright_selector(element_info)
        self.actions.append(PlaywrightAction(
            action_type="click",
            selector=selector,
            comment=comment or f"Click on element",
            tab_index=self.current_tab,
            metadata=element_info
        ))
        
    def capture_fill(self, element_info: Dict[str, Any], value: str, comment: str = None):
        """Capture input/fill action."""
        selector = self._extract_playwright_selector(element_info)
        self.actions.append(PlaywrightAction(
            action_type="fill",
            selector=selector,
            value=value,
            comment=comment or f"Fill input with '{value}'",
            tab_index=self.current_tab,
            metadata=element_info
        ))
        
    def capture_press(self, key: str, comment: str = None):
        """Capture keyboard press."""
        self.actions.append(PlaywrightAction(
            action_type="press",
            value=key,
            comment=comment or f"Press {key}",
            tab_index=self.current_tab
        ))
        
    def capture_scroll(self, direction: str, amount: int = None, comment: str = None):
        """Capture scroll action."""
        self.actions.append(PlaywrightAction(
            action_type="scroll",
            value=f"{direction}:{amount}" if amount else direction,
            comment=comment or f"Scroll {direction}",
            tab_index=self.current_tab
        ))
        
    def capture_wait(self, duration: int, comment: str = None):
        """Capture wait action."""
        self.actions.append(PlaywrightAction(
            action_type="wait",
            value=str(duration),
            comment=comment or f"Wait {duration}ms",
            tab_index=self.current_tab
        ))
        
    def capture_new_tab(self, comment: str = None):
        """Capture new tab creation."""
        self.tab_count += 1
        self.actions.append(PlaywrightAction(
            action_type="new_tab",
            comment=comment or "Open new tab",
            tab_index=self.current_tab
        ))
        
    def capture_switch_tab(self, tab_index: int, comment: str = None):
        """Capture tab switch."""
        self.current_tab = tab_index
        self.actions.append(PlaywrightAction(
            action_type="switch_tab",
            value=str(tab_index),
            comment=comment or f"Switch to tab {tab_index}",
            tab_index=tab_index
        ))
        
    def capture_alert(self, action: str, text: str = None, comment: str = None):
        """Capture alert handling."""
        self.actions.append(PlaywrightAction(
            action_type="alert",
            value=f"{action}:{text}" if text else action,
            comment=comment or f"Handle alert: {action}",
            tab_index=self.current_tab
        ))
        
    def _extract_playwright_selector(self, element_info: Dict[str, Any]) -> str:
        """Convert element info to Playwright selector."""
        # Priority order for selector generation
        
        # 1. Try data-testid or test attributes
        if 'data-testid' in element_info.get('attributes', {}):
            return f"[data-testid=\"{element_info['attributes']['data-testid']}\"]"
        
        # 2. Try ID
        if element_info.get('id'):
            return f"#{element_info['id']}"
        
        # 3. Try name attribute (for inputs)
        if 'name' in element_info.get('attributes', {}):
            tag = element_info.get('tag_name', 'input')
            name = element_info['attributes']['name']
            return f"{tag}[name=\"{name}\"]"
        
        # 4. Try aria-label
        if 'aria-label' in element_info.get('attributes', {}):
            label = element_info['attributes']['aria-label']
            return f"[aria-label=\"{label}\"]"
        
        # 5. Try role + accessible name
        if element_info.get('role') and element_info.get('text'):
            role = element_info['role']
            text = element_info['text'][:30]  # Truncate long text
            return f"role={role}[name=\"{text}\"]"
        
        # 6. Try placeholder (for inputs)
        if 'placeholder' in element_info.get('attributes', {}):
            placeholder = element_info['attributes']['placeholder']
            return f"[placeholder=\"{placeholder}\"]"
        
        # 7. Try class + text combination
        if element_info.get('class') and element_info.get('text'):
            classes = element_info['class'].split()[0]  # First class
            text = element_info['text'][:20]
            tag = element_info.get('tag_name', 'div')
            return f"{tag}.{classes}:has-text(\"{text}\")"
        
        # 8. Fallback to CSS selector from xpath or other info
        if element_info.get('xpath'):
            # Try to convert xpath to CSS if simple
            xpath = element_info['xpath']
            if '//' in xpath:
                parts = xpath.split('//')[-1].split('/')
                if parts:
                    return parts[0]
        
        # 9. Last resort: use tag + text
        if element_info.get('text'):
            tag = element_info.get('tag_name', '*')
            text = element_info['text'][:30]
            return f"{tag}:has-text(\"{text}\")"
        
        # 10. Ultimate fallback: tag name with index
        tag = element_info.get('tag_name', 'div')
        return f"{tag}:nth-of-type({element_info.get('index', 0)})"
    
    def get_actions(self) -> List[PlaywrightAction]:
        """Get all captured actions."""
        return self.actions
    
    def clear(self):
        """Clear all captured actions."""
        self.actions.clear()
        self.current_tab = 0
        self.tab_count = 1
