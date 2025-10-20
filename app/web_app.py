"""
Flask Web Application for Browser Automation
Provides web interface for users to input instructions
"""
from flask import Flask, render_template, request, jsonify
from app.mcp_stdio_client import MCPStdioClient
from app.browser_agent import BrowserAgent
import os
import configparser

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


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check if MCP server is accessible
        client, _ = get_mcp_client()
        
        if not client.initialized:
            client.initialize()
        
        return jsonify({
            'status': 'healthy',
            'mcp_connected': True,
            'transport': 'STDIO'
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
