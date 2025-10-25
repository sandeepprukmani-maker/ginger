"""
Flask Application Factory
"""
import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from app.models import db
from app.services.engine_orchestrator import EngineOrchestrator
from app.routes.api import create_api_routes

# Load .env file from project root with explicit path
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)


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
    
    # Session secret key - MUST be set in production
    session_secret = os.environ.get("SESSION_SECRET")
    if not session_secret:
        # Generate ephemeral random key for local development only
        import secrets
        session_secret = secrets.token_hex(32)
        logger.warning("⚠️  SESSION_SECRET not set! Using ephemeral random key for local dev.")
        logger.warning("⚠️  Set SESSION_SECRET environment variable for production!")
    
    app.config['SECRET_KEY'] = session_secret
    
    # Support both Replit (DATABASE_URL) and local development (SQLite fallback)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        # Use SQLite for local development
        database_url = "sqlite:///automation_history.db"
        logger.info("📝 Using SQLite database for local development")
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        logger.info("✅ Database initialized successfully")
    
    allowed_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '*').split(',')
    CORS(app, 
         resources={r"/api/*": {"origins": allowed_origins}},
         methods=["GET", "POST", "OPTIONS", "DELETE"],
         allow_headers=["Content-Type", "X-API-Key"],
         supports_credentials=True)
    
    logger.info(f"🔒 CORS configured with origins: {allowed_origins}")
    logger.info("📦 Initializing Engine Orchestrator")
    orchestrator = EngineOrchestrator()
    
    gemini_api_key = os.environ.get('GEMINI_API_KEY')
    if gemini_api_key:
        try:
            from app.services.semantic_search import SemanticSearchService
            app.semantic_search = SemanticSearchService(api_key=gemini_api_key)
            logger.info("✅ Semantic search service initialized with Gemini embeddings")
        except Exception as e:
            app.semantic_search = None
            logger.warning(f"⚠️  Failed to initialize semantic search: {e}")
    else:
        app.semantic_search = None
        logger.info("ℹ️  GEMINI_API_KEY not set. Task Library semantic search will be unavailable.")
    
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
    
    # Handle favicon request to prevent 404 errors
    @app.route('/favicon.ico')
    def favicon():
        """Return 204 No Content for favicon requests"""
        from flask import Response
        return Response(status=204)
    
    logger.info("✅ Application initialization complete")
    
    return app
