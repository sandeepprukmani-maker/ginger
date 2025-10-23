"""
Flask Application Factory
"""
import os
import logging
import sys
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from app.services.engine_orchestrator import EngineOrchestrator
from app.routes.api import create_api_routes

# Load .env file and override any existing environment variables
load_dotenv(override=True)


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
    
    allowed_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '*').split(',')
    CORS(app, 
         resources={r"/api/*": {"origins": allowed_origins}},
         methods=["GET", "POST", "OPTIONS"],
         allow_headers=["Content-Type", "X-API-Key"],
         supports_credentials=True)
    
    logger.info(f"🔒 CORS configured with origins: {allowed_origins}")
    logger.info("📦 Initializing Engine Orchestrator")
    orchestrator = EngineOrchestrator()
    
    logger.info("🔗 Registering API routes")
    api_routes = create_api_routes(orchestrator)
    app.register_blueprint(api_routes)
    
    # Add cache control headers to prevent browser caching issues
    @app.after_request
    def add_cache_control_headers(response):
        """Add Cache-Control headers to all responses to prevent caching"""
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, public, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    logger.info("✅ Application initialization complete")
    
    return app
