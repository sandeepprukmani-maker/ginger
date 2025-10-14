import asyncio
import os
import subprocess
from .config import AGENT_ID, SERVER_URL

class CodegenRecordingSessionManager:
    def __init__(self, socket_client):
        self.socket_client = socket_client
        self.sessions = {}  # session_id -> subprocess info

    async def start_recording_session(self, session_id: str, start_url: str = ""):
        """Start a Playwright codegen session in a subprocess."""
        if session_id in self.sessions:
            print(f"Session {session_id} is already running")
            return

        os.makedirs("recordings", exist_ok=True)
        output_file = os.path.join("recordings", f"{session_id}.py")

        cmd = [
            "playwright",
            "codegen",
            "--target=python",
            "--output", output_file
        ]
        if start_url:
            cmd.append(start_url)

        print(f"🎬 Starting codegen session {session_id}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.sessions[session_id] = {
            "process": process,
            "output_file": output_file,
            "start_url": start_url
        }

        self.socket_client.emit("recording_status", {
            "session_id": session_id,
            "status": "started",
            "output_file": output_file
        })
        
        asyncio.create_task(self._monitor_process(session_id))

    async def _monitor_process(self, session_id: str):
        """Monitor the recording process and auto-stop when browser closes."""
        session = self.sessions.get(session_id)
        if not session:
            return
        
        process = session["process"]
        
        await asyncio.get_event_loop().run_in_executor(None, process.wait)
        
        print(f"🔔 Browser closed for session {session_id}. Auto-stopping recording...")
        await self.stop_recording_session(session_id, auto_stopped=True)

    async def stop_recording_session(self, session_id: str, auto_stopped: bool = False):
        """Stop the codegen subprocess and read the generated file."""
        session = self.sessions.get(session_id)
        if not session:
            print(f"Session {session_id} not found")
            return

        process = session["process"]
        output_file = session["output_file"]
        
        if process.poll() is None:
            process.terminate()
            try:
                await asyncio.get_event_loop().run_in_executor(None, lambda: process.wait(timeout=5))
            except subprocess.TimeoutExpired:
                process.kill()
        
        await asyncio.sleep(0.5)
        
        playwright_code = None
        actions = []
        
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r') as f:
                    playwright_code = f.read()
                
                actions = self._extract_actions_from_code(playwright_code)
                print(f"✅ Extracted {len(actions)} actions from recording")
            except Exception as e:
                print(f"⚠️ Error reading recording file: {e}")
        
        self.socket_client.emit("recording_status", {
            "session_id": session_id,
            "status": "stopped",
            "output_file": output_file,
            "playwright_code": playwright_code,
            "actions": actions,
            "auto_stopped": auto_stopped
        })

        print(f"✅ Recording session {session_id} {'auto-' if auto_stopped else ''}stopped. Output: {output_file}")
        del self.sessions[session_id]
    
    def _extract_actions_from_code(self, code: str) -> list:
        """Extract human-readable actions with locators from generated Playwright code."""
        actions = []
        lines = code.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if 'page.goto(' in line:
                import re
                match = re.search(r'page\.goto\(["\']([^"\']+)["\']', line)
                if match:
                    actions.append({
                        'action': 'Navigate',
                        'locator': match.group(1),
                        'description': f'Navigate to {match.group(1)}'
                    })
            
            elif 'page.click(' in line:
                import re
                match = re.search(r'page\.click\(["\']([^"\']+)["\']', line)
                if match:
                    actions.append({
                        'action': 'Click',
                        'locator': match.group(1),
                        'description': f'Click element: {match.group(1)}'
                    })
            
            elif 'page.fill(' in line:
                import re
                match = re.search(r'page\.fill\(["\']([^"\']+)["\'],\s*["\']([^"\']*)["\']', line)
                if match:
                    actions.append({
                        'action': 'Type',
                        'locator': match.group(1),
                        'value': match.group(2),
                        'description': f'Type "{match.group(2)}" into {match.group(1)}'
                    })
            
            elif 'page.select_option(' in line:
                import re
                match = re.search(r'page\.select_option\(["\']([^"\']+)["\'],\s*["\']([^"\']*)["\']', line)
                if match:
                    actions.append({
                        'action': 'Select',
                        'locator': match.group(1),
                        'value': match.group(2),
                        'description': f'Select option "{match.group(2)}" in {match.group(1)}'
                    })
            
            elif 'page.check(' in line:
                import re
                match = re.search(r'page\.check\(["\']([^"\']+)["\']', line)
                if match:
                    actions.append({
                        'action': 'Check',
                        'locator': match.group(1),
                        'description': f'Check checkbox: {match.group(1)}'
                    })
            
            elif 'page.press(' in line or 'page.keyboard.press(' in line:
                import re
                match = re.search(r'press\(["\']([^"\']+)["\']', line)
                if match:
                    actions.append({
                        'action': 'Press Key',
                        'locator': match.group(1),
                        'description': f'Press key: {match.group(1)}'
                    })
        
        return actions
