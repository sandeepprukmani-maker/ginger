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

            # ENHANCED HEALING: Detect ALL error types and handle intelligently
            # CRITICAL FIX: Error detection runs EVEN WITHOUT active_page to catch API/code errors
            # IMPORTANT: Send request_ai_healing BEFORE healing_attempt_result to avoid race condition
            if not headless and not result.get('success'):
                # Extract error details using enhanced detection
                error_msg = ' '.join(result.get('logs', []))
                error_info = extract_failed_locator_local(error_msg)

                if error_info and error_info.get('is_healable'):
                    error_type = error_info.get('type', 'unknown')
                    print(f"🔍 DETECTED ERROR TYPE: {error_type}")
                    print(f"📋 Error details: {error_info.get('detail', error_info.get('full_error', 'No details'))[:200]}")

                    # Handle different error types with appropriate healing strategy
                    if error_type in ['api_misuse', 'general_error']:
                        # API/Code errors: Request AI regeneration (works WITHOUT page)
                        print(f"🤖 API/Code error detected - requesting AI regeneration")
                        print(f"💡 Server will automatically retry with improved code generation")
                        # Emit AI healing request FIRST (before result) to avoid race condition
                        self.socket_client.emit('request_ai_healing', {
                            'test_id': test_id,
                            'error_type': error_type,
                            'error_info': error_info,
                            'attempt': attempt
                        })
                        # Then emit result to server for tracking
                        self.socket_client.emit('healing_attempt_result', {
                            'test_id': test_id,
                            'success': result.get('success', False),
                            'logs': result.get('logs', []),
                            'screenshot': screenshot_b64
                        })
                        # Close browser, server will retry with new code
                        await self.cleanup_browser()
                        return  # Early return to avoid sending result twice
                        
                    elif error_type in ['locator_not_found', 'timeout', 'element_not_found', 'multiple_matches']:
                        # Locator errors: Require active page for widget
                        if self.active_page:
                            failed_locator = error_info.get('locator', 'unknown')
                            print(f"🎯 LOCATOR ERROR: {failed_locator}")
                            print(f"🚀 Injecting element selector widget for user guidance...")

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
                                # Send result back to server
                                self.socket_client.emit('healing_attempt_result', {
                                    'test_id': test_id,
                                    'success': result.get('success', False),
                                    'logs': result.get('logs', []),
                                    'screenshot': screenshot_b64
                                })
                                await self.cleanup_browser()
                        else:
                            print(f"⚠️  Locator error but no active page - cannot inject widget")
                            print(f"💡 Falling back to AI regeneration instead")
                            # Emit AI healing request FIRST (before result) to avoid race condition
                            self.socket_client.emit('request_ai_healing', {
                                'test_id': test_id,
                                'error_type': 'locator_without_page',
                                'error_info': error_info,
                                'attempt': attempt
                            })
                            # Then emit result to server for tracking
                            self.socket_client.emit('healing_attempt_result', {
                                'test_id': test_id,
                                'success': result.get('success', False),
                                'logs': result.get('logs', []),
                                'screenshot': screenshot_b64
                            })
                            await self.cleanup_browser()
                            return  # Early return to avoid sending result twice
                    else:
                        print(f"⚠️  Unknown healable error type: {error_type} - closing browser")
                        # Send result for cases that don't use AI healing
                        self.socket_client.emit('healing_attempt_result', {
                            'test_id': test_id,
                            'success': result.get('success', False),
                            'logs': result.get('logs', []),
                            'screenshot': screenshot_b64
                        })
                        await self.cleanup_browser()
                else:
                    print(f"ℹ️  No healable error detected (non-recoverable or success) - browser will close normally")
                    # Send result for cases that don't use AI healing
                    self.socket_client.emit('healing_attempt_result', {
                        'test_id': test_id,
                        'success': result.get('success', False),
                        'logs': result.get('logs', []),
                        'screenshot': screenshot_b64
                    })
                    await self.cleanup_browser()
            else:
                # For headless mode or success cases, always send result
                self.socket_client.emit('healing_attempt_result', {
                    'test_id': test_id,
                    'success': result.get('success', False),
                    'logs': result.get('logs', []),
                    'screenshot': screenshot_b64
                })

        except Exception as e:
            print(f"💥 Healing attempt error: {e}")
            import traceback
            traceback.print_exc()
            self.socket_client.emit('healing_attempt_result',
                                    {'test_id': test_id, 'success': False, 'logs': [str(e)], 'screenshot': None})
            await self.cleanup_browser()

    async def verify_locator_uniqueness(self, locator_code: str) -> int:
        """
        Verify how many elements a locator matches on the page.
        Returns the count of matching elements.
        From playwright_codegen_2.py - Fixed to handle attribute selectors correctly
        """
        if not self.active_page:
            return 999
            
        try:
            # Use regex to extract selector strings properly, handling escaped quotes
            import re
            
            # Extract the actual locator expression from the Python code
            if 'get_by_test_id' in locator_code:
                # Extract: page.get_by_test_id("value")
                match = re.search(r'get_by_test_id\("([^"]+)"\)', locator_code)
                if match:
                    test_id = match.group(1)
                    count = await self.active_page.locator(f'[data-testid="{test_id}"]').count()
                else:
                    return 999
            elif 'get_by_role' in locator_code:
                # Extract: page.get_by_role("role", name="name")
                role_match = re.search(r'get_by_role\("([^"]+)"', locator_code)
                name_match = re.search(r'name="([^"]+)"', locator_code)
                if role_match:
                    role = role_match.group(1)
                    name = name_match.group(1) if name_match else None
                    if name:
                        count = await self.active_page.get_by_role(role, name=name).count()
                    else:
                        count = await self.active_page.get_by_role(role).count()
                else:
                    return 999
            elif 'get_by_text' in locator_code:
                # Extract: page.get_by_text("text", exact=True)
                match = re.search(r'get_by_text\("([^"]+)"', locator_code)
                if match:
                    text = match.group(1)
                    exact = 'exact=True' in locator_code
                    count = await self.active_page.get_by_text(text, exact=exact).count()
                else:
                    return 999
            elif 'get_by_placeholder' in locator_code:
                # Extract: page.get_by_placeholder("placeholder")
                match = re.search(r'get_by_placeholder\("([^"]+)"', locator_code)
                if match:
                    placeholder = match.group(1)
                    count = await self.active_page.get_by_placeholder(placeholder).count()
                else:
                    return 999
            elif 'get_by_alt_text' in locator_code:
                # Extract: page.get_by_alt_text("alt")
                match = re.search(r'get_by_alt_text\("([^"]+)"', locator_code)
                if match:
                    alt = match.group(1)
                    count = await self.active_page.get_by_alt_text(alt).count()
                else:
                    return 999
            elif 'get_by_title' in locator_code:
                # Extract: page.get_by_title("title")
                match = re.search(r'get_by_title\("([^"]+)"', locator_code)
                if match:
                    title = match.group(1)
                    count = await self.active_page.get_by_title(title).count()
                else:
                    return 999
            elif 'get_by_label' in locator_code:
                # Extract: page.get_by_label("label")
                match = re.search(r'get_by_label\("([^"]+)"', locator_code)
                if match:
                    label = match.group(1)
                    count = await self.active_page.get_by_label(label).count()
                else:
                    return 999
            elif 'page.locator' in locator_code:
                # CSS or XPath - handle escaped quotes properly
                # Extract: page.locator("selector") where selector may contain \" 
                match = re.search(r'page\.locator\("([^"\\]*(\\.[^"\\]*)*)"\)', locator_code)
                if match:
                    selector = match.group(1).replace('\\"', '"')  # Unescape quotes
                    count = await self.active_page.locator(selector).count()
                else:
                    return 999
            else:
                count = 999

            return count
        except Exception as e:
            print(f"⚠️  Locator verification error for '{locator_code}': {e}")
            # If we can't verify, assume it's not unique
            return 999

    async def generate_best_locator(self, info: dict):
        """
        Generate ALL possible locators from pre-captured element information.
        Returns the best UNIQUE locator with highest success rate.
        Based on playwright_codegen_2.py logic
        """
        # Score tracking to determine primary locator (lower score = better)
        scores = []

        # 1. TEST ID LOCATORS (Score: 1 - highest priority)
        if info.get('testId'):
            loc = f'page.get_by_test_id("{info["testId"]}")'
            scores.append((1, loc, 'testid'))

        # 2. ROLE-BASED LOCATORS (Score: 100-150)
        role = None
        if info.get('role'):
            role = info['role']
        elif info['tag'] == 'button':
            role = 'button'
        elif info['tag'] == 'a':
            role = 'link'
        elif info['tag'] == 'input':
            input_type = info.get('type', '')
            if input_type == 'text' or input_type == '':
                role = 'textbox'
            elif input_type == 'checkbox':
                role = 'checkbox'
            elif input_type == 'radio':
                role = 'radio'
            elif input_type == 'submit':
                role = 'button'

        if role:
            name = info.get('text') or info.get('ariaLabel')
            if name:
                loc = f'page.get_by_role("{role}", name="{name}")'
                scores.append((100, loc, 'role_with_name'))
                loc_exact = f'page.get_by_role("{role}", name="{name}", exact=True)'
                scores.append((105, loc_exact, 'role_with_name_exact'))
            else:
                loc = f'page.get_by_role("{role}")'
                scores.append((510, loc, 'role'))

        # 3. PLACEHOLDER LOCATORS (Score: 120)
        if info.get('placeholder'):
            loc = f'page.get_by_placeholder("{info["placeholder"]}")'
            scores.append((120, loc, 'placeholder'))
            loc_exact = f'page.get_by_placeholder("{info["placeholder"]}", exact=True)'
            scores.append((125, loc_exact, 'placeholder_exact'))

        # 4. LABEL LOCATORS (Score: 140)
        if info.get('ariaLabel'):
            loc = f'page.get_by_label("{info["ariaLabel"]}")'
            scores.append((140, loc, 'label'))

        # 5. ALT TEXT LOCATORS (Score: 160)
        if info.get('alt'):
            loc = f'page.get_by_alt_text("{info["alt"]}")'
            scores.append((160, loc, 'alt'))
            loc_exact = f'page.get_by_alt_text("{info["alt"]}", exact=True)'
            scores.append((165, loc_exact, 'alt_exact'))

        # 6. TEXT LOCATORS (Score: 180)
        if info.get('text'):
            text = info['text'].strip()
            if text:
                loc = f'page.get_by_text("{text}", exact=True)'
                scores.append((185, loc, 'text_exact'))
                loc_partial = f'page.get_by_text("{text}")'
                scores.append((180, loc_partial, 'text'))

        # 7. TITLE LOCATORS (Score: 200)
        if info.get('title'):
            loc = f'page.get_by_title("{info["title"]}")'
            scores.append((200, loc, 'title'))

        # 8. CSS SELECTORS (Score: 500+)
        if info.get('id'):
            loc = f'page.locator("#{info["id"]}")'
            scores.append((500, loc, 'css_id'))

        if info.get('classes'):
            classes = info['classes'].strip().split()
            if classes:
                loc = f'page.locator("{info["tag"]}.{classes[0]}")'
                scores.append((520, loc, 'css_class'))

        if info.get('type'):
            loc = f'page.locator("{info["tag"]}[type=\\"{info["type"]}\\"]")'
            scores.append((520, loc, 'css_type'))

        # 9. Fallback to tag
        loc = f'page.locator("{info["tag"]}")'
        scores.append((530, loc, 'css_tag'))

        # Sort by score (lower is better)
        scores.sort(key=lambda x: x[0])

        # Verify uniqueness for each locator and find the best unique one
        print(f"🔍 Testing {len(scores)} locator strategies for uniqueness...")
        
        for score, locator, loc_type in scores:
            # Check how many elements this locator matches
            count = await self.verify_locator_uniqueness(locator)
            print(f"  - {loc_type}: {locator} → matches {count} element(s)")
            
            if count == 1:
                # Found a unique locator!
                return {
                    'locator': locator,
                    'type': loc_type,
                    'score': score,
                    'count': count,
                    'unique': True
                }

        # No unique locator found - use the best score but warn
        if scores:
            score, locator, loc_type = scores[0]
            count = await self.verify_locator_uniqueness(locator)
            print(f"⚠️  No unique locator found. Using best score: {loc_type} (matches {count} elements)")
            return {
                'locator': locator,
                'type': loc_type,
                'score': score,
                'count': count,
                'unique': False
            }

        return None

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
                let dragOffsetX = 0;
                let dragOffsetY = 0;
                
                header.addEventListener('mousedown', (e) => {
                    if (e.target.tagName !== 'BUTTON') {
                        isDragging = true;
                        const rect = header.getBoundingClientRect();
                        dragOffsetX = e.clientX - rect.left;
                        dragOffsetY = e.clientY - rect.top;
                        header.style.transition = 'none';
                    }
                });
                
                document.addEventListener('mousemove', (e) => {
                    if (isDragging) {
                        e.preventDefault();
                        const newX = e.clientX - dragOffsetX;
                        const newY = e.clientY - dragOffsetY;
                        header.style.left = newX + 'px';
                        header.style.top = newY + 'px';
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
                
                // Click handler to select element - Comprehensive info capture
                document.addEventListener('click', function selectHandler(e) {
                    if (!header.contains(e.target)) {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        const element = document.elementFromPoint(e.clientX, e.clientY);
                        
                        if (element && element !== overlay && !header.contains(element)) {
                            // Capture comprehensive element information
                            // This follows the approach from playwright_codegen_2.py
                            window.__selectedElementInfo = {
                                tag: element.tagName.toLowerCase(),
                                text: element.textContent?.trim().substring(0, 100) || '',
                                id: element.id || '',
                                classes: element.className || '',
                                testId: element.getAttribute('data-testid') || element.getAttribute('data-test') || '',
                                role: element.getAttribute('role') || '',
                                ariaLabel: element.getAttribute('aria-label') || '',
                                placeholder: element.getAttribute('placeholder') || '',
                                alt: element.getAttribute('alt') || '',
                                title: element.getAttribute('title') || '',
                                type: element.getAttribute('type') || '',
                                href: element.getAttribute('href') || '',
                                name: element.getAttribute('name') || '',
                                value: element.getAttribute('value') || '',
                                timestamp: Date.now()
                            };
                            
                            console.log('✅ Element info captured:', window.__selectedElementInfo);
                            
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
                element_info = None
                if hasattr(self.active_page, 'evaluate'):
                    element_info = await self.active_page.evaluate('() => window.__selectedElementInfo')
                if element_info:
                    print(f"✅ Element info captured: {element_info}")
                    
                    # Generate all possible locators with scoring and uniqueness verification
                    best_locator = await self.generate_best_locator(element_info)
                    
                    if best_locator:
                        print(f"✅ Best locator selected: {best_locator['locator']} (type: {best_locator['type']}, score: {best_locator['score']}, unique: {best_locator['unique']})")
                        self.socket_client.emit('element_selected', {
                            'test_id': test_id,
                            'selector': best_locator['locator'],
                            'failed_locator': failed_locator,
                            'locator_type': best_locator['type'],
                            'score': best_locator['score'],
                            'unique': best_locator['unique']
                        })
                    else:
                        print("⚠️  No unique locator found, using fallback")
                        self.socket_client.emit('element_selected', {
                            'test_id': test_id,
                            'selector': f"#{element_info.get('id')}" if element_info.get('id') else element_info.get('tag', 'div'),
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