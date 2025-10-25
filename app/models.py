"""
Database Models for AI Browser Automation
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import json


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class ExecutionHistory(db.Model):
    """Model for storing automation execution history"""
    
    __tablename__ = 'execution_history'
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    prompt = db.Column(db.Text, nullable=False)
    engine = db.Column(db.String(50), nullable=False)
    headless = db.Column(db.Boolean, nullable=False, default=False)
    
    success = db.Column(db.Boolean, nullable=False, default=False)
    error_message = db.Column(db.Text, nullable=True)
    
    generated_script = db.Column(db.Text, nullable=True)
    healed_script = db.Column(db.Text, nullable=True)
    screenshot_path = db.Column(db.String(500), nullable=True)
    execution_logs = db.Column(db.Text, nullable=True)
    
    iterations = db.Column(db.Integer, nullable=True)
    execution_time = db.Column(db.Float, nullable=True)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'prompt': self.prompt,
            'engine': self.engine,
            'headless': self.headless,
            'success': self.success,
            'error_message': self.error_message,
            'generated_script': self.generated_script,
            'healed_script': self.healed_script,
            'screenshot_path': self.screenshot_path,
            'execution_logs': self.execution_logs,
            'iterations': self.iterations,
            'execution_time': self.execution_time
        }


class LearnedTask(db.Model):
    """Model for storing learned automation tasks for the Task Library"""
    
    __tablename__ = 'learned_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    task_name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    steps = db.Column(db.Text, nullable=True)
    playwright_code = db.Column(db.Text, nullable=False)
    tags = db.Column(db.Text, nullable=True)
    embedding_vector = db.Column(db.LargeBinary, nullable=True)
    version = db.Column(db.Integer, default=1)
    parent_task_id = db.Column(db.String(100), nullable=True)
    success_count = db.Column(db.Integer, default=0)
    failure_count = db.Column(db.Integer, default=0)
    last_executed = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'description': self.description,
            'steps': json.loads(self.steps) if self.steps else [],
            'playwright_code': self.playwright_code,
            'tags': json.loads(self.tags) if self.tags else [],
            'version': self.version,
            'parent_task_id': self.parent_task_id,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'last_executed': self.last_executed.isoformat() if self.last_executed else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TaskExecution(db.Model):
    """Model for storing task execution history for feedback loop"""
    
    __tablename__ = 'task_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(100), db.ForeignKey('learned_tasks.task_id'), nullable=False)
    execution_result = db.Column(db.Text, nullable=True)
    success = db.Column(db.Boolean, nullable=False)
    error_message = db.Column(db.Text, nullable=True)
    execution_time_ms = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'execution_result': self.execution_result,
            'success': self.success,
            'error_message': self.error_message,
            'execution_time_ms': self.execution_time_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
