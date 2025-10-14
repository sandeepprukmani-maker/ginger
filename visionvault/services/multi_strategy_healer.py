"""
Multi-Strategy Parallel Healing

This module implements advanced healing that:
1. Generates multiple fix strategies simultaneously
2. Tests all strategies in parallel
3. Automatically selects the best working solution
4. Learns from successful strategies for future use
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
import json
import os


class MultiStrategyHealer:
    """Advanced healing with parallel strategy execution"""
    
    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.client = openai_client
        self.strategy_success_history = self._load_history()
    
    def _load_history(self) -> Dict:
        """Load history of successful strategies"""
        history_file = 'data/strategy_history.json'
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_history(self):
        """Save strategy success history"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/strategy_history.json', 'w') as f:
                json.dump(self.strategy_success_history, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save strategy history: {e}")
    
    def generate_multiple_strategies(
        self,
        failed_code: str,
        error_message: str,
        failed_step: int,
        page_content: str = ''
    ) -> List[Dict]:
        """
        Generate multiple different healing strategies in parallel.
        Each strategy uses a different approach to fix the same issue.
        """
        if not self.client:
            return self._generate_fallback_strategies(failed_code, error_message)
        
        try:
            # Identify the type of failure
            failure_type = self._classify_error(error_message)
            
            # Generate multiple strategies using GPT-4o
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": """You are an expert at generating MULTIPLE different strategies to fix automation failures.

Your task: Generate 3-4 DIFFERENT approaches to fix the same issue. Each strategy should use a fundamentally different technique.

STRATEGY TYPES TO CONSIDER:

1. LOCATOR-BASED STRATEGY
   - Use different locator types (role, text, placeholder, label, CSS, XPath)
   - Try multiple selectors for redundancy
   - Use chained locators or filters

2. TIMING-BASED STRATEGY
   - Add longer waits and timeouts
   - Wait for specific states (load, networkidle, visible, attached)
   - Add delays before interactions
   - Wait for animations to complete

3. NAVIGATION-BASED STRATEGY
   - Scroll element into view
   - Handle overlays/modals first
   - Navigate through page differently
   - Use keyboard navigation instead of clicks

4. ROBUST-APPROACH STRATEGY
   - Try multiple locators with fallback logic
   - Add retry loops with exponential backoff
   - Check element state before interaction
   - Handle dynamic content explicitly

For each strategy, provide:
1. Strategy name and type
2. Confidence score (0-100)
3. Complete fixed code for the failed step
4. Explanation of why this approach should work

Return as JSON array:
[
  {
    "name": "Strategy name",
    "type": "locator/timing/navigation/robust",
    "confidence": 85,
    "code": "Fixed code here",
    "explanation": "Why this works"
  }
]

Generate 3-4 diverse strategies that attack the problem from different angles."""},
                    {"role": "user", "content": f"""Failed automation needs multiple fix strategies:

FAILED STEP {failed_step}:
```python
{self._extract_failed_step_code(failed_code, failed_step)}
```

ERROR:
{error_message}

PAGE CONTEXT:
{page_content[:1000] if page_content else 'Not available'}

Generate 3-4 different strategies to fix this issue."""}
                ],
                temperature=0.4,  # Slightly higher for diversity
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content.strip()
            strategies_data = json.loads(result)
            
            # Extract strategies array (handle both array and object responses)
            if isinstance(strategies_data, dict) and 'strategies' in strategies_data:
                strategies = strategies_data['strategies']
            elif isinstance(strategies_data, list):
                strategies = strategies_data
            else:
                strategies = [strategies_data]
            
            # Sort by confidence
            strategies.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            print(f"\n🎯 Generated {len(strategies)} healing strategies:")
            for i, strat in enumerate(strategies, 1):
                print(f"   {i}. {strat.get('name', 'Strategy')} ({strat.get('type', 'unknown')}) - Confidence: {strat.get('confidence', 0)}%")
            
            return strategies
        
        except Exception as e:
            print(f"⚠️  Multi-strategy generation error: {e}")
            return self._generate_fallback_strategies(failed_code, error_message)
    
    def _classify_error(self, error_message: str) -> str:
        """Classify the type of error"""
        error_lower = error_message.lower()
        
        if 'timeout' in error_lower or 'timed out' in error_lower:
            return 'timeout'
        elif 'not found' in error_lower or 'no element' in error_lower:
            return 'element_not_found'
        elif 'not visible' in error_lower or 'not attached' in error_lower:
            return 'visibility'
        elif 'not clickable' in error_lower or 'intercept' in error_lower:
            return 'not_clickable'
        else:
            return 'unknown'
    
    def _extract_failed_step_code(self, code: str, step_num: int) -> str:
        """Extract just the failed step code"""
        lines = code.split('\n')
        step_lines = []
        in_step = False
        
        for line in lines:
            if f'STEP {step_num}:' in line or f'Step {step_num}:' in line:
                in_step = True
            elif in_step and ('STEP' in line or 'Step' in line) and str(step_num) not in line:
                break
            
            if in_step:
                step_lines.append(line)
        
        return '\n'.join(step_lines) if step_lines else code[:500]
    
    def _generate_fallback_strategies(self, failed_code: str, error_message: str) -> List[Dict]:
        """Generate basic strategies without AI"""
        return [
            {
                'name': 'Extended Timeout',
                'type': 'timing',
                'confidence': 60,
                'code': 'await element.click(timeout=15000)',
                'explanation': 'Increase timeout to handle slow loading'
            },
            {
                'name': 'Wait for Visible',
                'type': 'timing',
                'confidence': 55,
                'code': 'await element.wait_for(state="visible", timeout=10000)\nawait element.click()',
                'explanation': 'Explicitly wait for element visibility'
            },
            {
                'name': 'Scroll Into View',
                'type': 'navigation',
                'confidence': 50,
                'code': 'await element.scroll_into_view_if_needed()\nawait element.click()',
                'explanation': 'Ensure element is in viewport'
            }
        ]
    
    async def test_strategy(
        self,
        strategy: Dict,
        full_code: str,
        failed_step: int,
        executor_function
    ) -> Tuple[bool, Dict, str]:
        """
        Test a single strategy by executing it.
        Returns: (success, result, strategy_name)
        """
        strategy_name = strategy.get('name', 'Unknown')
        
        try:
            print(f"   🧪 Testing: {strategy_name}...")
            
            # Apply the strategy to the code
            healed_code = self._apply_strategy(full_code, failed_step, strategy)
            
            # Execute the healed code
            result = await executor_function(healed_code)
            
            success = result.get('success', False)
            
            if success:
                print(f"   ✅ {strategy_name} SUCCEEDED!")
                # Record success
                self._record_success(strategy)
            else:
                print(f"   ❌ {strategy_name} failed")
            
            return (success, result, strategy_name)
        
        except Exception as e:
            print(f"   ❌ {strategy_name} error: {e}")
            return (False, {'success': False, 'error': str(e)}, strategy_name)
    
    def _apply_strategy(self, full_code: str, failed_step: int, strategy: Dict) -> str:
        """Apply a strategy to the code"""
        # Find and replace the failed step with the strategy's code
        lines = full_code.split('\n')
        new_lines = []
        in_failed_step = False
        step_replaced = False
        
        for line in lines:
            # Check if we're at the failed step
            if f'STEP {failed_step}:' in line or f'Step {failed_step}:' in line:
                in_failed_step = True
                new_lines.append(line)  # Keep the comment
                # Add the strategy code
                strategy_code = strategy.get('code', '')
                for strategy_line in strategy_code.split('\n'):
                    new_lines.append(' ' * 12 + strategy_line)  # Proper indentation
                step_replaced = True
                continue
            
            # Skip original failed step code
            if in_failed_step:
                # Check if we've moved to next step
                if ('STEP' in line or 'Step' in line) and str(failed_step) not in line:
                    in_failed_step = False
                    new_lines.append(line)
                elif not line.strip().startswith('#'):
                    # Skip the original failed code
                    continue
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        if not step_replaced:
            # Fallback: just append strategy at the end
            return full_code + '\n' + strategy.get('code', '')
        
        return '\n'.join(new_lines)
    
    def _record_success(self, strategy: Dict):
        """Record a successful strategy"""
        strategy_type = strategy.get('type', 'unknown')
        
        if strategy_type not in self.strategy_success_history:
            self.strategy_success_history[strategy_type] = {
                'total_attempts': 0,
                'successes': 0,
                'success_rate': 0.0
            }
        
        self.strategy_success_history[strategy_type]['total_attempts'] += 1
        self.strategy_success_history[strategy_type]['successes'] += 1
        self.strategy_success_history[strategy_type]['success_rate'] = (
            self.strategy_success_history[strategy_type]['successes'] /
            self.strategy_success_history[strategy_type]['total_attempts'] * 100
        )
        
        self._save_history()
    
    async def heal_with_parallel_strategies(
        self,
        failed_code: str,
        error_message: str,
        failed_step: int,
        page_content: str,
        executor_function
    ) -> Dict:
        """
        Main healing function: Generate and test multiple strategies in parallel.
        Returns the best working solution.
        """
        print(f"\n🚀 Multi-Strategy Parallel Healing...")
        
        # Generate multiple strategies
        strategies = self.generate_multiple_strategies(
            failed_code,
            error_message,
            failed_step,
            page_content
        )
        
        if not strategies:
            return {
                'success': False,
                'error': 'No strategies generated'
            }
        
        # Test strategies in parallel
        print(f"\n🧪 Testing {len(strategies)} strategies in parallel...")
        
        tasks = [
            self.test_strategy(strategy, failed_code, failed_step, executor_function)
            for strategy in strategies
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Find the first successful strategy
        for success, result, strategy_name in results:
            if isinstance((success, result, strategy_name), Exception):
                continue
            
            if success:
                print(f"\n✅ SUCCESS! {strategy_name} worked!")
                return {
                    'success': True,
                    'healed_code': result.get('healed_code'),
                    'strategy_used': strategy_name,
                    'result': result
                }
        
        # If no strategy worked, return the result from the highest confidence strategy
        print(f"\n❌ All strategies failed. Using highest confidence attempt.")
        if results and not isinstance(results[0], Exception):
            _, result, strategy_name = results[0]
            return {
                'success': False,
                'attempted_strategies': len(strategies),
                'best_strategy': strategy_name,
                'result': result
            }
        
        return {
            'success': False,
            'error': 'All strategies failed'
        }
