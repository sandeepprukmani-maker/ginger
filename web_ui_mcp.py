import os
import asyncio
import threading
from flask import Flask, render_template, request, jsonify
from mcp_client import MCPClient

app = Flask(__name__)

global_loop = None
loop_thread = None
mcp_client = None
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
    """Initialize MCP client - runs once"""
    global mcp_client, initialized
    
    if not initialized:
        mcp_client = MCPClient()
        await mcp_client.start()
        initialized = True
        return True
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
    """Run automation using MCP server"""
    data = request.json
    url = data.get('url', '').strip()
    prompt = data.get('prompt', '').strip()
    
    if not url or not prompt:
        return jsonify({"error": "URL and prompt are required"}), 400
    
    try:
        if not initialized:
            run_coroutine(init_mcp_async())
        
        result = run_coroutine(
            mcp_client.call_tool('playwright_plan_and_execute', {
                'url': url,
                'prompt': prompt
            })
        )
        
        return jsonify({
            "success": result.get("success", False),
            "actions": result.get("actions", []),
            "results": result.get("results", [])
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Check if MCP server is ready"""
    try:
        if not initialized:
            run_coroutine(init_mcp_async())
        
        result = run_coroutine(
            mcp_client.call_tool('playwright_health_check', {})
        )
        
        return jsonify({
            "status": "ready",
            "mcp_server": result,
            "openai_configured": bool(os.getenv('OPENAI_API_KEY'))
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

def cleanup():
    """Cleanup resources on shutdown"""
    global global_loop, mcp_client, initialized
    
    if mcp_client and initialized:
        try:
            asyncio.run_coroutine_threadsafe(mcp_client.stop(), global_loop).result(timeout=5)
        except:
            pass
    
    if global_loop:
        global_loop.call_soon_threadsafe(global_loop.stop)
    
    initialized = False

import atexit
atexit.register(cleanup)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
