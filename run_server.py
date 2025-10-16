#!/usr/bin/env python3
"""Entry point for running the VisionVault server."""

from visionvault.web.app import app, socketio

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)