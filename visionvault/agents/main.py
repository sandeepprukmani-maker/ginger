import asyncio
import time
from .config import AGENT_ID, SERVER_URL
from .socket_client import SocketClient
from .test_executor import TestExecutor
from .healing_engine import HealingEngine
from .recording_session import CodegenRecordingSessionManager
import os

class VisionVaultAgent:
    def __init__(self):
        self.socket_client = SocketClient()
        self.test_executor = TestExecutor(self.socket_client)
        self.healing_engine = HealingEngine(self.socket_client)
        self.recording_manager = CodegenRecordingSessionManager(self.socket_client)

        # Set up event handlers
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Setup all Socket.IO event handlers"""

        @self.socket_client.sio.on('execute_on_agent')
        def handle_execute(data):
            if self.socket_client.event_loop:
                asyncio.run_coroutine_threadsafe(
                    self.test_executor.execute_test(
                        data['test_id'],
                        data['code'],
                        data['browser'],
                        data['mode']
                    ),
                    self.socket_client.event_loop
                )

        @self.socket_client.sio.on('start_recording')
        def handle_start_recording(data):
            if self.socket_client.event_loop:
                session_id = data['session_id']
                start_url = data.get('start_url', '')
                asyncio.run_coroutine_threadsafe(
                    self.recording_manager.start_recording_session(
                        session_id=session_id,
                        start_url=start_url  # No output_file here
                    ),
                    self.socket_client.event_loop
                )

        @self.socket_client.sio.on('execute_healing_attempt')
        def handle_healing_attempt(data):
            if self.socket_client.event_loop:
                asyncio.run_coroutine_threadsafe(
                    self.healing_engine.execute_healing_attempt(
                        data['test_id'],
                        data['code'],
                        data['browser'],
                        data['mode'],
                        data.get('attempt', 1)
                    ),
                    self.socket_client.event_loop
                )
        
        @self.socket_client.sio.on('healing_complete')
        def handle_healing_complete(data):
            """Handle healing completion - close browser and cleanup"""
            test_id = data.get('test_id')
            success = data.get('success', False)
            reason = data.get('reason', 'unknown')
            print(f"\n🏁 HEALING COMPLETE for test {test_id}")
            print(f"   Success: {success}")
            print(f"   Reason: {reason}")
            if self.socket_client.event_loop:
                asyncio.run_coroutine_threadsafe(
                    self.healing_engine.cleanup_browser(),
                    self.socket_client.event_loop
                )

        @self.socket_client.sio.on('element_selector_needed')
        def handle_element_selector_needed(data):
            mode = data.get('mode', 'headless')
            if mode == 'headful' and self.healing_engine.active_page and self.socket_client.event_loop:
                asyncio.run_coroutine_threadsafe(
                    self.healing_engine.inject_element_selector(
                        data['test_id'],
                        data['failed_locator']
                    ),
                    self.socket_client.event_loop
                )
            else:
                print(f"❌ Cannot inject widget (mode={mode}, page={'yes' if self.healing_engine.active_page else 'no'})")

        @self.socket_client.sio.on('stop_recording')
        def handle_stop_recording(data):
            if self.socket_client.event_loop:
                asyncio.run_coroutine_threadsafe(
                    self.recording_manager.stop_recording_session(data['session_id']),
                    self.socket_client.event_loop
                )

    async def send_heartbeat(self):
        while True:
            try:
                if self.socket_client.connected:
                    browser_status = "available"
                    active_sessions = len(getattr(self.recording_manager, 'sessions', {}))
                    if active_sessions > 0:
                        browser_status = f"recording_{active_sessions}_sessions"

                    self.socket_client.emit('heartbeat', {
                        'agent_id': AGENT_ID,
                        'timestamp': time.time(),
                        'browser_status': browser_status,
                        'capabilities': {
                            'recording': True,
                            'comprehensive_recording': True,
                            'test_execution': True,
                            'healing': True
                        }
                    })
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Heartbeat error: {e}")
                await asyncio.sleep(30)

    async def initialize_agent(self):
        try:
            from .utils import detect_browsers
            self.socket_client.emit('agent_register', {
                'agent_id': AGENT_ID,
                'browsers': detect_browsers(),
                'capabilities': {
                    'recording': True,
                    'comprehensive_recording': True,
                    'test_execution': True,
                    'healing': True,
                    'event_types': [
                        'click', 'input', 'keypress', 'navigation',
                        'form_submit', 'network_request', 'network_response',
                        'console', 'page_error', 'page_created'
                    ]
                },
                'status': 'ready'
            })
            print("✅ Agent registered with comprehensive recording capabilities")
        except Exception as e:
            print(f"❌ Agent initialization failed: {e}")

    def run(self):
        print("=" * 60)
        print("  VisionVault Browser Automation Agent")
        print("=" * 60)
        print(f"  Agent ID: {AGENT_ID}")
        print(f"  Server URL: {SERVER_URL}")
        print()

        try:
            print("Connecting to server...")
            self.socket_client.connect()
            print("Connection established! Initializing agent...")

            self.socket_client.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.socket_client.event_loop)

            self.socket_client.event_loop.run_until_complete(self.initialize_agent())
            self.socket_client.event_loop.create_task(self.send_heartbeat())

            print("✅ Agent ready! Waiting for tasks...\n")
            self.socket_client.event_loop.run_forever()

        except KeyboardInterrupt:
            print("\n🛑 Shutting down agent...")
            try:
                for session_id in list(getattr(self.recording_manager, 'sessions', {}).keys()):
                    print(f"🛑 Stopping recording session: {session_id}")
                    asyncio.run_coroutine_threadsafe(
                        self.recording_manager.stop_recording_session(session_id),
                        self.socket_client.event_loop
                    )
            except Exception as e:
                print(f"⚠️ Error stopping recordings: {e}")

            self.socket_client.disconnect()
            if self.socket_client.event_loop:
                self.socket_client.event_loop.close()

        except Exception as e:
            print(f"❌ Connection error: {e}")
            if self.socket_client.event_loop:
                self.socket_client.event_loop.close()


def main():
    agent = VisionVaultAgent()
    agent.run()


if __name__ == '__main__':
    main()
