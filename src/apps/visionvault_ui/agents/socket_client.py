import socketio
import asyncio
from .config import AGENT_ID, SERVER_URL
from .utils import detect_browsers


class SocketClient:
    def __init__(self):
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=100,
            reconnection_delay=1,
            reconnection_delay_max=10,
            request_timeout=30,
            logger=False,
            engineio_logger=False
        )
        self.setup_events()
        self.event_loop = None

    def setup_events(self):
        """Setup all Socket.IO event handlers"""

        @self.sio.event
        def connect():
            print(f"✅ Connected to server: {SERVER_URL}")
            available_browsers = detect_browsers()
            self.sio.emit('agent_register', {
                'agent_id': AGENT_ID,
                'browsers': available_browsers
            })
            print(f"📤 Sent registration with browsers: {available_browsers}")

        @self.sio.event
        def disconnect():
            print("⚠️ Disconnected from server - will auto-reconnect...")

        @self.sio.event
        def connect_error(data):
            print(f"❌ Connection error: {data}")
            print("   Retrying connection...")

        @self.sio.event
        def reconnect():
            print("🔄 Reconnected to server - re-registering...")
            available_browsers = detect_browsers()
            self.sio.emit('agent_register', {
                'agent_id': AGENT_ID,
                'browsers': available_browsers
            })

        @self.sio.event
        def agent_registered(data):
            print(f"Agent registered successfully: {data}")

    def connect(self):
        """Connect to the server"""
        self.sio.connect(SERVER_URL,
                         transports=['websocket', 'polling'],
                         wait_timeout=10)

    def disconnect(self):
        """Disconnect from server"""
        if self.sio.connected:
            self.sio.disconnect()

    def emit(self, event, data):
        """Emit an event to server"""
        self.sio.emit(event, data)

    def on(self, event, handler):
        """Register event handler"""
        self.sio.on(event, handler)

    @property
    def connected(self):
        return self.sio.connected