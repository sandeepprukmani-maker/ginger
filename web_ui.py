import os
import asyncio
import threading
from flask import Flask, render_template, request, jsonify
from through_app import MCPAutomationApp

app = Flask(__name__)

# Global event loop and MCP app instance
global_loop = None
loop_thread = None
mcp_app = None
initialized = False

def run_event_loop(loop):
    """Run the event loop in a separate thread"""
    asyncio.set_event_loop(loop)
    loop.run_forever()

def get_or_create_loop():
    """Get or create the persistent event loop"""
    global global_loop, loop_thread
    
    if global_loop is None:
        global_loop = asyncio.new_event_loop()
        loop_thread = threading.Thread(target=run_event_loop, args=(global_loop,), daemon=True)
        loop_thread.start()
    
    return global_loop

async def init_mcp_async():
    """Initialize MCP app - runs once"""
    global mcp_app, initialized
    
    if not initialized:
        mcp_app = MCPAutomationApp()
        openai_key = os.getenv('OPENAI_API_KEY')
        success = await mcp_app.initialize(openai_key)
        if success:
            initialized = True
            return True
        return False
    return True

def run_coroutine(coro):
    """Run a coroutine on the global event loop"""
    loop = get_or_create_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=60)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/automate', methods=['POST'])
def automate():
    """Run automation based on user prompt"""
    data = request.json
    url = data.get('url', '').strip()
    prompt = data.get('prompt', '').strip()
    
    if not url or not prompt:
        return jsonify({"error": "URL and prompt are required"}), 400
    
    try:
        # Initialize MCP if needed
        if not initialized:
            success = run_coroutine(init_mcp_async())
            if not success:
                return jsonify({"error": "Failed to initialize browser"}), 500
        
        # Run automation on the global event loop
        result = run_coroutine(
            mcp_app.process_automation_request(url, prompt, generate_code=True)
        )
        
        return jsonify({
            "success": result["success"],
            "actions": result["actions"],
            "generated_code": result.get("generated_code", ""),
            "code_file": result.get("code_file", ""),
            "results": result["results"]
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Check if system is ready"""
    return jsonify({
        "status": "ready", 
        "openai_configured": bool(os.getenv('OPENAI_API_KEY')),
        "browser_initialized": initialized
    })

def cleanup():
    """Cleanup resources on shutdown"""
    global global_loop, mcp_app, initialized
    
    if mcp_app and initialized:
        try:
            asyncio.run_coroutine_threadsafe(mcp_app.cleanup(), global_loop).result(timeout=5)
        except:
            pass
    
    if global_loop:
        global_loop.call_soon_threadsafe(global_loop.stop)
    
    initialized = False

import atexit
atexit.register(cleanup)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
