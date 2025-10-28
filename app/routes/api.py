"""
API Routes
RESTful endpoints for browser automation with security and validation
"""
import os
import json
import logging
import threading
import configparser
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

# Load configuration for default agent mode
config = configparser.ConfigParser()
config.read('config/config.ini')
DEFAULT_AGENT_MODE = config.get('playwright_mcp', 'default_agent_mode', fallback='automation')


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
        # Handle screenshot paths - convert array to JSON or handle single path
        screenshot_paths = result.get('screenshot_paths', [])
        screenshot_path_json = None
        
        if screenshot_paths and isinstance(screenshot_paths, list):
            screenshot_path_json = json.dumps(screenshot_paths)
        elif result.get('screenshot_path'):
            # Handle legacy single screenshot path
            screenshot_path_json = json.dumps([result.get('screenshot_path')])
        
        history_entry = ExecutionHistory(
            prompt=instruction,
            engine=engine_type,
            headless=headless,
            success=result.get('success', False),
            error_message=result.get('error') or result.get('message') if not result.get('success') else None,
            generated_script=result.get('generated_code'),
            healed_script=result.get('healed_code'),
            screenshot_path=screenshot_path_json,
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
            agent_mode = data.get('agent_mode', DEFAULT_AGENT_MODE)  # Use configured default agent mode
            
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
            logger.info(f"🎭 Agent Mode: {agent_mode}")
            logger.info(f"🌐 Client: {request.remote_addr}")
            logger.info("="*80)
            
            logger.info("🚀 Starting automation execution...")
            
            try:
                result = run_with_timeout(
                    orchestrator.execute_instruction,
                    300,
                    instruction,
                    engine_type,
                    headless,
                    None,  # progress_callback
                    agent_mode
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
                agent_mode = data.get('agent_mode', DEFAULT_AGENT_MODE)
                
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
                logger.info(f"🎭 Agent Mode: {agent_mode}")
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
                            progress_callback,
                            agent_mode
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
    
    @api.route('/api/mcp/status', methods=['GET'])
    def mcp_server_status():
        """Get Playwright MCP server status"""
        try:
            from app.engines.playwright_mcp import get_server_status
            status = get_server_status()
            
            return jsonify({
                'success': True,
                'server_mode': status['mode'],
                'persistent_running': status['persistent_running'],
                'message': f"MCP server in '{status['mode']}' mode"
            })
            
        except Exception as e:
            logger.error(f"Error getting MCP server status: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/api/mcp/restart', methods=['POST'])
    @require_api_key
    def restart_mcp_server():
        """Restart persistent MCP server (only works in 'always_run' mode)"""
        try:
            from app.engines.playwright_mcp import shutdown_server, get_server_status
            
            status = get_server_status()
            if status['mode'] != 'always_run':
                return jsonify({
                    'success': False,
                    'error': 'Server not in always_run mode',
                    'message': 'Server restart only available in always_run mode'
                }), 400
            
            shutdown_server()
            logger.info("🔄 MCP server restarted")
            
            return jsonify({
                'success': True,
                'message': 'MCP server shutdown. It will restart on next request.'
            })
            
        except Exception as e:
            logger.error(f"Error restarting MCP server: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            from app.engines.playwright_mcp import get_server_status
            mcp_status = get_server_status()
            
            return jsonify({
                'status': 'healthy',
                'engines': {
                    'browser_use': 'available',
                    'playwright_mcp': 'available'
                },
                'mcp_server': {
                    'mode': mcp_status['mode'],
                    'running': mcp_status['persistent_running']
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
            
            # Auto-promote healed script to generated script when opening history
            if item.healed_script:
                logger.info(f"📝 Auto-promoting healed script to generated script for history #{history_id}")
                item.generated_script = item.healed_script
                item.healed_script = None
                db.session.commit()
            
            return jsonify({
                'success': True,
                'history': item.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
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
    
    @api.route('/api/history/<int:history_id>/execute', methods=['POST'])
    @require_api_key
    @rate_limit
    def execute_from_history(history_id):
        """Execute a script from history with automatic healing if it fails"""
        try:
            item = ExecutionHistory.query.get(history_id)
            
            if not item:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'History item not found'
                }), 404
            
            if not item.generated_script:
                return jsonify({
                    'success': False,
                    'error': 'No script',
                    'message': 'No generated script found for this history item'
                }), 400
            
            logger.info(f"🔧 Executing script from history #{history_id} with auto-healing")
            
            # Get Playwright MCP engine for healing
            from app.engines.playwright_mcp.agent.healer_agent import HealerAgent
            from app.engines.playwright_mcp import create_engine as create_playwright_engine
            from auth.oauth_handler import get_oauth_token_with_retry
            from openai import OpenAI
            import configparser
            
            config = configparser.ConfigParser()
            config.read('config/config.ini')
            
            # Create MCP client and healer
            mcp_client, _ = create_playwright_engine(headless=item.headless)
            
            gateway_base_url = os.environ.get('GW_BASE_URL')
            oauth_token = get_oauth_token_with_retry(max_retries=3)
            
            llm_client = OpenAI(
                base_url=gateway_base_url,
                api_key=oauth_token,
                default_headers={"Authorization": f"Bearer {oauth_token}"}
            )
            
            model = config.get('openai', 'model', fallback='gpt-4.1-2025-04-14-eastus-dz')
            
            healer = HealerAgent(mcp_client, llm_client, model)
            
            # Run healer
            healing_result = healer.heal_test(
                test_code=item.generated_script,
                instruction=item.prompt,
                save_to_file=False
            )
            
            if healing_result.get('success'):
                healed_code = healing_result.get('healed_code')
                healing_status = healing_result.get('status', 'unknown')
                
                if healing_status == 'passing':
                    # Script passed without healing needed
                    logger.info("✅ Script executed successfully without healing needed")
                    return jsonify({
                        'success': True,
                        'message': 'Script executed successfully - no healing needed',
                        'status': 'passing',
                        'healing_needed': False,
                        'healing_attempts': healing_result.get('healing_attempts', 0),
                        'script': item.generated_script
                    })
                else:
                    # Script was healed
                    logger.info(f"🔧 Script healed successfully ({healing_result.get('healing_attempts', 0)} attempts)")
                    item.healed_script = healed_code
                    db.session.commit()
                    
                    return jsonify({
                        'success': True,
                        'message': f"Script healed successfully after {healing_result.get('healing_attempts', 0)} attempts",
                        'status': healing_status,
                        'healing_needed': True,
                        'healing_attempts': healing_result.get('healing_attempts', 0),
                        'healed_script': healed_code,
                        'healing_steps': len(healing_result.get('healing_steps', []))
                    })
            else:
                # Healing failed
                error_msg = healing_result.get('error', 'Unknown error')
                logger.error(f"❌ Healing failed: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': 'Healing failed',
                    'message': error_msg,
                    'healing_needed': True,
                    'healing_attempts': healing_result.get('healing_attempts', 0)
                }), 500
            
        except Exception as e:
            logger.error(f"Error executing from history: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Internal error',
                'message': sanitize_error_message(e)
            }), 500
    
    @api.route('/api/history/<int:history_id>/promote-healed', methods=['POST'])
    @require_api_key
    def promote_healed_script(history_id):
        """Promote healed script to generated script"""
        try:
            item = ExecutionHistory.query.get(history_id)
            
            if not item:
                return jsonify({
                    'success': False,
                    'error': 'Not found',
                    'message': 'History item not found'
                }), 404
            
            if not item.healed_script:
                return jsonify({
                    'success': False,
                    'error': 'No healed script',
                    'message': 'No healed script found for this history item'
                }), 400
            
            logger.info(f"📝 Promoting healed script to generated script for history #{history_id}")
            
            item.generated_script = item.healed_script
            item.healed_script = None
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Healed script promoted to generated script'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error promoting healed script: {str(e)}", exc_info=True)
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
