import re
import asyncio
from .browser_manager import BrowserManager
from .utils import extract_failed_locator_local


class HealingEngine(BrowserManager):
    def __init__(self, socket_client):
        super().__init__()
        self.socket_client = socket_client

    def modify_code_for_healing(self, code):
        """Transform code to keep browser open by removing async with context manager"""
        import re

        # Step 1: Find the async with line and its indentation
        lines = code.split('\n')
        new_lines = []
        in_async_with_block = False
        async_with_indent = 0
        block_indent = 0

        for i, line in enumerate(lines):
            # Check if this line contains 'async with async_playwright() as var:'
            async_with_match = re.match(r'^(\s*)async with async_playwright\(\) as (\w+):\s*$', line)

            if async_with_match and not in_async_with_block:
                # Found the async with line - replace it
                indent = async_with_match.group(1)
                var_name = async_with_match.group(2)
                async_with_indent = len(indent)

                # Replace with two lines at the same indentation
                new_lines.append(f'{indent}{var_name} = await async_playwright().start()')
                new_lines.append(f'{indent}globals()["__p_instance__"] = {var_name}')

                in_async_with_block = True
                # Determine the block indentation
                if i + 1 < len(lines) and lines[i + 1].strip():
                    block_indent = len(lines[i + 1]) - len(lines[i + 1].lstrip())
                else:
                    block_indent = async_with_indent + 4

            elif in_async_with_block:
                # Check if this line is still part of the async with block
                if line.strip():
                    current_indent = len(line) - len(line.lstrip())

                    # If indentation decreased to or below async_with level, we've exited the block
                    if current_indent <= async_with_indent:
                        in_async_with_block = False
                        new_lines.append(line)
                    else:
                        # Dedent by one level
                        dedent_amount = block_indent - async_with_indent
                        if current_indent >= block_indent:
                            dedented_line = line[dedent_amount:]
                            new_lines.append(dedented_line)
                        else:
                            new_lines.append(line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        modified_code = '\n'.join(new_lines)

        # Step 2: Inject page capture after page creation
        lines = modified_code.split('\n')
        new_lines = []
        page_captured = False

        for line in lines:
            new_lines.append(line)
            # Match any variable name pattern: var = await browser.new_page()
            if re.search(r'(\w+)\s*=\s*await\s+\w+\.new_page\(\)', line) and not page_captured:
                indent = len(line) - len(line.lstrip())
                var_match = re.search(r'(\w+)\s*=\s*await\s+\w+\.new_page\(\)', line)
                if var_match:
                    var_name = var_match.group(1)
                    new_lines.append(f'{" " * indent}globals()["__healing_page__"] = {var_name}')
                    page_captured = True
                    print(f"✅ Added page capture injection for variable '{var_name}'")

        modified_code = '\n'.join(new_lines)

        # Step 3: Replace browser.close() with pass to keep browser open for healing
        modified_code = re.sub(
            r'^(\s*)(await\s+)?browser\.close\(\)',
            r'\1pass  # browser.close() commented for healing',
            modified_code,
            flags=re.MULTILINE
        )

        print("✅ Code transformation: async with removed, body dedented, browser stays open for healing")
        return modified_code

    async def execute_healing_attempt(self, test_id, code, browser_name, mode, attempt):
        """Execute a healing attempt with widget injection on failure"""
        headless = mode == 'headless'

        try:
            print(
                f"🎯 Starting healing attempt {attempt} for test {test_id} in {'headless' if headless else 'headful'} mode")

            # Clean up any previous instances
            await self.cleanup_browser()

            # Use original code for headless, modified for headful
            if headless:
                modified_code = code
            else:
                modified_code = self.modify_code_for_healing(code)
                print("✅ Code modified for headful healing mode")

            global_vars = {'__healing_page__': None, '__p_instance__': None}
            local_vars = {}

            # Execute the code
            exec(modified_code, global_vars, local_vars)

            if 'run_test' not in local_vars:
                self.socket_client.emit('healing_attempt_result',
                                        {'test_id': test_id, 'success': False, 'logs': ['Error: run_test missing'],
                                         'screenshot': None})
                return

            run_test = local_vars['run_test']

            # Execute with timeout
            try:
                result = await asyncio.wait_for(
                    run_test(browser_name=browser_name, headless=headless),
                    timeout=60.0
                )
            except asyncio.TimeoutError:
                print(f"⏱️  Execution timeout for test {test_id}")
                result = {
                    'success': False,
                    'logs': ['Execution timeout - browser took too long to respond'],
                    'screenshot': None
                }

            # Store page reference for headful mode
            if not headless and global_vars.get('__healing_page__'):
                self.set_active_page(global_vars['__healing_page__'])
                if self.active_page and hasattr(self.active_page, 'url') and hasattr(self.active_page, 'is_closed'):
                    print(
                        f"✅ Page captured for healing - URL: {self.active_page.url if not self.active_page.is_closed() else 'CLOSED'}")
                else:
                    print(f"✅ Page captured for healing - but no valid URL or is_closed method")
            else:
                print(
                    f"ℹ️  No page captured (headless: {headless}, page available: {bool(global_vars.get('__healing_page__'))})")

            # Handle screenshot
            from .utils import encode_screenshot
            screenshot_b64 = encode_screenshot(result.get('screenshot'))

            print(f"Healing attempt {attempt} for test {test_id}: {'SUCCESS' if result.get('success') else 'FAILED'}")

            # Emit result to server for tracking
            self.socket_client.emit('healing_attempt_result', {
                'test_id': test_id,
                'success': result.get('success', False),
                'logs': result.get('logs', []),
                'screenshot': screenshot_b64
            })

            # LOCAL-FIRST HEALING: Detect failure and inject widget immediately
            if not headless and not result.get('success') and self.active_page:
                # Extract failed locator from error message
                error_msg = ' '.join(result.get('logs', []))
                failed_locator = extract_failed_locator_local(error_msg)

                if failed_locator:
                    print(f"🎯 LOCAL: Failed locator detected: {failed_locator}")
                    print(f"🚀 LOCAL: Injecting widget immediately (no server delay)")

                    # Inject widget immediately - no waiting for server
                    self.set_widget_event(asyncio.Event())

                    try:
                        # Inject widget NOW
                        await self.inject_element_selector(test_id, failed_locator)

                        # Wait for user interaction (5 minutes timeout)
                        print(f"⏳ Waiting for user to select element (300s timeout)...")
                        try:
                            await asyncio.wait_for(self.widget_injection_complete.wait(), timeout=300.0)
                            print(f"✅ User selection completed")
                        except asyncio.TimeoutError:
                            print(f"⏱️  User selection timeout (300s)")
                    finally:
                        # Always cleanup browser after widget interaction or timeout
                        self.set_widget_event(None)
                        print(f"🧹 Cleaning up browser after widget interaction...")
                        await self.cleanup_browser()
                else:
                    print(f"ℹ️  No locator error detected in headful mode - browser will close normally")

        except Exception as e:
            print(f"💥 Healing attempt error: {e}")
            import traceback
            traceback.print_exc()
            self.socket_client.emit('healing_attempt_result',
                                    {'test_id': test_id, 'success': False, 'logs': [str(e)], 'screenshot': None})
            await self.cleanup_browser()

    async def inject_element_selector(self, test_id, failed_locator):
        """Inject element selector widget into the page"""
        if not self.active_page:
            print(f"❌ No active page for element selection (test {test_id})")
            if self.widget_injection_complete and hasattr(self.widget_injection_complete, 'set'):
                self.widget_injection_complete.set()
            return

        try:
            if hasattr(self.active_page, 'is_closed') and self.active_page.is_closed():
                print(f"❌ Page already closed for test {test_id}")
                self.set_active_page(None)
                if self.widget_injection_complete and hasattr(self.widget_injection_complete, 'set'):
                    self.widget_injection_complete.set()
                return

            if hasattr(self.active_page, 'url'):
                print(f"🎯 Injecting element selector widget for test {test_id} on page: {self.active_page.url}")
            else:
                print(f"🎯 Injecting element selector widget for test {test_id} on page: [no url]")

            # JavaScript to inject element selector overlay
            selector_script = """
            (failedLocator) => {
                console.log('🔧 Injecting element selector for locator:', failedLocator);
                
                // Remove any existing overlays first
                const existingOverlay = document.getElementById('playwright-element-selector-overlay');
                if (existingOverlay) {
                    existingOverlay.remove();
                }
                
                // Create overlay (non-blocking)
                const overlay = document.createElement('div');
                overlay.id = 'playwright-element-selector-overlay';
                overlay.style.cssText = `
                    position: fixed !important;
                    top: 0 !important;
                    left: 0 !important;
                    width: 100% !important;
                    height: 100% !important;
                    background: rgba(0, 0, 0, 0.3) !important;
                    z-index: 2147483647 !important;
                    cursor: crosshair !important;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                    pointer-events: none !important;
                `;
                
                // Create draggable header with instructions
                const header = document.createElement('div');
                header.style.cssText = `
                    position: fixed !important;
                    top: 20px !important;
                    left: 50% !important;
                    transform: translateX(-50%) !important;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                    color: white !important;
                    padding: 16px 24px !important;
                    border-radius: 12px !important;
                    font-size: 15px !important;
                    font-weight: 600 !important;
                    z-index: 2147483648 !important;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.4) !important;
                    text-align: left !important;
                    cursor: move !important;
                    user-select: none !important;
                    pointer-events: auto !important;
                    backdrop-filter: blur(10px) !important;
                    border: 1px solid rgba(255,255,255,0.1) !important;
                `;
                header.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                        <span style="font-size: 20px;">🎯</span>
                        <span style="font-size: 16px;">Element Selector Mode</span>
                    </div>
                    <div style="font-size: 13px; font-weight: normal; opacity: 0.95; line-height: 1.5;">
                        <div style="margin-bottom: 4px;">Failed locator: <code style="background: rgba(0,0,0,0.3); padding: 2px 8px; border-radius: 4px; font-family: monospace;">${failedLocator}</code></div>
                        <div style="opacity: 0.85;">Click on the element you want to select</div>
                        <div style="font-size: 11px; opacity: 0.7; margin-top: 6px;">💡 Drag this panel to move it</div>
                    </div>
                `;
                
                // Make header draggable
                let isDragging = false;
                let currentX;
                let currentY;
                let initialX;
                let initialY;
                
                header.addEventListener('mousedown', (e) => {
                    if (e.target.tagName !== 'BUTTON') {
                        isDragging = true;
                        initialX = e.clientX - (parseInt(header.style.left) || e.clientX);
                        initialY = e.clientY - (parseInt(header.style.top) || 20);
                        header.style.transition = 'none';
                    }
                });
                
                document.addEventListener('mousemove', (e) => {
                    if (isDragging) {
                        e.preventDefault();
                        currentX = e.clientX - initialX;
                        currentY = e.clientY - initialY;
                        header.style.left = currentX + 'px';
                        header.style.top = currentY + 'px';
                        header.style.transform = 'none';
                    }
                });
                
                document.addEventListener('mouseup', () => {
                    isDragging = false;
                });
                
                // Create cancel button inside header
                const cancelBtn = document.createElement('button');
                cancelBtn.textContent = '✕';
                cancelBtn.style.cssText = `
                    position: absolute !important;
                    top: 12px !important;
                    right: 12px !important;
                    background: rgba(255,255,255,0.2) !important;
                    color: white !important;
                    border: none !important;
                    width: 28px !important;
                    height: 28px !important;
                    border-radius: 50% !important;
                    cursor: pointer !important;
                    font-size: 16px !important;
                    font-weight: bold !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    transition: background 0.2s !important;
                    pointer-events: auto !important;
                `;
                cancelBtn.onmouseover = () => {
                    cancelBtn.style.background = 'rgba(255,255,255,0.3)';
                };
                cancelBtn.onmouseout = () => {
                    cancelBtn.style.background = 'rgba(255,255,255,0.2)';
                };
                cancelBtn.onclick = (e) => {
                    e.stopPropagation();
                    overlay.remove();
                    header.remove();
                    window.__selectedSelector = null;
                };
                header.appendChild(cancelBtn);
                
                // Track highlighted element
                let highlightedElement = null;
                let highlightBox = null;
                
                // Mouse move handler to highlight elements
                document.addEventListener('mousemove', (e) => {
                    if (!isDragging) {
                        const elementUnderCursor = document.elementFromPoint(e.clientX, e.clientY);
                        
                        if (elementUnderCursor && elementUnderCursor !== overlay && !header.contains(elementUnderCursor)) {
                            if (highlightedElement !== elementUnderCursor) {
                                highlightedElement = elementUnderCursor;
                                
                                // Remove old highlight box
                                if (highlightBox) {
                                    highlightBox.remove();
                                }
                                
                                // Create new highlight box
                                const rect = highlightedElement.getBoundingClientRect();
                                highlightBox = document.createElement('div');
                                highlightBox.style.cssText = `
                                    position: fixed !important;
                                    top: ${rect.top}px !important;
                                    left: ${rect.left}px !important;
                                    width: ${rect.width}px !important;
                                    height: ${rect.height}px !important;
                                    border: 2px solid #667eea !important;
                                    background: rgba(102, 126, 234, 0.1) !important;
                                    z-index: 2147483646 !important;
                                    pointer-events: none !important;
                                    box-shadow: 0 0 20px rgba(102, 126, 234, 0.4) !important;
                                    border-radius: 4px !important;
                                `;
                                document.body.appendChild(highlightBox);
                            }
                        }
                    }
                });
                
                // Click handler to select element
                document.addEventListener('click', function selectHandler(e) {
                    if (!header.contains(e.target)) {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        const elementUnderCursor = document.elementFromPoint(e.clientX, e.clientY);
                        
                        if (elementUnderCursor && elementUnderCursor !== overlay && !header.contains(elementUnderCursor)) {
                            // Helper function to escape special characters in selectors
                            function escapeSelector(str) {
                                if (!str) return '';
                                // Escape quotes and backslashes
                                return str.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/'/g, "\\'");
                            }
                            
                            // Generate selector for the element
                            let selector = null;
                            
                            // Priority 1: Try ID (most reliable)
                            if (elementUnderCursor.id) {
                                selector = '#' + elementUnderCursor.id;
                            }
                            
                            // Priority 2: Try data-testid or data-test attributes
                            if (!selector && elementUnderCursor.getAttribute('data-testid')) {
                                const value = escapeSelector(elementUnderCursor.getAttribute('data-testid'));
                                selector = `[data-testid="${value}"]`;
                            }
                            if (!selector && elementUnderCursor.getAttribute('data-test')) {
                                const value = escapeSelector(elementUnderCursor.getAttribute('data-test'));
                                selector = `[data-test="${value}"]`;
                            }
                            
                            // Priority 3: Try role with accessible name
                            if (!selector && elementUnderCursor.getAttribute('role')) {
                                const role = elementUnderCursor.getAttribute('role');
                                const ariaLabel = elementUnderCursor.getAttribute('aria-label');
                                const innerText = elementUnderCursor.textContent?.trim().slice(0, 30);
                                
                                if (ariaLabel) {
                                    selector = `role=${role}[name="${escapeSelector(ariaLabel)}"]`;
                                } else if (innerText && innerText.length > 0 && innerText.length < 30) {
                                    selector = `role=${role}[name="${escapeSelector(innerText)}"]`;
                                }
                            }
                            
                            // Priority 4: Try text content for links, buttons, labels
                            if (!selector) {
                                const tag = elementUnderCursor.tagName.toLowerCase();
                                const innerText = elementUnderCursor.textContent?.trim();
                                
                                if (['a', 'button', 'label'].includes(tag) && innerText && innerText.length > 0 && innerText.length < 50) {
                                    selector = `${tag}:has-text("${escapeSelector(innerText)}")`;
                                }
                            }
                            
                            // Priority 5: Try placeholder for inputs
                            if (!selector && elementUnderCursor.placeholder) {
                                selector = `[placeholder="${escapeSelector(elementUnderCursor.placeholder)}"]`;
                            }
                            
                            // Priority 6: Try name attribute for form elements
                            if (!selector && elementUnderCursor.getAttribute('name')) {
                                const value = escapeSelector(elementUnderCursor.getAttribute('name'));
                                selector = `[name="${value}"]`;
                            }
                            
                            // Priority 7: Try aria-label
                            if (!selector && elementUnderCursor.getAttribute('aria-label')) {
                                const value = escapeSelector(elementUnderCursor.getAttribute('aria-label'));
                                selector = `[aria-label="${value}"]`;
                            }
                            
                            // Priority 8: Try unique class combinations (but verify uniqueness)
                            if (!selector && elementUnderCursor.className && typeof elementUnderCursor.className === 'string') {
                                const classes = elementUnderCursor.className.trim().split(/\\s+/).filter(c => c && !c.startsWith('_'));
                                if (classes.length > 0) {
                                    const classSelector = '.' + classes.join('.');
                                    // Check if selector is unique
                                    if (document.querySelectorAll(classSelector).length === 1) {
                                        selector = classSelector;
                                    }
                                }
                            }
                            
                            // Priority 9: Fall back to tag name with text content
                            if (!selector) {
                                const tag = elementUnderCursor.tagName.toLowerCase();
                                const innerText = elementUnderCursor.textContent?.trim().slice(0, 30);
                                if (innerText && innerText.length > 0) {
                                    selector = `${tag}:has-text("${escapeSelector(innerText)}")`;
                                }
                            }
                            
                            // Priority 10: Last resort - tag with nth-of-type
                            if (!selector) {
                                const tag = elementUnderCursor.tagName.toLowerCase();
                                const parent = elementUnderCursor.parentElement;
                                if (parent) {
                                    const siblings = Array.from(parent.children).filter(e => e.tagName === elementUnderCursor.tagName);
                                    const index = siblings.indexOf(elementUnderCursor);
                                    selector = `${tag}:nth-of-type(${index + 1})`;
                                } else {
                                    selector = tag;
                                }
                            }
                            
                            console.log('✅ Element selected:', selector);
                            window.__selectedSelector = selector;
                            
                            // Clean up
                            overlay.remove();
                            header.remove();
                            if (highlightBox) {
                                highlightBox.remove();
                            }
                            document.removeEventListener('click', selectHandler);
                        }
                    }
                }, true);
                
                // Add to DOM
                document.body.appendChild(overlay);
                document.body.appendChild(header);
                
                console.log('✅ Element selector widget injected successfully');
            }
            """

            # Inject the script
            if hasattr(self.active_page, 'evaluate'):
                await self.active_page.evaluate(selector_script, failed_locator)
                print("✅ Element selector widget injected successfully")
            else:
                print("❌ Cannot inject selector widget: active_page has no evaluate method")
                if self.widget_injection_complete and hasattr(self.widget_injection_complete, 'set'):
                    self.widget_injection_complete.set()
                return

            # Poll for user selection
            print("⏳ Polling for user element selection...")
            for i in range(600):
                await asyncio.sleep(0.2)
                selected = None
                if hasattr(self.active_page, 'evaluate'):
                    selected = await self.active_page.evaluate('() => window.__selectedSelector')
                if selected:
                    print(f"✅ User selected element: {selected}")
                    self.socket_client.emit('element_selected', {
                        'test_id': test_id,
                        'selector': selected,
                        'failed_locator': failed_locator
                    })
                    if self.widget_injection_complete and hasattr(self.widget_injection_complete, 'set'):
                        self.widget_injection_complete.set()
                    return
            print("⏱️  Element selection polling complete (300s)")
        except Exception as e:
            print(f"❌ Element selector injection error: {e}")
        finally:
            if self.widget_injection_complete and hasattr(self.widget_injection_complete, 'set'):
                self.widget_injection_complete.set()