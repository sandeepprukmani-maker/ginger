"""
Code Preview Service
Provides real-time code generation streaming with action history and locator quality
"""
import json
from typing import Dict, List, Optional, Generator
from app.services.locator_extractor import IntelligentLocatorExtractor


class CodePreviewService:
    """
    Service for streaming code generation with action tracking
    
    Features:
    - Real-time code generation as actions occur
    - Action history with quality scores
    - Locator extraction and confidence scoring
    - Alternative locator suggestions
    """
    
    def __init__(self):
        """Initialize the code preview service"""
        self.locator_extractor = IntelligentLocatorExtractor()
        self.actions = []
        self.current_code_lines = []
    
    def process_action(
        self,
        action_type: str,
        element_info: Optional[Dict] = None,
        value: Optional[str] = None,
        url: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """
        Process a single automation action and generate code
        
        Args:
            action_type: Type of action (click, fill, navigate, etc.)
            element_info: Element properties for locator extraction
            value: Value for fill/type actions
            url: URL for navigate actions
            description: Human-readable description
        
        Returns:
            Action result with code, locator info, and quality score
        """
        action_index = len(self.actions)
        
        # Generate Python code for this action
        code_lines = []
        locator_info = None
        
        # Extract locator if element info provided
        if element_info:
            locator_result = self.locator_extractor.extract_locator(element_info, action_type)
            quality = self.locator_extractor.get_quality_indicator(locator_result.confidence)
            
            locator_info = {
                'strategy': locator_result.strategy.value,
                'locator': locator_result.locator,
                'confidence': locator_result.confidence,
                'quality_level': quality['level'],
                'quality_color': quality['color'],
                'quality_emoji': quality['emoji'],
                'is_unique': locator_result.is_unique,
                'warnings': locator_result.warnings,
                'alternatives': [
                    {
                        'strategy': alt[0].value,
                        'locator': alt[1],
                        'confidence': alt[2]
                    }
                    for alt in locator_result.alternatives
                ]
            }
        
        # Generate code based on action type
        if action_type == 'navigate' or action_type == 'goto':
            code_lines.append(f"# {description or f'Navigate to {url}'}")
            code_lines.append(f"page.goto('{url}')")
        
        elif action_type == 'click':
            code_lines.append(f"# {description or 'Click element'}")
            if locator_info:
                code_lines.append(f"{locator_info['locator']}.click()")
                if locator_info['warnings']:
                    code_lines.append(f"# ⚠️  {locator_info['warnings'][0]}")
            else:
                code_lines.append("# TODO: Add locator for click action")
        
        elif action_type == 'fill' or action_type == 'type':
            code_lines.append(f"# {description or 'Fill input'}")
            if locator_info:
                escaped_value = value.replace("'", "\\'") if value else ""
                code_lines.append(f"{locator_info['locator']}.fill('{escaped_value}')")
            else:
                code_lines.append("# TODO: Add locator for fill action")
        
        elif action_type == 'select':
            code_lines.append(f"# {description or 'Select option'}")
            if locator_info:
                code_lines.append(f"{locator_info['locator']}.select_option('{value}')")
            else:
                code_lines.append("# TODO: Add locator for select action")
        
        elif action_type == 'check' or action_type == 'checkbox':
            code_lines.append(f"# {description or 'Check checkbox'}")
            if locator_info:
                code_lines.append(f"{locator_info['locator']}.check()")
            else:
                code_lines.append("# TODO: Add locator for checkbox action")
        
        elif action_type == 'hover':
            code_lines.append(f"# {description or 'Hover over element'}")
            if locator_info:
                code_lines.append(f"{locator_info['locator']}.hover()")
            else:
                code_lines.append("# TODO: Add locator for hover action")
        
        elif action_type == 'press':
            code_lines.append(f"# {description or 'Press key'}")
            code_lines.append(f"page.keyboard.press('{value}')")
        
        elif action_type == 'screenshot':
            code_lines.append(f"# {description or 'Take screenshot'}")
            filename = value or f'screenshot-{action_index}.png'
            code_lines.append(f"page.screenshot(path='{filename}')")
        
        elif action_type == 'wait':
            code_lines.append(f"# {description or 'Wait'}")
            timeout = int(value) if value else 1000
            code_lines.append(f"page.wait_for_timeout({timeout})")
        
        elif action_type == 'extract' or action_type == 'get_text':
            code_lines.append(f"# {description or 'Extract text'}")
            if locator_info:
                code_lines.append(f"text = {locator_info['locator']}.text_content()")
                code_lines.append(f"print(f'Extracted text: {{text}}')")
            else:
                code_lines.append("# TODO: Add locator for text extraction")
        
        else:
            code_lines.append(f"# TODO: Implement action type: {action_type}")
        
        # Create action record
        action_record = {
            'index': action_index,
            'action_type': action_type,
            'description': description or f'Step {action_index + 1}',
            'code': '\n'.join(code_lines),
            'code_lines': code_lines,
            'locator_info': locator_info,
            'value': value,
            'url': url,
            'timestamp': None  # Can be set by caller
        }
        
        self.actions.append(action_record)
        self.current_code_lines.extend(code_lines)
        
        return action_record
    
    def get_full_code(
        self,
        task_description: str = "Automated test",
        use_pytest: bool = True
    ) -> str:
        """
        Get complete test file with all actions
        
        Args:
            task_description: Description of what the test does
            use_pytest: Use pytest-playwright format
        
        Returns:
            Complete Python test file
        """
        lines = []
        
        # Header
        lines.append('"""')
        lines.append(f'{task_description}')
        lines.append('')
        lines.append('Generated by AI Browser Automation Platform')
        lines.append('Uses intelligent locators for stability')
        lines.append('"""')
        lines.append('')
        
        # Imports
        if use_pytest:
            lines.append('import pytest')
            lines.append('from playwright.sync_api import Page, expect')
            lines.append('')
            lines.append('')
            lines.append('def test_automation(page: Page):')
            lines.append(f'    """Test: {task_description}"""')
        else:
            lines.append('from playwright.sync_api import sync_playwright')
            lines.append('')
            lines.append('')
            lines.append('def main():')
            lines.append(f'    """Run automation: {task_description}"""')
            lines.append('    with sync_playwright() as p:')
            lines.append('        browser = p.chromium.launch(headless=False)')
            lines.append('        page = browser.new_page()')
        
        lines.append('')
        
        # Add actions
        indent = '    ' if use_pytest else '        '
        for action in self.actions:
            for code_line in action['code_lines']:
                lines.append(f"{indent}{code_line}")
            lines.append('')
        
        # Footer
        if not use_pytest:
            lines.append('        browser.close()')
            lines.append('')
            lines.append('')
            lines.append('if __name__ == "__main__":')
            lines.append('    main()')
        
        return '\n'.join(lines)
    
    def get_action_history(self) -> List[Dict]:
        """
        Get complete action history with quality indicators
        
        Returns:
            List of action records with locator info and quality scores
        """
        return self.actions
    
    def get_action_summary(self) -> Dict:
        """
        Get summary statistics of action quality
        
        Returns:
            Summary with quality distribution
        """
        total_actions = len(self.actions)
        
        if total_actions == 0:
            return {
                'total_actions': 0,
                'actions_with_locators': 0,
                'quality_distribution': {
                    'excellent': 0,
                    'good': 0,
                    'fair': 0,
                    'poor': 0
                },
                'average_confidence': 0.0
            }
        
        actions_with_locators = sum(1 for a in self.actions if a.get('locator_info'))
        
        quality_counts = {
            'excellent': 0,
            'good': 0,
            'fair': 0,
            'poor': 0
        }
        
        total_confidence = 0.0
        confidence_count = 0
        
        for action in self.actions:
            locator_info = action.get('locator_info')
            if locator_info:
                quality_level = locator_info['quality_level']
                quality_counts[quality_level] = quality_counts.get(quality_level, 0) + 1
                total_confidence += locator_info['confidence']
                confidence_count += 1
        
        return {
            'total_actions': total_actions,
            'actions_with_locators': actions_with_locators,
            'quality_distribution': quality_counts,
            'average_confidence': total_confidence / confidence_count if confidence_count > 0 else 0.0
        }
    
    def clear(self):
        """Clear all actions and reset state"""
        self.actions = []
        self.current_code_lines = []


def stream_code_generation(
    actions_generator: Generator[Dict, None, None],
    task_description: str = "Automated test"
) -> Generator[str, None, None]:
    """
    Stream code generation events as SSE (Server-Sent Events)
    
    Args:
        actions_generator: Generator yielding action dictionaries
        task_description: Test description
    
    Yields:
        SSE-formatted event strings
    
    Example:
        def action_generator():
            yield {'action_type': 'goto', 'url': 'https://example.com'}
            yield {'action_type': 'click', 'element': {...}}
        
        for event in stream_code_generation(action_generator()):
            print(event)
    """
    service = CodePreviewService()
    
    # Send initial event
    yield f"data: {json.dumps({'type': 'start', 'task': task_description})}\n\n"
    
    # Process each action
    for action_data in actions_generator:
        action_result = service.process_action(
            action_type=action_data.get('action_type'),
            element_info=action_data.get('element'),
            value=action_data.get('value'),
            url=action_data.get('url'),
            description=action_data.get('description')
        )
        
        # Send action event
        yield f"data: {json.dumps({'type': 'action', 'data': action_result})}\n\n"
    
    # Send summary
    summary = service.get_action_summary()
    full_code = service.get_full_code(task_description)
    
    yield f"data: {json.dumps({'type': 'summary', 'summary': summary})}\n\n"
    yield f"data: {json.dumps({'type': 'complete', 'code': full_code, 'actions': service.get_action_history()})}\n\n"
