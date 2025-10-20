"""
Main entry point for the AI Browser Automation web application
"""
from app.app import app

if __name__ == '__main__':
    # Run Flask on port 5000, bound to all interfaces for Replit
    app.run(host='0.0.0.0', port=5000, debug=False)
