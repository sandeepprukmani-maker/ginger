from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime
import os

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    instruction = Column(Text, nullable=False)
    status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_steps = Column(Integer, default=0)
    successful_steps = Column(Integer, default=0)
    failed_steps = Column(Integer, default=0)
    healed_steps = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    generated_script_path = Column(String(500), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'instruction': self.instruction,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_steps': self.total_steps,
            'successful_steps': self.successful_steps,
            'failed_steps': self.failed_steps,
            'healed_steps': self.healed_steps,
            'error_message': self.error_message,
            'generated_script_path': self.generated_script_path
        }

class ActionLog(Base):
    __tablename__ = 'action_logs'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, nullable=False)
    step_number = Column(Integer, nullable=False)
    action_type = Column(String(100), nullable=False)
    url = Column(String(2000), nullable=True)
    locator = Column(JSON, nullable=True)
    original_locator = Column(JSON, nullable=True)
    status = Column(String(50), default='pending')
    error_message = Column(Text, nullable=True)
    healing_attempted = Column(Boolean, default=False)
    healing_source = Column(String(50), nullable=True)
    healed_locator = Column(JSON, nullable=True)
    execution_time = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    retry_count = Column(Integer, default=0)
    page_context = Column(JSON, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'step_number': self.step_number,
            'action_type': self.action_type,
            'url': self.url,
            'locator': self.locator,
            'original_locator': self.original_locator,
            'status': self.status,
            'error_message': self.error_message,
            'healing_attempted': self.healing_attempted,
            'healing_source': self.healing_source,
            'healed_locator': self.healed_locator,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'retry_count': self.retry_count,
            'page_context': self.page_context
        }

class HealingEvent(Base):
    __tablename__ = 'healing_events'
    
    id = Column(Integer, primary_key=True)
    action_log_id = Column(Integer, nullable=False)
    task_id = Column(Integer, nullable=False)
    healing_source = Column(String(50), nullable=False)
    original_locator = Column(JSON, nullable=False)
    healed_locator = Column(JSON, nullable=False)
    success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    healing_time = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'action_log_id': self.action_log_id,
            'task_id': self.task_id,
            'healing_source': self.healing_source,
            'original_locator': self.original_locator,
            'healed_locator': self.healed_locator,
            'success': self.success,
            'error_message': self.error_message,
            'healing_time': self.healing_time,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class DatabaseManager:
    def __init__(self, db_path='data/automation.db'):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.engine = create_engine(f'sqlite:///{db_path}', 
                                   connect_args={'check_same_thread': False},
                                   pool_pre_ping=True)
        Base.metadata.create_all(self.engine)
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
    
    def get_session(self):
        return self.Session()
    
    def close_session(self):
        self.Session.remove()
