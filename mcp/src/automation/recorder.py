"""
Browser Action Recorder
Captures user interactions and generates natural language commands + Playwright code
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from openai import AsyncOpenAI


@dataclass
class RecordedAction:
    """Represents a single recorded browser action."""
    timestamp: str
    action_type: str  # click, type, navigate, select, etc.
    selector: Optional[str] = None
    element_text: Optional[str] = None
    element_tag: Optional[str] = None
    value: Optional[str] = None  # For typing, selecting
    url: Optional[str] = None  # For navigation
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BrowserRecorder:
    """Records browser interactions and generates automation code."""
    
    def __init__(self, openai_api_key: str):
        self.is_recording = False
        self.recorded_actions: List[RecordedAction] = []
        self.session_start_time: Optional[datetime] = None
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self._fetched_count = 0  # Track how many events we've already fetched
        
        # JavaScript code to inject into browser for event capture
        self.recorder_script = """
        (function() {
            // Use sessionStorage to persist events across page loads
            const STORAGE_KEY_EVENTS = '__recordedEvents';
            const STORAGE_KEY_LAST_URL = '__lastRecordedUrl';
            
            // Load existing events from sessionStorage
            let events = [];
            try {
                const stored = sessionStorage.getItem(STORAGE_KEY_EVENTS);
                if (stored) {
                    events = JSON.parse(stored);
                }
            } catch (e) {}
            window.__recordedEvents = events;
            
            // Get last URL from storage
            const lastUrl = sessionStorage.getItem(STORAGE_KEY_LAST_URL) || '';
            const currentUrl = window.location.href;
            
            // If URL changed (full page load), record navigation
            if (lastUrl && currentUrl !== lastUrl) {
                window.__recordedEvents.push({
                    type: 'navigate',
                    url: currentUrl,
                    timestamp: Date.now()
                });
                // Save immediately
                try {
                    sessionStorage.setItem(STORAGE_KEY_EVENTS, JSON.stringify(window.__recordedEvents));
                } catch (e) {}
            }
            
            // Update last URL in storage
            try {
                sessionStorage.setItem(STORAGE_KEY_LAST_URL, currentUrl);
            } catch (e) {}
            
            // Helper to save events to sessionStorage
            function saveEvents() {
                try {
                    sessionStorage.setItem(STORAGE_KEY_EVENTS, JSON.stringify(window.__recordedEvents));
                } catch (e) {}
            }
            
            // Prevent duplicate listener registration
            if (window.__recorderInjected) return;
            window.__recorderInjected = true;
            
            // Helper to get unique selector for element
            function getSelector(el) {
                if (!el) return null;
                
                // Try ID first
                if (el.id) return '#' + el.id;
                
                // Try name attribute
                if (el.name) return `[name="${el.name}"]`;
                
                // Try aria-label
                if (el.getAttribute('aria-label')) {
                    return `[aria-label="${el.getAttribute('aria-label')}"]`;
                }
                
                // Try placeholder
                if (el.placeholder) return `[placeholder="${el.placeholder}"]`;
                
                // Try text content for buttons/links
                if (['BUTTON', 'A'].includes(el.tagName)) {
                    const text = el.innerText?.trim();
                    if (text && text.length < 50) {
                        return `text=${text}`;
                    }
                }
                
                // Try role
                const role = el.getAttribute('role');
                if (role) return `[role="${role}"]`;
                
                // Fallback to tag + nth-child
                let selector = el.tagName.toLowerCase();
                if (el.className) {
                    const classes = el.className.split(' ').filter(c => c).slice(0, 2);
                    if (classes.length) {
                        selector += '.' + classes.join('.');
                    }
                }
                
                return selector;
            }
            
            // Track navigation events
            function recordNavigation(url) {
                const lastUrl = sessionStorage.getItem(STORAGE_KEY_LAST_URL) || '';
                if (url !== lastUrl) {
                    window.__recordedEvents.push({
                        type: 'navigate',
                        url: url,
                        timestamp: Date.now()
                    });
                    saveEvents();
                    try {
                        sessionStorage.setItem(STORAGE_KEY_LAST_URL, url);
                    } catch (e) {}
                }
            }
            
            // Listen for URL changes (SPA navigation)
            window.addEventListener('popstate', function() {
                recordNavigation(window.location.href);
            });
            
            // Intercept pushState and replaceState
            const originalPushState = history.pushState;
            const originalReplaceState = history.replaceState;
            
            history.pushState = function() {
                originalPushState.apply(this, arguments);
                recordNavigation(window.location.href);
            };
            
            history.replaceState = function() {
                originalReplaceState.apply(this, arguments);
                recordNavigation(window.location.href);
            };
            
            // Record click events
            document.addEventListener('click', function(e) {
                const el = e.target;
                window.__recordedEvents.push({
                    type: 'click',
                    selector: getSelector(el),
                    text: el.innerText?.trim().substring(0, 100) || null,
                    tag: el.tagName.toLowerCase(),
                    timestamp: Date.now()
                });
                saveEvents();
            }, true);
            
            // Record input events (text, email, password, search, etc.)
            document.addEventListener('input', function(e) {
                const el = e.target;
                if (['INPUT', 'TEXTAREA'].includes(el.tagName)) {
                    window.__recordedEvents.push({
                        type: 'type',
                        selector: getSelector(el),
                        value: el.value,
                        tag: el.tagName.toLowerCase(),
                        inputType: el.type || 'text',
                        timestamp: Date.now()
                    });
                    saveEvents();
                }
            }, true);
            
            // Record change events (checkboxes, radios, selects)
            document.addEventListener('change', function(e) {
                const el = e.target;
                
                if (el.tagName === 'SELECT') {
                    window.__recordedEvents.push({
                        type: 'select',
                        selector: getSelector(el),
                        value: el.value,
                        text: el.options[el.selectedIndex]?.text,
                        tag: 'select',
                        timestamp: Date.now()
                    });
                    saveEvents();
                } else if (el.type === 'checkbox') {
                    window.__recordedEvents.push({
                        type: 'check',
                        selector: getSelector(el),
                        checked: el.checked,
                        tag: 'checkbox',
                        timestamp: Date.now()
                    });
                    saveEvents();
                } else if (el.type === 'radio') {
                    window.__recordedEvents.push({
                        type: 'radio',
                        selector: getSelector(el),
                        value: el.value,
                        tag: 'radio',
                        timestamp: Date.now()
                    });
                    saveEvents();
                }
            }, true);
            
            // Record form submissions
            document.addEventListener('submit', function(e) {
                const form = e.target;
                window.__recordedEvents.push({
                    type: 'submit',
                    selector: getSelector(form),
                    tag: 'form',
                    timestamp: Date.now()
                });
                saveEvents();
            }, true);
            
            console.log('🎥 Browser recorder activated - all interactions are being captured');
        })();
        """
    
    async def start_recording(self, mcp_client) -> str:
        """Start recording browser interactions."""
        self.is_recording = True
        self.recorded_actions = []
        self._fetched_count = 0  # Reset offset
        self.session_start_time = datetime.now()
        
        # Clear any stale sessionStorage data from previous sessions
        try:
            await mcp_client.evaluate("""
                sessionStorage.removeItem('__recordedEvents');
                sessionStorage.removeItem('__lastRecordedUrl');
                window.__recordedEvents = [];
            """)
        except Exception:
            pass
        
        return "Recording started - perform your actions in the browser"
    
    def stop_recording(self) -> str:
        """Stop recording browser interactions."""
        self.is_recording = False
        action_count = len(self.recorded_actions)
        return f"Recording stopped - captured {action_count} actions"
    
    async def maintain_recording(self, mcp_client) -> None:
        """Periodically reinject recorder script and pull events to Python.
        This ensures events are persisted even across cross-origin navigations.
        Should be called in a background loop while recording is active.
        """
        if not self.is_recording:
            return
        
        try:
            # Reinject the script to capture any new page loads
            await mcp_client.evaluate(self.recorder_script)
            
            # Pull events from browser to Python (backup for cross-origin navigation)
            await self.fetch_recorded_events(mcp_client, clear_after_fetch=False)
        except Exception:
            pass  # Silently fail if page is not ready
    
    def get_recorder_script(self) -> str:
        """Get the JavaScript to inject for recording."""
        return self.recorder_script
    
    async def fetch_recorded_events(self, mcp_client, clear_after_fetch: bool = True) -> List[RecordedAction]:
        """Fetch NEW events from browser and convert to RecordedAction objects.
        
        Args:
            mcp_client: The MCP client to use for evaluation
            clear_after_fetch: If True, clears events from browser after fetching (default)
                             If False, only fetches new events since last fetch (for periodic backups)
        """
        try:
            # Get events from browser
            if clear_after_fetch:
                # Final fetch - only get NEW events we haven't fetched yet, then clear
                result = await mcp_client.evaluate(f"""
                    (function() {{
                        const allEvents = window.__recordedEvents || [];
                        const newEvents = allEvents.slice({self._fetched_count});
                        window.__recordedEvents = [];  // Clear after fetching
                        sessionStorage.removeItem('__recordedEvents');  // Clear storage too
                        return newEvents;
                    }})();
                """)
                self._fetched_count = 0  # Reset offset
            else:
                # Periodic fetch - only get new events since last fetch
                result = await mcp_client.evaluate(f"""
                    (function() {{
                        const allEvents = window.__recordedEvents || [];
                        const newEvents = allEvents.slice({self._fetched_count});
                        return newEvents;
                    }})();
                """)
            
            if isinstance(result, list) and len(result) > 0:
                # Convert events to RecordedAction objects
                for event in result:
                    metadata = {}
                    if event.get('inputType'):
                        metadata['inputType'] = event['inputType']
                    if 'checked' in event:
                        metadata['checked'] = event['checked']
                    
                    action = RecordedAction(
                        timestamp=datetime.fromtimestamp(event.get('timestamp', 0) / 1000).isoformat(),
                        action_type=event.get('type', 'unknown'),
                        selector=event.get('selector'),
                        element_text=event.get('text'),
                        element_tag=event.get('tag'),
                        value=event.get('value'),
                        url=event.get('url'),
                        metadata=metadata if metadata else None
                    )
                    self.recorded_actions.append(action)
                
                # Update fetched count if doing periodic fetch
                if not clear_after_fetch:
                    self._fetched_count += len(result)
            
            return self.recorded_actions
        except Exception as e:
            print(f"Error fetching recorded events: {e}")
            return []
    
    def _deduplicate_actions(self, actions: List[RecordedAction]) -> List[RecordedAction]:
        """Remove duplicate/redundant actions (e.g., multiple type events for same field)."""
        if not actions:
            return []
        
        deduplicated = []
        i = 0
        
        while i < len(actions):
            current = actions[i]
            
            # For 'type' actions, merge consecutive types on same element
            if current.action_type == 'type':
                # Look ahead for more type actions on same selector
                j = i + 1
                while j < len(actions) and actions[j].action_type == 'type' and actions[j].selector == current.selector:
                    # Use the last value (final text)
                    current.value = actions[j].value
                    j += 1
                i = j
            else:
                i += 1
            
            deduplicated.append(current)
        
        return deduplicated
    
    async def generate_natural_language(self, actions: List[RecordedAction]) -> str:
        """Use AI to generate natural language description of recorded actions."""
        if not actions:
            return "No actions recorded"
        
        # Deduplicate first
        actions = self._deduplicate_actions(actions)
        
        # Create a summary of actions
        action_summary = []
        for action in actions:
            if action.action_type == 'navigate':
                action_summary.append(f"Navigated to {action.url}")
            elif action.action_type == 'click':
                desc = f"Clicked {action.element_tag}"
                if action.element_text:
                    desc += f" with text '{action.element_text[:50]}'"
                action_summary.append(desc)
            elif action.action_type == 'type':
                desc = f"Typed '{action.value}' into {action.element_tag}"
                if action.selector:
                    desc += f" ({action.selector})"
                action_summary.append(desc)
            elif action.action_type == 'select':
                action_summary.append(f"Selected '{action.value}' from dropdown")
            elif action.action_type == 'check':
                action_summary.append(f"{'Checked' if action.metadata and action.metadata.get('checked') else 'Unchecked'} checkbox")
            elif action.action_type == 'radio':
                action_summary.append(f"Selected radio button '{action.value}'")
            elif action.action_type == 'submit':
                action_summary.append("Submitted form")
        
        # Use AI to create natural language command
        prompt = f"""Convert these browser actions into a single, clear natural language automation command:

Actions performed:
{chr(10).join(f'{i+1}. {a}' for i, a in enumerate(action_summary))}

Generate a concise natural language command that describes this workflow (1-2 sentences max).
Focus on the user's intent, not technical details.

Examples:
- "Search for Python tutorials on Google"
- "Fill out contact form and submit"
- "Login with credentials and navigate to dashboard"

Natural language command:"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            content = response.choices[0].message.content
            return content.strip() if content else ""
        except Exception as e:
            # Fallback to simple concatenation
            return " and ".join(action_summary[:5])
    
    def generate_playwright_code(self, actions: List[RecordedAction]) -> str:
        """Generate clean Playwright Python code from recorded actions."""
        if not actions:
            return "# No actions recorded"
        
        # Deduplicate actions
        actions = self._deduplicate_actions(actions)
        
        code_lines = [
            "# Generated from recorded browser interactions",
            f"# Recorded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "from playwright.async_api import async_playwright",
            "",
            "async def recorded_workflow():",
            "    async with async_playwright() as p:",
            "        browser = await p.chromium.launch(headless=True)",
            "        page = await browser.new_page()",
            ""
        ]
        
        for action in actions:
            if action.action_type == 'navigate':
                code_lines.append(f"        # Navigate to page")
                code_lines.append(f"        await page.goto('{action.url}')")
                
            elif action.action_type == 'click':
                code_lines.append(f"        # Click element")
                if action.selector:
                    code_lines.append(f"        await page.locator('{action.selector}').click()")
                else:
                    code_lines.append(f"        # TODO: Add proper selector for click")
                    
            elif action.action_type == 'type':
                code_lines.append(f"        # Type into field")
                if action.selector:
                    code_lines.append(f"        await page.locator('{action.selector}').fill('{action.value}')")
                else:
                    code_lines.append(f"        # TODO: Add proper selector for input")
                    
            elif action.action_type == 'select':
                code_lines.append(f"        # Select dropdown option")
                if action.selector:
                    code_lines.append(f"        await page.locator('{action.selector}').select_option('{action.value}')")
                    
            elif action.action_type == 'check':
                checked = action.metadata and action.metadata.get('checked', False)
                code_lines.append(f"        # {'Check' if checked else 'Uncheck'} checkbox")
                if action.selector:
                    if checked:
                        code_lines.append(f"        await page.locator('{action.selector}').check()")
                    else:
                        code_lines.append(f"        await page.locator('{action.selector}').uncheck()")
                        
            elif action.action_type == 'radio':
                code_lines.append(f"        # Select radio button")
                if action.selector:
                    code_lines.append(f"        await page.locator('{action.selector}').check()")
                    
            elif action.action_type == 'submit':
                code_lines.append(f"        # Submit form")
                if action.selector:
                    code_lines.append(f"        await page.locator('{action.selector}').press('Enter')")
            
            code_lines.append("")
        
        code_lines.extend([
            "        await browser.close()",
            "",
            "if __name__ == '__main__':",
            "    import asyncio",
            "    asyncio.run(recorded_workflow())"
        ])
        
        return "\n".join(code_lines)
    
    def export_recording(self, actions: List[RecordedAction], format: str = 'json') -> str:
        """Export recorded actions in various formats."""
        if format == 'json':
            return json.dumps([a.to_dict() for a in actions], indent=2)
        else:
            return str(actions)
    
    def clear_recording(self):
        """Clear all recorded actions."""
        self.recorded_actions = []
        self.session_start_time = None
