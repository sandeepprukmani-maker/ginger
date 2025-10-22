"""
Main entry point for the AI Browser Automation web application
"""
from server import create_app

if __name__ == '__main__':
    app = create_app()
    # Run Flask on port 5000, bound to all interfaces for Replit
    app.run(host='0.0.0.0', port=5000, debug=False)
