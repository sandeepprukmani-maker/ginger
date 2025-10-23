from flask import Blueprint, render_template, request, jsonify, send_file
from app.models.database import DatabaseManager, Task, ActionLog, HealingEvent
from app.services.code_generator import PlaywrightCodeGenerator
import os
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

def init_routes(db_manager: DatabaseManager, code_generator: PlaywrightCodeGenerator):
    """Initialize routes with dependencies"""
    
    @main_bp.route('/')
    def index():
        """Main dashboard"""
        return render_template('index.html')
    
    @main_bp.route('/api/tasks', methods=['GET'])
    def get_tasks():
        """Get all tasks"""
        try:
            session = db_manager.get_session()
            tasks = session.query(Task).order_by(Task.created_at.desc()).all()
            result = [task.to_dict() for task in tasks]
            db_manager.close_session()
            return jsonify({'success': True, 'tasks': result})
        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @main_bp.route('/api/tasks/<int:task_id>', methods=['GET'])
    def get_task(task_id):
        """Get a specific task"""
        try:
            session = db_manager.get_session()
            task = session.query(Task).filter_by(id=task_id).first()
            
            if not task:
                return jsonify({'success': False, 'error': 'Task not found'}), 404
            
            result = task.to_dict()
            db_manager.close_session()
            return jsonify({'success': True, 'task': result})
        except Exception as e:
            logger.error(f"Error getting task: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @main_bp.route('/api/tasks/<int:task_id>/logs', methods=['GET'])
    def get_task_logs(task_id):
        """Get action logs for a task"""
        try:
            session = db_manager.get_session()
            logs = session.query(ActionLog).filter_by(task_id=task_id).order_by(ActionLog.step_number).all()
            result = [log.to_dict() for log in logs]
            db_manager.close_session()
            return jsonify({'success': True, 'logs': result})
        except Exception as e:
            logger.error(f"Error getting task logs: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @main_bp.route('/api/tasks/<int:task_id>/healing', methods=['GET'])
    def get_task_healing(task_id):
        """Get healing events for a task"""
        try:
            session = db_manager.get_session()
            events = session.query(HealingEvent).filter_by(task_id=task_id).order_by(HealingEvent.timestamp).all()
            result = [event.to_dict() for event in events]
            db_manager.close_session()
            return jsonify({'success': True, 'healing_events': result})
        except Exception as e:
            logger.error(f"Error getting healing events: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @main_bp.route('/api/tasks/<int:task_id>/generate-script', methods=['POST'])
    def generate_script(task_id):
        """Generate Playwright script for a task"""
        try:
            session = db_manager.get_session()
            task = session.query(Task).filter_by(id=task_id).first()
            
            if not task:
                return jsonify({'success': False, 'error': 'Task not found'}), 404
            
            script_path = code_generator.generate_script(task_id)
            
            if script_path:
                task.generated_script_path = script_path
                session.commit()
                db_manager.close_session()
                
                return jsonify({
                    'success': True,
                    'script_path': script_path,
                    'message': 'Script generated successfully'
                })
            else:
                db_manager.close_session()
                return jsonify({'success': False, 'error': 'Failed to generate script'}), 500
                
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @main_bp.route('/api/tasks/<int:task_id>/download-script', methods=['GET'])
    def download_script(task_id):
        """Download generated script"""
        try:
            session = db_manager.get_session()
            task = session.query(Task).filter_by(id=task_id).first()
            
            if not task:
                return jsonify({'success': False, 'error': 'Task not found'}), 404
            
            script_path = task.generated_script_path or code_generator.get_script_path(task_id)
            
            if script_path and os.path.exists(script_path):
                db_manager.close_session()
                return send_file(script_path, as_attachment=True, download_name=os.path.basename(script_path))
            else:
                db_manager.close_session()
                return jsonify({'success': False, 'error': 'Script not found'}), 404
                
        except Exception as e:
            logger.error(f"Error downloading script: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @main_bp.route('/api/tasks/<int:task_id>/script', methods=['GET'])
    def get_script_content(task_id):
        """Get generated script content for viewing"""
        try:
            session = db_manager.get_session()
            task = session.query(Task).filter_by(id=task_id).first()
            
            if not task:
                return jsonify({'success': False, 'error': 'Task not found'}), 404
            
            script_path = task.generated_script_path or code_generator.get_script_path(task_id)
            
            if script_path and os.path.exists(script_path):
                with open(script_path, 'r') as f:
                    content = f.read()
                db_manager.close_session()
                return jsonify({
                    'success': True,
                    'content': content,
                    'path': script_path,
                    'filename': os.path.basename(script_path)
                })
            else:
                db_manager.close_session()
                return jsonify({'success': False, 'error': 'Script not found'}), 404
                
        except Exception as e:
            logger.error(f"Error getting script content: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @main_bp.route('/api/tasks/<int:task_id>/execute-script', methods=['POST'])
    def execute_script(task_id):
        """Execute the generated script"""
        try:
            session = db_manager.get_session()
            task = session.query(Task).filter_by(id=task_id).first()
            
            if not task:
                return jsonify({'success': False, 'error': 'Task not found'}), 404
            
            script_path = task.generated_script_path or code_generator.get_script_path(task_id)
            
            if not script_path or not os.path.exists(script_path):
                db_manager.close_session()
                return jsonify({'success': False, 'error': 'Script not found'}), 404
            
            db_manager.close_session()
            
            # Execute the script in a subprocess
            import subprocess
            import threading
            
            result = {'success': False, 'output': '', 'error': ''}
            
            def run_script():
                try:
                    process = subprocess.Popen(
                        ['python', script_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=os.path.dirname(script_path)
                    )
                    
                    stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout
                    
                    result['success'] = process.returncode == 0
                    result['output'] = stdout
                    result['error'] = stderr
                    result['exit_code'] = process.returncode
                    
                except subprocess.TimeoutExpired:
                    process.kill()
                    result['success'] = False
                    result['error'] = 'Script execution timed out (5 minutes)'
                except Exception as e:
                    result['success'] = False
                    result['error'] = str(e)
            
            # Run in thread to avoid blocking
            thread = threading.Thread(target=run_script)
            thread.start()
            thread.join(timeout=305)  # Slightly longer than subprocess timeout
            
            return jsonify({
                'success': result.get('success', False),
                'output': result.get('output', ''),
                'error': result.get('error', ''),
                'exit_code': result.get('exit_code', -1),
                'message': 'Script executed' if result.get('success') else 'Script execution failed'
            })
                
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @main_bp.route('/api/stats', methods=['GET'])
    def get_stats():
        """Get dashboard statistics"""
        try:
            session = db_manager.get_session()
            
            total_tasks = session.query(Task).count()
            completed_tasks = session.query(Task).filter_by(status='completed').count()
            failed_tasks = session.query(Task).filter_by(status='failed').count()
            running_tasks = session.query(Task).filter_by(status='running').count()
            
            total_healing_events = session.query(HealingEvent).count()
            successful_healings = session.query(HealingEvent).filter_by(success=True).count()
            browser_use_healings = session.query(HealingEvent).filter_by(healing_source='browser-use', success=True).count()
            mcp_healings = session.query(HealingEvent).filter_by(healing_source='mcp', success=True).count()
            
            stats = {
                'tasks': {
                    'total': total_tasks,
                    'completed': completed_tasks,
                    'failed': failed_tasks,
                    'running': running_tasks
                },
                'healing': {
                    'total_events': total_healing_events,
                    'successful': successful_healings,
                    'browser_use': browser_use_healings,
                    'mcp': mcp_healings
                }
            }
            
            db_manager.close_session()
            return jsonify({'success': True, 'stats': stats})
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return main_bp
