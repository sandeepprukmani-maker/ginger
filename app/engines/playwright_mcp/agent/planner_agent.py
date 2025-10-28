"""
Playwright Planner Agent
Explores the application and creates comprehensive test plans
Based on Microsoft's Playwright Test Agents specification
"""
import json
import logging
import configparser
from typing import Dict, Any, Optional
from openai import OpenAI
from ..file_manager import AgentFileManager

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    🎭 Planner Agent - Explores the app and produces a Markdown test plan
    
    Following Microsoft's Playwright Test Agents conventions:
    - Explores web applications based on instructions
    - Creates structured test plans in Markdown format  
    - Saves plans to specs/ directory
    - Uses seed tests for context and initialization
    """
    
    def __init__(self, mcp_client, llm_client: OpenAI, model: str, file_manager: Optional[AgentFileManager] = None):
        """
        Initialize the Planner Agent
        
        Args:
            mcp_client: MCP client for browser automation
            llm_client: OpenAI client instance
            model: Model name to use
            file_manager: Optional file manager for saving specs
        """
        self.mcp_client = mcp_client
        self.client = llm_client
        self.model = model
        self.file_manager = file_manager or AgentFileManager()
        
        # Read max_iterations from config
        config = configparser.ConfigParser()
        config.read('config/config.ini')
        self.max_iterations = config.getint('agent', 'max_steps', fallback=40)
        
    def create_test_plan(self, instruction: str, seed_test: Optional[str] = None, 
                         prd: Optional[str] = None, save_to_file: bool = True) -> Dict[str, Any]:
        """
        Create a comprehensive test plan by exploring the application
        
        Based on Microsoft's 🎭 Planner specification:
        - Explores the app based on instruction
        - Uses seed test for initialization context
        - Creates structured Markdown test plan
        - Saves plan to specs/ directory
        
        Args:
            instruction: User's instruction (e.g., "Generate a plan for guest checkout")
            seed_test: Optional seed test code for context
            prd: Optional Product Requirement Document for additional context
            save_to_file: Whether to save the plan to specs/ directory
            
        Returns:
            Dictionary with test plan, file path, and exploration steps
        """
        if not self.mcp_client.initialized:
            self.mcp_client.initialize()
        
        tools = self.mcp_client.get_tools_schema()
        
        # Microsoft's exact Planner prompt
        system_prompt = """You are the 🎭 Planner Agent from Microsoft's Playwright Test Agents.

Your role is to explore web applications and produce comprehensive, structured test plans in Markdown format.

**Input:**
- A clear request for what to test
- A seed test that sets up the environment
- (Optional) A Product Requirement Document (PRD) for context

**Your Process:**
1. Understand the request and what user flows need to be tested
2. Navigate to the application using browser tools
3. Explore the relevant user flows and interactions
4. Identify all key scenarios, including:
   - Happy path scenarios
   - Edge cases
   - Validation and error scenarios
   - Different user roles or states
5. Document each scenario with precise steps and expected outcomes

**Browser Tools Available:**
- Navigate to pages and inspect structure
- Click elements and fill forms to explore flows
- Identify interactive elements and their states
- Understand application behavior and responses

**Output Format:**

# [Feature Name] Test Plan

## Application Overview
[Brief description of the feature and its purpose]
[Key features and capabilities]
[State persistence and user experience notes]

## Test Scenarios

### Scenario 1: [Descriptive Name]

**Seed:** `tests/seed.spec.py`

#### 1.1 [Sub-scenario Name]

**Steps:**
1. [Precise action with element details]
2. [Next action]
3. [Continue...]

**Expected Results:**
- [Specific expected outcome with details]
- [Visual feedback or state changes]
- [Counter/indicator updates]
- [UI element visibility changes]

### Scenario 2: [Next Major Scenario]
[Continue with same detailed structure...]

**Quality Standards:**
- Be precise about element names, labels, and identifiers
- Include all visual feedback and state changes
- Document counters, indicators, and UI updates
- Think through the complete user journey
- Consider accessibility and usability

When exploration is complete, provide the complete test plan in the format above."""

        # Build user message with all context
        user_message_parts = [f"**Request:** {instruction}"]
        
        if seed_test:
            user_message_parts.append(f"\n**Seed Test:**\n```python\n{seed_test}\n```")
        
        if prd:
            user_message_parts.append(f"\n**Product Requirements:**\n{prd}")
        
        user_message = "\n".join(user_message_parts)
        
        conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        exploration_steps = []
        iteration = 0
        test_plan = ""
        
        while iteration < self.max_iterations:
            iteration += 1
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=conversation_history,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=4096
                )
                
                message = response.choices[0].message
                conversation_history.append(message.model_dump())
                
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        logger.info(f"🎭 Planner exploring: {tool_name}")
                        
                        try:
                            result = self.mcp_client.call_tool(tool_name, tool_args)
                            
                            step_info = {
                                "tool": tool_name,
                                "arguments": tool_args,
                                "success": True
                            }
                            exploration_steps.append(step_info)
                            
                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result, indent=2)
                            })
                            
                        except Exception as e:
                            error_msg = str(e)
                            logger.error(f"❌ Planner action failed: {error_msg}")
                            
                            exploration_steps.append({
                                "tool": tool_name,
                                "arguments": tool_args,
                                "success": False,
                                "error": error_msg
                            })
                            
                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": f"Error: {error_msg}"
                            })
                else:
                    # LLM finished - extract test plan
                    test_plan = message.content or ""
                    
                    logger.info(f"✅ Test plan created ({len(test_plan)} chars)")
                    
                    # Save to file if requested
                    spec_file_path = None
                    if save_to_file and test_plan:
                        # Extract feature name from plan for filename
                        spec_name = self._extract_spec_name(test_plan, instruction)
                        metadata = {
                            "instruction": instruction,
                            "agent": "planner",
                            "iterations": iteration
                        }
                        spec_file_path = self.file_manager.save_spec(spec_name, test_plan, metadata)
                    
                    return {
                        "success": True,
                        "test_plan": test_plan,
                        "spec_file": spec_file_path,
                        "exploration_steps": exploration_steps,
                        "iterations": iteration
                    }
                    
            except Exception as e:
                logger.error(f"❌ Planner error: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "exploration_steps": exploration_steps,
                    "iterations": iteration
                }
        
        return {
            "success": False,
            "error": "Max iterations reached",
            "test_plan": test_plan,
            "exploration_steps": exploration_steps,
            "iterations": iteration
        }
    
    def _extract_spec_name(self, test_plan: str, instruction: str) -> str:
        """
        Extract a suitable spec name from the test plan or instruction
        
        Args:
            test_plan: The generated test plan
            instruction: Original user instruction
            
        Returns:
            Spec name for the file
        """
        # Try to extract from first heading
        lines = test_plan.split('\n')
        for line in lines:
            if line.startswith('# '):
                # Remove '# ' and any 'Test Plan' suffix
                name = line[2:].strip()
                name = name.replace(' Test Plan', '').replace(' - Test Plan', '')
                return name.lower().replace(' ', '-')
        
        # Fallback to instruction-based name
        return instruction.lower().replace(' ', '-')[:50]
