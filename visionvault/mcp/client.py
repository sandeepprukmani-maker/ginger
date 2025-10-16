"""
MCP Client Integration for Code Generation and Healing

This module integrates MCP tools into the code generation and healing workflow,
allowing AI models to leverage VisionVault's intelligence for better automation code.
"""

from typing import Dict, List, Any, Optional
import json


class MCPEnhancedCodeGenerator:
    """Enhances code generation with MCP tool integration."""
    
    def __init__(self, mcp_server, openai_client):
        """
        Initialize MCP-enhanced code generator.
        
        Args:
            mcp_server: VisionVaultMCPServer instance
            openai_client: OpenAI client for AI generation
        """
        self.mcp_server = mcp_server
        self.openai_client = openai_client
    
    async def generate_with_mcp(self, command: str, browser: str = 'chromium', 
                                url: str = None) -> Dict[str, Any]:
        """
        Generate Playwright code using MCP tools for enhanced intelligence.
        
        Args:
            command: Natural language automation command
            browser: Browser type
            url: Target URL (optional)
            
        Returns:
            Dict with generated code and MCP insights
        """
        mcp_context = {}
        
        # Step 1: Search for similar learned tasks via MCP
        learned_tasks_result = await self.mcp_server.handle_tool_call(
            'search_learned_tasks',
            {'query': command, 'top_k': 3}
        )
        
        if learned_tasks_result['success']:
            mcp_context['learned_tasks'] = learned_tasks_result['result']
        
        # Step 2: Get execution history via MCP
        history_result = await self.mcp_server.handle_tool_call(
            'get_task_execution_history',
            {'task_description': command, 'limit': 5}
        )
        
        if history_result['success']:
            mcp_context['execution_history'] = history_result['result']
        
        # Step 3: If URL provided, analyze DOM via MCP
        if url:
            dom_result = await self.mcp_server.handle_tool_call(
                'analyze_page_dom',
                {'url': url, 'intent': command}
            )
            
            if dom_result['success']:
                mcp_context['dom_analysis'] = dom_result['result']
        
        # Step 4: Build enhanced system prompt with MCP context
        system_prompt = self._build_mcp_enhanced_prompt(mcp_context)
        
        # Step 5: Generate code with AI using MCP context
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate Playwright code for: {command}\nBrowser: {browser}"}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        generated_code = response.choices[0].message.content.strip()
        
        # Clean up code formatting
        if generated_code.startswith('```python'):
            generated_code = generated_code[9:]
        elif generated_code.startswith('```'):
            generated_code = generated_code[3:]
        if generated_code.endswith('```'):
            generated_code = generated_code[:-3]
        
        generated_code = generated_code.strip()
        
        return {
            'code': generated_code,
            'mcp_context': mcp_context,
            'insights': self._extract_insights(mcp_context)
        }
    
    def _build_mcp_enhanced_prompt(self, mcp_context: Dict) -> str:
        """Build system prompt enhanced with MCP tool results."""
        
        base_prompt = """You are an expert at converting natural language commands into Playwright Python code.
Your code is enhanced with intelligence from VisionVault's MCP (Model Context Protocol) tools.

Generate complete, executable Playwright code that:
1. Uses async/await syntax
2. Includes proper browser launch
3. Has error handling with proper cleanup
4. Returns a dict with 'success', 'logs', 'screenshot', and 'current_step' keys
5. ALWAYS takes screenshot BEFORE closing browser
6. Uses the most reliable locator strategies

"""
        
        # Add learned tasks context
        if 'learned_tasks' in mcp_context and mcp_context['learned_tasks'].get('found'):
            tasks = mcp_context['learned_tasks']['tasks']
            base_prompt += f"\n🎓 LEARNED TASKS (from MCP):\n"
            base_prompt += f"Found {len(tasks)} similar tasks you can learn from:\n\n"
            
            for i, task in enumerate(tasks, 1):
                similarity = task.get('similarity_score', 0)
                base_prompt += f"Task {i} (Similarity: {similarity:.0%}): {task['task_name']}\n"
                if task.get('playwright_code'):
                    base_prompt += f"Proven Code:\n```python\n{task['playwright_code'][:500]}...\n```\n\n"
        
        # Add execution history insights
        if 'execution_history' in mcp_context and mcp_context['execution_history'].get('found'):
            history = mcp_context['execution_history']
            base_prompt += f"\n📊 EXECUTION HISTORY (from MCP):\n"
            base_prompt += f"Success Rate: {history['success_rate']}%\n"
            
            if history.get('insights'):
                base_prompt += "Insights:\n"
                for insight in history['insights']:
                    base_prompt += f"- {insight}\n"
        
        # Add DOM analysis
        if 'dom_analysis' in mcp_context and mcp_context['dom_analysis'].get('success'):
            dom = mcp_context['dom_analysis']
            base_prompt += f"\n🔍 PAGE ANALYSIS (from MCP):\n"
            
            if dom.get('intent_matched'):
                base_prompt += f"Intent-Matched Elements: {len(dom['intent_matched'])}\n"
                for elem in dom['intent_matched'][:3]:
                    base_prompt += f"  - {elem.get('tag', 'unknown')}: {elem.get('text', '')[:50]}\n"
            
            if dom.get('recommended_locators'):
                base_prompt += f"\nRecommended Locators:\n"
                for loc in dom['recommended_locators'][:5]:
                    base_prompt += f"  - {loc}\n"
        
        base_prompt += """

CRITICAL RULES:
1. Use MCP insights above to write better, more reliable code
2. Prefer locators from learned tasks (proven to work)
3. Apply lessons from execution history (avoid past failures)
4. Use DOM analysis locators (verified to exist on page)
5. Add 5000ms timeout to LOCATOR action methods only (click, fill, press)
6. NEVER add timeout to: locator() calls, page.keyboard.press()

Return ONLY the complete Python code:"""
        
        return base_prompt
    
    def _extract_insights(self, mcp_context: Dict) -> List[str]:
        """Extract key insights from MCP context."""
        insights = []
        
        if 'learned_tasks' in mcp_context and mcp_context['learned_tasks'].get('found'):
            count = mcp_context['learned_tasks']['count']
            insights.append(f'Found {count} similar learned tasks to reuse patterns from')
        
        if 'execution_history' in mcp_context and mcp_context['execution_history'].get('found'):
            rate = mcp_context['execution_history']['success_rate']
            insights.append(f'Historical success rate: {rate}%')
        
        if 'dom_analysis' in mcp_context and mcp_context['dom_analysis'].get('success'):
            insights.append('Page DOM analyzed for optimal locators')
        
        return insights


class MCPEnhancedHealer:
    """Enhances healing process with MCP tool integration."""
    
    def __init__(self, mcp_server, openai_client):
        """
        Initialize MCP-enhanced healer.
        
        Args:
            mcp_server: VisionVaultMCPServer instance
            openai_client: OpenAI client for AI healing
        """
        self.mcp_server = mcp_server
        self.openai_client = openai_client
    
    async def heal_with_mcp(self, original_code: str, error_message: str, 
                           error_type: str, failed_step: int = 0) -> Dict[str, Any]:
        """
        Heal failed code using MCP tools for intelligent strategy selection.
        
        Args:
            original_code: The original/failed code
            error_message: Error message from execution
            error_type: Type of error (locator_not_found, timeout, etc.)
            failed_step: Step number that failed
            
        Returns:
            Dict with healed code and MCP insights
        """
        # Step 1: Get healing strategies from MCP
        strategies_result = await self.mcp_server.handle_tool_call(
            'get_healing_strategies',
            {
                'error_type': error_type,
                'error_message': error_message,
                'failed_step': failed_step
            }
        )
        
        mcp_strategies = strategies_result['result'] if strategies_result['success'] else {}
        
        # Step 2: Build healing prompt with MCP strategies
        system_prompt = f"""You are an expert at healing failed Playwright automation code.
You have access to MCP (Model Context Protocol) healing intelligence.

MCP HEALING STRATEGIES for {error_type}:
"""
        
        if mcp_strategies.get('strategies'):
            for i, strategy in enumerate(mcp_strategies['strategies'], 1):
                system_prompt += f"{i}. {strategy}\n"
        
        system_prompt += f"\nPriority: {mcp_strategies.get('priority', 'medium')}"
        system_prompt += f"\nRecommendation: {mcp_strategies.get('recommendation', 'Apply best practices')}"
        
        system_prompt += """

HEALING RULES:
1. Apply MCP strategies in order of priority
2. Preserve working code from other steps
3. Focus healing on the failed step only
4. Use proven locator patterns
5. Add appropriate waits and timeouts
6. Return ONLY the complete healed code

Original code that failed:"""
        
        # Step 3: Generate healed code with AI
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
Failed Code:
```python
{original_code}
```

Error at STEP {failed_step}: {error_message}

Generate the healed code:"""}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        healed_code = response.choices[0].message.content.strip()
        
        # Clean up formatting
        if healed_code.startswith('```python'):
            healed_code = healed_code[9:]
        elif healed_code.startswith('```'):
            healed_code = healed_code[3:]
        if healed_code.endswith('```'):
            healed_code = healed_code[:-3]
        
        healed_code = healed_code.strip()
        
        # Step 4: Format healed code for reusability using MCP
        format_result = await self.mcp_server.handle_tool_call(
            'format_reusable_script',
            {
                'code': healed_code,
                'task_description': f'Healed automation script (fixed: {error_type})',
                'healing_notes': f'Applied MCP strategies: {", ".join(mcp_strategies.get("strategies", [])[:3])}'
            }
        )
        
        if format_result['success']:
            formatted_code = format_result['result']['formatted_code']
        else:
            formatted_code = healed_code
        
        return {
            'healed_code': healed_code,
            'reusable_code': formatted_code,
            'mcp_strategies': mcp_strategies,
            'applied_strategies': mcp_strategies.get('strategies', [])[:3],
            'improvements': format_result['result'].get('improvements', []) if format_result['success'] else []
        }
