"""
Flask Web Application for Browser Automation
Provides web interface for users to input instructions
"""
from flask import Flask, render_template, request, jsonify
from app.mcp_stdio_client import MCPStdioClient
from app.browser_agent import BrowserAgent
import os
import re
import configparser
from datetime import datetime

# Load configuration from .ini file
config = configparser.ConfigParser()
config.read('config.ini')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Initialize MCP client and agent (using STDIO transport)
mcp_client = None
browser_agent = None

def get_mcp_client():
    """Lazy initialization of MCP client"""
    global mcp_client, browser_agent
    if mcp_client is None:
        # MCP client will read browser settings from config.ini
        mcp_client = MCPStdioClient()
        browser_agent = BrowserAgent(mcp_client)
    return mcp_client, browser_agent


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


def generate_playwright_code(steps, instruction):
    """Generate Playwright test code from execution steps"""
    code_lines = [
        "import { test, expect } from '@playwright/test';",
        "",
        f"test('{instruction}', async ({{ page }}) => {{",
    ]
    
    # Track page snapshots to extract selectors
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
            # Check if result has snapshot
            if isinstance(result, dict) and 'snapshot' in result:
                last_snapshot = result['snapshot']
            
        elif tool == 'browser_snapshot':
            # Store snapshot for reference extraction
            if isinstance(result, dict) and 'snapshot' in result:
                last_snapshot = result['snapshot']
                
        elif tool == 'browser_click':
            ref = args.get('ref', '')
            selector = extract_selector_from_ref(ref, last_snapshot, result)
            if selector:
                code_lines.append(f"  await page.locator('{selector}').click();")
            else:
                code_lines.append(f"  // Click element [ref={ref}] - TODO: Add proper selector")
            
        elif tool == 'browser_fill':
            ref = args.get('ref', '')
            value = args.get('value', '').replace("'", "\\'")
            selector = extract_selector_from_ref(ref, last_snapshot, result)
            if selector:
                code_lines.append(f"  await page.locator('{selector}').fill('{value}');")
            else:
                code_lines.append(f"  // Fill element [ref={ref}] with '{value}' - TODO: Add proper selector")
            
        elif tool == 'browser_screenshot':
            code_lines.append(f"  await page.screenshot({{ path: 'screenshot.png' }});")
            
        elif tool == 'browser_close':
            code_lines.append(f"  // Browser will close automatically after test")
    
    code_lines.extend([
        "});",
        "",
        "// Note: This is a template generated from AI execution.",
        "// You may need to:",
        "// 1. Refine selectors for better stability (use data-testid when available)",
        "// 2. Add waits and assertions as needed",
        "// 3. Handle dynamic content appropriately"
    ])
    
    return '\n'.join(code_lines)


def extract_selector_from_ref(ref, snapshot, result):
    """
    Extract a usable CSS selector from ref and snapshot data
    Returns the best available selector or None
    """
    if not ref:
        return None
    
    # Try to parse the snapshot YAML to find element info
    # The snapshot contains element references like [ref=e1]
    # We need to find the element and extract its selector
    
    # For now, we'll look for common patterns in the result
    # The MCP server might include selector info in the result
    if isinstance(result, dict):
        # Check if result contains content with element info
        content = result.get('content', [])
        if isinstance(content, list) and len(content) > 0:
            first_content = content[0]
            if isinstance(first_content, dict):
                text = first_content.get('text', '')
                # Try to extract selector from text
                if 'selector' in text.lower():
                    # Parse for selector info
                    pass
    
    # If we have snapshot data, parse it
    if snapshot and isinstance(snapshot, str):
        # Parse YAML-like snapshot to find the ref
        # Look for the ref in the snapshot and try to find associated tag/attributes
        ref_pattern = rf'\[ref={re.escape(ref)}\]'
        lines = snapshot.split('\n')
        
        for i, line in enumerate(lines):
            if ref_pattern in line:
                # Found the reference, try to extract tag and attributes from previous lines
                # Look for role, name, or tag information
                for j in range(max(0, i-5), i):
                    prev_line = lines[j]
                    # Check for role attribute
                    if 'role=' in prev_line:
                        role_match = re.search(r"role=['\"]([^'\"]+)['\"]", prev_line)
                        if role_match:
                            role = role_match.group(1)
                            # Try to get name or text
                            name_match = re.search(r"name=['\"]([^'\"]+)['\"]", line)
                            if name_match:
                                name = name_match.group(1)
                                return f"[role='{role}'][name='{name}']"
                            return f"[role='{role}']"
                
                # Try to extract text content
                text_match = re.search(r'["\']([^"\']+)["\'].*\[ref=', line)
                if text_match:
                    text = text_match.group(1)
                    # Use text selector
                    return f"text='{text}'"
    
    return None


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


if __name__ == '__main__':
    # Read host and port from config.ini
    host = config.get('server', 'host')
    port = config.getint('server', 'port')
    app.run(host=host, port=port, debug=True)
