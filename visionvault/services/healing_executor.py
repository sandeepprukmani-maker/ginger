import asyncio
import json
import re
from visionvault.services.code_validator import CodeValidator
from openai import OpenAI
import os

# Import advanced locator validator
try:
    from visionvault.services.advanced_locator_validator import AdvancedLocatorValidator
    ADVANCED_VALIDATOR_AVAILABLE = True
except ImportError:
    ADVANCED_VALIDATOR_AVAILABLE = False
    print("⚠️  Advanced locator validator not available")

# Import multi-strategy healer
try:
    from visionvault.services.multi_strategy_healer import MultiStrategyHealer
    MULTI_STRATEGY_HEALER_AVAILABLE = True
except ImportError:
    MULTI_STRATEGY_HEALER_AVAILABLE = False
    print("⚠️  Multi-strategy healer not available")

class HealingExecutor:
    def __init__(self, socketio, api_key=None, use_gpt4o=True):
        self.socketio = socketio
        # Use provided API key or fallback to environment variable
        openai_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.client = OpenAI(api_key=openai_key) if openai_key else None
        self.healed_script = None
        self.failed_locators = []
        self.retry_count = 0
        self.max_retries = 5  # Increased from 3 to 5 attempts before user intervention
        self.user_selector_event = None
        self.user_selected_selector = None
        self.execution_mode = 'server'  # 'server' or 'agent'
        self.agent_result = None
        self.agent_result_event = None
        self.agent_sid = None  # Agent session ID for targeted emits
        
        # GPT-4o usage is DECOUPLED from validator availability
        # Always use GPT-4o for better accuracy (not conditional)
        self.use_gpt4o = use_gpt4o
        
        # Advanced validator is OPTIONAL and independent of GPT-4o
        self.use_advanced_validator = ADVANCED_VALIDATOR_AVAILABLE
        self.advanced_validator = None  # Will be initialized when page is available
        
        # Multi-strategy healer is OPTIONAL and independent of GPT-4o
        self.use_multi_strategy = MULTI_STRATEGY_HEALER_AVAILABLE
        if self.use_multi_strategy and self.client:
            self.multi_strategy_healer = MultiStrategyHealer(openai_client=self.client)
        else:
            self.multi_strategy_healer = None
        
        # AI healing request tracking (set by handle_ai_healing_request)
        self.ai_healing_requested = False
        self.error_context = None
        
        # Log configuration
        features = []
        if self.use_gpt4o:
            features.append("GPT-4o")
        if self.use_advanced_validator:
            features.append("Advanced Validator")
        if self.use_multi_strategy:
            features.append("Multi-Strategy Healing")
        
        features_str = " + ".join(features) if features else "GPT-4o-mini"
        print(f"✅ Enhanced AI healing enabled ({features_str} + 5 attempts)")
        
    def parse_code_steps(self, code):
        """Parse code to extract individual steps with their line numbers."""
        steps = []
        lines = code.split('\n')
        current_step = None
        current_step_lines = []
        
        for i, line in enumerate(lines):
            # Check for STEP comment markers
            if '# STEP' in line and ':' in line:
                # Save previous step if exists
                if current_step is not None and current_step_lines:
                    steps.append({
                        'step_num': current_step,
                        'lines': current_step_lines.copy(),
                        'start_line': current_step_lines[0][0] if current_step_lines else i,
                        'end_line': current_step_lines[-1][0] if current_step_lines else i
                    })
                
                # Extract step number
                try:
                    step_match = re.search(r'STEP\s+(\d+)', line)
                    if step_match:
                        current_step = int(step_match.group(1))
                        current_step_lines = [(i, line)]
                except:
                    pass
            elif current_step is not None:
                # Add line to current step
                current_step_lines.append((i, line))
        
        # Save last step
        if current_step is not None and current_step_lines:
            steps.append({
                'step_num': current_step,
                'lines': current_step_lines.copy(),
                'start_line': current_step_lines[0][0],
                'end_line': current_step_lines[-1][0]
            })
        
        return steps
    
    def extract_page_locators(self, page_html, max_length=3000):
        """Extract available locators from page HTML for AI analysis."""
        import re
        
        # Extract elements with useful locator attributes
        locators = []
        
        # Find elements with data-testid
        test_ids = re.findall(r'data-testid="([^"]+)"', page_html)
        for tid in test_ids[:10]:  # Limit to 10
            locators.append(f"get_by_test_id('{tid}')")
        
        # Find elements with placeholder
        placeholders = re.findall(r'placeholder="([^"]+)"', page_html)
        for ph in placeholders[:10]:
            locators.append(f"get_by_placeholder('{ph}')")
        
        # Find elements with aria-label
        aria_labels = re.findall(r'aria-label="([^"]+)"', page_html)
        for al in aria_labels[:10]:
            locators.append(f"get_by_label('{al}')")
        
        # Find buttons with text
        button_texts = re.findall(r'<button[^>]*>([^<]+)</button>', page_html)
        for bt in button_texts[:10]:
            if bt.strip():
                locators.append(f"get_by_role('button', name='{bt.strip()}')")
        
        # Find links with text
        link_texts = re.findall(r'<a[^>]*>([^<]+)</a>', page_html)
        for lt in link_texts[:10]:
            if lt.strip() and len(lt.strip()) > 2:
                locators.append(f"get_by_role('link', name='{lt.strip()}')")
        
        # Find input fields with name or id
        input_names = re.findall(r'<input[^>]*(?:name|id)="([^"]+)"[^>]*>', page_html)
        for inp in input_names[:10]:
            locators.append(f"get_by_role('textbox', name='{inp}')")
        
        return locators[:30]  # Return top 30 locators
    
    def regenerate_failed_step_only(self, original_code, error_message, failed_step=0, attempt_num=1, page_context=''):
        """Use AI to regenerate ONLY the failed step, preserving successful ones."""
        if not self.client or failed_step == 0:
            return self.regenerate_code_with_ai(original_code, error_message, failed_step, attempt_num)
        
        try:
            print(f"\n🎯 STEP-BY-STEP HEALING (Attempt {attempt_num}/3)")
            print(f"   Targeting STEP {failed_step} only")
            print(f"   Preserving all successful steps")
            
            # Parse code to find the failed step
            steps = self.parse_code_steps(original_code)
            failed_step_content = None
            
            for step in steps:
                if step['step_num'] == failed_step:
                    failed_step_content = '\n'.join([line[1] for line in step['lines']])
                    break
            
            if not failed_step_content:
                print(f"⚠️ Could not isolate step {failed_step}, falling back to full regeneration")
                return self.regenerate_code_with_ai(original_code, error_message, failed_step, attempt_num)
            
            # Extract available locators from page if context provided
            available_locators = []
            if page_context:
                available_locators = self.extract_page_locators(page_context)
                print(f"   📊 Found {len(available_locators)} available locators on page")
            
            locators_hint = ""
            if available_locators:
                locators_hint = f"""

AVAILABLE LOCATORS ON PAGE (use these if they match your target):
{chr(10).join([f"- {loc}" for loc in available_locators[:15]])}"""
            
            # ALWAYS use GPT-4o for better accuracy (decoupled from validator)
            model = "gpt-4o" if self.use_gpt4o else "gpt-4o-mini"
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": """You are an expert at fixing specific Playwright automation steps by analyzing the actual page.

Your job is to fix ONLY the failed step while preserving all other steps exactly as they are.

CRITICAL RULES:
1. Analyze the available locators from the page and choose the best match
2. Return ONLY the fixed code for the specific step mentioned
3. Use better locators (get_by_role, get_by_text, get_by_placeholder, get_by_label, etc.)
4. Add explicit timeouts (10000ms) to all operations for reliability
5. Add proper wait strategies (wait_for_load_state, wait_for_selector with visible state)
6. Maintain the step number and structure
7. Keep the same log messages format
8. Return ONLY the replacement code lines, nothing else

LOCATOR PRIORITY (prefer in this order):
1. get_by_test_id (most reliable - 99% success rate)
2. get_by_role with exact name (accessibility-first - 95% success rate)
3. get_by_placeholder with exact match (for inputs - 90% success rate)
4. get_by_label (for form fields - 85% success rate)
5. get_by_text with exact match (for unique text - 80% success rate)
6. CSS selectors with IDs (last resort - 70% success rate)

BEST PRACTICES:
- Always add .wait_for(state='visible', timeout=10000) before interacting
- Use exact=True for text/name matches when possible
- Combine multiple strategies (e.g., role + filter by text)
- Add error handling for dynamic content"""},
                    {"role": "user", "content": f"""This specific step failed during execution:

FAILED STEP {failed_step}:
```python
{failed_step_content}
```

Error: {error_message}{locators_hint}

Analyze the available locators above and generate ONLY the fixed code for STEP {failed_step}. Include:
1. The # STEP {failed_step}: comment
2. The current_step = {failed_step} line
3. The fixed Playwright operations with better locators from the page
4. The success log message

Return only the replacement code for this step:"""}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            fixed_step = response.choices[0].message.content.strip()
            
            # Clean up formatting
            if fixed_step.startswith('```'):
                lines = fixed_step.split('\n')
                fixed_step = '\n'.join(lines[1:-1] if lines[-1].startswith('```') else lines[1:])
            
            # Replace the failed step in the original code
            lines = original_code.split('\n')
            for step in steps:
                if step['step_num'] == failed_step:
                    # Replace lines
                    start = step['start_line']
                    end = step['end_line'] + 1
                    fixed_lines = fixed_step.split('\n')
                    lines[start:end] = fixed_lines
                    break
            
            improved_code = '\n'.join(lines)
            
            if 'async def run_test' in improved_code:
                print(f"✅ Fixed STEP {failed_step}, preserved all other steps")
                return improved_code
            else:
                print(f"⚠️ Step fix invalid, falling back to full regeneration")
                return self.regenerate_code_with_ai(original_code, error_message, failed_step, attempt_num)
                
        except Exception as e:
            print(f"❌ Step-by-step healing error: {e}")
            return self.regenerate_code_with_ai(original_code, error_message, failed_step, attempt_num)

    def regenerate_code_with_ai(self, original_code, error_message, failed_step=0, attempt_num=1):
        """Use AI to regenerate improved code based on execution failure."""
        if not self.client:
            print("⚠️ OpenAI client not available, cannot regenerate code")
            return original_code
            
        try:
            print(f"\n🤖 AI CODE REGENERATION (Attempt {attempt_num}/{self.max_retries})")
            print(f"   Failed at step: {failed_step}")
            print(f"   Error: {error_message[:200]}...")
            print(f"   Using model: {'GPT-4o' if self.use_gpt4o else 'GPT-4o-mini'}")
            
            # ALWAYS use GPT-4o for better accuracy (decoupled from validator)
            model = "gpt-4o" if self.use_gpt4o else "gpt-4o-mini"
            
            response = self.client.chat.completions.create(
                model=model,
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
            # ALWAYS use GPT-4o for better locator suggestions (decoupled from validator)
            model = "gpt-4o" if self.use_gpt4o else "gpt-4o-mini"
            
            response = self.client.chat.completions.create(
                model=model,
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
        result = {'success': False, 'logs': [], 'screenshot': None}
        
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
            
            # Extract error details BEFORE any processing (needed for both healing paths)
            error_message = result.get('error_message', '')
            failed_step = result.get('failed_step', 0)  # Get from result, fallback to 0
            failed_locator = result.get('failed_locator')
            
            import sys
            print(f"\n🔍 HEALING ATTEMPT {attempt + 1}/{self.max_retries}:", flush=True)
            print(f"   Failed step: {failed_step}", flush=True)
            print(f"   Failed locator: {failed_locator}", flush=True)
            print(f"   Mode: {'headful' if not headless else 'headless'}", flush=True)
            sys.stdout.flush()
            
            # CHECK FOR AI HEALING REQUEST (from agent's request_ai_healing event)
            if self.ai_healing_requested and self.error_context:
                print(f"\n🤖 AI HEALING REQUEST DETECTED:", flush=True)
                print(f"   Error type: {self.error_context.get('type')}", flush=True)
                print(f"   Regenerating code with AI...", flush=True)
                
                # Use error context from the request, with safe fallback
                error_detail = self.error_context.get('info', {}).get('detail', '') or error_message or 'Unknown error'
                
                # Regenerate entire code with AI based on error
                regenerated_code = self.regenerate_code_with_ai(
                    current_code, 
                    error_detail, 
                    failed_step, 
                    attempt + 1
                )
                
                if regenerated_code != current_code:
                    current_code = regenerated_code
                    self.healed_script = regenerated_code
                    result['logs'].append(f"✅ AI regenerated complete code based on error analysis")
                    print(f"   ✅ Code regenerated successfully ({len(regenerated_code)} chars)", flush=True)
                    
                    self.socketio.emit('script_healed', {
                        'test_id': test_id,
                        'healed_script': current_code,
                        'failed_locator': failed_locator or '',
                        'healed_locator': 'AI regenerated',
                        'attempt': attempt + 1,
                        'method': 'ai_healing_request'
                    })
                else:
                    print(f"   ⚠️ AI regeneration produced same code", flush=True)
                
                # Reset the flag
                self.ai_healing_requested = False
                self.error_context = None
                
                # Continue to next attempt with regenerated code
                continue
            
            # ENHANCED AI-GUIDED RETRY STRATEGY
            # Attempts 1-2: Step-by-step healing
            # Attempt 3: Multi-strategy parallel healing (if available)
            # Attempt 4: Advanced locator validation
            # Attempt 5: User intervention (only as last resort)
            
            if attempt < 4:  # First 4 attempts: Automated AI healing
                healing_mode = "Enhanced (GPT-4o)" if self.use_gpt4o else "Standard (GPT-4o-mini)"
                if attempt == 2 and self.use_multi_strategy:
                    healing_mode = "Multi-Strategy Parallel Healing"
                elif self.use_advanced_validator:
                    healing_mode += " + Validator"
                result['logs'].append(f"🤖 AI Retry {attempt + 1}/4: {healing_mode}...")
                
                # Get page content for analysis
                page_content = result.get('page_content', '')
                if page_content:
                    result['logs'].append(f"📊 Captured page context ({len(page_content)} chars) for locator analysis")
                
                # Try step-by-step healing first (preserves successful steps)
                regenerated_code = self.regenerate_failed_step_only(
                    current_code, 
                    error_message, 
                    failed_step, 
                    attempt + 1,
                    page_content
                )
                
                if regenerated_code != current_code:
                    current_code = regenerated_code
                    self.healed_script = regenerated_code
                    result['logs'].append(f"✅ Fixed STEP {failed_step}, all other steps preserved")
                    
                    self.socketio.emit('script_healed', {
                        'test_id': test_id,
                        'healed_script': current_code,
                        'failed_locator': failed_locator or '',
                        'healed_locator': f'Step {failed_step} fixed',
                        'attempt': attempt + 1,
                        'method': 'step_by_step_healing'
                    })
                else:
                    # Fallback to locator improvement if step regeneration failed
                    result['logs'].append(f"⚠️ Step healing unchanged, trying locator improvement...")
                    if failed_locator:
                        improved_locator = self.improve_locator_with_ai(
                            failed_locator, 
                            error_message,
                            result.get('page_content', '')
                        )
                        current_code = self.heal_script(current_code, failed_locator, improved_locator)
                        result['logs'].append(f"🔧 Improved locator: {improved_locator}")
                
            # Final attempt (5th): Show user widget in headful mode as last resort
            elif attempt >= 4:  # 5th attempt: User intervention only as last resort
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
                page_content = result.get('page_html', '')  # Get page HTML if available
                
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
            
            # ALWAYS use GPT-4o for better analysis (decoupled from validator)
            model = "gpt-4o" if self.use_gpt4o else "gpt-4o-mini"
            
            response = self.client.chat.completions.create(
                model=model,
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
