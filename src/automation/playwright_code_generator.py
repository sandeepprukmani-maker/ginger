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
            if self.verbose:
                print("⚠️  No history provided to parse")
            return

        if self.verbose:
            print("🔍 Parsing action history...")
            print(f"   History type: {type(history)}")
            print(f"   History attributes: {dir(history)[:10]}...")

        # For browser-use 0.5.9+, AgentHistoryList has a .history attribute containing AgentHistory objects
        # Do NOT iterate directly over AgentHistoryList as it returns tuples

        actions_found = False

        # Method 1: history.history attribute (the correct way for browser-use 0.5.9)
        if hasattr(history, 'history'):
            try:
                hist_items = history.history
                if self.verbose:
                    print(f"   Found history.history: {len(hist_items)} AgentHistory items")
                for item in hist_items:
                    if self.verbose:
                        print(f"     Processing AgentHistory item: has model_output={hasattr(item, 'model_output')}")
                    # Each item is an AgentHistory object with model_output
                    if hasattr(item, 'model_output') and item.model_output:
                        self._extract_from_agent_history(item)
                        actions_found = True
            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️  Could not access history.history: {e}")

        # Method 2: model_actions method (older browser-use versions)
        if not actions_found and hasattr(history, 'model_actions'):
            try:
                model_actions = history.model_actions()
                if self.verbose:
                    print(
                        f"   Found model_actions: {len(model_actions) if hasattr(model_actions, '__len__') else 'unknown'} items")
                for action in model_actions:
                    self._extract_action(action)
                    actions_found = True
            except Exception as e:
                if self.verbose:
                    print(f"   ⚠️  Could not access model_actions: {e}")

        if self.verbose:
            print(f"✓ Parsed {len(self.actions)} actions")
            if len(self.actions) == 0:
                print("⚠️  WARNING: No actions were extracted from history!")
                print("   This will result in empty generated code.")

    def _extract_from_agent_history(self, agent_history) -> None:
        """Extract actions from AgentHistory object (browser-use 0.5.9)"""
        if not hasattr(agent_history, 'model_output') or not agent_history.model_output:
            return

        model_output = agent_history.model_output

        if self.verbose:
            print(f"       model_output type: {type(model_output)}")
            if hasattr(model_output, '__dict__'):
                print(f"       model_output keys: {list(model_output.__dict__.keys())}")

        # model_output should have the action information
        if hasattr(model_output, 'action') and model_output.action:
            actions = model_output.action if isinstance(model_output.action, list) else [model_output.action]

            if self.verbose:
                print(f"       Found {len(actions)} action(s)")

            for action in actions:
                if self.verbose:
                    print(f"       Action type: {type(action)}")
                    if hasattr(action, '__dict__'):
                        print(f"       Action dict keys: {list(action.__dict__.keys())}")
                    # Check if action has a 'root' attribute which might contain the actual action
                    if hasattr(action, 'root'):
                        print(f"       Action.root type: {type(action.root)}")
                        if hasattr(action.root, '__dict__'):
                            print(f"       Action.root keys: {list(action.root.__dict__.keys())}")

                # Handle 'root' wrapper in Pydantic models
                if hasattr(action, 'root'):
                    actual_action = action.root
                    if isinstance(actual_action, list):
                        for sub_action in actual_action:
                            self._extract_action(sub_action)
                    else:
                        self._extract_action(actual_action)
                else:
                    self._extract_action(action)
        elif hasattr(model_output, '__dict__'):
            # Try to extract action from model_output dict
            self._extract_action(model_output)

    def _extract_action(self, action) -> None:
        """Extract action details from browser-use action object"""
        action_data = {
            'type': 'unknown',
            'params': {},
            'element': None,
            'locators': [],
            'description': ''
        }

        # Convert action to dict
        if hasattr(action, '__dict__'):
            action_dict = action.__dict__
        elif isinstance(action, dict):
            action_dict = action
        else:
            if self.verbose:
                print(f"   ⚠️  Skipping action of unknown type: {type(action)}")
            return

        if self.verbose:
            print(f"   Examining action: {list(action_dict.keys())[:5]}...")

        # Browser-use 0.5.9+ uses simpler action keys: navigate, click, input, etc.
        # Handle the new action structure first
        if 'navigate' in action_dict:
            nav_data = action_dict.get('navigate', {})
            if hasattr(nav_data, '__dict__'):
                nav_data = nav_data.__dict__
            action_data['type'] = 'goto'
            action_data['params'] = {'url': nav_data.get('url', '') if isinstance(nav_data, dict) else str(nav_data)}
            action_data['description'] = f"Navigate to URL"

        elif 'click' in action_dict:
            click_data = action_dict.get('click', {})
            if hasattr(click_data, '__dict__'):
                click_data = click_data.__dict__
            action_data['type'] = 'click'
            # In new format, element info might be in 'element_index' or similar
            element = click_data.get('element', click_data) if isinstance(click_data, dict) else {}
            action_data['element'] = element
            action_data['locators'] = self._generate_locators(element)
            action_data['description'] = f"Click element"

        elif 'input' in action_dict:
            input_data = action_dict.get('input', {})
            if hasattr(input_data, '__dict__'):
                input_data = input_data.__dict__
            action_data['type'] = 'fill'
            element = input_data.get('element', input_data) if isinstance(input_data, dict) else {}
            action_data['element'] = element
            action_data['params'] = {'text': input_data.get('text', '') if isinstance(input_data, dict) else ''}
            action_data['locators'] = self._generate_locators(element)
            action_data['description'] = f"Input text"

        elif 'done' in action_dict:
            # Skip 'done' action as it's just a completion signal
            if self.verbose:
                print(f"   ✓ Skipping 'done' action (completion signal)")
            return

        # Legacy browser-use format support (older versions)
        elif 'go_to_url' in action_dict:
            url_data = action_dict.get('go_to_url', {})
            if hasattr(url_data, '__dict__'):
                url_data = url_data.__dict__
            action_data['type'] = 'goto'
            action_data['params'] = {'url': url_data.get('url', '') if isinstance(url_data, dict) else str(url_data)}
            action_data['description'] = f"Navigate to URL"

        elif 'go_to_url' in actual_action:
            url_data = actual_action.get('go_to_url', {})
            if hasattr(url_data, '__dict__'):
                url_data = url_data.__dict__
            action_data['type'] = 'goto'
            action_data['params'] = {'url': url_data.get('url', '') if isinstance(url_data, dict) else str(url_data)}
            action_data['description'] = f"Navigate to URL"

        elif 'click_element' in action_dict:
            click_data = action_dict.get('click_element', {})
            if hasattr(click_data, '__dict__'):
                click_data = click_data.__dict__
            action_data['type'] = 'click'
            action_data['element'] = click_data.get('element', {}) if isinstance(click_data, dict) else {}
            action_data['locators'] = self._generate_locators(action_data['element'])
            action_data['description'] = f"Click element"

        elif 'click_element' in actual_action:
            click_data = actual_action.get('click_element', {})
            if hasattr(click_data, '__dict__'):
                click_data = click_data.__dict__
            action_data['type'] = 'click'
            action_data['element'] = click_data.get('element', {}) if isinstance(click_data, dict) else {}
            action_data['locators'] = self._generate_locators(action_data['element'])
            action_data['description'] = f"Click element"

        elif 'input_text' in action_dict:
            input_data = action_dict.get('input_text', {})
            if hasattr(input_data, '__dict__'):
                input_data = input_data.__dict__
            action_data['type'] = 'fill'
            action_data['element'] = input_data.get('element', {}) if isinstance(input_data, dict) else {}
            action_data['params'] = {'text': input_data.get('text', '') if isinstance(input_data, dict) else ''}
            action_data['locators'] = self._generate_locators(action_data['element'])
            action_data['description'] = f"Input text"

        elif 'input_text' in actual_action:
            input_data = actual_action.get('input_text', {})
            if hasattr(input_data, '__dict__'):
                input_data = input_data.__dict__
            action_data['type'] = 'fill'
            action_data['element'] = input_data.get('element', {}) if isinstance(input_data, dict) else {}
            action_data['params'] = {'text': input_data.get('text', '') if isinstance(input_data, dict) else ''}
            action_data['locators'] = self._generate_locators(action_data['element'])
            action_data['description'] = f"Input text"

        elif 'extract_content' in action_dict or 'extract_content' in actual_action:
            action_data['type'] = 'extract'
            extract_data = action_dict.get('extract_content', actual_action.get('extract_content', {}))
            action_data['params'] = extract_data if isinstance(extract_data, dict) else {}
            action_data['description'] = f"Extract content"

        if action_data['type'] != 'unknown':
            self.actions.append(action_data)
            if self.verbose:
                print(f"   ✓ Extracted {action_data['type']} action")
        else:
            if self.verbose:
                print(f"   ⚠️  Could not extract action from: {list(action_dict.keys())}")

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

        code_lines.append(
            "async def self_healing_locator(page: Page, primary: str, fallbacks: List[str] = None) -> Locator:")
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
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        if self.verbose:
            print(f"✓ Code saved to: {filepath}")
