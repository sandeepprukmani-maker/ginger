import os
import json
import subprocess
import time
import signal
import requests
from flask import Flask, render_template, request, jsonify
from openai import OpenAI

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user

app = Flask(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Global variable to track MCP server process
mcp_server_process = None
MCP_SERVER_URL = "http://localhost:8080/mcp"

def start_mcp_server():
    """Start the Playwright MCP server if not already running"""
    global mcp_server_process
    
    if mcp_server_process is not None:
        return {"status": "already_running"}
    
    try:
        # Start the MCP server process
        mcp_server_process = subprocess.Popen(
            ["node", "cli.js", "--headless", "--port", "8080", "--host", "localhost"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give the server a moment to start
        # The MCP server doesn't have a health endpoint, so we just wait
        time.sleep(2)
        
        # Check if process is still running (didn't crash immediately)
        if mcp_server_process.poll() is None:
            return {"status": "started", "url": MCP_SERVER_URL}
        else:
            mcp_server_process = None
            return {"status": "error", "message": "Server failed to start"}
    except Exception as e:
        mcp_server_process = None
        return {"status": "error", "message": str(e)}

def stop_mcp_server():
    """Stop the Playwright MCP server"""
    global mcp_server_process
    
    if mcp_server_process is None:
        return {"status": "not_running"}
    
    try:
        mcp_server_process.send_signal(signal.SIGTERM)
        mcp_server_process.wait(timeout=5)
        mcp_server_process = None
        return {"status": "stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def interpret_natural_language(user_input):
    """Use OpenAI to interpret natural language and convert to Playwright actions"""
    try:
        system_prompt = """You are an expert at converting natural language UI automation instructions into Playwright code.

Given a user's natural language description of a web automation task, generate clean, executable Playwright Python code.

Guidelines:
- Use async/await syntax with Playwright async API
- Include proper imports
- Generate complete, runnable code
- Use best practices for selectors (prefer data-testid, accessible roles, or text content)
- Add reasonable waits and error handling
- Include comments explaining each step
- The code should be ready to run as-is

Return your response as JSON with this structure:
{
    "playwright_code": "the complete Python code",
    "explanation": "brief explanation of what the code does",
    "actions": ["list", "of", "key", "actions"]
}"""

        response = openai_client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Convert this to Playwright code: {user_input}"}
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=2048
        )
        
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            return result
        else:
            return {
                "error": "Empty response from OpenAI",
                "playwright_code": "# Error generating code",
                "explanation": "Received empty response",
                "actions": []
            }
    except Exception as e:
        return {
            "error": str(e),
            "playwright_code": "# Error generating code",
            "explanation": f"Failed to generate code: {str(e)}",
            "actions": []
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/interpret', methods=['POST'])
def interpret():
    """API endpoint to interpret natural language and generate Playwright code"""
    data = request.json or {}
    user_input = data.get('input', '')
    
    if not user_input:
        return jsonify({"error": "No input provided"}), 400
    
    result = interpret_natural_language(user_input)
    return jsonify(result)

@app.route('/api/server/start', methods=['POST'])
def server_start():
    """Start the MCP server"""
    result = start_mcp_server()
    return jsonify(result)

@app.route('/api/server/stop', methods=['POST'])
def server_stop():
    """Stop the MCP server"""
    result = stop_mcp_server()
    return jsonify(result)

@app.route('/api/server/status', methods=['GET'])
def server_status():
    """Check MCP server status"""
    global mcp_server_process
    
    if mcp_server_process is None:
        return jsonify({"status": "stopped"})
    
    if mcp_server_process.poll() is None:
        return jsonify({"status": "running", "url": MCP_SERVER_URL})
    else:
        mcp_server_process = None
        return jsonify({"status": "stopped"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
