"""
API Routes
RESTful endpoints for browser automation with security and validation
"""
import os
import json
import logging
import threading
from queue import Queue
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, Response, stream_with_context, current_app
from app.models import db, ExecutionHistory
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


def save_execution_to_history(instruction, engine_type, headless, result):
    """
    Save execution result to history database
    
    Args:
        instruction: The automation instruction
        engine_type: The engine used (browser_use or playwright_mcp)
        headless: Whether execution was headless
        result: The execution result dictionary
    """
    try:
        history_entry = ExecutionHistory(
            prompt=instruction,
            engine=engine_type,
            headless=headless,
            success=result.get('success', False),
            error_message=result.get('error') or result.get('message') if not result.get('success') else None,
            generated_script=result.get('generated_code'),
            healed_script=result.get('healed_code'),
            screenshot_path=result.get('screenshot_path'),
            execution_logs=json.dumps(result.get('history', [])) if result.get('history') else None,
            iterations=result.get('iterations'),
            execution_time=result.get('execution_time')
        )
        
        db.session.add(history_entry)
        db.session.commit()
        
        logger.info(f"💾 Saved execution to history (ID: {history_entry.id})")
        return history_entry.id
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to save execution to history: {str(e)}", exc_info=True)
        return None


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
        """Render dashboard page"""
        return render_template('dashboard.html')
    
    @api.route('/history')
    def history():
        """Render history page"""
        return render_template('history.html')
    
    @api.route('/configuration')
    def configuration():
        """Render configuration page"""
        return render_template('configuration.html')
    
    @api.route('/teaching-mode')
    def teaching_mode():
        """Render teaching mode page"""
        return render_template('teaching-mode.html')
    
    @api.route('/task-library')
    def task_library():
        """Render task library page"""
        return render_template('task-library.html')
    
    @api.route('/recall-mode')
    def recall_mode():
        """Render recall mode page"""
        return render_template('recall-mode.html')
    
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
            engine_type = data.get('engine', 'browser_use')
            headless = data.get('headless', False)

            print(instruction,engine_type)
            
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
            
            save_execution_to_history(instruction, engine_type, headless, result)
            
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
    
    @api.route('/api/execute/stream', methods=['POST'])
    @require_api_key
    @rate_limit
    def execute_instruction_stream():
        """Execute a browser automation instruction with Server-Sent Events streaming"""
        def generate_progress():
            """Generator function for SSE streaming"""
            try:
                data = request.get_json()
                
                if not data:
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid request', 'message': 'Request body must be valid JSON'})}\n\n"
                    return
                
                instruction = data.get('instruction', '').strip()
                engine_type = data.get('engine', 'browser_use')
                headless = data.get('headless', False)
                
                # Validation
                is_valid, error_msg = validate_instruction(instruction)
                if not is_valid:
                    logger.warning(f"⚠️  Invalid instruction: {error_msg}")
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid instruction', 'message': error_msg})}\n\n"
                    return
                
                is_valid, error_msg = validate_engine_type(engine_type)
                if not is_valid:
                    logger.warning(f"⚠️  Invalid engine type: {error_msg}")
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid engine type', 'message': error_msg})}\n\n"
                    return
                
                if not isinstance(headless, bool):
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Invalid parameter', 'message': 'headless must be a boolean'})}\n\n"
                    return
                
                logger.info("="*80)
                logger.info("📨 NEW AUTOMATION REQUEST (STREAMING)")
                logger.info(f"📝 Instruction: {instruction}")
                logger.info(f"🔧 Engine: {engine_type}")
                logger.info(f"👁️  Headless: {headless}")
                logger.info(f"🌐 Client: {request.remote_addr}")
                logger.info("="*80)
                
                # Send start event
                yield f"data: {json.dumps({'type': 'start', 'message': 'Starting automation...'})}\n\n"
                
                # Create a queue for progress updates
                progress_queue = Queue()
                result_holder = {}
                
                # Capture the Flask app object for use in the thread
                app = current_app._get_current_object()
                
                def progress_callback(event_type, data):
                    """Callback function to send progress updates"""
                    progress_queue.put({'type': event_type, 'data': data})
                
                def execute_in_thread():
                    """Execute automation in a separate thread"""
                    try:
                        result = orchestrator.execute_instruction_with_progress(
                            instruction,
                            engine_type,
                            headless,
                            progress_callback
                        )
                        result_holder['result'] = result
                        # Use app context for database operations in thread
                        with app.app_context():
                            save_execution_to_history(instruction, engine_type, headless, result)
                        progress_queue.put({'type': 'done', 'result': result})
                    except Exception as e:
                        logger.error(f"💥 Exception in threaded execution: {str(e)}", exc_info=True)
                        result_holder['error'] = str(e)
                        error_result = {
                            'success': False,
                            'error': str(e),
                            'message': sanitize_error_message(e)
                        }
                        # Use app context for database operations in thread
                        with app.app_context():
                            save_execution_to_history(instruction, engine_type, headless, error_result)
                        progress_queue.put({'type': 'error', 'error': str(e), 'message': sanitize_error_message(e)})
                
                # Start execution in thread
                execution_thread = threading.Thread(target=execute_in_thread)
                execution_thread.daemon = True
                execution_thread.start()
                
                # Stream progress updates
                while True:
                    event = progress_queue.get()
                    
                    if event['type'] == 'done':
                        # Send final result
                        yield f"data: {json.dumps(event)}\n\n"
                        logger.info("✅ Streaming completed successfully")
                        break
                    elif event['type'] == 'error':
                        # Send error and stop
                        yield f"data: {json.dumps(event)}\n\n"
                        logger.error(f"❌ Streaming failed: {event.get('error')}")
                        break
                    else:
                        # Send progress update
                        yield f"data: {json.dumps(event)}\n\n"
                
                logger.info("="*80)
                
            except Exception as e:
                logger.error(f"💥 Exception in SSE streaming: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'error': 'Internal error', 'message': sanitize_error_message(e)})}\n\n"
        
        return Response(
            stream_with_context(generate_progress()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
    
    @api.route('/api/tools', methods=['GET'])
    def get_tools():
        """Get available browser tools"""
        try:
            engine_type = request.args.get('engine', 'browser_use')
            
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
            engine_type = data.get('engine', 'browser_use')
            
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
                    'browser_use': 'available',
                    'playwright_mcp': 'available'
                },
                'message': 'AI browser automation ready',
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
    
    @api.route('/api/history', methods=['GET'])
    def get_history():
        """Get all execution history"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            history_query = ExecutionHistory.query.order_by(
                ExecutionHistory.created_at.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            return jsonify({
                'success': True,
                'history': [item.to_dict() for item in history_query.items],
                'total': history_query.total,
                'page': page,
                'pages': history_query.pages,
                'per_page': per_page
            })
            
        except Exception as e:
            logger.error(f"Error getting history: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/api/history/<int:history_id>', methods=['GET'])
    def get_history_item(history_id):
        """Get a specific execution history item"""
        try:
            item = ExecutionHistory.query.get(history_id)
            
            if not item:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'History item not found'
                }), 404
            
            return jsonify({
                'success': True,
                'history': item.to_dict()
            })
            
        except Exception as e:
            logger.error(f"Error getting history item: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/api/history', methods=['DELETE'])
    @require_api_key
    def delete_all_history():
        """Delete all execution history"""
        try:
            count = ExecutionHistory.query.delete()
            db.session.commit()
            
            logger.info(f"🗑️  Deleted {count} history items")
            
            return jsonify({
                'success': True,
                'message': f'Deleted {count} history items',
                'count': count
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting history: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/api/history/<int:history_id>', methods=['DELETE'])
    @require_api_key
    def delete_history_item(history_id):
        """Delete a specific execution history item"""
        try:
            item = ExecutionHistory.query.get(history_id)
            
            if not item:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'History item not found'
                }), 404
            
            db.session.delete(item)
            db.session.commit()
            
            logger.info(f"🗑️  Deleted history item {history_id}")
            
            return jsonify({
                'success': True,
                'message': 'History item deleted'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting history item: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/api/code/download/<int:history_id>', methods=['GET'])
    def download_code(history_id):
        """Download generated code as .py file"""
        try:
            from flask import send_file, make_response
            import io
            
            item = ExecutionHistory.query.get(history_id)
            
            if not item:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'History item not found'
                }), 404
            
            code = item.generated_script or "# No code generated"
            
            # Create file-like object
            buffer = io.BytesIO()
            buffer.write(code.encode('utf-8'))
            buffer.seek(0)
            
            # Generate filename
            prompt_slug = ''.join(c if c.isalnum() else '_' for c in item.prompt[:30])
            filename = f"test_{prompt_slug}_{history_id}.py"
            
            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='text/x-python'
            )
            
        except Exception as e:
            logger.error(f"Error downloading code: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    return api
