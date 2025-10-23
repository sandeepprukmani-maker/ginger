import eventlet
eventlet.monkey_patch()

import os
import logging
import yaml
import asyncio
from flask import Flask
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from app.models.database import DatabaseManager, Task
from app.routes.main import main_bp, init_routes
from app.services.code_generator import PlaywrightCodeGenerator
from app.services.healing_orchestrator import HealingOrchestrator
from datetime import datetime

load_dotenv()

os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/automation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = os.getenv('SESSION_SECRET', os.urandom(24))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

db_manager = DatabaseManager(os.getenv('DATABASE_PATH', 'data/automation.db'))
code_generator = PlaywrightCodeGenerator(db_manager, config.get('export', {}).get('script_directory', 'data/generated_scripts'))

initialized_main_bp = init_routes(db_manager, code_generator)
app.register_blueprint(initialized_main_bp)

def emit_callback(event_type, data):
    """Callback to emit events via SocketIO"""
    try:
        socketio.emit(event_type, data)
    except Exception as e:
        logger.error(f"Error emitting event {event_type}: {e}")

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

@socketio.on('execute_task')
def handle_execute_task(data):
    """Handle task execution request"""
    try:
        instruction = data.get('instruction')
        headless = data.get('headless', True)
        
        if not instruction:
            emit('error', {'message': 'Instruction is required'})
            return
        
        session = db_manager.get_session()
        task = Task(
            instruction=instruction,
            status='pending'
        )
        session.add(task)
        session.commit()
        task_id = task.id
        db_manager.close_session()
        
        emit('task_created', {'task_id': task_id, 'instruction': instruction})
        
        logger.info(f"Task {task_id} created: {instruction} (headless={headless})")
        
        def run_async_task():
            """Run the async task in a new event loop"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                task_config = config.copy()
                task_config['browser'] = task_config.get('browser', {}).copy()
                task_config['browser']['headless'] = headless
                
                orchestrator = HealingOrchestrator(task_config, db_manager)
                result = loop.run_until_complete(
                    orchestrator.execute_with_healing(task_id, instruction, emit_callback)
                )
                
                if result['success']:
                    script_path = code_generator.generate_script(task_id, headless=headless)
                    
                    session = db_manager.get_session()
                    task = session.query(Task).filter_by(id=task_id).first()
                    if task and script_path:
                        task.generated_script_path = script_path
                        session.commit()
                    db_manager.close_session()
                    
                    socketio.emit('task_complete', {
                        'task_id': task_id,
                        'success': True,
                        'script_path': script_path
                    })
                else:
                    socketio.emit('task_complete', {
                        'task_id': task_id,
                        'success': False,
                        'error': result.get('error')
                    })
                    
            except Exception as e:
                logger.error(f"Error executing task {task_id}: {e}")
                socketio.emit('task_error', {
                    'task_id': task_id,
                    'error': str(e)
                })
            finally:
                loop.close()
        
        eventlet.spawn(run_async_task)
        
    except Exception as e:
        logger.error(f"Error in handle_execute_task: {e}")
        emit('error', {'message': str(e)})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}

if __name__ == '__main__':
    logger.info("Starting Self-Healing Browser Automation System")
    logger.info(f"Dashboard available at: http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True, use_reloader=True, log_output=True)
