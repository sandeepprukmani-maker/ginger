"""
Playwright Planner Agent
Explores the application and creates comprehensive test plans
"""
import json
import logging
from typing import Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    AI agent that explores web applications and creates test plans
    """
    
    def __init__(self, mcp_client, llm_client: OpenAI, model: str):
        """
        Initialize the Planner Agent
        
        Args:
            mcp_client: MCP client for browser automation
            llm_client: OpenAI client instance
            model: Model name to use
        """
        self.mcp_client = mcp_client
        self.client = llm_client
        self.model = model
        self.max_iterations = 15
        
    def create_test_plan(self, instruction: str) -> Dict[str, Any]:
        """
        Create a comprehensive test plan by exploring the application
        
        Args:
            instruction: User's instruction (e.g., "Test the checkout flow")
            
        Returns:
            Dictionary with test plan and exploration steps
        """
        if not self.mcp_client.initialized:
            self.mcp_client.initialize()
        
        tools = self.mcp_client.get_tools_schema()
        
        system_prompt = """You are a Playwright Test Planner Agent.

Your role is to explore web applications and create comprehensive, structured test plans.

When given an instruction:
1. Navigate to the application and explore the relevant user flows
2. Identify all key scenarios that need to be tested
3. Document each scenario with clear steps and expected outcomes
4. Think about edge cases, validation, and error scenarios
5. Create a detailed test plan in Markdown format

Use the browser tools to:
- Navigate to pages
- Inspect elements and page structure
- Identify interactive elements
- Understand the application flow

Create a test plan with this structure:

# Test Plan: [Feature Name]

## Application Overview
Brief description of the feature being tested

## Test Scenarios

### Scenario 1: [Name]
**Description**: What this scenario tests

**Steps**:
1. [Action 1]
2. [Action 2]
...

**Expected Results**:
- [Expected outcome 1]
- [Expected outcome 2]
...

### Scenario 2: [Name]
...

Respond with a tool call to create the test plan, or finish with the plan when exploration is complete."""

        conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction}
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
                    
                    return {
                        "success": True,
                        "test_plan": test_plan,
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
