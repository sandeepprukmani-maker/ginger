"""
Main entry point for Gunicorn WSGI server
"""
from src.web import create_app

app = create_app()
