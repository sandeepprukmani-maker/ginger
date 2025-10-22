"""
Flask Routes for Browser Automation
"""
from flask import render_template, request, jsonify
from server.services.mcp_client import MCPStdioClient
from server.services.browser_agent import BrowserAgent
import re
from datetime import datetime

# Initialize MCP client and agent (using STDIO transport)
mcp_client = None
browser_agent = None


def get_mcp_client():
    """Lazy initialization of MCP client"""
    global mcp_client, browser_agent
    if mcp_client is None:
        mcp_client = MCPStdioClient()
        browser_agent = BrowserAgent(mcp_client)
    return mcp_client, browser_agent


def register_routes(app):
    """Register all routes with the Flask app"""
    
    @app.route('/')
    def index():
        """Render main page"""
        return render_template('index.html')
    
    
    @app.route('/api/execute', methods=['POST'])
    def execute_instruction():
        """Execute a browser automation instruction"""
        try:
            data = request.get_json()
            instruction = data.get('instruction', '').strip()
            
            if not instruction:
                return jsonify({
                    'success': False,
                    'error': 'Please provide an instruction'
                }), 400
            
            # Get or create MCP client
            _, agent = get_mcp_client()
            
            # Execute the instruction
            result = agent.execute_instruction(instruction)
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    
    @app.route('/api/tools', methods=['GET'])
    def get_tools():
        """Get available browser tools"""
        try:
            client, _ = get_mcp_client()
            
            if not client.initialized:
                client.initialize()
            
            tools = client.list_tools()
            
            return jsonify({
                'success': True,
                'tools': tools
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    
    @app.route('/api/reset', methods=['POST'])
    def reset_agent():
        """Reset the browser agent"""
        try:
            _, agent = get_mcp_client()
            agent.reset_conversation()
            
            return jsonify({
                'success': True,
                'message': 'Agent reset successfully'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    
    @app.route('/api/export-playwright', methods=['POST'])
    def export_playwright():
        """Export last execution as Playwright code"""
        try:
            data = request.get_json()
            steps = data.get('steps', [])
            instruction = data.get('instruction', 'Automated task')
            language = data.get('language', 'python')  # Default to Python
            
            if not steps:
                return jsonify({
                    'success': False,
                    'error': 'No steps to export'
                }), 400
            
            # Generate Playwright code based on language
            if language == 'python':
                playwright_code = generate_playwright_code_python(steps, instruction)
            else:
                playwright_code = generate_playwright_code_javascript(steps, instruction)
            
            # Enhanced JSON export with selector information
            json_export = {
                'instruction': instruction,
                'timestamp': datetime.now().isoformat(),
                'steps': steps,
                'language': language,
                'usage_notes': {
                    'description': 'Steps executed by AI with full context',
                    'replay': 'Can be used to replay automation programmatically',
                    'selectors': 'Check result.snapshot fields for element information'
                }
            }
            
            return jsonify({
                'success': True,
                'playwright_code': playwright_code,
                'json_export': json_export
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            # Only check if MCP client exists, don't force initialization
            global mcp_client
            
            if mcp_client is not None:
                # Client exists, check if process is alive
                if mcp_client.process and mcp_client.process.poll() is None:
                    return jsonify({
                        'status': 'healthy',
                        'mcp_connected': True,
                        'transport': 'STDIO'
                    })
            
            # MCP client not yet initialized, but that's okay
            return jsonify({
                'status': 'healthy',
                'mcp_connected': False,
                'message': 'MCP will initialize on first use'
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'mcp_connected': False,
                'error': str(e)
            }), 503


def generate_playwright_code_python(steps, instruction):
    """Generate Python Playwright code from execution steps with native locators"""
    code_lines = [
        "from playwright.sync_api import sync_playwright, expect",
        "import re",
        "",
        "",
        "def run():",
        '    """' + instruction + '"""',
        "    with sync_playwright() as p:",
        "        # Launch browser",
        "        browser = p.chromium.launch(headless=False)",
        "        page = browser.new_page()",
        "",
    ]
    
    # Track page snapshots to extract locators
    last_snapshot = None
    step_number = 1
    
    for step in steps:
        if not step.get('success'):
            continue
            
        tool = step.get('tool', '')
        args = step.get('arguments', {})
        result = step.get('result', {})
        
        # Update snapshot from result - normalize to string
        if isinstance(result, dict) and 'snapshot' in result:
            snapshot_data = result['snapshot']
            if isinstance(snapshot_data, dict):
                # MCP returns snapshot as dict with logicalTree or ariaTree
                last_snapshot = snapshot_data.get('logicalTree') or snapshot_data.get('ariaTree')
            elif isinstance(snapshot_data, str):
                last_snapshot = snapshot_data
        
        if tool == 'browser_navigate':
            url = args.get('url', '')
            code_lines.append(f'        # {step_number}. Navigate to page')
            code_lines.append(f'        page.goto("{url}")')
            code_lines.append('')
            step_number += 1
            
        elif tool == 'browser_snapshot':
            # Snapshot already updated above
            pass
                
        elif tool == 'browser_click':
            ref = args.get('ref', '')
            locator_code = extract_playwright_locator_python(ref, last_snapshot, result)
            if locator_code:
                code_lines.append(f'        # {step_number}. Click element')
                code_lines.append(f'        {locator_code}.click()')
                code_lines.append('')
            else:
                code_lines.append(f'        # TODO: Click element [ref={ref}] - Could not extract locator')
                code_lines.append('')
            step_number += 1
            
        elif tool == 'browser_fill':
            ref = args.get('ref', '')
            value = args.get('value', '').replace('"', '\\"')
            locator_code = extract_playwright_locator_python(ref, last_snapshot, result)
            if locator_code:
                code_lines.append(f'        # {step_number}. Fill form field')
                code_lines.append(f'        {locator_code}.fill("{value}")')
                code_lines.append('')
            else:
                code_lines.append(f'        # TODO: Fill element [ref={ref}] with "{value}" - Could not extract locator')
                code_lines.append('')
            step_number += 1
        
        elif tool == 'browser_type':
            # Handle browser_type tool (types text and optionally presses Enter)
            ref = args.get('ref', '')
            text = args.get('text', '').replace('"', '\\"')
            submit = args.get('submit', False)
            
            locator_code = extract_playwright_locator_python(ref, last_snapshot, result)
            if locator_code:
                code_lines.append(f'        # {step_number}. Type text into field')
                code_lines.append(f'        {locator_code}.fill("{text}")')
                if submit:
                    code_lines.append(f'        {locator_code}.press("Enter")')
                code_lines.append('')
            else:
                code_lines.append(f'        # TODO: Type "{text}" into element [ref={ref}] - Could not extract locator')
                if submit:
                    code_lines.append(f'        # TODO: Press Enter')
                code_lines.append('')
            step_number += 1
            
        elif tool == 'browser_screenshot':
            code_lines.append(f'        # {step_number}. Take screenshot')
            code_lines.append('        page.screenshot(path="screenshot.png")')
            code_lines.append('')
            step_number += 1
            
        elif tool == 'browser_close':
            code_lines.append('        # Close browser')
            code_lines.append('        browser.close()')
            code_lines.append('')
    
    # Add browser close if not already added
    if not any('browser.close()' in line for line in code_lines):
        code_lines.append('        # Close browser')
        code_lines.append('        browser.close()')
        code_lines.append('')
    
    code_lines.extend([
        "",
        'if __name__ == "__main__":',
        "    run()",
        "",
        "# Generated from AI Browser Automation Agent",
        "# Uses Playwright Python with native locators for better stability and readability",
        "# Tip: Add assertions with expect() to verify page state"
    ])
    
    return '\n'.join(code_lines)


def generate_playwright_code_javascript(steps, instruction):
    """Generate JavaScript Playwright test code from execution steps with native locators"""
    code_lines = [
        "import { test, expect } from '@playwright/test';",
        "",
        f"test('{instruction}', async ({{ page }}) => {{",
    ]
    
    # Track page snapshots to extract locators
    last_snapshot = None
    
    for step in steps:
        if not step.get('success'):
            continue
            
        tool = step.get('tool', '')
        args = step.get('arguments', {})
        result = step.get('result', {})
        
        # Update snapshot from result - normalize to string
        if isinstance(result, dict) and 'snapshot' in result:
            snapshot_data = result['snapshot']
            if isinstance(snapshot_data, dict):
                # MCP returns snapshot as dict with logicalTree or ariaTree
                last_snapshot = snapshot_data.get('logicalTree') or snapshot_data.get('ariaTree')
            elif isinstance(snapshot_data, str):
                last_snapshot = snapshot_data
        
        if tool == 'browser_navigate':
            url = args.get('url', '')
            code_lines.append(f"  await page.goto('{url}');")
            
        elif tool == 'browser_snapshot':
            # Snapshot already updated above
            pass
                
        elif tool == 'browser_click':
            ref = args.get('ref', '')
            locator_code = extract_playwright_locator(ref, last_snapshot, result)
            if locator_code:
                code_lines.append(f"  await {locator_code}.click();")
            else:
                code_lines.append(f"  // TODO: Click element [ref={ref}] - Could not extract locator")
            
        elif tool == 'browser_fill':
            ref = args.get('ref', '')
            value = args.get('value', '').replace("'", "\\'")
            locator_code = extract_playwright_locator(ref, last_snapshot, result)
            if locator_code:
                code_lines.append(f"  await {locator_code}.fill('{value}');")
            else:
                code_lines.append(f"  // TODO: Fill element [ref={ref}] with '{value}' - Could not extract locator")
        
        elif tool == 'browser_type':
            # Handle browser_type tool (types text and optionally presses Enter)
            ref = args.get('ref', '')
            text = args.get('text', '').replace("'", "\\'")
            submit = args.get('submit', False)
            
            locator_code = extract_playwright_locator(ref, last_snapshot, result)
            if locator_code:
                code_lines.append(f"  await {locator_code}.fill('{text}');")
                if submit:
                    code_lines.append(f"  await {locator_code}.press('Enter');")
            else:
                code_lines.append(f"  // TODO: Type '{text}' into element [ref={ref}] - Could not extract locator")
                if submit:
                    code_lines.append(f"  // TODO: Press Enter")
            
        elif tool == 'browser_screenshot':
            code_lines.append(f"  await page.screenshot({{ path: 'screenshot.png' }});")
            
        elif tool == 'browser_close':
            code_lines.append(f"  // Browser will close automatically after test")
    
    code_lines.extend([
        "});",
        "",
        "// Generated from AI Browser Automation Agent",
        "// Uses Playwright native locators for better stability and readability",
        "// Tip: Add assertions with expect() to verify page state"
    ])
    
    return '\n'.join(code_lines)


def extract_playwright_locator_python(ref, snapshot, result):
    """
    Extract Python Playwright native locator code from ref and snapshot data
    Returns Python Playwright locator code string or None
    
    Examples:
        page.get_by_role("button", name="Submit")
        page.get_by_text("Click here")
        page.get_by_label("Email")
        page.get_by_placeholder("Search...")
    """
    if not ref:
        return None
    
    # First, try to extract structured locator from result
    if isinstance(result, dict):
        # Check for structured locator metadata
        if 'locator' in result:
            locator_info = result['locator']
            if isinstance(locator_info, dict):
                # Extract locator from structured data
                locator_type = locator_info.get('type', '')
                locator_value = locator_info.get('value', '')
                if locator_type and locator_value:
                    # Convert JavaScript locator to Python (getByRole -> get_by_role)
                    python_locator_type = locator_type.replace('getBy', 'get_by_').replace('By', '_by_').lower()
                    value_escaped = locator_value.replace('"', '\\"')
                    return f'page.{python_locator_type}("{value_escaped}")'
        
        # Try to extract from content (MCP server often includes Playwright code)
        content = result.get('content', [])
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                text = item.get('text', '')
                # Look for Playwright locator code in the result
                # Format: await page.getByRole('button', { name: 'Submit' }).action();
                locator_match = re.search(r'await\s+page\.(getBy\w+)\(([^)]+)\)', text)
                if locator_match:
                    method = locator_match.group(1)
                    args_str = locator_match.group(2)
                    
                    # Convert method name to Python (getByRole -> get_by_role)
                    python_method = 'get_by_role' if 'Role' in method else \
                                   'get_by_label' if 'Label' in method else \
                                   'get_by_placeholder' if 'Placeholder' in method else \
                                   'get_by_text' if 'Text' in method else method.lower()
                    
                    # Convert JavaScript object syntax to Python kwargs
                    # Change { name: 'Submit' } to name="Submit"
                    # Change 'text' to "text"
                    python_args = args_str.replace("'", '"')  # Use double quotes
                    
                    # Convert { key: value } to key=value
                    python_args = re.sub(r'\{\s*(\w+):\s*([^}]+)\s*\}', r'\1=\2', python_args)
                    
                    return f"page.{python_method}({python_args})"
    
    # Fallback to snapshot parsing
    if not snapshot or not isinstance(snapshot, str):
        return None
    
    # Parse the snapshot to find the element with this ref
    ref_pattern = rf'\[ref={re.escape(ref)}\]'
    lines = snapshot.split('\n')
    
    for i, line in enumerate(lines):
        if ref_pattern not in line:
            continue
        
        # Found the ref, now extract element information
        element_info = {
            'role': None,
            'name': None,
            'text': None,
            'placeholder': None,
            'label': None,
            'tag': None
        }
        
        # Search context around the ref (typically 10 lines before and 2 after)
        context_start = max(0, i - 10)
        context_end = min(len(lines), i + 3)
        context_lines = lines[context_start:context_end]
        
        # Extract attributes from the context
        for ctx_line in context_lines:
            # Extract role
            if 'role=' in ctx_line:
                role_match = re.search(r"role=['\"]([^'\"]+)['\"]", ctx_line)
                if role_match:
                    element_info['role'] = role_match.group(1)
            
            # Extract name attribute (often used with role)
            if 'name=' in ctx_line:
                name_match = re.search(r"name=['\"]([^'\"]+)['\"]", ctx_line)
                if name_match:
                    element_info['name'] = name_match.group(1)
            
            # Extract placeholder
            if 'placeholder=' in ctx_line:
                placeholder_match = re.search(r"placeholder=['\"]([^'\"]+)['\"]", ctx_line)
                if placeholder_match:
                    element_info['placeholder'] = placeholder_match.group(1)
            
            # Extract label text (for get_by_label)
            if 'label=' in ctx_line or '<label' in ctx_line.lower():
                label_match = re.search(r"(?:label=|>)[\s]*['\"]?([^'\"<>]+)['\"]?", ctx_line)
                if label_match:
                    element_info['label'] = label_match.group(1).strip()
        
        # Extract text content from the line with ref
        text_match = re.search(r'["\']([^"\']{1,100})["\'].*?\[ref=', line)
        if text_match:
            element_info['text'] = text_match.group(1)
        
        # Generate Python Playwright native locator code based on available info
        # Priority: role with name > text > placeholder > label > fallback
        
        # 1. Try get_by_role (most stable and accessible)
        if element_info['role']:
            role = element_info['role']
            name = element_info['name'] or element_info['text']
            
            # Escape double quotes in name
            if name:
                name_escaped = name.replace('"', '\\"')
                return f'page.get_by_role("{role}", name="{name_escaped}")'
            else:
                return f'page.get_by_role("{role}")'
        
        # 2. Try get_by_placeholder (for input fields)
        if element_info['placeholder']:
            placeholder_escaped = element_info['placeholder'].replace('"', '\\"')
            return f'page.get_by_placeholder("{placeholder_escaped}")'
        
        # 3. Try get_by_label (for form fields)
        if element_info['label']:
            label_escaped = element_info['label'].replace('"', '\\"')
            return f'page.get_by_label("{label_escaped}")'
        
        # 4. Try get_by_text (for elements with visible text)
        if element_info['text']:
            # Use exact match for short text
            text_escaped = element_info['text'].replace('"', '\\"')
            if len(element_info['text']) < 50:
                return f'page.get_by_text("{text_escaped}")'
            else:
                # Use substring match for long text
                text_preview = element_info['text'][:30].replace('"', '\\"')
                return f'page.locator(f"text={text_preview}")'
        
        # 5. Extract CSS selector as fallback from the snapshot
        css_selector = extract_css_selector_from_line(line, ref)
        if css_selector:
            return f'page.locator("{css_selector}")'
        
        # 6. Last resort: use the ref attribute with a comment
        # Note: This won't work in production, but shows what element was targeted
        return f'page.locator("[ref={ref}]")  # Note: ref attribute may not exist in actual page'
    
    # If we couldn't find the ref at all in snapshot, try to use structured data
    return None


def extract_css_selector_from_line(line, ref):
    """
    Extract a CSS selector from the snapshot line
    Returns CSS selector string or None
    """
    # Try to extract ID
    id_match = re.search(r'id=["\']([^"\']+)["\']', line)
    if id_match:
        element_id = id_match.group(1)
        return f'#{element_id}'
    
    # Try to extract class (use first class)
    class_match = re.search(r'class=["\']([^"\']+)["\']', line)
    if class_match:
        classes = class_match.group(1).split()
        if classes:
            # Use first class as selector
            return f'.{classes[0]}'
    
    # Try to extract tag name with attributes
    tag_match = re.search(r'<(\w+)', line)
    if tag_match:
        tag = tag_match.group(1)
        
        # If it has a name attribute, use that
        name_match = re.search(r'name=["\']([^"\']+)["\']', line)
        if name_match:
            name = name_match.group(1)
            return f'{tag}[name="{name}"]'
        
        # If it has a type attribute (for inputs)
        type_match = re.search(r'type=["\']([^"\']+)["\']', line)
        if type_match:
            input_type = type_match.group(1)
            return f'{tag}[type="{input_type}"]'
    
    return None


def extract_playwright_locator(ref, snapshot, result):
    """
    Extract Playwright native locator code from ref and snapshot data
    Returns Playwright locator code string or None
    
    Examples:
        page.getByRole('button', { name: 'Submit' })
        page.getByText('Click here')
        page.getByLabel('Email')
        page.getByPlaceholder('Search...')
    """
    if not ref:
        return None
    
    # First, try to extract structured locator from result
    if isinstance(result, dict):
        # Check for structured locator metadata
        if 'locator' in result:
            locator_info = result['locator']
            if isinstance(locator_info, dict):
                # Extract locator from structured data
                locator_type = locator_info.get('type', '')
                locator_value = locator_info.get('value', '')
                if locator_type and locator_value:
                    value_escaped = locator_value.replace("'", "\\'")
                    return f"page.{locator_type}('{value_escaped}')"
        
        # Try to extract from content (MCP server often includes Playwright code)
        content = result.get('content', [])
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                text = item.get('text', '')
                # Look for Playwright locator code in the result
                # Format: await page.getByRole(...).action();
                locator_match = re.search(r'await\s+page\.(getBy\w+\([^)]+(?:\s*,\s*\{[^}]+\})?\))', text)
                if locator_match:
                    return f"page.{locator_match.group(1)}"
    
    # Fallback to snapshot parsing
    if not snapshot or not isinstance(snapshot, str):
        return None
    
    # Parse the snapshot to find the element with this ref
    ref_pattern = rf'\[ref={re.escape(ref)}\]'
    lines = snapshot.split('\n')
    
    for i, line in enumerate(lines):
        if ref_pattern not in line:
            continue
        
        # Found the ref, now extract element information
        element_info = {
            'role': None,
            'name': None,
            'text': None,
            'placeholder': None,
            'label': None,
            'tag': None
        }
        
        # Search context around the ref (typically 10 lines before and 2 after)
        context_start = max(0, i - 10)
        context_end = min(len(lines), i + 3)
        context_lines = lines[context_start:context_end]
        
        # Extract attributes from the context
        for ctx_line in context_lines:
            # Extract role
            if 'role=' in ctx_line:
                role_match = re.search(r"role=['\"]([^'\"]+)['\"]", ctx_line)
                if role_match:
                    element_info['role'] = role_match.group(1)
            
            # Extract name attribute (often used with role)
            if 'name=' in ctx_line:
                name_match = re.search(r"name=['\"]([^'\"]+)['\"]", ctx_line)
                if name_match:
                    element_info['name'] = name_match.group(1)
            
            # Extract placeholder
            if 'placeholder=' in ctx_line:
                placeholder_match = re.search(r"placeholder=['\"]([^'\"]+)['\"]", ctx_line)
                if placeholder_match:
                    element_info['placeholder'] = placeholder_match.group(1)
            
            # Extract label text (for getByLabel)
            if 'label=' in ctx_line or '<label' in ctx_line.lower():
                label_match = re.search(r"(?:label=|>)[\s]*['\"]?([^'\"<>]+)['\"]?", ctx_line)
                if label_match:
                    element_info['label'] = label_match.group(1).strip()
        
        # Extract text content from the line with ref
        text_match = re.search(r'["\']([^"\']{1,100})["\'].*?\[ref=', line)
        if text_match:
            element_info['text'] = text_match.group(1)
        
        # Generate Playwright native locator code based on available info
        # Priority: role with name > text > placeholder > label > fallback
        
        # 1. Try getByRole (most stable and accessible)
        if element_info['role']:
            role = element_info['role']
            name = element_info['name'] or element_info['text']
            
            # Escape single quotes in name
            if name:
                name_escaped = name.replace("'", "\\'")
                return f"page.getByRole('{role}', {{ name: '{name_escaped}' }})"
            else:
                return f"page.getByRole('{role}')"
        
        # 2. Try getByPlaceholder (for input fields)
        if element_info['placeholder']:
            placeholder_escaped = element_info['placeholder'].replace("'", "\\'")
            return f"page.getByPlaceholder('{placeholder_escaped}')"
        
        # 3. Try getByLabel (for form fields)
        if element_info['label']:
            label_escaped = element_info['label'].replace("'", "\\'")
            return f"page.getByLabel('{label_escaped}')"
        
        # 4. Try getByText (for elements with visible text)
        if element_info['text']:
            # Use exact match for short text, partial for longer text
            text_escaped = element_info['text'].replace("'", "\\'")
            if len(element_info['text']) < 50:
                return f"page.getByText('{text_escaped}')"
            else:
                # Use substring match for long text
                text_preview = element_info['text'][:30].replace("'", "\\'")
                return f"page.getByText('{text_preview}', {{ exact: false }})"
        
        # 5. Fallback: could not extract enough information
        break
    
    return None
