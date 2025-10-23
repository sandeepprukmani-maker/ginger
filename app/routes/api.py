"""
API Routes
RESTful endpoints for browser automation with security and validation
"""
import os
import logging
from flask import Blueprint, render_template, request, jsonify
from app.services.engine_orchestrator import EngineOrchestrator
from app.middleware.security import (
    require_api_key,
    rate_limit,
    validate_engine_type,
    validate_instruction,
    sanitize_error_message
)
from app.utils.timeout import run_with_timeout, TimeoutError

logger = logging.getLogger(__name__)


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
    @require_api_key
    @rate_limit
    def execute_instruction():
        """Execute a browser automation instruction"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Invalid request',
                    'message': 'Request body must be valid JSON'
                }), 400
            
            instruction = data.get('instruction', '').strip()
            engine_type = data.get('engine', 'hybrid')
            headless = data.get('headless', False)
            
            is_valid, error_msg = validate_instruction(instruction)
            if not is_valid:
                logger.warning(f"⚠️  Invalid instruction: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid instruction',
                    'message': error_msg
                }), 400
            
            is_valid, error_msg = validate_engine_type(engine_type)
            if not is_valid:
                logger.warning(f"⚠️  Invalid engine type: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid engine type',
                    'message': error_msg
                }), 400
            
            if not isinstance(headless, bool):
                return jsonify({
                    'success': False,
                    'error': 'Invalid parameter',
                    'message': 'headless must be a boolean'
                }), 400
            
            logger.info("="*80)
            logger.info("📨 NEW AUTOMATION REQUEST")
            logger.info(f"📝 Instruction: {instruction}")
            logger.info(f"🔧 Engine: {engine_type}")
            logger.info(f"👁️  Headless: {headless}")
            logger.info(f"🌐 Client: {request.remote_addr}")
            logger.info("="*80)
            
            logger.info("🚀 Starting automation execution...")
            
            try:
                result = run_with_timeout(
                    orchestrator.execute_instruction,
                    300,
                    instruction,
                    engine_type,
                    headless
                )
            except TimeoutError as e:
                logger.error(f"⏱️  Automation timed out: {str(e)}")
                orchestrator.cleanup_after_timeout(engine_type, headless)
                return jsonify({
                    'success': False,
                    'error': 'Timeout',
                    'message': 'Operation timed out. The task took longer than 5 minutes to complete.',
                    'timeout': True
                }), 408
            
            if result.get('success'):
                logger.info(f"✅ Automation completed successfully in {result.get('iterations', 0)} steps")
            else:
                logger.error(f"❌ Automation failed: {result.get('error', 'Unknown error')}")
            
            logger.info("="*80)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"💥 Exception in execute_instruction: {str(e)}", exc_info=True)
            
            user_message = sanitize_error_message(e)
            
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': user_message
            }), 500
    
    @api.route('/api/tools', methods=['GET'])
    def get_tools():
        """Get available browser tools"""
        try:
            engine_type = request.args.get('engine', 'hybrid')
            
            is_valid, error_msg = validate_engine_type(engine_type)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': 'Invalid engine type',
                    'message': error_msg
                }), 400
            
            tools = orchestrator.get_tools(engine_type)
            
            return jsonify({
                'success': True,
                'tools': tools,
                'engine': engine_type
            })
            
        except Exception as e:
            logger.error(f"Error getting tools: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/api/reset', methods=['POST'])
    @require_api_key
    def reset_agent():
        """Reset the browser agent"""
        try:
            data = request.get_json() or {}
            engine_type = data.get('engine', 'hybrid')
            
            is_valid, error_msg = validate_engine_type(engine_type)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': 'Invalid engine type',
                    'message': error_msg
                }), 400
            
            orchestrator.reset_agent(engine_type)
            
            return jsonify({
                'success': True,
                'message': 'Agent reset successfully',
                'engine': engine_type
            })
            
        except Exception as e:
            logger.error(f"Error resetting agent: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
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
                'message': 'Hybrid-engine browser automation ready',
                'security': {
                    'authentication': 'enabled' if os.environ.get('API_KEY') else 'disabled',
                    'rate_limiting': 'enabled'
                }
            })
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return jsonify({
                'status': 'unhealthy',
                'error': 'Service unavailable'
            }), 503
    
    return api
