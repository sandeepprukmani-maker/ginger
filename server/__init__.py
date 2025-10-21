"""
AI Browser Automation Server
Flask application for browser automation using OpenAI + Playwright MCP
"""
from flask import Flask
import os


def create_app():
    """Application factory for Flask app"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)
    
    # Register routes
    from server.routes import register_routes
    register_routes(app)
    
    return app
