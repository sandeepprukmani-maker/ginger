#!/usr/bin/env python3
"""Entry point for running the VisionVault server."""

from visionvault.web.app import app, socketio
from visionvault.core.config import config

if __name__ == '__main__':
    # Use centralized configuration
    host = config.host
    port = config.port
    debug = config.debug
    
    print(f"🚀 Starting VisionVault server on {host}:{port}")
    print(f"   Debug mode: {'enabled' if debug else 'disabled'}")
    
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)