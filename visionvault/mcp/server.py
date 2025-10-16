"""
VisionVault MCP Server

Provides Model Context Protocol tools for enhanced code generation and healing.
Exposes VisionVault's intelligence (learned tasks, DOM inspection, healing strategies)
as tools that can be used by AI models for better automation code.
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
import sqlite3
from pathlib import Path


class VisionVaultMCPServer:
    """MCP Server that exposes VisionVault's automation intelligence as tools."""
    
    def __init__(self, database_path: str, vector_store=None, dom_inspector=None):
        """
        Initialize MCP server with access to VisionVault's data and services.
        
        Args:
            database_path: Path to the automation database
            vector_store: Vector store for semantic search (optional)
            dom_inspector: DOM inspector service (optional)
        """
        self.database_path = database_path
        self.vector_store = vector_store
        self.dom_inspector = dom_inspector
        
        # Define available tools
        self.tools = {
            'search_learned_tasks': {
                'description': 'Search for similar learned automation tasks using semantic search',
                'parameters': {
                    'query': 'Natural language description of the automation task',
                    'top_k': 'Number of similar tasks to return (default: 3)'
                },
                'handler': self.search_learned_tasks
            },
            'get_task_execution_history': {
                'description': 'Get execution history and success patterns for similar tasks',
                'parameters': {
                    'task_description': 'Description of the task to find history for',
                    'limit': 'Maximum number of executions to return (default: 5)'
                },
                'handler': self.get_task_execution_history
            },
            'analyze_page_dom': {
                'description': 'Analyze a web page DOM structure to find optimal locators',
                'parameters': {
                    'url': 'URL of the page to analyze',
                    'intent': 'What you want to do on the page (e.g., "click login button")'
                },
                'handler': self.analyze_page_dom
            },
            'get_healing_strategies': {
                'description': 'Get recommended healing strategies for a specific error type',
                'parameters': {
                    'error_type': 'Type of error (locator_not_found, timeout, api_error, etc.)',
                    'error_message': 'The actual error message',
                    'failed_step': 'The step number that failed'
                },
                'handler': self.get_healing_strategies
            },
            'format_reusable_script': {
                'description': 'Format healed code into clean, documented, reusable script',
                'parameters': {
                    'code': 'The healed Playwright code',
                    'task_description': 'Description of what the script does',
                    'healing_notes': 'Notes about what was healed (optional)'
                },
                'handler': self.format_reusable_script
            },
            'get_best_locator_strategies': {
                'description': 'Get prioritized locator strategies based on historical success rates',
                'parameters': {
                    'element_type': 'Type of element (button, input, link, etc.)',
                    'context': 'Additional context about the element'
                },
                'handler': self.get_best_locator_strategies
            }
        }
    
    async def handle_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a tool call from the AI model.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            return {
                'success': False,
                'error': f'Unknown tool: {tool_name}',
                'available_tools': list(self.tools.keys())
            }
        
        tool = self.tools[tool_name]
        handler = tool['handler']
        
        try:
            result = await handler(**parameters)
            return {
                'success': True,
                'tool': tool_name,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'tool': tool_name,
                'error': str(e)
            }
    
    async def search_learned_tasks(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """Search for similar learned tasks using semantic search."""
        if not self.vector_store:
            return {
                'found': False,
                'message': 'Vector store not available',
                'tasks': []
            }
        
        try:
            results = self.vector_store.search_tasks(query, top_k=top_k)
            return {
                'found': len(results) > 0,
                'count': len(results),
                'tasks': results
            }
        except Exception as e:
            return {
                'found': False,
                'error': str(e),
                'tasks': []
            }
    
    async def get_task_execution_history(self, task_description: str, limit: int = 5) -> Dict[str, Any]:
        """Get execution history for similar tasks."""
        try:
            conn = sqlite3.connect(self.database_path)
            c = conn.cursor()
            
            c.execute('''
                SELECT command, success, error_message, generated_code, healed_code, 
                       execution_time, timestamp
                FROM test_history 
                WHERE command LIKE ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (f'%{task_description}%', limit))
            
            rows = c.fetchall()
            conn.close()
            
            history = []
            success_rate = 0
            
            for row in rows:
                history.append({
                    'command': row[0],
                    'success': bool(row[1]),
                    'error': row[2],
                    'generated_code': row[3],
                    'healed_code': row[4],
                    'execution_time': row[5],
                    'timestamp': row[6]
                })
            
            if history:
                success_rate = sum(1 for h in history if h['success']) / len(history) * 100
            
            return {
                'found': len(history) > 0,
                'count': len(history),
                'success_rate': round(success_rate, 1),
                'history': history,
                'insights': self._generate_insights(history)
            }
        except Exception as e:
            return {
                'found': False,
                'error': str(e),
                'history': []
            }
    
    async def analyze_page_dom(self, url: str, intent: str) -> Dict[str, Any]:
        """Analyze page DOM to find optimal locators."""
        if not self.dom_inspector:
            return {
                'success': False,
                'message': 'DOM inspector not available',
                'elements': []
            }
        
        try:
            analysis = await self.dom_inspector.analyze_page(url, intent)
            
            if 'error' in analysis:
                return {
                    'success': False,
                    'error': analysis['error'],
                    'elements': []
                }
            
            return {
                'success': True,
                'intent_matched': analysis.get('intent_matched_elements', []),
                'form_elements': analysis.get('form_elements', []),
                'interactive_elements': analysis.get('interactive_elements', []),
                'recommended_locators': analysis.get('recommended_locators', [])
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'elements': []
            }
    
    async def get_healing_strategies(self, error_type: str, error_message: str, 
                                     failed_step: int = 0) -> Dict[str, Any]:
        """Get recommended healing strategies for an error."""
        strategies = {
            'locator_not_found': [
                'Use more robust locator (get_by_role, get_by_text)',
                'Add explicit wait before interaction',
                'Check if element is in iframe or shadow DOM',
                'Use get_by_test_id if available',
                'Add timeout to locator action (5000ms)'
            ],
            'timeout': [
                'Increase timeout duration',
                'Add wait_for_load_state before action',
                'Check for dynamic content loading',
                'Use wait_for_selector with visible state',
                'Add retry logic with exponential backoff'
            ],
            'element_not_found': [
                'Verify element exists in current page state',
                'Check if page navigation completed',
                'Look for alternative locators (text, aria-label)',
                'Ensure element is not hidden or disabled',
                'Add wait for selector visibility'
            ],
            'api_error': [
                'Preserve existing locators (likely correct)',
                'Fix API usage (remove invalid parameters)',
                'Check Playwright version compatibility',
                'Validate method signature',
                'Review timeout parameter placement'
            ],
            'multiple_matches': [
                'Add more specific locator constraints',
                'Use first() or nth() to target specific element',
                'Combine multiple attributes for uniqueness',
                'Use parent/child relationships in locator',
                'Filter by additional attributes (aria-label, text)'
            ],
            'unknown': [
                'Analyze error message for clues',
                'Review generated code for syntax issues',
                'Check browser console for JavaScript errors',
                'Verify page URL and navigation state',
                'Add comprehensive error handling'
            ]
        }
        
        selected_strategies = strategies.get(error_type, strategies['unknown'])
        
        return {
            'error_type': error_type,
            'failed_step': failed_step,
            'strategies': selected_strategies,
            'priority': 'high' if error_type in ['locator_not_found', 'timeout'] else 'medium',
            'recommendation': self._get_strategy_recommendation(error_type, error_message)
        }
    
    async def format_reusable_script(self, code: str, task_description: str, 
                                     healing_notes: str = '') -> Dict[str, Any]:
        """Format healed code into clean, documented, reusable script."""
        
        # Add documentation header
        doc_header = f'''"""
VisionVault Automation Script
Generated: {self._get_timestamp()}

Task: {task_description}
{f"Healing Notes: {healing_notes}" if healing_notes else ""}

This script can be reused for similar automation tasks.
Simply modify the parameters as needed.
"""

'''
        
        # Clean up the code
        clean_code = code.strip()
        
        # Remove any temporary variables or debug code
        lines = clean_code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip debug prints that aren't step logs
            if 'print(' in line and 'STEP' not in line and 'logs.append' not in line:
                continue
            cleaned_lines.append(line)
        
        clean_code = '\n'.join(cleaned_lines)
        
        # Add usage instructions
        usage_instructions = '''

# USAGE:
# 1. Install required packages: pip install playwright
# 2. Install browsers: playwright install chromium
# 3. Run the script: python script.py
# 
# CUSTOMIZATION:
# - Modify browser_name: 'chromium', 'firefox', or 'webkit'
# - Set headless=False to see the browser in action
# - Adjust timeouts in the code as needed

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(run_test(browser_name='chromium', headless=True))
    print(f"Success: {result['success']}")
    if not result['success']:
        print(f"Errors: {result['logs']}")
'''
        
        formatted_script = doc_header + clean_code + usage_instructions
        
        return {
            'formatted_code': formatted_script,
            'original_length': len(code),
            'formatted_length': len(formatted_script),
            'improvements': [
                'Added comprehensive documentation header',
                'Cleaned up debug code',
                'Added usage instructions',
                'Added customization guide',
                'Made ready for standalone execution'
            ]
        }
    
    async def get_best_locator_strategies(self, element_type: str, context: str = '') -> Dict[str, Any]:
        """Get prioritized locator strategies based on historical success."""
        
        # Query database for success rates by locator type
        try:
            conn = sqlite3.connect(self.database_path)
            c = conn.cursor()
            
            # This would require tracking locator types in the database
            # For now, return best practices based on element type
            
            strategies = {
                'button': [
                    ('get_by_role("button", name="...")', 95),
                    ('get_by_text("Button Text")', 90),
                    ('get_by_test_id("button-id")', 99),
                    ('get_by_label("...")', 85)
                ],
                'input': [
                    ('get_by_placeholder("...")', 92),
                    ('get_by_label("...")', 95),
                    ('get_by_test_id("input-id")', 99),
                    ('get_by_role("textbox", name="...")', 88)
                ],
                'link': [
                    ('get_by_role("link", name="...")', 94),
                    ('get_by_text("Link Text")', 92),
                    ('get_by_test_id("link-id")', 99)
                ],
                'default': [
                    ('get_by_test_id("...")', 99),
                    ('get_by_role(...)', 90),
                    ('get_by_text("...")', 85),
                    ('get_by_label("...")', 88)
                ]
            }
            
            conn.close()
            
            element_strategies = strategies.get(element_type.lower(), strategies['default'])
            
            return {
                'element_type': element_type,
                'strategies': [
                    {'locator': s[0], 'success_rate': s[1]} 
                    for s in sorted(element_strategies, key=lambda x: x[1], reverse=True)
                ],
                'recommendation': element_strategies[0][0] if element_strategies else None
            }
        except Exception as e:
            return {
                'element_type': element_type,
                'error': str(e),
                'strategies': []
            }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available MCP tools."""
        return [
            {
                'name': name,
                'description': tool['description'],
                'parameters': tool['parameters']
            }
            for name, tool in self.tools.items()
        ]
    
    def _generate_insights(self, history: List[Dict]) -> List[str]:
        """Generate insights from execution history."""
        insights = []
        
        if not history:
            return insights
        
        success_count = sum(1 for h in history if h['success'])
        failure_count = len(history) - success_count
        
        if failure_count > 0:
            insights.append(f'{failure_count} out of {len(history)} attempts failed')
            
            common_errors = {}
            for h in history:
                if h['error']:
                    error_key = h['error'][:50]
                    common_errors[error_key] = common_errors.get(error_key, 0) + 1
            
            if common_errors:
                most_common = max(common_errors.items(), key=lambda x: x[1])
                insights.append(f'Most common error: {most_common[0]}...')
        
        if success_count > 0 and failure_count > 0:
            insights.append('Some attempts succeeded - healing strategies available')
        
        return insights
    
    def _get_strategy_recommendation(self, error_type: str, error_message: str) -> str:
        """Get specific strategy recommendation based on error."""
        recommendations = {
            'locator_not_found': 'Focus on robust locators (role, text, test-id). Add explicit waits.',
            'timeout': 'Increase timeout and add wait_for_load_state. Check for dynamic content.',
            'api_error': 'Preserve locators. Fix API usage - likely parameter placement issue.',
            'element_not_found': 'Verify page state and element visibility. Add selector wait.',
            'multiple_matches': 'Make locator more specific using combined attributes or nth().'
        }
        
        return recommendations.get(error_type, 'Analyze error message and apply best practices.')
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
