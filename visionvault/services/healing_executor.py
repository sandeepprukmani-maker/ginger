import asyncio
import json
import re
from visionvault.services.code_validator import CodeValidator
from openai import OpenAI
import os

class HealingExecutor:
    def __init__(self, socketio, api_key=None):
        self.socketio = socketio
        # Use provided API key or fallback to environment variable
        openai_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.client = OpenAI(api_key=openai_key) if openai_key else None
        self.healed_script = None
        self.failed_locators = []
        self.retry_count = 0
        self.max_retries = 3
        self.user_selector_event = None
        self.user_selected_selector = None
        self.execution_mode = 'server'  # 'server' or 'agent'
        self.agent_result = None
        self.agent_result_event = None
        self.agent_sid = None  # Agent session ID for targeted emits
        
    def regenerate_code_with_ai(self, original_code, error_message, failed_step=0, attempt_num=1):
        """Use AI to regenerate improved code based on execution failure."""
        if not self.client:
            print("⚠️ OpenAI client not available, cannot regenerate code")
            return original_code
            
        try:
            print(f"\n🤖 AI CODE REGENERATION (Attempt {attempt_num}/3)")
            print(f"   Failed at step: {failed_step}")
            print(f"   Error: {error_message[:200]}...")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """You are an expert at debugging and fixing Playwright automation code.

When code fails, you MUST:
1. Analyze the error message to understand what went wrong
2. Identify the problematic step and locator
3. Generate improved code with better locators, waits, or error handling
4. Maintain the same overall structure and step numbering
5. Add explicit timeouts (5000ms default) to all locator operations
6. Use more robust locator strategies (text content, role-based, data-testid)
7. Add appropriate waits before interactions if timing issues detected

CRITICAL: Return ONLY the complete improved function code, no explanations."""},
                    {"role": "user", "content": f"""This Playwright code failed during execution:

```python
{original_code}
```

Error occurred at STEP {failed_step}:
{error_message}

Generate the COMPLETE improved code with fixes. Focus on:
1. Better locator for the failed step (more specific, robust, or alternative strategy)
2. Appropriate waits and timeouts
3. Maintaining all other steps unchanged
4. Keeping the same return structure

Return only the improved Python code:"""}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            improved_code = response.choices[0].message.content.strip()
            
            # Clean up code formatting
            if improved_code.startswith('```python'):
                improved_code = improved_code[9:]
            elif improved_code.startswith('```'):
                improved_code = improved_code[3:]
            if improved_code.endswith('```'):
                improved_code = improved_code[:-3]
            
            improved_code = improved_code.strip()
            
            if improved_code and 'async def run_test' in improved_code:
                print(f"✅ AI generated improved code ({len(improved_code)} chars)")
                return improved_code
            else:
                print(f"⚠️ AI response invalid, using original code")
                return original_code
                
        except Exception as e:
            print(f"❌ AI code regeneration error: {e}")
            return original_code
    
    def improve_locator_with_ai(self, failed_locator, error_message, page_html_snippet=''):
        """Use AI to suggest better locator strategies."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """You are an expert at web automation and CSS/XPath selectors.
When a locator fails, suggest better, more robust alternatives. Consider:
1. Using text content locators when possible
2. Using data-testid or aria-labels
3. Using role-based selectors
4. Creating more specific CSS selectors
5. Using XPath as last resort

Return ONLY the improved locator string, nothing else."""},
                    {"role": "user", "content": f"""Failed locator: {failed_locator}
Error: {error_message}
Page context: {page_html_snippet[:500] if page_html_snippet else 'Not available'}

Suggest a better locator:"""}
                ],
                temperature=0.3
            )
            
            improved = response.choices[0].message.content.strip()
            if improved.startswith('```'):
                improved = improved.split('\n')[1]
            if improved.endswith('```'):
                improved = improved.rsplit('\n', 1)[0]
                
            return improved.strip('"\'')
        except Exception as e:
            print(f"AI locator improvement error: {e}")
            return failed_locator
    
    def heal_script(self, original_code, failed_locator, healed_locator):
        """Replace failed locator with healed one in the script."""
        print(f"\n🔧 HEALING SCRIPT:")
        print(f"  Failed locator: '{failed_locator}'")
        print(f"  Healed locator: '{healed_locator}'")
        print(f"  Searching for '{failed_locator}' in code...")
        print(f"  Found: {failed_locator in original_code}")
        
        healed = original_code.replace(failed_locator, healed_locator)
        self.healed_script = healed
        
        print(f"  Replacement successful: {healed != original_code}")
        if healed != original_code:
            print(f"  Code changed from {len(original_code)} to {len(healed)} chars")
        else:
            print(f"  ⚠️  WARNING: Code unchanged after replacement!")
        
        return healed
    
    async def wait_for_user_selector(self, timeout=300):
        """Wait for user to select an element interactively."""
        self.user_selector_event = asyncio.Event()
        self.user_selected_selector = None
        
        try:
            await asyncio.wait_for(self.user_selector_event.wait(), timeout=timeout)
            return self.user_selected_selector
        except asyncio.TimeoutError:
            return None
    
    def set_user_selector(self, selector):
        """Called when user selects an element."""
        self.user_selected_selector = selector
        if self.user_selector_event:
            self.user_selector_event.set()
    
    def set_agent_result(self, result):
        """Called when agent returns result."""
        self.agent_result = result
        if self.agent_result_event:
            self.agent_result_event.set()

    async def _execute_on_agent(self, code, browser_name, headless, test_id, attempt_num, logs):
        """Execute code on agent and wait for result."""
        import base64

        # Setup event to wait for agent result
        self.agent_result_event = asyncio.Event()
        self.agent_result = None

        # For headful mode, use modified code that keeps browser open
        execution_code = code
        if not headless:
            # Add a small delay to ensure browser is ready for widget injection
            execution_code = code.replace(
                "async def run_test(browser_name='chromium', headless=True):",
                "async def run_test(browser_name='chromium', headless=True):\n    import asyncio\n    await asyncio.sleep(1)  # Ensure browser is ready"
            )

        # Emit execution request to agent (targeted to specific agent)
        mode = 'headless' if headless else 'headful'
        if self.agent_sid:
            self.socketio.emit('execute_healing_attempt', {
                'test_id': test_id,
                'code': execution_code,
                'browser': browser_name,
                'mode': mode,
                'attempt': attempt_num + 1
            }, to=self.agent_sid)
        else:
            # Fallback to broadcast if no specific agent
            self.socketio.emit('execute_healing_attempt', {
                'test_id': test_id,
                'code': execution_code,
                'browser': browser_name,
                'mode': mode,
                'attempt': attempt_num + 1
            })

        # Wait for agent result with extended timeout for headful mode
        timeout = 180 if not headless else 120  # 3 minutes for headful, 2 for headless
        try:
            await asyncio.wait_for(self.agent_result_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            return {
                'success': False,
                'logs': logs + ['❌ Agent execution timeout'],
                'screenshot': None,
                'can_heal': False
            }

        result = self.agent_result
        if not result:
            return {
                'success': False,
                'logs': logs + ['❌ No result from agent'],
                'screenshot': None,
                'can_heal': False
            }
        
        # Decode screenshot if present
        screenshot = None
        if result.get('screenshot'):
            try:
                screenshot = base64.b64decode(result['screenshot'])
            except:
                pass
        
        logs.extend(result.get('logs', []))
        
        if result.get('success'):
            logs.append("✅ Execution completed successfully")
            return {
                'success': True,
                'logs': logs,
                'screenshot': screenshot
            }
        else:
            # Extract failed locator and step from error
            error_msg = ' '.join(result.get('logs', []))
            failed_locator = self.extract_failed_locator(error_msg)
            failed_step = self.extract_failed_step(error_msg)
            
            if failed_locator:
                self.failed_locators.append({
                    'locator': failed_locator,
                    'error': error_msg,
                    'attempt': attempt_num + 1,
                    'step': failed_step
                })
                
                return {
                    'success': False,
                    'logs': logs,
                    'screenshot': screenshot,
                    'can_heal': True,
                    'failed_locator': failed_locator,
                    'failed_step': failed_step,
                    'error_message': error_msg,
                    'page_content': ''
                }
            else:
                return {
                    'success': False,
                    'logs': logs,
                    'screenshot': screenshot,
                    'can_heal': False
                }
    
    async def execute_with_healing(self, code, browser_name, headless, test_id):
        """Execute code with advanced AI-guided healing and retry on failures.
        
        Each failed step gets up to 3 AI-guided retry attempts before user intervention.
        """
        validator = CodeValidator()
        if not validator.validate(code):
            return {
                'success': False,
                'logs': ['Security validation failed: ' + '; '.join(validator.get_errors())],
                'screenshot': None,
                'healed_script': None
            }
        
        self.healed_script = code
        current_code = code
        
        for attempt in range(self.max_retries):
            result = await self._execute_single_attempt(current_code, browser_name, headless, test_id, attempt)
            
            if result['success']:
                final_result = {
                    'success': True,
                    'logs': result['logs'],
                    'screenshot': result['screenshot'],
                    'healed_script': self.healed_script if self.healed_script != code else None,
                    'failed_locators': self.failed_locators
                }
                
                if self.failed_locators:
                    await self.report_failures_to_ai(test_id)
                    final_result['logs'].append("📊 AI analysis complete - check insights for improvement recommendations")
                
                return final_result
            
            if not result.get('can_heal'):
                return result
            
            error_message = result.get('error_message', '')
            failed_step = result.get('failed_step', 0)  # Get from result, fallback to 0
            failed_locator = result.get('failed_locator')
            
            import sys
            print(f"\n🔍 HEALING ATTEMPT {attempt + 1}/{self.max_retries}:", flush=True)
            print(f"   Failed step: {failed_step}", flush=True)
            print(f"   Failed locator: {failed_locator}", flush=True)
            print(f"   Mode: {'headful' if not headless else 'headless'}", flush=True)
            sys.stdout.flush()
            
            # AI-guided retry strategy (attempts 1-2)
            if attempt < 2:  # First 2 attempts: Use AI code regeneration
                result['logs'].append(f"🤖 AI Retry {attempt + 1}/3: Analyzing error and regenerating improved code...")
                
                # Use AI to regenerate the entire code with improvements
                regenerated_code = self.regenerate_code_with_ai(
                    current_code, 
                    error_message, 
                    failed_step, 
                    attempt + 1
                )
                
                if regenerated_code != current_code:
                    current_code = regenerated_code
                    self.healed_script = regenerated_code
                    result['logs'].append(f"✅ AI generated improved code, retrying...")
                    
                    self.socketio.emit('script_healed', {
                        'test_id': test_id,
                        'healed_script': current_code,
                        'failed_locator': failed_locator or '',
                        'healed_locator': 'AI-improved code',
                        'attempt': attempt + 1,
                        'method': 'ai_regeneration'
                    })
                else:
                    # Fallback to locator improvement if regeneration failed
                    result['logs'].append(f"⚠️ AI regeneration unchanged, trying locator improvement...")
                    if failed_locator:
                        improved_locator = self.improve_locator_with_ai(
                            failed_locator, 
                            error_message,
                            result.get('page_content', '')
                        )
                        current_code = self.heal_script(current_code, failed_locator, improved_locator)
                        result['logs'].append(f"🔧 Improved locator: {improved_locator}")
                
            # Final attempt (3rd): Show user widget in headful mode
            elif attempt == 2:  # 3rd attempt: User intervention
                if failed_locator:
                    improved_locator = None
                    
                    if not headless:
                        # User widget intervention
                        mode = 'headful' if not headless else 'headless'
                        print(f"🔔 SERVER: Emitting element_selector_needed (final attempt) for test {test_id}", flush=True)
                        sys.stdout.flush()
                        
                        result['logs'].append(f"👆 Final attempt: Requesting user help to locate element...")
                        
                        if self.agent_sid:
                            self.socketio.emit('element_selector_needed', {
                                'test_id': test_id,
                                'failed_locator': failed_locator,
                                'error': error_message,
                                'attempt': attempt + 1,
                                'mode': mode
                            }, to=self.agent_sid)
                        else:
                            self.socketio.emit('element_selector_needed', {
                                'test_id': test_id,
                                'failed_locator': failed_locator,
                                'error': error_message,
                                'attempt': attempt + 1,
                                'mode': mode
                            })
                        
                        user_selector = await self.wait_for_user_selector(timeout=300)
                        
                        if user_selector:
                            improved_locator = user_selector
                            print(f"\n✅ USER SELECTED: '{improved_locator}'", flush=True)
                            result['logs'].append(f"✅ User selected element: {improved_locator}")
                        else:
                            result['logs'].append(f"⏱️ User selection timeout, final AI attempt...")
                            improved_locator = self.improve_locator_with_ai(
                                failed_locator, 
                                error_message,
                                result.get('page_content', '')
                            )
                            result['logs'].append(f"🤖 Final AI suggestion: {improved_locator}")
                    else:
                        # Headless mode: Final AI attempt
                        result['logs'].append(f"🤖 Final AI retry in headless mode...")
                        improved_locator = self.improve_locator_with_ai(
                            failed_locator, 
                            error_message,
                            result.get('page_content', '')
                        )
                        result['logs'].append(f"🔧 Final locator attempt: {improved_locator}")
                    
                    if improved_locator:
                        current_code = self.heal_script(current_code, failed_locator, improved_locator)
                        
                        self.socketio.emit('script_healed', {
                            'test_id': test_id,
                            'healed_script': current_code,
                            'failed_locator': failed_locator,
                            'healed_locator': improved_locator,
                            'attempt': attempt + 1,
                            'method': 'user_selection' if not headless else 'final_ai'
                        })
                
                await asyncio.sleep(0.5)
        
        print(f"\n❌ HEALING FAILED after {self.max_retries} attempts")
        print(f"  self.healed_script is None: {self.healed_script is None}")
        print(f"  self.healed_script length: {len(self.healed_script) if self.healed_script else 0}", flush=True)
        
        final_result = {
            'success': False,
            'logs': result.get('logs', []) + [f'❌ Failed after {self.max_retries} healing attempts'],
            'screenshot': result.get('screenshot'),
            'healed_script': self.healed_script,
            'failed_locators': self.failed_locators
        }
        
        if self.failed_locators:
            await self.report_failures_to_ai(test_id)
        
        return final_result
    
    async def _execute_single_attempt(self, code, browser_name, headless, test_id, attempt_num):
        """Execute a single attempt of the automation code."""
        logs = [f"▶️  Attempt {attempt_num + 1}: Executing automation..."]
        screenshot = None
        page_content = ''
        
        # If agent execution mode, delegate to agent
        if self.execution_mode == 'agent':
            return await self._execute_on_agent(code, browser_name, headless, test_id, attempt_num, logs)
        
        try:
            from playwright.async_api import TimeoutError as PlaywrightTimeout
            
            restricted_globals = {
                '__builtins__': {
                    'True': True, 'False': False, 'None': None,
                    'dict': dict, 'list': list, 'str': str, 'int': int,
                    'float': float, 'bool': bool, 'len': len,
                    'Exception': Exception, '__import__': __import__,
                }
            }
            
            local_vars = {}
            
            try:
                exec(code, restricted_globals, local_vars)
                
                if 'run_test' not in local_vars:
                    logs.append("❌ Error: Generated code must contain a run_test function")
                    return {
                        'success': False,
                        'logs': logs,
                        'screenshot': None,
                        'can_heal': False
                    }
                
                result = await local_vars['run_test'](browser_name=browser_name, headless=headless)
                logs.extend(result.get('logs', []))
                screenshot = result.get('screenshot')
                
                if result.get('success'):
                    logs.append("✅ Execution completed successfully")
                    return {
                        'success': True,
                        'logs': logs,
                        'screenshot': screenshot
                    }
                else:
                    error_msg = ' '.join(result.get('logs', []))
                    failed_locator = self.extract_failed_locator(error_msg)
                    failed_step = self.extract_failed_step(error_msg)
                    
                    if failed_locator:
                        self.failed_locators.append({
                            'locator': failed_locator,
                            'error': error_msg,
                            'attempt': attempt_num + 1,
                            'step': failed_step
                        })
                        
                        return {
                            'success': False,
                            'logs': logs,
                            'screenshot': screenshot,
                            'can_heal': True,
                            'failed_locator': failed_locator,
                            'failed_step': failed_step,
                            'error_message': error_msg,
                            'page_content': page_content
                        }
                    else:
                        return {
                            'success': False,
                            'logs': logs,
                            'screenshot': screenshot,
                            'can_heal': False
                        }
                        
            except PlaywrightTimeout as e:
                error_msg = str(e)
                logs.append(f"⏱️  Timeout error: {error_msg}")
                
                failed_locator = self.extract_failed_locator(error_msg)
                failed_step = self.extract_failed_step(error_msg)
                
                if failed_locator:
                    self.failed_locators.append({
                        'locator': failed_locator,
                        'error': error_msg,
                        'attempt': attempt_num + 1,
                        'step': failed_step
                    })
                    
                    return {
                        'success': False,
                        'logs': logs,
                        'screenshot': screenshot,
                        'can_heal': True,
                        'failed_locator': failed_locator,
                        'failed_step': failed_step,
                        'error_message': error_msg,
                        'page_content': page_content
                    }
                else:
                    return {
                        'success': False,
                        'logs': logs,
                        'screenshot': screenshot,
                        'can_heal': False
                    }
            
            except Exception as e:
                error_msg = str(e)
                logs.append(f"❌ Execution error: {error_msg}")
                
                failed_locator = self.extract_failed_locator(error_msg)
                failed_step = self.extract_failed_step(error_msg)
                
                if failed_locator:
                    self.failed_locators.append({
                        'locator': failed_locator,
                        'error': error_msg,
                        'attempt': attempt_num + 1,
                        'step': failed_step
                    })
                    
                    return {
                        'success': False,
                        'logs': logs,
                        'screenshot': screenshot,
                        'can_heal': True,
                        'failed_locator': failed_locator,
                        'failed_step': failed_step,
                        'error_message': error_msg,
                        'page_content': page_content
                    }
                else:
                    return {
                        'success': False,
                        'logs': logs,
                        'screenshot': screenshot,
                        'can_heal': False
                    }
            
        except Exception as e:
            logs.append(f'💥 Fatal error: {str(e)}')
            return {
                'success': False,
                'logs': logs,
                'screenshot': screenshot,
                'can_heal': False
            }
    
    def extract_failed_step(self, error_message):
        """Extract the failed step number from error message."""
        # Look for patterns like "Error at STEP 3:" or "STEP 2:" in the error
        patterns = [
            r'Error at STEP\s+(\d+)',
            r'STEP\s+(\d+):',
            r'step\s+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return 0  # Default to 0 if no step found
    
    def extract_failed_locator(self, error_message):
        """Extract the failed locator from error message."""
        patterns = [
            r'locator\("([^"]+)"\)',
            r'selector "([^"]+)"',
            r'element "([^"]+)"',
            r'get_by_text\("([^"]+)"\)',
            r'get_by_role\("([^"]+)"\)',
            r"locator\('([^']+)'\)",
            r"selector '([^']+)'",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    async def report_failures_to_ai(self, test_id):
        """Report all failures and healing attempts to AI for continuous improvement."""
        if not self.failed_locators or not self.client:
            return
        
        try:
            failure_report = {
                'test_id': test_id,
                'total_failures': len(self.failed_locators),
                'failures': self.failed_locators,
                'healed_script': self.healed_script
            }
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """You are an automation quality analyst. 
Analyze the failures and healing attempts to provide insights for improving automation scripts.
Identify patterns, suggest best practices, and recommend preventive measures."""},
                    {"role": "user", "content": f"""Analyze these automation failures and healing attempts:

Test ID: {test_id}
Total Failures: {len(self.failed_locators)}

Failures:
{json.dumps(self.failed_locators, indent=2)}

Final Healed Script:
{self.healed_script[:500] if self.healed_script else 'None'}

Provide:
1. Key insights about failure patterns
2. Recommendations for better locator strategies
3. Preventive measures for future scripts"""}
                ],
                temperature=0.3
            )
            
            insights = response.choices[0].message.content.strip()
            
            self.socketio.emit('ai_insights', {
                'test_id': test_id,
                'insights': insights,
                'failure_count': len(self.failed_locators)
            })
            
            return insights
        except Exception as e:
            print(f"AI feedback error: {e}")
            return None
