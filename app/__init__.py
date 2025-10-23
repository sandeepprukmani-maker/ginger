"""
Flask Application Factory
"""
from flask import Flask
from app.services.engine_orchestrator import EngineOrchestrator
from app.routes.api import create_api_routes
import os
import logging
import sys


def create_app():
    """
    Create and configure the Flask application
    
    Returns:
        Configured Flask app instance
    """
    # Configure detailed logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set browser-use and agent loggers to INFO to see detailed steps
    logging.getLogger('browser_use').setLevel(logging.INFO)
    logging.getLogger('Agent').setLevel(logging.INFO)
    logging.getLogger('service').setLevel(logging.INFO)
    logging.getLogger('tools').setLevel(logging.INFO)
    logging.getLogger('BrowserSession').setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting AI Browser Automation application")
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get("SESSION_SECRET")
    
    logger.info("📦 Initializing Engine Orchestrator")
    orchestrator = EngineOrchestrator()
    
    logger.info("🔗 Registering API routes")
    api_routes = create_api_routes(orchestrator)
    app.register_blueprint(api_routes)
    
    logger.info("✅ Application initialization complete")
    
    return app
