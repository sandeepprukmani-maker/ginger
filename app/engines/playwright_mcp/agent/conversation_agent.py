"""
OpenAI-powered Browser Agent
Interprets natural language instructions and executes browser actions
Supports Playwright Agent modes: direct, planner, generator, healer, full_agent
Based on Microsoft's Playwright Test Agents specification
"""
import json
import os
import logging
import time
import configparser
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI
from auth.oauth_handler import get_oauth_token_with_retry
from app.utils.logging_config import (
    should_log_llm_requests, 
    should_log_llm_responses,
    should_log_browser_actions,
    should_log_page_state,
    should_log_performance
)
from app.engines.playwright_mcp.agent.planner_agent import PlannerAgent
from app.engines.playwright_mcp.agent.generator_agent import GeneratorAgent
from app.engines.playwright_mcp.agent.healer_agent import HealerAgent
from app.engines.playwright_mcp.agent.automation_agent import AutomationAgent
from app.engines.playwright_mcp.file_manager import AgentFileManager

# Load .env file from project root with explicit path
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)


class BrowserAgent:
    """
    AI agent that performs browser automation based on natural language instructions
    
    Implements Microsoft's Playwright Test Agents:
    - 🎭 Planner: Explores app and creates test plans
    - 🎨 Generator: Transforms plans into executable tests
    - 🔧 Healer: Automatically repairs failing tests
    """
    
    def __init__(self, mcp_client: Any, workspace_root: str = "."):
        """
        Initialize the Browser Agent
        
        Args:
            mcp_client: MCP client for browser automation
            workspace_root: Root directory for specs/ and tests/ (default: current directory)
        """
        config = configparser.ConfigParser()
        config.read('config/config.ini')
        
        self.mcp_client = mcp_client
        
        gateway_base_url = os.environ.get('GW_BASE_URL')
        if not gateway_base_url:
            raise ValueError("GW_BASE_URL must be set as environment variable to connect to the gateway endpoint.")
        
        try:
            oauth_token = get_oauth_token_with_retry(max_retries=3)
        except Exception as e:
            raise ValueError(f"Failed to obtain OAuth token: {str(e)}. Please check your OAuth configuration.")
        
        self.client = OpenAI(
            base_url=gateway_base_url,
            api_key=oauth_token,
            default_headers={
                "Authorization": f"Bearer {oauth_token}"
            }
        )
        self.model = config.get('openai', 'model', fallback='gpt-4.1-2025-04-14-eastus-dz')
        self.conversation_history = []
        self.max_iterations = 10
        
        # Logging configuration
        self.logger = logging.getLogger(__name__)
        self.log_llm_requests = should_log_llm_requests()
        self.log_llm_responses = should_log_llm_responses()
        self.log_browser_actions = should_log_browser_actions()
        self.log_page_state = should_log_page_state()
        self.log_performance = should_log_performance()
        
        # Store gateway URL for logging
        self.gateway_base_url = gateway_base_url
        
        # Initialize File Manager for Microsoft's file-based workflow
        self.file_manager = AgentFileManager(workspace_root)
        self.file_manager.initialize_directories()
        
        # Initialize Playwright Agents with file manager
        self.planner = PlannerAgent(mcp_client, self.client, self.model, self.file_manager)
        self.generator = GeneratorAgent(mcp_client, self.client, self.model, self.file_manager)
        self.healer = HealerAgent(mcp_client, self.client, self.model, self.file_manager)
        self.automation = AutomationAgent(mcp_client, self.client, self.model, self.file_manager)
        
    def execute_instruction(self, instruction: str, mode: str = "direct") -> Dict[str, Any]:
        """
        Execute a natural language instruction with specified agent mode
        
        Args:
            instruction: User's natural language instruction
            mode: Agent mode - "direct", "automation", "planner", "generator", "healer", or "full_agent"
            
        Returns:
            Dictionary with execution results and steps taken
        """
        if mode == "automation":
            return self._execute_automation_mode(instruction)
        elif mode == "planner":
            return self._execute_planner_mode(instruction)
        elif mode == "generator":
            return self._execute_generator_mode(instruction)
        elif mode == "healer":
            return self._execute_healer_mode(instruction)
        elif mode == "full_agent":
            return self._execute_full_agent_mode(instruction)
        else:
            # Default: direct execution
            return self._execute_direct_mode(instruction)
    
    def _execute_full_agent_mode(self, instruction: str) -> Dict[str, Any]:
        """
        Execute full agent workflow: Planner -> Generator -> Healer
        
        Args:
            instruction: User's natural language instruction
            
        Returns:
            Dictionary with test plan, generated code, and healed code
        """
        self.logger.info("=" * 80)
        self.logger.info("🎭 FULL AGENT MODE: Planner -> Generator -> Healer")
        self.logger.info("=" * 80)
        
        # Step 1: Planner creates test plan
        self.logger.info("📝 Step 1/3: Creating test plan...")
        
        # Try to read seed test if it exists
        seed_test_content = self.file_manager.read_test("seed.spec")
        
        planner_result = self.planner.create_test_plan(
            instruction, 
            seed_test=seed_test_content,
            save_to_file=True
        )
        
        if not planner_result.get('success'):
            return {
                "success": False,
                "error": "Planner failed",
                "message": planner_result.get('error', 'Unknown error'),
                "planner_result": planner_result
            }
        
        test_plan = planner_result.get('test_plan', '')
        self.logger.info(f"✅ Test plan created ({len(test_plan)} chars)")
        
        # Step 2: Generator creates executable code
        self.logger.info("🎨 Step 2/3: Generating executable test code...")
        
        seed_test_content = self.file_manager.read_test("seed.spec")
        spec_file = planner_result.get('spec_file')
        
        generator_result = self.generator.generate_test_code(
            test_plan, 
            instruction,
            seed_test=seed_test_content,
            spec_file=spec_file,
            save_to_file=True
        )
        
        if not generator_result.get('success'):
            return {
                "success": False,
                "error": "Generator failed",
                "message": generator_result.get('error', 'Unknown error'),
                "test_plan": test_plan,
                "planner_result": planner_result,
                "generator_result": generator_result
            }
        
        generated_code = generator_result.get('generated_code', '')
        self.logger.info(f"✅ Test code generated ({len(generated_code)} chars)")
        
        # Step 3: Healer validates and fixes the code
        self.logger.info("🔧 Step 3/3: Validating and healing test code...")
        
        test_file = generator_result.get('test_file')
        
        healer_result = self.healer.heal_test(
            generated_code, 
            instruction,
            test_file=test_file,
            save_to_file=True
        )
        
        healed_code = healer_result.get('healed_code', generated_code)
        healing_success = healer_result.get('success', False)
        
        if healing_success:
            self.logger.info("✅ Test code healed and validated")
        else:
            self.logger.warning("⚠️ Healing attempted but test may still have issues")
        
        # Return comprehensive result
        return {
            "success": True,
            "message": "Full agent workflow completed",
            "test_plan": test_plan,
            "generated_code": generated_code,
            "healed_code": healed_code if healed_code != generated_code else None,
            "planner_result": planner_result,
            "generator_result": generator_result,
            "healer_result": healer_result,
            "iterations": (
                planner_result.get('iterations', 0) +
                generator_result.get('iterations', 0) +
                healer_result.get('healing_attempts', 0)
            )
        }
    
    def _execute_planner_mode(self, instruction: str) -> Dict[str, Any]:
        """Execute only the planner agent"""
        result = self.planner.create_test_plan(instruction)
        result['mode'] = 'planner'
        return result
    
    def _execute_generator_mode(self, instruction: str) -> Dict[str, Any]:
        """Execute only the generator agent (requires test_plan in instruction)"""
        result = self.generator.generate_test_code(instruction, instruction)
        result['mode'] = 'generator'
        return result
    
    def _execute_healer_mode(self, instruction: str) -> Dict[str, Any]:
        """Execute only the healer agent (requires test_code in instruction)"""
        result = self.healer.heal_test(instruction, instruction)
        result['mode'] = 'healer'
        return result
    
    def _execute_direct_mode(self, instruction: str) -> Dict[str, Any]:
        """
        Execute a natural language instruction
        
        Args:
            instruction: User's natural language instruction
            
        Returns:
            Dictionary with execution results and steps taken
        """
        if not self.mcp_client.initialized:
            self.mcp_client.initialize()
        
        tools = self.mcp_client.get_tools_schema()
        
        self.conversation_history = [
            {
                "role": "system",
                "content": """You are an intelligent browser automation assistant. 
You help users automate web browsing tasks using natural language instructions.

When given an instruction:
1. Break it down into browser automation steps
2. Use the available browser tools to accomplish the task
3. Navigate to websites, click elements, fill forms, and extract information as needed
4. Always check the page state after navigation to understand what's available
5. Use element references (ref) from the page snapshot when clicking or filling forms
6. Be precise and follow the user's intent carefully

Important: When you see page snapshots in YAML format, look for element references like [ref=e1], [ref=e2], etc. 
Use these references when calling browser_click or browser_fill tools.

Respond with tool calls to accomplish the task."""
            },
            {
                "role": "user",
                "content": instruction
            }
        ]
        
        steps = []
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            try:
                # Log LLM request details
                if self.log_llm_requests:
                    self.logger.debug("=" * 80)
                    self.logger.debug(f"📤 LLM REQUEST (Iteration {iteration}/{self.max_iterations})")
                    self.logger.debug(f"Model: {self.model}")
                    self.logger.debug(f"Gateway: {self.gateway_base_url}")
                    self.logger.debug(f"Messages count: {len(self.conversation_history)}")
                    self.logger.debug(f"Tools available: {len(tools)}")
                    self.logger.debug("=" * 80)
                
                if self.log_performance:
                    start_time = time.time()
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,  # type: ignore
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=4096
                )
                
                if self.log_performance:
                    elapsed = time.time() - start_time
                    self.logger.debug(f"⏱️  LLM response received in {elapsed:.2f}s")
                
                # Log LLM response details
                if self.log_llm_responses:
                    self.logger.debug("=" * 80)
                    self.logger.debug(f"📥 LLM RESPONSE (Iteration {iteration})")
                    self.logger.debug(f"Finish reason: {response.choices[0].finish_reason}")
                    if response.usage:
                        self.logger.debug(f"Tokens - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}, Total: {response.usage.total_tokens}")
                    self.logger.debug("=" * 80)
                
                message = response.choices[0].message
                self.conversation_history.append(message.model_dump())
                
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name  # type: ignore
                        tool_args = json.loads(tool_call.function.arguments)  # type: ignore
                        
                        # Log browser action
                        if self.log_browser_actions:
                            self.logger.debug("=" * 80)
                            self.logger.debug(f"🎬 BROWSER ACTION: {tool_name}")
                            self.logger.debug(f"Arguments: {json.dumps(tool_args, indent=2)}")
                            self.logger.debug("=" * 80)
                        
                        try:
                            if self.log_performance:
                                action_start = time.time()
                            
                            result = self.mcp_client.call_tool(tool_name, tool_args)
                            
                            if self.log_performance:
                                action_elapsed = time.time() - action_start
                                self.logger.debug(f"⏱️  Action '{tool_name}' completed in {action_elapsed:.2f}s")
                            
                            # Log action result
                            if self.log_browser_actions:
                                self.logger.debug(f"✅ Action '{tool_name}' succeeded")
                                if self.log_page_state and result:
                                    self.logger.debug(f"Result preview: {str(result)[:200]}...")
                            
                            step_info = {
                                "tool": tool_name,
                                "arguments": tool_args,
                                "success": True,
                                "result": result
                            }
                            steps.append(step_info)
                            
                            self.conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result, indent=2)
                            })
                            
                        except Exception as e:
                            error_msg = str(e)
                            
                            # Log action failure
                            if self.log_browser_actions:
                                self.logger.error("=" * 80)
                                self.logger.error(f"❌ Action '{tool_name}' FAILED")
                                self.logger.error(f"Error: {error_msg}")
                                self.logger.error("=" * 80)
                            
                            steps.append({
                                "tool": tool_name,
                                "arguments": tool_args,
                                "success": False,
                                "error": error_msg
                            })
                            
                            self.conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": f"Error: {error_msg}"
                            })
                else:
                    final_response = message.content or "Task completed"
                    
                    # Generate Playwright code from MCP steps
                    playwright_code = None
                    try:
                        from app.engines.playwright_mcp.mcp_code_generator import generate_playwright_code_from_mcp_steps
                        playwright_code = generate_playwright_code_from_mcp_steps(
                            steps,
                            task_description=instruction
                        )
                    except Exception as e:
                        # Code generation is optional, don't fail the task
                        pass
                    
                    result = {
                        "success": True,
                        "message": final_response,
                        "steps": steps,
                        "iterations": iteration
                    }
                    
                    if playwright_code:
                        result["playwright_code"] = playwright_code
                    
                    return result
                    
            except Exception as e:
                self.logger.error("=" * 80)
                self.logger.error("❌ LLM CALL FAILED")
                self.logger.error(f"Error Type: {type(e).__name__}")
                self.logger.error(f"Error Message: {str(e)}")
                self.logger.error(f"Iteration: {iteration}/{self.max_iterations}")
                self.logger.error("=" * 80)
                import traceback
                self.logger.error(traceback.format_exc())
                
                return {
                    "success": False,
                    "error": str(e),
                    "steps": steps,
                    "iterations": iteration
                }
        
        # Generate Playwright code even if max iterations reached
        playwright_code = None
        try:
            from app.engines.playwright_mcp.mcp_code_generator import generate_playwright_code_from_mcp_steps
            playwright_code = generate_playwright_code_from_mcp_steps(
                steps,
                task_description=instruction
            )
        except Exception:
            pass
        
        result = {
            "success": False,
            "error": "Max iterations reached",
            "steps": steps,
            "iterations": iteration
        }
        
        if playwright_code:
            result["playwright_code"] = playwright_code
        
        return result
    
    def _execute_automation_mode(self, instruction: str) -> Dict[str, Any]:
        """
        Execute automation mode: Direct execution -> Generate self-healing script
        
        This mode:
        1. Executes the task directly using browser automation
        2. Captures all execution steps
        3. Generates a single Python automation script with self-healing capabilities
        
        Args:
            instruction: User's natural language instruction
            
        Returns:
            Dictionary with execution results and generated automation script
        """
        self.logger.info("=" * 80)
        self.logger.info("🤖 AUTOMATION MODE: Execute -> Generate Self-Healing Script")
        self.logger.info("=" * 80)
        
        # Step 1: Execute the task directly to capture steps
        self.logger.info("📝 Step 1/2: Executing task to capture automation steps...")
        
        direct_result = self._execute_direct_mode(instruction)
        
        if not direct_result.get('success'):
            return {
                "success": False,
                "error": "Task execution failed",
                "message": direct_result.get('error', 'Unknown error'),
                "execution_result": direct_result
            }
        
        steps = direct_result.get('steps', [])
        self.logger.info(f"✅ Task executed successfully ({len(steps)} steps captured)")
        
        # Step 2: Generate self-healing automation script
        self.logger.info("🎨 Step 2/2: Generating self-healing automation script...")
        
        automation_result = self.automation.generate_automation_script(
            execution_steps=steps,
            instruction=instruction,
            save_to_file=True
        )
        
        if not automation_result.get('success'):
            return {
                "success": False,
                "error": "Script generation failed",
                "message": automation_result.get('error', 'Unknown error'),
                "execution_result": direct_result,
                "automation_result": automation_result
            }
        
        generated_code = automation_result.get('generated_code', '')
        script_file = automation_result.get('script_file')
        
        self.logger.info(f"✅ Self-healing script generated ({len(generated_code)} chars)")
        if script_file:
            self.logger.info(f"📄 Saved to: {script_file}")
        
        # Return comprehensive result
        return {
            "success": True,
            "message": f"Automation script generated successfully{' and saved to ' + script_file if script_file else ''}",
            "generated_code": generated_code,
            "script_file": script_file,
            "execution_result": direct_result,
            "automation_result": automation_result,
            "steps": steps,
            "iterations": direct_result.get('iterations', 0),
            "mode": "automation"
        }
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []
