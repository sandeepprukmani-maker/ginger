"""
DOM Inspector Service
Analyzes web pages to extract element information for intelligent locator selection.
"""
import asyncio
import re
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Page


class DOMInspector:
    """Inspects DOM structure to help AI select perfect locators"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
    
    async def analyze_page(self, url: str, user_command: str) -> Dict:
        """
        Navigate to a page and extract element information for intelligent locator selection.
        
        Args:
            url: The URL to analyze
            user_command: The user's natural language command to understand intent
            
        Returns:
            Dict containing available elements, their attributes, and recommended locators
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate to the page
                await page.goto(url, timeout=15000, wait_until='domcontentloaded')
                
                # Extract page information
                page_info = {
                    'url': url,
                    'title': await page.title(),
                    'interactive_elements': await self._extract_interactive_elements(page),
                    'form_elements': await self._extract_form_elements(page),
                    'navigation_elements': await self._extract_navigation_elements(page),
                    'intent_matched_elements': await self._match_user_intent(page, user_command)
                }
                
                await browser.close()
                return page_info
                
        except Exception as e:
            return {
                'error': str(e),
                'url': url,
                'message': 'Could not inspect DOM, AI will use standard locator strategies'
            }
    
    async def _extract_interactive_elements(self, page: Page) -> List[Dict]:
        """Extract all interactive elements (buttons, links, inputs)"""
        try:
            elements = await page.evaluate('''() => {
                const elements = [];
                
                // Buttons
                document.querySelectorAll('button, input[type="button"], input[type="submit"]').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {  // Only visible elements
                        elements.push({
                            type: 'button',
                            text: el.textContent.trim() || el.value || '',
                            role: el.getAttribute('role') || 'button',
                            name: el.getAttribute('aria-label') || el.textContent.trim() || el.value || '',
                            id: el.id,
                            testid: el.getAttribute('data-testid'),
                            classes: el.className
                        });
                    }
                });
                
                // Links
                document.querySelectorAll('a').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        elements.push({
                            type: 'link',
                            text: el.textContent.trim(),
                            href: el.href,
                            role: el.getAttribute('role') || 'link',
                            name: el.getAttribute('aria-label') || el.textContent.trim(),
                            id: el.id,
                            testid: el.getAttribute('data-testid')
                        });
                    }
                });
                
                return elements;
            }''')
            return elements
        except:
            return []
    
    async def _extract_form_elements(self, page: Page) -> List[Dict]:
        """Extract form inputs with their labels and attributes"""
        try:
            elements = await page.evaluate('''() => {
                const elements = [];
                
                // Text inputs, textareas
                document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], input[type="search"], input:not([type]), textarea').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        // Find associated label
                        let labelText = '';
                        if (el.id) {
                            const label = document.querySelector(`label[for="${el.id}"]`);
                            if (label) labelText = label.textContent.trim();
                        }
                        if (!labelText) {
                            const parentLabel = el.closest('label');
                            if (parentLabel) labelText = parentLabel.textContent.trim();
                        }
                        
                        elements.push({
                            type: 'input',
                            inputType: el.type || 'text',
                            placeholder: el.placeholder,
                            label: labelText,
                            role: el.getAttribute('role') || (el.type === 'search' ? 'combobox' : 'textbox'),
                            name: el.getAttribute('aria-label') || labelText || el.placeholder || '',
                            id: el.id,
                            testid: el.getAttribute('data-testid'),
                            autocomplete: el.autocomplete
                        });
                    }
                });
                
                // Checkboxes and radios
                document.querySelectorAll('input[type="checkbox"], input[type="radio"]').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        let labelText = '';
                        if (el.id) {
                            const label = document.querySelector(`label[for="${el.id}"]`);
                            if (label) labelText = label.textContent.trim();
                        }
                        
                        elements.push({
                            type: el.type,
                            label: labelText,
                            role: el.type,
                            name: el.getAttribute('aria-label') || labelText || '',
                            id: el.id,
                            testid: el.getAttribute('data-testid')
                        });
                    }
                });
                
                // Select dropdowns
                document.querySelectorAll('select').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        let labelText = '';
                        if (el.id) {
                            const label = document.querySelector(`label[for="${el.id}"]`);
                            if (label) labelText = label.textContent.trim();
                        }
                        
                        elements.push({
                            type: 'select',
                            label: labelText,
                            role: 'combobox',
                            name: el.getAttribute('aria-label') || labelText || '',
                            id: el.id,
                            testid: el.getAttribute('data-testid')
                        });
                    }
                });
                
                return elements;
            }''')
            return elements
        except:
            return []
    
    async def _extract_navigation_elements(self, page: Page) -> List[Dict]:
        """Extract navigation elements (nav links, menus)"""
        try:
            elements = await page.evaluate('''() => {
                const elements = [];
                
                document.querySelectorAll('nav a, [role="navigation"] a').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        elements.push({
                            type: 'nav-link',
                            text: el.textContent.trim(),
                            href: el.href,
                            role: 'link',
                            name: el.textContent.trim()
                        });
                    }
                });
                
                return elements;
            }''')
            return elements
        except:
            return []
    
    async def _match_user_intent(self, page: Page, user_command: str) -> List[Dict]:
        """
        Match user intent to specific elements on the page.
        For example: "search for cats" -> find search box
        """
        command_lower = user_command.lower()
        matched_elements = []
        
        # Search intent
        if any(word in command_lower for word in ['search', 'find', 'look for', 'query']):
            search_elements = await page.evaluate('''() => {
                const elements = [];
                
                // Find search inputs
                document.querySelectorAll('input[type="search"], input[name*="search" i], input[placeholder*="search" i], input[aria-label*="search" i]').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        elements.push({
                            type: 'search-input',
                            placeholder: el.placeholder,
                            role: el.getAttribute('role') || 'combobox',
                            name: el.getAttribute('aria-label') || el.placeholder || 'Search',
                            testid: el.getAttribute('data-testid'),
                            id: el.id,
                            recommended_locator: el.getAttribute('aria-label') 
                                ? `get_by_role("combobox", name="${el.getAttribute('aria-label')}")`
                                : (el.placeholder ? `get_by_placeholder("${el.placeholder}")` : null)
                        });
                    }
                });
                
                return elements;
            }''')
            matched_elements.extend(search_elements)
        
        # Login intent
        if any(word in command_lower for word in ['login', 'log in', 'sign in', 'signin']):
            login_elements = await page.evaluate('''() => {
                const elements = [];
                
                // Find login buttons
                document.querySelectorAll('button, a, input[type="submit"]').forEach(el => {
                    const text = el.textContent.trim() || el.value || '';
                    if (text.match(/log ?in|sign ?in/i)) {
                        elements.push({
                            type: 'login-button',
                            text: text,
                            role: 'button',
                            name: text,
                            recommended_locator: `get_by_role("button", name="${text}")`
                        });
                    }
                });
                
                return elements;
            }''')
            matched_elements.extend(login_elements)
        
        # Submit intent
        if any(word in command_lower for word in ['submit', 'send', 'post']):
            submit_elements = await page.evaluate('''() => {
                const elements = [];
                
                document.querySelectorAll('button[type="submit"], input[type="submit"], button').forEach(el => {
                    const text = el.textContent.trim() || el.value || '';
                    if (text.match(/submit|send|post|continue|next/i)) {
                        elements.push({
                            type: 'submit-button',
                            text: text,
                            role: 'button',
                            name: text,
                            recommended_locator: `get_by_role("button", name="${text}")`
                        });
                    }
                });
                
                return elements;
            }''')
            matched_elements.extend(submit_elements)
        
        return matched_elements
    
    def generate_locator_recommendations(self, page_info: Dict) -> str:
        """
        Generate a detailed report of available locators for the AI to use.
        """
        if 'error' in page_info:
            return ""
        
        recommendations = []
        recommendations.append("=== REAL PAGE ANALYSIS ===")
        recommendations.append(f"Page: {page_info.get('title', 'Unknown')} ({page_info.get('url', '')})")
        recommendations.append("")
        
        # Intent-matched elements (highest priority)
        if page_info.get('intent_matched_elements'):
            recommendations.append("🎯 ELEMENTS MATCHING USER INTENT (Use these first!):")
            for elem in page_info['intent_matched_elements'][:5]:
                if elem.get('recommended_locator'):
                    recommendations.append(f"  • {elem['type']}: {elem.get('text', elem.get('name', ''))} → {elem['recommended_locator']}")
                else:
                    recommendations.append(f"  • {elem['type']}: {elem.get('text', elem.get('name', ''))}")
            recommendations.append("")
        
        # Form elements
        if page_info.get('form_elements'):
            recommendations.append("📝 FORM ELEMENTS AVAILABLE:")
            for elem in page_info['form_elements'][:10]:
                locators = []
                if elem.get('testid'):
                    locators.append(f"get_by_test_id(\"{elem['testid']}\")")
                if elem.get('label'):
                    locators.append(f"get_by_label(\"{elem['label']}\")")
                if elem.get('placeholder'):
                    locators.append(f"get_by_placeholder(\"{elem['placeholder']}\")")
                if elem.get('role') and elem.get('name'):
                    locators.append(f"get_by_role(\"{elem['role']}\", name=\"{elem['name']}\")")
                
                if locators:
                    recommendations.append(f"  • {elem.get('type', 'input')} ({elem.get('inputType', '')}): {' OR '.join(locators[:2])}")
            recommendations.append("")
        
        # Interactive elements
        if page_info.get('interactive_elements'):
            recommendations.append("🔘 BUTTONS & LINKS AVAILABLE:")
            for elem in page_info['interactive_elements'][:10]:
                locators = []
                if elem.get('testid'):
                    locators.append(f"get_by_test_id(\"{elem['testid']}\")")
                if elem.get('role') and elem.get('name'):
                    locators.append(f"get_by_role(\"{elem['role']}\", name=\"{elem['name']}\")")
                if elem.get('text'):
                    locators.append(f"get_by_text(\"{elem['text']}\", exact=True)")
                
                if locators:
                    recommendations.append(f"  • {elem.get('type', 'element')}: {locators[0]}")
            recommendations.append("")
        
        recommendations.append("✅ USE THESE EXACT LOCATORS - They are confirmed to exist on the page!")
        recommendations.append("=" * 60)
        
        return "\n".join(recommendations)


# Singleton instance
dom_inspector = DOMInspector()
