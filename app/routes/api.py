"""
API Routes
RESTful endpoints for browser automation
"""
from flask import Blueprint, render_template, request, jsonify
from app.services.engine_orchestrator import EngineOrchestrator
import logging

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
    def execute_instruction():
        """Execute a browser automation instruction"""
        import signal
        from contextlib import contextmanager
        
        @contextmanager
        def timeout(seconds):
            """Context manager for operation timeout"""
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Operation timed out after {seconds} seconds")
            
            # Set the signal handler and alarm
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        try:
            data = request.get_json()
            instruction = data.get('instruction', '').strip()
            engine_type = data.get('engine', 'hybrid')
            headless = data.get('headless', False)
            
            logger.info("="*80)
            logger.info("📨 NEW AUTOMATION REQUEST")
            logger.info(f"📝 Instruction: {instruction}")
            logger.info(f"🔧 Engine: {engine_type}")
            logger.info(f"👁️  Headless: {headless}")
            logger.info("="*80)
            
            if not instruction:
                logger.warning("⚠️  Empty instruction received")
                return jsonify({
                    'success': False,
                    'error': 'Please provide an instruction'
                }), 400
            
            logger.info("🚀 Starting automation execution...")
            
            # Execute with 5-minute timeout for long-running tasks
            try:
                with timeout(300):  # 5 minutes
                    result = orchestrator.execute_instruction(instruction, engine_type, headless)
            except TimeoutError as e:
                logger.error(f"⏱️ Automation timed out: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Operation timed out. The task took longer than 5 minutes to complete.',
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
