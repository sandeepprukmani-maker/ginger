"""
Flask Web Application for Browser Automation
Provides web interface for users to input instructions
"""
from flask import Flask, render_template, request, jsonify
from app.mcp_stdio_client import MCPStdioClient
from app.browser_agent import BrowserAgent
from app.browser_use_engine import BrowserUseEngine
import os
import configparser

# Load configuration from .ini file
config = configparser.ConfigParser()
config.read('config.ini')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Engine instances cache
engine_instances = {
    'playwright_mcp': {},  # {headless: instance}
    'browser_use': {}      # {headless: instance}
}

def get_engine(engine_type: str, headless: bool):
    """
    Get or create engine instance
    
    Args:
        engine_type: 'playwright_mcp' or 'browser_use'
        headless: Run in headless mode
        
    Returns:
        Tuple of (client/engine, agent/None)
    """
    global engine_instances
    
    # Use headless as cache key
    cache_key = headless
    
    if engine_type == 'playwright_mcp':
        # Cache Playwright MCP instances (thread-safe subprocess communication)
        if cache_key not in engine_instances['playwright_mcp']:
            mcp_client = MCPStdioClient(headless=headless)
            browser_agent = BrowserAgent(mcp_client)
            engine_instances['playwright_mcp'][cache_key] = (mcp_client, browser_agent)
        return engine_instances['playwright_mcp'][cache_key]
    
    elif engine_type == 'browser_use':
        # DO NOT cache browser-use instances - create fresh each time
        # Each request creates its own event loop and browser for thread safety
        browser_use_engine = BrowserUseEngine(headless=headless)
        return (browser_use_engine, None)
    
    else:
        raise ValueError(f"Unknown engine type: {engine_type}")


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
        engine_type = data.get('engine', 'browser_use')  # Default to browser_use
        headless = data.get('headless', False)  # Default to headful (visible)
        
        if not instruction:
            return jsonify({
                'success': False,
                'error': 'Please provide an instruction'
            }), 400
        
        # Get appropriate engine
        if engine_type == 'playwright_mcp':
            client, agent = get_engine('playwright_mcp', headless)
            
            # Ensure client is initialized
            if not client.initialized:
                client.initialize()
            
            # Execute the instruction
            result = agent.execute_instruction(instruction)
        
        elif engine_type == 'browser_use':
            browser_use_engine, _ = get_engine('browser_use', headless)
            
            # Execute using browser-use
            result = browser_use_engine.execute_instruction_sync(instruction)
        
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown engine type: {engine_type}'
            }), 400
        
        # Add engine info to result
        result['engine'] = engine_type
        result['headless'] = headless
        
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
        engine_type = request.args.get('engine', 'playwright_mcp')
        
        if engine_type == 'playwright_mcp':
            client, _ = get_engine('playwright_mcp', headless=True)
            
            if not client.initialized:
                client.initialize()
            
            tools = client.list_tools()
        else:
            # browser-use doesn't expose tools in the same way
            tools = [
                {'name': 'browser_use_agent', 'description': 'AI-powered browser automation'}
            ]
        
        return jsonify({
            'success': True,
            'tools': tools,
            'engine': engine_type
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
        data = request.get_json() or {}
        engine_type = data.get('engine', 'playwright_mcp')
        
        if engine_type == 'playwright_mcp':
            # Reset Playwright MCP agent
            _, agent = get_engine('playwright_mcp', headless=True)
            agent.reset_conversation()
        else:
            # Browser-use doesn't maintain conversation state
            # Each request creates a fresh instance, so nothing to reset
            pass
        
        return jsonify({
            'success': True,
            'message': 'Agent reset successfully',
            'engine': engine_type
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
        # Application is healthy if Flask is running
        return jsonify({
            'status': 'healthy',
            'engines': {
                'browser_use': 'available',
                'playwright_mcp': 'available'
            },
            'message': 'Dual-engine browser automation ready'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


if __name__ == '__main__':
    # Read host and port from config.ini
    host = config.get('server', 'host')
    port = config.getint('server', 'port')
    app.run(host=host, port=port, debug=True)
