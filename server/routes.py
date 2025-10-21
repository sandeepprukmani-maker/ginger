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
            
            if not steps:
                return jsonify({
                    'success': False,
                    'error': 'No steps to export'
                }), 400
            
            # Generate Playwright code
            playwright_code = generate_playwright_code(steps, instruction)
            
            # Enhanced JSON export with selector information
            json_export = {
                'instruction': instruction,
                'timestamp': datetime.now().isoformat(),
                'steps': steps,
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


def generate_playwright_code(steps, instruction):
    """Generate Playwright test code from execution steps with native locators"""
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
        
        if tool == 'browser_navigate':
            url = args.get('url', '')
            code_lines.append(f"  await page.goto('{url}');")
            if isinstance(result, dict) and 'snapshot' in result:
                last_snapshot = result['snapshot']
            
        elif tool == 'browser_snapshot':
            if isinstance(result, dict) and 'snapshot' in result:
                last_snapshot = result['snapshot']
                
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
    
    # First, try to extract from the result (MCP server often includes Playwright code)
    if isinstance(result, dict):
        content = result.get('content', [])
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                text = item.get('text', '')
                # Look for Playwright locator code in the result
                # Format: await page.getByRole(...).action();
                locator_match = re.search(r'await\s+page\.(getBy\w+\([^)]+(?:\s*,\s*\{[^}]+\})?\))', text)
                if locator_match:
                    return f"page.{locator_match.group(1)}"
    
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
