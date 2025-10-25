#!/usr/bin/env python3
"""
Playwright Codegen Locator Capture Script

This script replicates the core functionality of `npx playwright codegen` by:
1. Launching a browser (Chromium)
2. Opening a specified webpage
3. Capturing and displaying locators for elements that the user clicks
4. Properly closing the browser when finished

Based on analysis of the Playwright source code:
- packages/playwright-core/src/server/recorder.ts - Server-side recorder
- packages/injected/src/recorder/recorder.ts - Browser-injected recorder
- packages/injected/src/selectorGenerator.ts - Selector generation logic
"""

import sys
import asyncio
from playwright.async_api import async_playwright, Page, ElementHandle

class PlaywrightCodegenCapture:
    """
    Captures and displays element locators similar to Playwright's codegen tool.

    The selector generation follows Playwright's priority order:
    1. Test ID attributes (data-testid, etc.)
    2. Role-based locators (accessibility-first approach)
    3. Text content
    4. Label associations
    5. Placeholder text
    6. CSS selectors (fallback)
    """

    def __init__(self, url: str):
        self.url = url
        self.page = None
        self.browser = None
        self.context = None

    async def generate_locator_suggestions(self, element: ElementHandle) -> dict:
        """
        Generate multiple locator suggestions for an element.

        This mimics the selector generation logic from:
        packages/injected/src/selectorGenerator.ts

        The generator prioritizes selectors in order of reliability:
        - Test IDs (score: 1-2)
        - Role with name (score: 100)
        - Placeholder (score: 120)
        - Label (score: 140)
        - Alt text (score: 160)
        - Text content (score: 180)
        - CSS selectors (score: 500+)
        """
        locators = {}

        try:
            # Strategy 1: Test ID attribute (highest priority)
            # From selectorGenerator.ts: kTestIdScore = 1
            test_id = await element.get_attribute('data-testid')
            if test_id:
                locators['testid'] = f'page.get_by_test_id("{test_id}")'

            # Strategy 2: Role-based locator (accessibility-first)
            # From selectorGenerator.ts: kRoleWithNameScore = 100
            role = await element.evaluate('''
                element => {
                    const role = element.getAttribute('role') ||
                                 (element.tagName === 'BUTTON' ? 'button' :
                                  element.tagName === 'A' ? 'link' :
                                  element.tagName === 'INPUT' && element.type === 'text' ? 'textbox' :
                                  element.tagName === 'INPUT' && element.type === 'checkbox' ? 'checkbox' :
                                  null);
                    const name = element.textContent?.trim() ||
                                element.getAttribute('aria-label') ||
                                element.getAttribute('title');
                    return { role, name };
                }
            ''')

            if role.get('role'):
                if role.get('name'):
                    locators['role_with_name'] = f'page.get_by_role("{role["role"]}", name="{role["name"]}")'
                else:
                    locators['role'] = f'page.get_by_role("{role["role"]}")'

            # Strategy 3: Text content
            # From selectorGenerator.ts: kTextScore = 180
            text_content = await element.text_content()
            if text_content and text_content.strip():
                # Use exact match if short, otherwise use contains
                text = text_content.strip()
                if len(text) <= 50:
                    locators['text'] = f'page.get_by_text("{text}", exact=True)'
                else:
                    locators['text_partial'] = f'page.get_by_text("{text[:30]}...", exact=False)'

            # Strategy 4: Label (for form inputs)
            # From selectorGenerator.ts: kLabelScore = 140
            label = await element.evaluate('''
                element => {
                    if (element.id) {
                        const label = document.querySelector(`label[for="${element.id}"]`);
                        if (label) return label.textContent?.trim();
                    }
                    const parentLabel = element.closest('label');
                    if (parentLabel) return parentLabel.textContent?.trim();
                    return null;
                }
            ''')
            if label:
                locators['label'] = f'page.get_by_label("{label}")'

            # Strategy 5: Placeholder
            # From selectorGenerator.ts: kPlaceholderScore = 120
            placeholder = await element.get_attribute('placeholder')
            if placeholder:
                locators['placeholder'] = f'page.get_by_placeholder("{placeholder}")'

            # Strategy 6: Alt text (for images)
            # From selectorGenerator.ts: kAltTextScore = 160
            alt_text = await element.get_attribute('alt')
            if alt_text:
                locators['alt'] = f'page.get_by_alt_text("{alt_text}")'

            # Strategy 7: CSS selector (fallback)
            # From selectorGenerator.ts: kCSSFallbackScore = 10000000
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            css_id = await element.get_attribute('id')
            css_class = await element.get_attribute('class')

            if css_id:
                locators['css_id'] = f'page.locator("#{css_id}")'
            elif css_class:
                classes = css_class.strip().split()[0] if css_class.strip() else None
                if classes:
                    locators['css_class'] = f'page.locator("{tag_name}.{classes}")'
            else:
                locators['css_tag'] = f'page.locator("{tag_name}")'

        except Exception as e:
            locators['error'] = f'Error generating locators: {str(e)}'

        return locators

    async def verify_locator_uniqueness(self, locator_code: str) -> int:
        """
        Verify how many elements a locator matches on the page.
        Returns the count of matching elements.
        """
        try:
            # Extract the actual locator expression from the Python code
            # Handle different locator types
            if 'get_by_test_id' in locator_code:
                test_id = locator_code.split('"')[1]
                count = await self.page.locator(f'[data-testid="{test_id}"]').count()
            elif 'get_by_role' in locator_code:
                # Parse role and name if present
                parts = locator_code.split('"')
                role = parts[1]
                name = parts[3] if len(parts) > 3 and 'name=' in locator_code else None
                if name:
                    count = await self.page.get_by_role(role, name=name).count()
                else:
                    count = await self.page.get_by_role(role).count()
            elif 'get_by_text' in locator_code:
                text = locator_code.split('"')[1]
                exact = 'exact=True' in locator_code
                count = await self.page.get_by_text(text, exact=exact).count()
            elif 'get_by_placeholder' in locator_code:
                placeholder = locator_code.split('"')[1]
                count = await self.page.get_by_placeholder(placeholder).count()
            elif 'get_by_alt_text' in locator_code:
                alt = locator_code.split('"')[1]
                count = await self.page.get_by_alt_text(alt).count()
            elif 'get_by_title' in locator_code:
                title = locator_code.split('"')[1]
                count = await self.page.get_by_title(title).count()
            elif 'get_by_label' in locator_code:
                label = locator_code.split('"')[1]
                count = await self.page.get_by_label(label).count()
            elif 'page.locator' in locator_code:
                # CSS or XPath
                selector = locator_code.split('"')[1]
                count = await self.page.locator(selector).count()
            elif '.filter(' in locator_code or '.get_by_text(' in locator_code:
                # Chained locator - harder to evaluate, skip for now
                count = 999
            else:
                count = 999

            return count
        except Exception as e:
            # If we can't verify, assume it's not unique
            return 999

    async def generate_locators_from_info(self, info: dict) -> dict:
        """
        Generate ALL possible locators from pre-captured element information.
        Returns primary (best) locator and all valid secondary locators.
        """
        primary = None
        secondary = []

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
        elif info['tag'] == 'img':
            role = 'img'
        elif info['tag'] == 'h1':
            role = 'heading'
        elif info['tag'] in ['h2', 'h3', 'h4', 'h5', 'h6']:
            role = 'heading'

        if role:
            name = info.get('text') or info.get('ariaLabel')
            if name:
                loc = f'page.get_by_role("{role}", name="{name}")'
                scores.append((100, loc, 'role_with_name'))
                # Also add exact match variant
                loc_exact = f'page.get_by_role("{role}", name="{name}", exact=True)'
                scores.append((105, loc_exact, 'role_with_name_exact'))
            else:
                loc = f'page.get_by_role("{role}")'
                scores.append((510, loc, 'role'))

        # 3. LABEL LOCATORS (Score: 140)
        # Note: We can't detect actual labels from pre-captured info, but include placeholder
        if info.get('ariaLabel'):
            loc = f'page.get_by_label("{info["ariaLabel"]}")'
            scores.append((140, loc, 'label'))

        # 4. PLACEHOLDER LOCATORS (Score: 120)
        if info.get('placeholder'):
            loc = f'page.get_by_placeholder("{info["placeholder"]}")'
            scores.append((120, loc, 'placeholder'))
            loc_exact = f'page.get_by_placeholder("{info["placeholder"]}", exact=True)'
            scores.append((125, loc_exact, 'placeholder_exact'))

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
                # Exact text match
                loc = f'page.get_by_text("{text}", exact=True)'
                scores.append((185, loc, 'text_exact'))
                # Partial text match
                loc_partial = f'page.get_by_text("{text}")'
                scores.append((180, loc_partial, 'text'))
                # Regex variant
                if len(text) > 3:
                    loc_regex = f'page.get_by_text(re.compile(r"{text[:20]}"))'
                    scores.append((250, loc_regex, 'text_regex'))

        # 7. TITLE LOCATORS (Score: 200)
        if info.get('title'):
            loc = f'page.get_by_title("{info["title"]}")'
            scores.append((200, loc, 'title'))

        # 8. CSS SELECTORS (Score: 500+)
        css_selectors = []

        # CSS by ID
        if info.get('id'):
            loc = f'page.locator("#{info["id"]}")'
            scores.append((500, loc, 'css_id'))
            css_selectors.append(f'#{info["id"]}')

        # CSS by class
        if info.get('classes'):
            classes = info['classes'].strip().split()
            if classes:
                # First class
                loc = f'page.locator("{info["tag"]}.{classes[0]}")'
                scores.append((520, loc, 'css_class'))
                css_selectors.append(f'{info["tag"]}.{classes[0]}')
                # All classes
                all_classes = '.'.join(classes)
                loc_all = f'page.locator("{info["tag"]}.{all_classes}")'
                scores.append((515, loc_all, 'css_all_classes'))
                css_selectors.append(f'{info["tag"]}.{all_classes}')

        # CSS by tag + attributes
        if info.get('type'):
            loc = f'page.locator("{info["tag"]}[type=\\"{info["type"]}\\"]")'
            scores.append((520, loc, 'css_type'))
            css_selectors.append(f'{info["tag"]}[type="{info["type"]}"]')

        if info.get('href'):
            loc = f'page.locator("{info["tag"]}[href=\\"{info["href"]}\\"]")'
            scores.append((525, loc, 'css_href'))
            css_selectors.append(f'{info["tag"]}[href="{info["href"]}"]')

        # CSS by tag only
        loc = f'page.locator("{info["tag"]}")'
        scores.append((530, loc, 'css_tag'))
        css_selectors.append(info["tag"])

        # 9. XPATH SELECTORS (Score: 600+)
        xpath_selectors = []

        # XPath by ID
        if info.get('id'):
            loc = f'page.locator("xpath=//{info["tag"]}[@id=\\"{info["id"]}\\"]")'
            scores.append((600, loc, 'xpath_id'))
            xpath_selectors.append(f'//{info["tag"]}[@id="{info["id"]}"]')

        # XPath by class
        if info.get('classes'):
            classes = info['classes'].strip().split()
            if classes:
                loc = f'page.locator("xpath=//{info["tag"]}[contains(@class, \\"{classes[0]}\\")]")'
                scores.append((610, loc, 'xpath_class'))
                xpath_selectors.append(f'//{info["tag"]}[contains(@class, "{classes[0]}")]')

        # XPath by text
        if info.get('text'):
            text = info['text'].strip()
            if text:
                loc = f'page.locator("xpath=//{info["tag"]}[text()=\\"{text}\\"]")'
                scores.append((620, loc, 'xpath_text'))
                xpath_selectors.append(f'//{info["tag"]}[text()="{text}"]')
                loc_contains = f'page.locator("xpath=//{info["tag"]}[contains(text(), \\"{text[:20]}\\")]")'
                scores.append((625, loc_contains, 'xpath_text_contains'))
                xpath_selectors.append(f'//{info["tag"]}[contains(text(), "{text[:20]}")]')

        # XPath by tag
        loc = f'page.locator("xpath=//{info["tag"]}")'
        scores.append((630, loc, 'xpath_tag'))
        xpath_selectors.append(f'//{info["tag"]}')

        # 10. CHAINED LOCATORS (Score: 300+)
        chained = []

        # Chain: Role + Text filter
        if role and info.get('text'):
            text = info['text'].strip()
            if text:
                loc = f'page.get_by_role("{role}").filter(has_text="{text}")'
                scores.append((300, loc, 'chained_role_text'))
                chained.append(loc)

        # Chain: Locator + Text filter
        if css_selectors and info.get('text'):
            text = info['text'].strip()
            if text and css_selectors[0]:
                loc = f'page.locator("{css_selectors[0]}").filter(has_text="{text}")'
                scores.append((310, loc, 'chained_css_text'))
                chained.append(loc)

        # Chain: Locator + get_by_text
        if css_selectors and info.get('text'):
            text = info['text'].strip()
            if text and css_selectors[0]:
                loc = f'page.locator("{css_selectors[0]}").get_by_text("{text}")'
                scores.append((320, loc, 'chained_css_getbytext'))
                chained.append(loc)

        # INTELLIGENT PRIMARY LOCATOR SELECTION
        # Sort by score (lower is better)
        scores.sort(key=lambda x: x[0])

        # Verify uniqueness for each locator and find the best unique one
        primary = None
        secondary = []
        verified_scores = []

        for score, locator, loc_type in scores:
            # Check how many elements this locator matches
            count = await self.verify_locator_uniqueness(locator)
            verified_scores.append({
                'locator': locator,
                'type': loc_type,
                'score': score,
                'count': count,
                'unique': count == 1
            })

        # Find the best UNIQUE locator (prioritize by score, but must be unique)
        unique_locators = [v for v in verified_scores if v['unique']]

        if unique_locators:
            # Best unique locator becomes primary
            primary = unique_locators[0]
            # All others (unique or not) become secondary
            secondary = [v for v in verified_scores if v != primary]
        else:
            # No unique locator found - use the best score but mark as non-unique
            # Try to build a more specific CSS selector as fallback
            if verified_scores:
                primary = verified_scores[0]
                primary['warning'] = f'⚠️  Matches {primary["count"]} elements - not unique!'
                secondary = verified_scores[1:]

        return {
            'primary': primary,
            'secondary': secondary,
            'css_selectors': css_selectors,
            'xpath_selectors': xpath_selectors,
            'chained': chained
        }

    async def setup_click_handler(self):
        """
        Inject JavaScript to capture click events and highlight elements.

        This mimics the behavior from:
        packages/injected/src/recorder/recorder.ts - RecordActionTool class

        The injected script:
        1. Listens for click events on the page
        2. Prevents default action temporarily
        3. Sends element info back to Python
        4. Highlights clicked elements
        """
        if not self.page:
            return

        await self.page.evaluate('''
            () => {
                // Remove any existing listeners
                if (window.__playwrightCodegenHandler) {
                    document.removeEventListener('click', window.__playwrightCodegenHandler, true);
                }

                // Highlight element on hover (similar to Playwright Inspector)
                let currentHighlight = null;

                document.addEventListener('mouseover', (e) => {
                    if (currentHighlight) {
                        currentHighlight.style.outline = '';
                        currentHighlight.style.backgroundColor = '';
                    }

                    // Highlight color from packages/injected/src/recorder/recorder.ts
                    // HighlightColors.action = '#dc6f6f7f'
                    e.target.style.outline = '2px solid #dc6f6f';
                    e.target.style.backgroundColor = 'rgba(220, 111, 111, 0.1)';
                    currentHighlight = e.target;
                }, true);

                // Click handler - captures element info WITHOUT triggering actions
                // This mimics Playwright codegen behavior - record but don't execute
                const clickHandler = (e) => {
                    const element = e.target;

                    // PREVENT default action (like codegen does)
                    // This stops navigation, form submission, etc.
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();

                    // Capture element info for locator generation
                    window.__lastClickedElementInfo = {
                        tag: element.tagName.toLowerCase(),
                        text: element.textContent?.trim().substring(0, 50),
                        id: element.id || '',
                        classes: element.className || '',
                        testId: element.getAttribute('data-testid') || '',
                        role: element.getAttribute('role') || '',
                        ariaLabel: element.getAttribute('aria-label') || '',
                        placeholder: element.getAttribute('placeholder') || '',
                        alt: element.getAttribute('alt') || '',
                        title: element.getAttribute('title') || '',
                        type: element.getAttribute('type') || '',
                        href: element.getAttribute('href') || '',
                        timestamp: Date.now()
                    };

                    // Visual feedback - flash the element
                    const originalBg = element.style.backgroundColor;
                    element.style.backgroundColor = 'rgba(220, 111, 111, 0.3)';
                    setTimeout(() => {
                        element.style.backgroundColor = originalBg;
                    }, 200);
                };

                window.__playwrightCodegenHandler = clickHandler;
                document.addEventListener('click', clickHandler, true);

                console.log('Playwright Codegen: Click capture enabled');
            }
        ''')

    async def start_capture(self):
        """
        Main capture loop - launches browser and listens for user interactions.

        Flow mirrors Playwright's recorder:
        1. Launch browser with recorder mode enabled
        2. Navigate to target URL
        3. Inject event listeners
        4. Wait for user interactions
        5. Generate and display locators
        """
        async with async_playwright() as p:
            print("🎭 Playwright Codegen Locator Capture")
            print("=" * 60)
            print(f"Opening: {self.url}")
            print("\nInstructions:")
            print("  • Click on any element to see its locators")
            print("  • Press Ctrl+C to exit")
            print("=" * 60)
            print()

            # Launch browser in headed mode (similar to codegen)
            # From recorder.ts: browser is launched with headful mode
            self.browser = await p.chromium.launch(
                headless=False,
                args=['--disable-blink-features=AutomationControlled']
            )

            # Create context (similar to Recorder._create in recorder.ts)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

            # Navigate to URL
            await self.page.goto(self.url)

            # Inject click capture handler
            await self.setup_click_handler()

            # Monitor for clicks (actions are prevented like codegen)
            # Elements are recorded but not executed
            last_processed_timestamp = 0

            try:
                while True:
                    # Check if a new element was clicked
                    element_info = await self.page.evaluate(
                        '() => window.__lastClickedElementInfo'
                    )

                    if element_info and element_info.get('timestamp', 0) > last_processed_timestamp:
                        last_processed_timestamp = element_info['timestamp']

                        # Display element info
                        print(f"\n{'='*70}")
                        print(f"🎯 Element: <{element_info['tag']}>")
                        if element_info.get('id'):
                            print(f"   ID: {element_info['id']}")
                        if element_info.get('text'):
                            print(f"   Text: {element_info['text']}")
                        if element_info.get('href'):
                            print(f"   Href: {element_info['href']}")
                        print(f"{'='*70}")

                        # Generate all possible locators (with uniqueness verification)
                        result = await self.generate_locators_from_info(element_info)

                        # Build locators dictionary
                        primary_info = {
                            'locator': result['primary']['locator'] if result['primary'] else None,
                            'count': result['primary']['count'] if result['primary'] else 0,
                            'unique': result['primary']['unique'] if result['primary'] else False
                        }

                        # Add warning if not unique
                        if result['primary'] and result['primary'].get('warning'):
                            primary_info['warning'] = result['primary']['warning']

                        locators_dict = {
                            'primary_locator': primary_info,
                            'all_locators': {}
                        }

                        # Organize by method type
                        by_role = []
                        by_text = []
                        by_label = []
                        by_placeholder = []
                        by_alt = []
                        by_title = []
                        by_testid = []
                        css_locators = []
                        xpath_locators = []
                        chained_locators = []

                        # Add primary (with uniqueness info)
                        if result['primary']:
                            loc_type = result['primary']['type']
                            loc_str = result['primary']['locator']
                            count = result['primary']['count']
                            unique = result['primary']['unique']

                            loc_with_info = {
                                'locator': loc_str,
                                'count': count,
                                'unique': unique
                            }

                            if 'role' in loc_type:
                                by_role.append(loc_with_info)
                            elif 'text' in loc_type:
                                by_text.append(loc_with_info)
                            elif 'label' in loc_type:
                                by_label.append(loc_with_info)
                            elif 'placeholder' in loc_type:
                                by_placeholder.append(loc_with_info)
                            elif 'alt' in loc_type:
                                by_alt.append(loc_with_info)
                            elif 'title' in loc_type:
                                by_title.append(loc_with_info)
                            elif 'testid' in loc_type:
                                by_testid.append(loc_with_info)
                            elif 'css' in loc_type:
                                css_locators.append(loc_with_info)
                            elif 'xpath' in loc_type:
                                xpath_locators.append(loc_with_info)
                            elif 'chained' in loc_type:
                                chained_locators.append(loc_with_info)

                        # Add secondary (with uniqueness info)
                        for sec in result['secondary']:
                            loc_type = sec['type']
                            loc_str = sec['locator']
                            count = sec['count']
                            unique = sec['unique']

                            # Format: "locator_string (count: N, unique: True/False)"
                            loc_with_info = {
                                'locator': loc_str,
                                'count': count,
                                'unique': unique
                            }

                            if 'role' in loc_type:
                                by_role.append(loc_with_info)
                            elif 'text' in loc_type:
                                by_text.append(loc_with_info)
                            elif 'label' in loc_type:
                                by_label.append(loc_with_info)
                            elif 'placeholder' in loc_type:
                                by_placeholder.append(loc_with_info)
                            elif 'alt' in loc_type:
                                by_alt.append(loc_with_info)
                            elif 'title' in loc_type:
                                by_title.append(loc_with_info)
                            elif 'testid' in loc_type:
                                by_testid.append(loc_with_info)
                            elif 'css' in loc_type:
                                css_locators.append(loc_with_info)
                            elif 'xpath' in loc_type:
                                xpath_locators.append(loc_with_info)
                            elif 'chained' in loc_type:
                                chained_locators.append(loc_with_info)

                        # Build final dictionary
                        if by_testid:
                            locators_dict['all_locators']['getByTestId'] = by_testid
                        if by_role:
                            locators_dict['all_locators']['getByRole'] = by_role
                        if by_text:
                            locators_dict['all_locators']['getByText'] = by_text
                        if by_label:
                            locators_dict['all_locators']['getByLabel'] = by_label
                        if by_placeholder:
                            locators_dict['all_locators']['getByPlaceholder'] = by_placeholder
                        if by_alt:
                            locators_dict['all_locators']['getByAltText'] = by_alt
                        if by_title:
                            locators_dict['all_locators']['getByTitle'] = by_title
                        if css_locators:
                            locators_dict['all_locators']['locator_css'] = css_locators
                        if xpath_locators:
                            locators_dict['all_locators']['locator_xpath'] = xpath_locators
                        if chained_locators:
                            locators_dict['all_locators']['chained_locators'] = chained_locators

                        # Also include raw CSS and XPath selectors
                        if result['css_selectors']:
                            locators_dict['css_selectors'] = result['css_selectors']
                        if result['xpath_selectors']:
                            locators_dict['xpath_selectors'] = result['xpath_selectors']

                        # Display as formatted dictionary
                        import json
                        print("\n📍 LOCATORS DICTIONARY:")
                        print(json.dumps(locators_dict, indent=2))
                        print()

                    # Small delay to prevent high CPU usage
                    await asyncio.sleep(0.1)

            except KeyboardInterrupt:
                print("\n\n👋 Exiting Playwright Codegen Capture...")
            finally:
                # Cleanup: close browser properly
                # This mirrors the cleanup in recorder.ts
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
                print("✓ Browser closed successfully")

def main():
    """
    Entry point - parses URL from command line arguments.

    Usage:
        python playwright_codegen.py <URL>
        python playwright_codegen.py https://example.com
    """
    if len(sys.argv) < 2:
        print("Usage: python playwright_codegen.py <URL>")
        print("\nExample:")
        print("  python playwright_codegen.py https://example.com")
        print("  python playwright_codegen.py https://playwright.dev")
        sys.exit(1)

    url = sys.argv[1]

    # Ensure URL has a protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Create and run the capture tool
    capture = PlaywrightCodegenCapture(url)

    try:
        asyncio.run(capture.start_capture())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
