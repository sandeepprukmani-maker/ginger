"""
Flask Application Factory
"""
from flask import Flask
from app.services.engine_orchestrator import EngineOrchestrator
from app.routes.api import create_api_routes
import os


def create_app():
    """
    Create and configure the Flask application
    
    Returns:
        Configured Flask app instance
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)
    
    orchestrator = EngineOrchestrator()
    
    api_routes = create_api_routes(orchestrator)
    app.register_blueprint(api_routes)
    
    return app
