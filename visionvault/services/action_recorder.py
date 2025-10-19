import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from playwright.async_api import Page, Browser, async_playwright
import uuid


class ActionRecorder:
    """Records browser actions for teaching mode."""
    
    def __init__(self):
        self.actions: List[Dict] = []
        self.is_recording = False
        self.page: Optional[Page] = None
        self.browser: Optional[Browser] = None
        self.playwright_instance = None
    
    async def start_recording(self, browser_name='chromium', headless=False):
        """Start recording browser actions."""
        self.actions = []
        self.is_recording = True
        self.playwright_instance = await async_playwright().start()
        browser_type = getattr(self.playwright_instance, browser_name)
        self.browser = await browser_type.launch(headless=headless)
        self.page = await self.browser.new_page()

        # Use add_init_script for persistent listeners
        await self.page.add_init_script(self._get_event_listener_js())
        await self.page.expose_function('recordUserAction', self._handle_user_action)
        self.page.on('framenavigated', lambda frame: asyncio.create_task(self._on_navigation(frame)))
        self.page.on('close', lambda: self._on_page_close())
        return self.page

    def _get_event_listener_js(self):
        # JS to listen for click, input, change, keyboard events and call recordUserAction
        return '''
        (function() {
            // Use WeakMap to track debounce timers by element identity, not selector
            const inputTimers = new WeakMap();
            const DEBOUNCE_DELAY = 500; // Wait 500ms after last keystroke
            
            function getSelector(el) {
                let selector = el.tagName.toLowerCase();
                if (el.id) {
                    selector += '#' + el.id;
                } else if (el.className && typeof el.className === 'string') {
                    const classes = el.className.split(' ').filter(c => c.trim());
                    if (classes.length > 0) {
                        selector += '.' + classes.join('.');  // Include ALL classes for specificity
                    }
                }
                return selector;
            }
            
            function sendAction(type, selector, value, text, key) {
                if (window.recordUserAction) {
                    const action = {type, selector, value, text, timestamp: new Date().toISOString()};
                    if (key) action.key = key;
                    window.recordUserAction(action);
                }
            }
            
            // Record clicks
            document.addEventListener('click', function(e) {
                const selector = getSelector(e.target);
                const text = e.target.innerText ? e.target.innerText.substring(0, 50) : null;
                sendAction('click', selector, null, text);
            }, true);
            
            // Record input with debouncing - track by element identity using WeakMap
            document.addEventListener('input', function(e) {
                const el = e.target;
                const selector = getSelector(el);
                
                // Clear existing timer for THIS SPECIFIC element
                if (inputTimers.has(el)) {
                    clearTimeout(inputTimers.get(el));
                }
                
                // Set new timer - will only fire if user stops typing for DEBOUNCE_DELAY ms
                const timer = setTimeout(() => {
                    sendAction('fill', selector, el.value, null);
                    inputTimers.delete(el);
                }, DEBOUNCE_DELAY);
                
                inputTimers.set(el, timer);
            }, true);
            
            // Record change events (for selects, checkboxes, radios)
            document.addEventListener('change', function(e) {
                const el = e.target;
                const selector = getSelector(el);
                
                if (el.type === 'checkbox' || el.type === 'radio') {
                    sendAction('check', selector, el.checked, null);
                } else if (el.tagName.toLowerCase() === 'select') {
                    sendAction('select', selector, el.value, null);
                }
            }, true);
            
            // Record keyboard events (Enter, Tab, Escape, etc.)
            document.addEventListener('keydown', function(e) {
                // Only record special keys, not regular characters (those are captured via input)
                const specialKeys = ['Enter', 'Tab', 'Escape', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
                
                if (specialKeys.includes(e.key)) {
                    const el = e.target;
                    const selector = getSelector(el);
                    
                    // If Enter key and there's a pending input timer, send it immediately
                    if (e.key === 'Enter' && inputTimers.has(el)) {
                        clearTimeout(inputTimers.get(el));
                        sendAction('fill', selector, el.value, null);
                        inputTimers.delete(el);
                    }
                    
                    sendAction('press', selector, null, null, e.key);
                }
            }, true);
            
            // Record form submissions
            document.addEventListener('submit', function(e) {
                const selector = getSelector(e.target);
                sendAction('submit', selector, null, null);
            }, true);
        })();
        '''

    async def _on_navigation(self, frame):
        """Record navigation events."""
        if frame == self.page.main_frame:
            self.record_action({
                'type': 'navigate',
                'url': frame.url,
                'timestamp': datetime.now().isoformat()
            })
            # Re-expose function after navigation
            try:
                await self.page.expose_function('recordUserAction', self._handle_user_action)
            except Exception as e:
                pass

    def _on_page_close(self):
        self.is_recording = False

    async def _handle_user_action(self, action):
        # Receives actions from JS and records them
        self.record_action(action)

    def record_action(self, action: Dict):
        """Record an action with deduplication."""
        if self.is_recording:
            # Deduplicate consecutive identical actions
            if self.actions and self._is_duplicate_action(self.actions[-1], action):
                return  # Skip duplicate
            self.actions.append(action)
    
    def _is_duplicate_action(self, action1: Dict, action2: Dict) -> bool:
        """Check if two actions are duplicates - only deduplicate identical fills and navigation."""
        action_type = action1.get('type')
        
        # Different types are never duplicates
        if action_type != action2.get('type'):
            return False
        
        # For fill actions: same selector AND same value = duplicate
        if action_type == 'fill':
            return (action1.get('selector') == action2.get('selector') and 
                    action1.get('value') == action2.get('value'))
        
        # For navigation: same URL = duplicate
        if action_type in ('navigate', 'goto'):
            return action1.get('url') == action2.get('url')
        
        # Allow all other actions (clicks, presses, etc.) - user may intentionally repeat them
        return False
    
    def record_goto(self, url: str):
        """Record a goto action."""
        self.record_action({
            'type': 'goto',
            'url': url,
            'timestamp': datetime.now().isoformat()
        })
    
    def record_click(self, selector: str, text: Optional[str] = None):
        """Record a click action."""
        self.record_action({
            'type': 'click',
            'selector': selector,
            'text': text,
            'timestamp': datetime.now().isoformat()
        })
    
    def record_fill(self, selector: str, value: str):
        """Record a fill/input action."""
        self.record_action({
            'type': 'fill',
            'selector': selector,
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
    
    def record_select(self, selector: str, value: str):
        """Record a select action."""
        self.record_action({
            'type': 'select',
            'selector': selector,
            'value': value,
            'timestamp': datetime.now().isoformat()
        })
    
    def record_check(self, selector: str):
        """Record a checkbox/radio check action."""
        self.record_action({
            'type': 'check',
            'selector': selector,
            'timestamp': datetime.now().isoformat()
        })
    
    def record_wait(self, wait_type: str, selector: Optional[str] = None, timeout: int = 5000):
        """Record a wait action."""
        action = {
            'type': 'wait',
            'wait_type': wait_type,  # 'navigation', 'selector', 'timeout'
            'timeout': timeout,
            'timestamp': datetime.now().isoformat()
        }
        if selector:
            action['selector'] = selector
        self.record_action(action)
    
    async def stop_recording(self):
        """Stop recording and return captured actions."""
        self.is_recording = False
        
        # Close browser
        if self.browser:
            await self.browser.close()
        if self.playwright_instance:
            await self.playwright_instance.stop()
        
        return self.actions
    
    def generate_playwright_code(self, actions: Optional[List[Dict]] = None) -> str:
        """Generate Playwright code from recorded actions."""
        if actions is None:
            actions = self.actions
        
        if not actions:
            return ""
        
        # Start building the code
        code_lines = [
            "async def run_test(browser_name='chromium', headless=True):",
            "    from playwright.async_api import async_playwright",
            "    logs = []",
            "    screenshot = None",
            "    ",
            "    try:",
            "        async with async_playwright() as p:",
            "            browser = await getattr(p, browser_name).launch(headless=headless)",
            "            page = await browser.new_page()",
            "            ",
        ]
        
        # Convert actions to code
        for i, action in enumerate(actions):
            action_type = action.get('type')
            
            if action_type == 'goto' or action_type == 'navigate':
                url = action.get('url')
                code_lines.append(f"            await page.goto('{url}')")
                code_lines.append(f"            logs.append('Navigated to {url}')")
            
            elif action_type == 'click':
                selector = action.get('selector')
                code_lines.append(f"            await page.click('{selector}')")
                code_lines.append(f"            logs.append('Clicked {selector}')")
            
            elif action_type == 'fill':
                selector = action.get('selector')
                value = action.get('value', '').replace("'", "\\'")
                code_lines.append(f"            await page.fill('{selector}', '{value}')")
                code_lines.append(f"            logs.append('Filled {selector}')")
            
            elif action_type == 'select':
                selector = action.get('selector')
                value = action.get('value')
                code_lines.append(f"            await page.select_option('{selector}', '{value}')")
                code_lines.append(f"            logs.append('Selected option in {selector}')")
            
            elif action_type == 'check':
                selector = action.get('selector')
                code_lines.append(f"            await page.check('{selector}')")
                code_lines.append(f"            logs.append('Checked {selector}')")
            
            elif action_type == 'wait':
                wait_type = action.get('wait_type')
                if wait_type == 'navigation':
                    code_lines.append("            await page.wait_for_load_state('networkidle')")
                    code_lines.append("            logs.append('Waited for navigation')")
                elif wait_type == 'selector':
                    selector = action.get('selector')
                    timeout = action.get('timeout', 5000)
                    code_lines.append(f"            await page.wait_for_selector('{selector}', timeout={timeout})")
                    code_lines.append(f"            logs.append('Waited for {selector}')")
                elif wait_type == 'timeout':
                    timeout = action.get('timeout', 1000)
                    code_lines.append(f"            await page.wait_for_timeout({timeout})")
                    code_lines.append(f"            logs.append('Waited {timeout}ms')")
            
            elif action_type == 'press':
                selector = action.get('selector')
                key = action.get('key', 'Enter')
                code_lines.append(f"            await page.press('{selector}', '{key}')")
                code_lines.append(f"            logs.append('Pressed {key} on {selector}')")
            
            elif action_type == 'submit':
                selector = action.get('selector')
                code_lines.append(f"            await page.locator('{selector}').press('Enter')")
                code_lines.append(f"            logs.append('Submitted form {selector}')")
        
        # Add screenshot and closing code
        code_lines.extend([
            "            ",
            "            # Take screenshot before closing",
            "            screenshot = await page.screenshot()",
            "            logs.append('Screenshot captured')",
            "            ",
            "            await browser.close()",
            "            return {'success': True, 'logs': logs, 'screenshot': screenshot}",
            "    ",
            "    except Exception as e:",
            "        logs.append(f'Error: {str(e)}')",
            "        if 'page' in locals():",
            "            try:",
            "                screenshot = await page.screenshot()",
            "            except:",
            "                pass",
            "        if 'browser' in locals():",
            "            try:",
            "                await browser.close()",
            "            except:",
            "                pass",
            "        return {'success': False, 'logs': logs, 'screenshot': screenshot}"
        ])
        
        return "\n".join(code_lines)
    
    @staticmethod
    def parse_code_to_actions(playwright_code: str) -> List[Dict]:
        """
        Parse Playwright code to extract actions (reverse operation).
        This is a simple parser that looks for common patterns.
        """
        actions = []
        lines = playwright_code.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Parse goto
            if 'page.goto(' in line:
                import re
                match = re.search(r"page\.goto\(['\"](.+?)['\"]\)", line)
                if match:
                    actions.append({
                        'type': 'goto',
                        'url': match.group(1)
                    })
            
            # Parse click
            elif 'page.click(' in line:
                import re
                match = re.search(r"page\.click\(['\"](.+?)['\"]\)", line)
                if match:
                    actions.append({
                        'type': 'click',
                        'selector': match.group(1)
                    })
            
            # Parse fill
            elif 'page.fill(' in line:
                import re
                match = re.search(r"page\.fill\(['\"](.+?)['\"],\s*['\"](.+?)['\"]\)", line)
                if match:
                    actions.append({
                        'type': 'fill',
                        'selector': match.group(1),
                        'value': match.group(2)
                    })
            
            # Add more parsers as needed
        
        return actions


class InteractiveRecorder(ActionRecorder):
    """
    Enhanced recorder that can intercept and record actual user interactions.
    This would be used with a UI where users can click through a task.
    """
    
    async def start_interactive_recording(self, browser_name='chromium'):
        """Start interactive recording with visible browser."""
        page = await self.start_recording(browser_name, headless=False)
        
        # Inject improved JavaScript with debouncing and keyboard capture
        await page.add_init_script("""
            window.__recordedActions = [];
            const inputTimers = new WeakMap();  // Track by element identity, not selector
            const DEBOUNCE_DELAY = 500;
            
            // Helper to generate CSS selector (must be defined first!)
            function getSelector(element) {
                let selector = element.tagName.toLowerCase();
                if (element.id) {
                    selector += '#' + element.id;
                } else if (element.className && typeof element.className === 'string') {
                    const classes = element.className.split(' ').filter(c => c.trim());
                    if (classes.length > 0) {
                        selector += '.' + classes.join('.');  // Include ALL classes for specificity
                    }
                }
                return selector;
            }
            
            // Record clicks
            document.addEventListener('click', (e) => {
                const selector = getSelector(e.target);
                window.__recordedActions.push({
                    type: 'click',
                    selector: selector,
                    text: e.target.textContent ? e.target.textContent.trim().substring(0, 50) : '',
                    timestamp: new Date().toISOString()
                });
                console.log('🎬 Recorded click:', selector);
            }, true);
            
            // Record input with debouncing - track by element identity using WeakMap
            document.addEventListener('input', (e) => {
                const el = e.target;
                const selector = getSelector(el);
                
                if (inputTimers.has(el)) {
                    clearTimeout(inputTimers.get(el));
                }
                
                const timer = setTimeout(() => {
                    window.__recordedActions.push({
                        type: 'fill',
                        selector: selector,
                        value: el.value,
                        timestamp: new Date().toISOString()
                    });
                    console.log('🎬 Recorded fill:', selector, '=', el.value);
                    inputTimers.delete(el);
                }, DEBOUNCE_DELAY);
                
                inputTimers.set(el, timer);
            }, true);
            
            // Record keyboard events
            document.addEventListener('keydown', (e) => {
                const specialKeys = ['Enter', 'Tab', 'Escape', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
                
                if (specialKeys.includes(e.key)) {
                    const el = e.target;
                    const selector = getSelector(el);
                    
                    // If Enter and there's pending input, send it immediately
                    if (e.key === 'Enter' && inputTimers.has(el)) {
                        clearTimeout(inputTimers.get(el));
                        window.__recordedActions.push({
                            type: 'fill',
                            selector: selector,
                            value: el.value,
                            timestamp: new Date().toISOString()
                        });
                        console.log('🎬 Recorded fill (Enter):', selector, '=', el.value);
                        inputTimers.delete(el);
                    }
                    
                    window.__recordedActions.push({
                        type: 'press',
                        selector: selector,
                        key: e.key,
                        timestamp: new Date().toISOString()
                    });
                    console.log('🎬 Recorded keypress:', e.key, 'on', selector);
                }
            }, true);
            
            console.log('✅ VisionVault recording initialized - actions will be captured automatically');
        """)
        
        return page
    
    async def get_recorded_actions_from_page(self):
        """Get actions recorded by JavaScript injection."""
        if not self.page:
            return []
        
        try:
            js_actions = await self.page.evaluate("window.__recordedActions || []")
            return js_actions
        except:
            return []
