"""
API Routes
RESTful endpoints for browser automation
"""
from flask import Blueprint, render_template, request, jsonify
from app.services.engine_orchestrator import EngineOrchestrator


def create_api_routes(orchestrator: EngineOrchestrator) -> Blueprint:
    """
    Create API routes blueprint
    
    Args:
        orchestrator: Engine orchestrator instance
        
    Returns:
        Flask Blueprint with all routes
    """
    api = Blueprint('api', __name__)
    
    @api.route('/')
    def index():
        """Render main page"""
        return render_template('index.html')
    
    @api.route('/api/execute', methods=['POST'])
    def execute_instruction():
        """Execute a browser automation instruction"""
        try:
            data = request.get_json()
            instruction = data.get('instruction', '').strip()
            engine_type = data.get('engine', 'hybrid')
            headless = data.get('headless', False)
            
            if not instruction:
                return jsonify({
                    'success': False,
                    'error': 'Please provide an instruction'
                }), 400
            
            result = orchestrator.execute_instruction(instruction, engine_type, headless)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @api.route('/api/tools', methods=['GET'])
    def get_tools():
        """Get available browser tools"""
        try:
            engine_type = request.args.get('engine', 'hybrid')
            tools = orchestrator.get_tools(engine_type)
            
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
    
    @api.route('/api/reset', methods=['POST'])
    def reset_agent():
        """Reset the browser agent"""
        try:
            data = request.get_json() or {}
            engine_type = data.get('engine', 'hybrid')
            
            orchestrator.reset_agent(engine_type)
            
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
    
    @api.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            return jsonify({
                'status': 'healthy',
                'engines': {
                    'hybrid': 'available',
                    'browser_use': 'available',
                    'playwright_mcp': 'available'
                },
                'message': 'Hybrid-engine browser automation ready'
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 503
    
    return api
