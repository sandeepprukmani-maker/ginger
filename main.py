from application import app, socketio, logger

if __name__ == '__main__':
    logger.info("Starting Self-Healing Browser Automation System")
    socketio.run(app,port=5000, debug=True, allow_unsafe_werkzeug=True)
