import asyncio
from .utils import encode_screenshot


class TestExecutor:
    def __init__(self, socket_client):
        self.socket_client = socket_client

    async def execute_test(self, test_id, code, browser_name, mode):
        """Execute a test case"""
        headless = mode == 'headless'

        try:
            self.socket_client.emit('agent_log', {
                'test_id': test_id,
                'message': f'Preparing to execute test in {mode} mode...'
            })

            local_vars = {}
            exec(code, {}, local_vars)

            if 'run_test' not in local_vars:
                self.socket_client.emit('agent_result', {
                    'test_id': test_id,
                    'success': False,
                    'logs': ['Error: run_test missing'],
                    'screenshot': None
                })
                return

            run_test = local_vars['run_test']
            result = await run_test(browser_name=browser_name, headless=headless)

            screenshot_b64 = encode_screenshot(result.get('screenshot'))

            self.socket_client.emit('agent_result', {
                'test_id': test_id,
                'success': result.get('success', False),
                'logs': result.get('logs', []),
                'screenshot': screenshot_b64
            })

            print(f"Test {test_id} completed: {'SUCCESS' if result.get('success') else 'FAILED'}")

        except Exception as e:
            print(f"Execution error: {e}")
            self.socket_client.emit('agent_result', {
                'test_id': test_id,
                'success': False,
                'logs': [str(e)],
                'screenshot': None
            })