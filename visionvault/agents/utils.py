import os
import sys
import subprocess
import re
import base64


def detect_browsers():
    """Detect available browsers on the system"""
    browsers = []
    try:
        if sys.platform == 'win32':
            paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            if any(os.path.exists(p) for p in paths):
                browsers.append('chromium')
        elif sys.platform == 'darwin':
            if os.path.exists('/Applications/Google Chrome.app'):
                browsers.append('chromium')
            if os.path.exists('/Applications/Firefox.app'):
                browsers.append('firefox')
            if os.path.exists('/Applications/Safari.app'):
                browsers.append('webkit')
        else:
            if subprocess.run(['which', 'google-chrome'], capture_output=True).returncode == 0:
                browsers.append('chromium')
            if subprocess.run(['which', 'firefox'], capture_output=True).returncode == 0:
                browsers.append('firefox')
        if not browsers:
            browsers = ['chromium']
    except Exception as e:
        print(f"Browser detection error: {e}")
        browsers = ['chromium']

    print(f"Detected browsers: {browsers}")
    return browsers


def extract_failed_locator_local(error_message):
    """
    Enhanced error detection - catches ALL types of automation errors.
    Returns a dict with error type and details for intelligent healing.
    """
    if not error_message:
        return None
    
    error_info = {
        'type': 'unknown',
        'locator': None,
        'full_error': error_message,
        'is_healable': False
    }
    
    # 1. API Misuse Errors (NEW - catches code generation bugs)
    api_errors = [
        (r"'(\w+)' object has no attribute '(\w+)'", 'api_misuse'),
        (r"takes (\d+) positional argument.*?but (\d+) (?:were|was) given", 'api_misuse'),
        (r"unexpected keyword argument", 'api_misuse'),
        (r"missing \d+ required positional argument", 'api_misuse'),
    ]
    
    for pattern, error_type in api_errors:
        if re.search(pattern, error_message, re.IGNORECASE):
            error_info['type'] = error_type
            error_info['is_healable'] = True
            error_info['detail'] = re.search(pattern, error_message, re.IGNORECASE).group(0)
            return error_info
    
    # 2. Locator/Element Not Found Errors (existing patterns enhanced)
    locator_patterns = [
        (r'locator\(["\']([^"\']+)["\']\)', 'locator_not_found'),
        (r'waiting for locator\(["\']([^"\']+)["\']\)', 'timeout'),
        (r'Timeout.*?locator\(["\']([^"\']+)["\']\)', 'timeout'),
        (r'Error: (?:element )?not found: ([^\n]+)', 'element_not_found'),
        (r'strict mode violation.*?(\d+) elements', 'multiple_matches'),
    ]
    
    for pattern, error_type in locator_patterns:
        match = re.search(pattern, error_message, re.IGNORECASE)
        if match:
            error_info['type'] = error_type
            error_info['locator'] = match.group(1)
            error_info['is_healable'] = True
            return error_info
    
    # 3. Timeout Errors (general)
    if re.search(r'timeout|timed out', error_message, re.IGNORECASE):
        error_info['type'] = 'timeout'
        error_info['is_healable'] = True
        return error_info
    
    # 4. Navigation/Page Errors
    if re.search(r'navigation|net::|ERR_', error_message, re.IGNORECASE):
        error_info['type'] = 'navigation_error'
        error_info['is_healable'] = False
        return error_info
    
    # 5. Any error is potentially healable with AI retry
    if 'Error at STEP' in error_message or 'error' in error_message.lower():
        error_info['type'] = 'general_error'
        error_info['is_healable'] = True
        return error_info
    
    return error_info if error_info['is_healable'] else None


def encode_screenshot(screenshot_bytes):
    """Encode screenshot to base64 string"""
    if screenshot_bytes:
        return base64.b64encode(screenshot_bytes).decode('utf-8')
    return None