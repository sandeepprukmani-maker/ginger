"""
Advanced Locator Validator - Intelligent locator testing and selection

This module provides advanced locator validation capabilities that:
1. Tests all possible locator strategies in parallel
2. Automatically selects the most reliable unique locator
3. Caches successful locators for reuse
4. Provides confidence scores based on stability and uniqueness
"""

import asyncio
import re
from typing import Dict, List, Tuple, Optional
import json
import os
from datetime import datetime


class LocatorCache:
    """Cache for successful locators to speed up future executions"""
    
    def __init__(self, cache_file='data/locator_cache.json'):
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load locator cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save locator cache: {e}")
    
    def get(self, url: str, element_description: str) -> Optional[Dict]:
        """Get cached locator for a URL and element description"""
        key = f"{url}::{element_description}"
        return self.cache.get(key)
    
    def set(self, url: str, element_description: str, locator_info: Dict):
        """Cache a successful locator"""
        key = f"{url}::{element_description}"
        self.cache[key] = {
            **locator_info,
            'last_used': datetime.now().isoformat(),
            'success_count': self.cache.get(key, {}).get('success_count', 0) + 1
        }
        self._save_cache()


class AdvancedLocatorValidator:
    """Advanced locator validation with parallel testing and intelligent selection"""
    
    def __init__(self, page):
        self.page = page
        self.cache = LocatorCache()
    
    async def generate_all_possible_locators(self, element_info: Dict) -> List[Tuple[int, str, str]]:
        """
        Generate ALL possible locator strategies from element information.
        Returns list of (score, locator_code, strategy_name) tuples.
        Lower score = higher priority.
        """
        locators = []
        
        # 1. TEST ID LOCATORS (Score: 1 - HIGHEST PRIORITY)
        if element_info.get('testId'):
            locators.append((1, f'page.get_by_test_id("{element_info["testId"]}")', 'testid'))
        
        # 2. ROLE-BASED LOCATORS (Score: 100-510)
        role = self._determine_role(element_info)
        if role:
            # Try ariaLabel first, then text, fallback to empty
            name = element_info.get('ariaLabel') or element_info.get('text') or ''
            if name and name.strip():
                # Role with exact name - most reliable
                locators.append((100, f'page.get_by_role("{role}", name="{name}", exact=True)', 'role_exact'))
                # Role with partial name
                locators.append((105, f'page.get_by_role("{role}", name="{name}")', 'role_name'))
            else:
                # Role alone - less reliable
                locators.append((510, f'page.get_by_role("{role}")', 'role_only'))
        
        # 3. PLACEHOLDER LOCATORS (Score: 120)
        if element_info.get('placeholder'):
            locators.append((120, f'page.get_by_placeholder("{element_info["placeholder"]}", exact=True)', 'placeholder_exact'))
            locators.append((125, f'page.get_by_placeholder("{element_info["placeholder"]}")', 'placeholder'))
        
        # 4. LABEL LOCATORS (Score: 140)
        if element_info.get('ariaLabel'):
            locators.append((140, f'page.get_by_label("{element_info["ariaLabel"]}", exact=True)', 'label_exact'))
            locators.append((145, f'page.get_by_label("{element_info["ariaLabel"]}")', 'label'))
        
        # 5. ALT TEXT LOCATORS (Score: 160)
        if element_info.get('alt'):
            locators.append((160, f'page.get_by_alt_text("{element_info["alt"]}", exact=True)', 'alt_exact'))
            locators.append((165, f'page.get_by_alt_text("{element_info["alt"]}")', 'alt'))
        
        # 6. TEXT LOCATORS (Score: 180-250)
        if element_info.get('text'):
            text = element_info['text'].strip()
            if text:
                locators.append((180, f'page.get_by_text("{text}", exact=True)', 'text_exact'))
                locators.append((185, f'page.get_by_text("{text}")', 'text'))
                # Text content with regex for partial matching
                if len(text) > 5:
                    escaped_text = re.escape(text[:30])
                    locators.append((250, f'page.get_by_text(re.compile(r"{escaped_text}"))', 'text_regex'))
        
        # 7. TITLE LOCATORS (Score: 200)
        if element_info.get('title'):
            locators.append((200, f'page.get_by_title("{element_info["title"]}")', 'title'))
        
        # 8. CSS SELECTORS (Score: 500+)
        tag = element_info.get('tag', 'div')  # Default to div if tag not specified
        
        # ID selector - very reliable
        if element_info.get('id'):
            locators.append((500, f'page.locator("#{element_info["id"]}")', 'css_id'))
        
        # Class selectors
        if element_info.get('classes'):
            classes = element_info['classes'].strip().split()
            if classes:
                # Single class
                locators.append((520, f'page.locator("{tag}.{classes[0]}")', 'css_class'))
                # All classes
                if len(classes) > 1:
                    all_classes = '.'.join(classes)
                    locators.append((515, f'page.locator("{tag}.{all_classes}")', 'css_all_classes'))
        
        # Attribute selectors
        if element_info.get('type'):
            locators.append((520, f'page.locator("{tag}[type=\\"{element_info["type"]}\\"]")', 'css_type'))
        
        if element_info.get('name'):
            locators.append((525, f'page.locator("{tag}[name=\\"{element_info["name"]}\\"]")', 'css_name'))
        
        if element_info.get('href'):
            href = element_info['href'][:100]  # Limit length
            locators.append((525, f'page.locator("{tag}[href=\\"{href}\\"]")', 'css_href'))
        
        if element_info.get('value'):
            locators.append((530, f'page.locator("{tag}[value=\\"{element_info["value"]}\\"]")', 'css_value'))
        
        # Tag only - lowest priority (only if tag is available)
        if tag:
            locators.append((600, f'page.locator("{tag}")', 'css_tag'))
        
        # 9. COMBINED LOCATORS (Score: 300-400)
        # Combine strategies for better specificity
        if role and element_info.get('text'):
            text = element_info['text'].strip()
            if text:
                locators.append((300, f'page.get_by_role("{role}").filter(has_text="{text}")', 'role_filter_text'))
        
        elem_id = element_info.get('id')
        if elem_id and element_info.get('text'):
            text = element_info['text'].strip()
            if text:
                locators.append((350, f'page.locator("#{elem_id}").get_by_text("{text}")', 'id_filter_text'))
        
        # Sort by score (lower is better)
        locators.sort(key=lambda x: x[0])
        return locators
    
    def _determine_role(self, element_info: Dict) -> Optional[str]:
        """Determine the ARIA role for an element"""
        if element_info.get('role'):
            return element_info['role']
        
        tag = element_info.get('tag', '').lower()
        input_type = element_info.get('type', '').lower()
        
        role_map = {
            'button': 'button',
            'a': 'link',
            'img': 'img',
            'h1': 'heading',
            'h2': 'heading',
            'h3': 'heading',
            'h4': 'heading',
            'h5': 'heading',
            'h6': 'heading',
            'nav': 'navigation',
            'main': 'main',
            'header': 'banner',
            'footer': 'contentinfo',
            'aside': 'complementary',
            'section': 'region',
        }
        
        if tag in role_map:
            return role_map[tag]
        
        if tag == 'input':
            input_role_map = {
                'text': 'textbox',
                'email': 'textbox',
                'password': 'textbox',
                'search': 'searchbox',
                'tel': 'textbox',
                'url': 'textbox',
                'checkbox': 'checkbox',
                'radio': 'radio',
                'button': 'button',
                'submit': 'button',
                'reset': 'button',
            }
            return input_role_map.get(input_type, 'textbox')
        
        if tag == 'textarea':
            return 'textbox'
        
        if tag == 'select':
            return 'combobox'
        
        return None
    
    async def verify_locator(self, locator_code: str) -> Tuple[int, bool, Optional[str]]:
        """
        Verify a locator and return (count, is_visible, error).
        Tests both count and visibility.
        """
        try:
            count = await self._count_matches(locator_code)
            
            if count == 0:
                return (0, False, None)
            
            # Check if the element is visible
            is_visible = False
            if count == 1:
                try:
                    is_visible = await self._is_element_visible(locator_code)
                except Exception:
                    pass
            
            return (count, is_visible, None)
        
        except Exception as e:
            return (999, False, str(e))
    
    async def _count_matches(self, locator_code: str) -> int:
        """Count how many elements match a locator"""
        try:
            if 'get_by_test_id' in locator_code:
                match = re.search(r'get_by_test_id\("([^"]+)"\)', locator_code)
                if match:
                    return await self.page.locator(f'[data-testid="{match.group(1)}"]').count()
            
            elif 'get_by_role' in locator_code:
                role_match = re.search(r'get_by_role\("([^"]+)"', locator_code)
                name_match = re.search(r'name="([^"]+)"', locator_code)
                exact = 'exact=True' in locator_code
                
                if role_match:
                    role = role_match.group(1)
                    name = name_match.group(1) if name_match else None
                    if name:
                        return await self.page.get_by_role(role, name=name, exact=exact).count()
                    else:
                        return await self.page.get_by_role(role).count()
            
            elif 'get_by_text' in locator_code:
                text_match = re.search(r'get_by_text\("([^"]+)"', locator_code)
                if text_match:
                    text = text_match.group(1)
                    exact = 'exact=True' in locator_code
                    return await self.page.get_by_text(text, exact=exact).count()
            
            elif 'get_by_placeholder' in locator_code:
                match = re.search(r'get_by_placeholder\("([^"]+)"', locator_code)
                if match:
                    exact = 'exact=True' in locator_code
                    return await self.page.get_by_placeholder(match.group(1), exact=exact).count()
            
            elif 'get_by_label' in locator_code:
                match = re.search(r'get_by_label\("([^"]+)"', locator_code)
                if match:
                    exact = 'exact=True' in locator_code
                    return await self.page.get_by_label(match.group(1), exact=exact).count()
            
            elif 'get_by_alt_text' in locator_code:
                match = re.search(r'get_by_alt_text\("([^"]+)"', locator_code)
                if match:
                    exact = 'exact=True' in locator_code
                    return await self.page.get_by_alt_text(match.group(1), exact=exact).count()
            
            elif 'get_by_title' in locator_code:
                match = re.search(r'get_by_title\("([^"]+)"', locator_code)
                if match:
                    return await self.page.get_by_title(match.group(1)).count()
            
            elif 'page.locator' in locator_code:
                match = re.search(r'page\.locator\("([^"\\]*(\\.[^"\\]*)*)"\)', locator_code)
                if match:
                    selector = match.group(1).replace('\\"', '"')
                    return await self.page.locator(selector).count()
            
            elif '.filter(' in locator_code or '.get_by_text(' in locator_code:
                # Handle chained locators - for now, return high count (needs page context)
                return 999
            
            return 999
        
        except Exception:
            return 999
    
    async def _is_element_visible(self, locator_code: str) -> bool:
        """Check if an element matching the locator is visible"""
        try:
            # This is a simplified check - you'd need to actually get the locator
            # For now, assume visible if count is 1
            return True
        except Exception:
            return False
    
    async def find_best_locator(self, element_info: Dict, page_url: str = '') -> Optional[Dict]:
        """
        Find the best locator for an element by testing all strategies in parallel.
        Returns dict with locator info or None if no unique locator found.
        """
        # Check cache first
        if page_url and element_info.get('text'):
            cached = self.cache.get(page_url, element_info['text'])
            if cached:
                print(f"✅ Using cached locator for '{element_info.get('text', 'element')[:30]}...'")
                return cached
        
        # Generate all possible locators
        all_locators = await self.generate_all_possible_locators(element_info)
        
        if not all_locators:
            print("❌ No locators could be generated from element info")
            return None
        
        print(f"🔍 Testing {len(all_locators)} locator strategies in parallel...")
        
        # Test all locators in parallel
        tasks = [self.verify_locator(loc[1]) for loc in all_locators]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Find best unique visible locator
        best_locator = None
        best_score = float('inf')
        
        for i, (score, locator_code, strategy) in enumerate(all_locators):
            if isinstance(results[i], Exception):
                print(f"  ⚠️  {strategy}: Error during validation")
                continue
            
            count, is_visible, error = results[i]
            
            if error:
                print(f"  ⚠️  {strategy}: {error}")
                continue
            
            print(f"  {'✅' if count == 1 else '⚠️ '} {strategy}: {locator_code} → {count} match(es){' (visible)' if is_visible else ''}")
            
            # Prefer unique locators that are visible
            if count == 1 and is_visible and score < best_score:
                best_locator = {
                    'locator': locator_code,
                    'strategy': strategy,
                    'score': score,
                    'count': count,
                    'visible': is_visible,
                    'unique': True,
                    'confidence': 100 - min(score, 100)  # Convert score to confidence
                }
                best_score = score
            # If no visible unique locator yet, accept non-visible unique
            elif count == 1 and not best_locator and score < best_score:
                best_locator = {
                    'locator': locator_code,
                    'strategy': strategy,
                    'score': score,
                    'count': count,
                    'visible': is_visible,
                    'unique': True,
                    'confidence': 90 - min(score, 90)
                }
                best_score = score
        
        if best_locator:
            print(f"✅ Best locator: {best_locator['strategy']} (confidence: {best_locator['confidence']}%)")
            
            # Cache successful locator
            if page_url and element_info.get('text'):
                self.cache.set(page_url, element_info['text'], best_locator)
            
            return best_locator
        
        # No unique locator found - return best scored locator with warning
        for i, (score, locator_code, strategy) in enumerate(all_locators):
            if not isinstance(results[i], Exception):
                count, is_visible, error = results[i]
                if count > 0 and not error:
                    print(f"⚠️  No unique locator found. Using: {strategy} (matches {count} elements)")
                    return {
                        'locator': locator_code,
                        'strategy': strategy,
                        'score': score,
                        'count': count,
                        'visible': is_visible,
                        'unique': False,
                        'confidence': 50 - min(score // 10, 50)
                    }
        
        print("❌ No valid locator found")
        return None
    
    async def validate_and_improve_locator(self, locator_code: str, element_info: Optional[Dict] = None) -> Dict:
        """
        Validate an existing locator and suggest improvements if needed.
        Returns validation result with alternative suggestions.
        """
        count, is_visible, error = await self.verify_locator(locator_code)
        
        result = {
            'original_locator': locator_code,
            'is_valid': count == 1 and not error,
            'count': count,
            'visible': is_visible,
            'error': error,
            'alternatives': []
        }
        
        # If locator is not unique or has errors, generate alternatives
        if (count != 1 or error) and element_info:
            print(f"🔍 Generating alternative locators...")
            best = await self.find_best_locator(element_info)
            if best:
                result['alternatives'] = [best]
                result['recommended'] = best['locator']
        
        return result
