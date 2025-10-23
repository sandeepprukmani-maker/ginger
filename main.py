from application import app, socketio, logger

if __name__ == '__main__':
    logger.info("Starting Self-Healing Browser Automation System")
    logger.info(f"Dashboard available at: http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
