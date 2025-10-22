import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LocatorStrategy:
    """Represents a locator with multiple fallback strategies"""
    primary: str
    fallbacks: List[str]
    description: str


class PlaywrightCodeGenerator:
    """Converts browser-use action history to reusable Playwright Python code"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.actions: List[Dict[str, Any]] = []
        self.imports = set([
            "import asyncio",
            "from playwright.async_api import async_playwright, Page, Browser, Locator",
            "from typing import Optional",
        ])
    
    def parse_history(self, history) -> None:
        """Parse browser-use history and extract actions"""
        if not history:
            return
        
        if self.verbose:
            print("🔍 Parsing action history...")
        
        if hasattr(history, 'model_actions'):
            model_actions = history.model_actions()
            for action in model_actions:
                self._extract_action(action)
        elif hasattr(history, 'history') and history.history:
            for item in history.history:
                self._extract_action(item)
        
        if self.verbose:
            print(f"✓ Parsed {len(self.actions)} actions")
    
    def _extract_action(self, action) -> None:
        """Extract action details from browser-use action object"""
        action_data = {
            'type': 'unknown',
            'params': {},
            'element': None,
            'locators': []
        }
        
        if hasattr(action, '__dict__'):
            action_dict = action.__dict__
        elif isinstance(action, dict):
            action_dict = action
        else:
            action_dict = {}
        
        action_type = action_dict.get('action', {}) if isinstance(action_dict.get('action'), dict) else {}
        
        if 'go_to_url' in action_dict or (isinstance(action_type, dict) and 'go_to_url' in action_type):
            url_data = action_dict.get('go_to_url', action_type.get('go_to_url', {}))
            action_data['type'] = 'goto'
            action_data['params'] = {'url': url_data.get('url', '')}
        
        elif 'click_element' in action_dict or (isinstance(action_type, dict) and 'click_element' in action_type):
            click_data = action_dict.get('click_element', action_type.get('click_element', {}))
            action_data['type'] = 'click'
            action_data['element'] = click_data.get('element', {})
            action_data['locators'] = self._generate_locators(action_data['element'])
        
        elif 'input_text' in action_dict or (isinstance(action_type, dict) and 'input_text' in action_type):
            input_data = action_dict.get('input_text', action_type.get('input_text', {}))
            action_data['type'] = 'fill'
            action_data['element'] = input_data.get('element', {})
            action_data['params'] = {'text': input_data.get('text', '')}
            action_data['locators'] = self._generate_locators(action_data['element'])
        
        elif 'extract_content' in action_dict or (isinstance(action_type, dict) and 'extract_content' in action_type):
            action_data['type'] = 'extract'
            action_data['params'] = action_dict.get('extract_content', action_type.get('extract_content', {}))
        
        if action_data['type'] != 'unknown':
            self.actions.append(action_data)
    
    def _generate_locators(self, element: Dict[str, Any]) -> List[LocatorStrategy]:
        """Generate multiple locator strategies for an element"""
        strategies = []
        
        if not element:
            return strategies
        
        text = element.get('text', '').strip()
        role = element.get('role', '').strip()
        tag = element.get('tag', '').strip()
        attributes = element.get('attributes', {})
        
        if text:
            strategies.append(LocatorStrategy(
                primary=f'page.get_by_text("{self._escape_quotes(text)}")',
                fallbacks=[
                    f'page.locator(\'text="{self._escape_quotes(text)}"\')',
                    f'page.locator(\'//*[contains(text(), "{self._escape_quotes(text)}")]\')',
                ],
                description=f"Text: {text[:50]}"
            ))
        
        if role:
            role_locator = f'page.get_by_role("{role}"'
            if text:
                role_locator += f', name="{self._escape_quotes(text)}"'
            role_locator += ')'
            
            strategies.append(LocatorStrategy(
                primary=role_locator,
                fallbacks=[f'page.locator(\'[role="{role}"]\')', ],
                description=f"Role: {role}"
            ))
        
        if attributes:
            for key, value in attributes.items():
                if key in ['id', 'data-testid', 'name', 'aria-label']:
                    if key == 'id':
                        strategies.append(LocatorStrategy(
                            primary=f'page.locator("#{value}")',
                            fallbacks=[f'page.get_by_test_id("{value}")'],
                            description=f"ID: {value}"
                        ))
                    elif key == 'data-testid':
                        strategies.append(LocatorStrategy(
                            primary=f'page.get_by_test_id("{value}")',
                            fallbacks=[f'page.locator(\'[data-testid="{value}"]\')', ],
                            description=f"Test ID: {value}"
                        ))
                    elif key == 'name':
                        strategies.append(LocatorStrategy(
                            primary=f'page.locator(\'[name="{value}"]\')',
                            fallbacks=[f'page.get_by_label("{value}")'],
                            description=f"Name: {value}"
                        ))
                    elif key == 'aria-label':
                        strategies.append(LocatorStrategy(
                            primary=f'page.get_by_label("{value}")',
                            fallbacks=[f'page.locator(\'[aria-label="{value}"]\')', ],
                            description=f"Aria-label: {value}"
                        ))
        
        if tag and not strategies:
            strategies.append(LocatorStrategy(
                primary=f'page.locator("{tag}")',
                fallbacks=[],
                description=f"Tag: {tag}"
            ))
        
        return strategies
    
    def _escape_quotes(self, text: str) -> str:
        """Escape quotes in text for code generation"""
        return text.replace('"', '\\"').replace("'", "\\'")
    
    def generate_code(self, function_name: str = "automated_task") -> str:
        """Generate complete Playwright Python code from actions"""
        if not self.actions:
            return "# No actions to generate code from"
        
        code_lines = []
        
        code_lines.extend(sorted(self.imports))
        code_lines.append("")
        code_lines.append("")
        
        code_lines.append(f"async def {function_name}():")
        code_lines.append('    """Generated Playwright automation code with self-healing support"""')
        code_lines.append("    async with async_playwright() as p:")
        code_lines.append("        browser = await p.chromium.launch(headless=False)")
        code_lines.append("        context = await browser.new_context()")
        code_lines.append("        page = await context.new_page()")
        code_lines.append("")
        code_lines.append("        try:")
        
        for i, action in enumerate(self.actions):
            code_lines.append(f"            # Step {i + 1}: {action['type']}")
            
            if action['type'] == 'goto':
                url = action['params'].get('url', '')
                code_lines.append(f'            await page.goto("{url}")')
                code_lines.append("            await page.wait_for_load_state('networkidle')")
            
            elif action['type'] == 'click':
                locators = action.get('locators', [])
                if locators:
                    primary = locators[0]
                    code_lines.append(f"            # {primary.description}")
                    code_lines.append(f"            element = await self_healing_locator(")
                    code_lines.append(f"                page,")
                    code_lines.append(f"                primary={primary.primary},")
                    fallback_str = ", ".join([f'"{fb}"' for fb in primary.fallbacks])
                    code_lines.append(f"                fallbacks=[{fallback_str}]")
                    code_lines.append(f"            )")
                    code_lines.append(f"            await element.click()")
                else:
                    code_lines.append(f"            # Unable to determine locator for click action")
            
            elif action['type'] == 'fill':
                locators = action.get('locators', [])
                text = action['params'].get('text', '')
                if locators:
                    primary = locators[0]
                    code_lines.append(f"            # {primary.description}")
                    code_lines.append(f"            element = await self_healing_locator(")
                    code_lines.append(f"                page,")
                    code_lines.append(f"                primary={primary.primary},")
                    fallback_str = ", ".join([f'"{fb}"' for fb in primary.fallbacks])
                    code_lines.append(f"                fallbacks=[{fallback_str}]")
                    code_lines.append(f"            )")
                    code_lines.append(f'            await element.fill("{self._escape_quotes(text)}")')
                else:
                    code_lines.append(f"            # Unable to determine locator for fill action")
            
            elif action['type'] == 'extract':
                code_lines.append("            # Extract content (implement based on your needs)")
                code_lines.append("            content = await page.content()")
            
            code_lines.append("")
        
        code_lines.append('            print("✅ Task completed successfully!")')
        code_lines.append("")
        code_lines.append("        except Exception as e:")
        code_lines.append('            print(f"❌ Error during automation: {e}")')
        code_lines.append("            raise")
        code_lines.append("        finally:")
        code_lines.append("            await browser.close()")
        code_lines.append("")
        code_lines.append("")
        
        code_lines.append("async def self_healing_locator(page: Page, primary: str, fallbacks: List[str] = None) -> Locator:")
        code_lines.append('    """Try primary locator, fall back to alternatives if it fails"""')
        code_lines.append("    fallbacks = fallbacks or []")
        code_lines.append("    ")
        code_lines.append("    # Try primary locator")
        code_lines.append("    try:")
        code_lines.append("        locator = eval(primary)")
        code_lines.append("        await locator.wait_for(timeout=5000)")
        code_lines.append("        return locator")
        code_lines.append("    except Exception as e:")
        code_lines.append('        print(f"⚠️  Primary locator failed: {primary}")')
        code_lines.append("    ")
        code_lines.append("    # Try fallback locators")
        code_lines.append("    for fallback in fallbacks:")
        code_lines.append("        try:")
        code_lines.append("            locator = eval(fallback)")
        code_lines.append("            await locator.wait_for(timeout=5000)")
        code_lines.append('            print(f"✓ Fallback locator succeeded: {fallback}")')
        code_lines.append("            return locator")
        code_lines.append("        except Exception:")
        code_lines.append("            continue")
        code_lines.append("    ")
        code_lines.append('    raise Exception(f"All locators failed for: {primary}")')
        code_lines.append("")
        code_lines.append("")
        code_lines.append('if __name__ == "__main__":')
        code_lines.append(f"    asyncio.run({function_name}())")
        
        return "\n".join(code_lines)
    
    def save_code(self, filepath: str, function_name: str = "automated_task") -> None:
        """Generate and save code to a file"""
        code = self.generate_code(function_name)
        with open(filepath, 'w') as f:
            f.write(code)
        
        if self.verbose:
            print(f"✓ Code saved to: {filepath}")
