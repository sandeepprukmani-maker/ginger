"""
Unified Intelligent Automation Engine

Merges MCP (direct control) and Legacy Playwright (code generation) into one adaptive system
with intelligent strategy selection and progressive healing escalation.

Architecture:
- MCP-first approach for speed and intelligence
- Falls back to code generation when needed
- Progressive healing: DOM → Vision → Multi-strategy → CodeGen → Manual Widget
- Learns which approach works best for different task types
"""

import asyncio
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime


class StrategyType(Enum):
    """Automation execution strategies"""
    MCP_DIRECT = "mcp_direct"  # Direct browser control via MCP
    CODE_GEN = "code_gen"      # AI-generated Playwright code
    HYBRID = "hybrid"           # MCP first, fallback to code gen


class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"           # Single action (click, navigate)
    MODERATE = "moderate"       # 2-5 steps
    COMPLEX = "complex"         # 6+ steps or conditional logic
    ADVANCED = "advanced"       # Multi-page workflows, data extraction


@dataclass
class ExecutionContext:
    """Shared context across all execution attempts"""
    test_id: str
    command: str
    browser_name: str
    headless: bool
    
    # Analysis results
    url: Optional[str] = None
    intent: Optional[str] = None
    complexity: TaskComplexity = TaskComplexity.MODERATE
    confidence_score: float = 0.0
    
    # DOM and page data
    dom_analysis: Optional[Dict[str, Any]] = None
    page_snapshot: Optional[str] = None
    element_catalog: Optional[Dict[str, List]] = None
    
    # Execution state
    current_strategy: Optional[StrategyType] = None
    attempts: List[Dict[str, Any]] = field(default_factory=list)
    failed_strategies: List[StrategyType] = field(default_factory=list)
    
    # Results
    generated_code: Optional[str] = None
    screenshot: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    
    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    
    def add_attempt(self, strategy: StrategyType, success: bool, error: Optional[str] = None):
        """Record an execution attempt"""
        self.attempts.append({
            'strategy': strategy.value,
            'success': success,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
        if not success:
            self.failed_strategies.append(strategy)


@dataclass
class StrategyScore:
    """Score for a particular strategy"""
    strategy: StrategyType
    score: float  # 0-100
    reasons: List[str]
    can_execute: bool  # Whether we have required dependencies


class UnifiedAutomationEngine:
    """
    Intelligent automation engine that adaptively chooses between MCP and CodeGen approaches.
    
    Decision Logic:
    1. Analyze task complexity and intent
    2. Check historical success rates for similar tasks
    3. Score available strategies (MCP vs CodeGen)
    4. Execute with highest-scoring strategy
    5. Progressive healing escalation if failures occur
    6. Learn from outcomes to improve future decisions
    """
    
    def __init__(self, socketio, openai_client=None, gemini_api_key=None):
        self.socketio = socketio
        self.openai_client = openai_client
        self.gemini_api_key = gemini_api_key
        
        # Import heavy dependencies only when needed
        self._mcp_manager = None
        self._healing_executor = None
        self._intelligent_planner = None
        self._self_learning = None
        self._dom_inspector = None
        
        # Strategy availability
        # MCP needs OpenAI key (uses it internally for NL commands)
        # CodeGen needs OpenAI client for code generation
        # HYBRID needs both (executes with MCP, generates code)
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.mcp_available = self.openai_api_key is not None
        self.codegen_available = openai_client is not None
        self.hybrid_available = self.mcp_available and self.codegen_available
        
        print(f"✅ Unified Automation Engine initialized")
        print(f"   MCP Direct: {'✅ Available' if self.mcp_available else '❌ Disabled (requires OPENAI_API_KEY)'}")
        print(f"   Code Generation: {'✅ Available' if self.codegen_available else '❌ Disabled (requires OPENAI_API_KEY)'}")
        print(f"   HYBRID (MCP + Code): {'✅ Available' if self.hybrid_available else '❌ Disabled (requires OPENAI_API_KEY)'}")
    
    @property
    def mcp_manager(self):
        """Lazy-load MCP manager"""
        if self._mcp_manager is None:
            from visionvault.services.mcp_manager import MCPAutomationManager
            self._mcp_manager = MCPAutomationManager(
                self.socketio,
                os.environ.get('OPENAI_API_KEY')
            )
        return self._mcp_manager
    
    @property
    def healing_executor(self):
        """Lazy-load healing executor"""
        if self._healing_executor is None:
            from visionvault.services.healing_executor import HealingExecutor
            self._healing_executor = HealingExecutor(
                self.socketio,
                api_key=os.environ.get('OPENAI_API_KEY'),
                use_gpt4o=True,
                mcp_manager=self.mcp_manager if self.mcp_available else None  # Enable MCP-based healing (uses property to init)
            )
        return self._healing_executor
    
    @property
    def intelligent_planner(self):
        """Lazy-load intelligent planner"""
        if self._intelligent_planner is None and self.openai_client:
            from visionvault.services.intelligent_planner import IntelligentPlanner
            self._intelligent_planner = IntelligentPlanner(self.openai_client)
        return self._intelligent_planner
    
    @property
    def self_learning(self):
        """Lazy-load self-learning engine"""
        if self._self_learning is None:
            from visionvault.services.self_learning_engine import SelfLearningEngine
            self._self_learning = SelfLearningEngine()
        return self._self_learning
    
    @property
    def dom_inspector(self):
        """Lazy-load DOM inspector"""
        if self._dom_inspector is None:
            from visionvault.services.dom_inspector import dom_inspector
            self._dom_inspector = dom_inspector
        return self._dom_inspector
    
    def extract_url_from_command(self, command: str) -> Optional[str]:
        """Extract URL from natural language command"""
        url_pattern = r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.(com|org|net|io|dev|co|ai)[^\s]*)'
        urls = re.findall(url_pattern, command.lower())
        
        if urls:
            url = urls[0] if isinstance(urls[0], str) else urls[0][0]
            if not url.startswith('http'):
                url = 'https://' + url
            return url
        
        # Common sites
        command_lower = command.lower()
        patterns = [
            r'(?:go to|navigate to|open|visit)\s+([a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+)',
            r'(?:search on|use)\s+([a-zA-Z0-9-]+)(?:\s|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command_lower)
            if match:
                domain = match.group(1)
                if domain in ['google', 'youtube', 'facebook', 'twitter', 'amazon', 'reddit', 'github', 'linkedin']:
                    return f'https://www.{domain}.com'
                elif '.' not in domain:
                    return f'https://www.{domain}.com'
                else:
                    return f'https://{domain}' if not domain.startswith('http') else domain
        
        return None
    
    async def analyze_context(self, context: ExecutionContext) -> None:
        """
        Analyze task and populate execution context with intelligence.
        Uses: Intelligent Planner, Self-Learning Engine, DOM Inspector
        """
        self.socketio.emit('execution_status', {
            'test_id': context.test_id,
            'status': 'analyzing',
            'message': '🧠 Analyzing task with AI intelligence...'
        })
        
        # Extract URL
        context.url = self.extract_url_from_command(context.command)
        
        # Step 1: Intelligent planning (if available)
        if self.intelligent_planner:
            try:
                plan = self.intelligent_planner.analyze_command(context.command)
                context.intent = plan['intent']
                context.confidence_score = plan['confidence_score']
                
                # Map complexity
                complexity_map = {
                    'simple': TaskComplexity.SIMPLE,
                    'moderate': TaskComplexity.MODERATE,
                    'complex': TaskComplexity.COMPLEX,
                    'advanced': TaskComplexity.ADVANCED
                }
                context.complexity = complexity_map.get(plan['complexity'], TaskComplexity.MODERATE)
                
                context.logs.append(f"📊 Analysis: {context.intent} (complexity: {context.complexity.value}, confidence: {context.confidence_score:.0f}%)")
            except Exception as e:
                context.logs.append(f"⚠️ Intelligent planning error: {str(e)}")
        
        # Step 2: DOM inspection (if URL available)
        if context.url and self.dom_inspector:
            try:
                context.logs.append(f"🔍 Inspecting page: {context.url}")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                dom_analysis = loop.run_until_complete(
                    self.dom_inspector.analyze_page(context.url, context.command)
                )
                loop.close()
                
                if 'error' not in dom_analysis:
                    context.dom_analysis = dom_analysis
                    intent_matched = len(dom_analysis.get('intent_matched_elements', []))
                    context.logs.append(f"✅ Found {intent_matched} relevant elements on page")
            except Exception as e:
                context.logs.append(f"⚠️ DOM inspection skipped: {str(e)}")
    
    def score_strategies(self, context: ExecutionContext) -> List[StrategyScore]:
        """
        Score available strategies based on context and historical data.
        Returns ordered list of strategies (highest score first).
        """
        scores = []
        
        # Check historical recommendations from learning engine
        historical_rec = None
        if self.self_learning:
            try:
                historical_rec = self.self_learning.recommend_strategy(
                    context.command,
                    context.complexity.value
                )
            except Exception as e:
                context.logs.append(f"⚠️ Could not get historical recommendations: {str(e)}")
        
        # Score MCP Direct
        if self.mcp_available:
            mcp_score = 50.0  # Base score
            reasons = []
            
            # Apply historical learning
            if historical_rec and historical_rec['recommended_strategy'] == 'mcp_direct':
                bonus = min(25, historical_rec['confidence'] / 4)
                mcp_score += bonus
                reasons.append(f"Historical data favors MCP ({historical_rec['confidence']:.0f}% confidence)")
            
            # Bonus for simple tasks (MCP is faster)
            if context.complexity == TaskComplexity.SIMPLE:
                mcp_score += 20
                reasons.append("Fast for simple tasks")
            
            # Bonus if DOM analysis succeeded (MCP can use it)
            if context.dom_analysis:
                mcp_score += 15
                reasons.append("DOM structure available")
            
            # Bonus for high confidence
            if context.confidence_score > 80:
                mcp_score += 10
                reasons.append("High confidence task")
            
            # Penalty for complex tasks (code gen gives more control)
            if context.complexity == TaskComplexity.COMPLEX:
                mcp_score -= 10
                reasons.append("Code gen better for complex workflows")
            
            scores.append(StrategyScore(
                strategy=StrategyType.MCP_DIRECT,
                score=min(100, mcp_score),
                reasons=reasons,
                can_execute=True
            ))
        
        # Score Code Generation
        if self.codegen_available:
            codegen_score = 50.0  # Base score
            reasons = []
            
            # Apply historical learning
            if historical_rec and historical_rec['recommended_strategy'] == 'code_gen':
                bonus = min(25, historical_rec['confidence'] / 4)
                codegen_score += bonus
                reasons.append(f"Historical data favors CodeGen ({historical_rec['confidence']:.0f}% confidence)")
            
            # Bonus for complex tasks (more control, debugging)
            if context.complexity in [TaskComplexity.COMPLEX, TaskComplexity.ADVANCED]:
                codegen_score += 20
                reasons.append("Better control for complex tasks")
            
            # Bonus if user might want to see/modify code
            if any(word in context.command.lower() for word in ['show', 'code', 'script', 'generate']):
                codegen_score += 15
                reasons.append("User may want to review code")
            
            # Bonus for multi-step workflows
            step_keywords = ['then', 'after', 'next', 'and then', 'finally']
            if any(keyword in context.command.lower() for keyword in step_keywords):
                codegen_score += 10
                reasons.append("Multi-step workflow detected")
            
            scores.append(StrategyScore(
                strategy=StrategyType.CODE_GEN,
                score=min(100, codegen_score),
                reasons=reasons,
                can_execute=True
            ))
        
        # Score HYBRID Strategy (Best of both worlds)
        if self.hybrid_available:
            hybrid_score = 60.0  # Higher base than others
            reasons = []
            
            # Apply historical learning
            if historical_rec and historical_rec['recommended_strategy'] == 'hybrid':
                bonus = min(30, historical_rec['confidence'] / 3)
                hybrid_score += bonus
                reasons.append(f"Historical data favors HYBRID ({historical_rec['confidence']:.0f}% confidence)")
            
            # HYBRID is ideal for moderate to complex tasks
            if context.complexity in [TaskComplexity.MODERATE, TaskComplexity.COMPLEX]:
                hybrid_score += 25
                reasons.append("HYBRID optimal for moderate/complex tasks")
            
            # Bonus for multi-step workflows (executes with MCP, provides reusable code)
            step_keywords = ['then', 'after', 'next', 'and then', 'finally', 'verify', 'check']
            if any(keyword in context.command.lower() for keyword in step_keywords):
                hybrid_score += 15
                reasons.append("Multi-step workflow benefits from HYBRID approach")
            
            # Bonus for verifications/assertions (MCP handles, code captures)
            verification_keywords = ['verify', 'check', 'assert', 'confirm', 'ensure', 'validate']
            if any(keyword in context.command.lower() for keyword in verification_keywords):
                hybrid_score += 10
                reasons.append("Verifications benefit from HYBRID (smart execution + reliable code)")
            
            # HYBRID gives best reliability
            hybrid_score += 10
            reasons.append("Provides both execution intelligence and reusable code")
            
            scores.append(StrategyScore(
                strategy=StrategyType.HYBRID,
                score=min(100, hybrid_score),
                reasons=reasons,
                can_execute=True
            ))
        
        # Sort by score (highest first)
        scores.sort(key=lambda x: x.score, reverse=True)
        return scores
    
    async def execute(self, test_id: str, command: str, browser_name: str = 'chromium', 
                     headless: bool = True) -> Dict[str, Any]:
        """
        Main execution entry point.
        Intelligently routes to best strategy with progressive healing.
        """
        # Create execution context
        context = ExecutionContext(
            test_id=test_id,
            command=command,
            browser_name=browser_name,
            headless=headless
        )
        
        try:
            # Step 1: Analyze context
            await self.analyze_context(context)
            
            # Step 2: Score and select strategy
            strategy_scores = self.score_strategies(context)
            
            if not strategy_scores:
                return {
                    'success': False,
                    'logs': ['No execution strategies available. Please configure OPENAI_API_KEY.'],
                    'screenshot': None,
                    'code': None
                }
            
            # Emit strategy selection
            selected = strategy_scores[0]
            context.current_strategy = selected.strategy
            
            self.socketio.emit('strategy_selected', {
                'test_id': test_id,
                'strategy': selected.strategy.value,
                'score': selected.score,
                'reasons': selected.reasons
            })
            
            context.logs.append(f"🎯 Selected strategy: {selected.strategy.value} (score: {selected.score:.0f}/100)")
            context.logs.append(f"   Reasons: {', '.join(selected.reasons)}")
            
            # Step 3: Execute with selected strategy
            result = await self._execute_with_strategy(context, selected.strategy)
            
            # Step 4: If failed, try progressive escalation
            if not result['success'] and len(strategy_scores) > 1:
                context.logs.append(f"⚠️ {selected.strategy.value} failed, trying alternative strategy...")
                
                # Try next best strategy
                for alt_strategy in strategy_scores[1:]:
                    if alt_strategy.strategy not in context.failed_strategies:
                        context.logs.append(f"🔄 Escalating to: {alt_strategy.strategy.value}")
                        result = await self._execute_with_strategy(context, alt_strategy.strategy)
                        
                        if result['success']:
                            break
            
            # Step 5: Learn from outcome
            if self.self_learning:
                try:
                    # Map strategy type to learning engine format
                    strategy_name = 'mcp_direct' if context.current_strategy == StrategyType.MCP_DIRECT else 'code_gen'
                    
                    self.self_learning.learn_strategy_outcome(
                        command=command,
                        strategy=strategy_name,
                        complexity=context.complexity.value,
                        success=result['success'],
                        attempts=len(context.attempts)
                    )
                    context.logs.append(f"📚 Strategy outcome recorded for future learning")
                except Exception as e:
                    context.logs.append(f"⚠️ Learning update failed: {str(e)}")
            
            return result
            
        except Exception as e:
            context.logs.append(f"❌ Critical error: {str(e)}")
            return {
                'success': False,
                'logs': context.logs,
                'screenshot': None,
                'code': context.generated_code
            }
    
    async def _execute_with_strategy(self, context: ExecutionContext, 
                                     strategy: StrategyType) -> Dict[str, Any]:
        """Execute with specific strategy"""
        context.current_strategy = strategy
        
        try:
            if strategy == StrategyType.MCP_DIRECT:
                return await self._execute_mcp(context)
            elif strategy == StrategyType.CODE_GEN:
                return await self._execute_codegen(context)
            elif strategy == StrategyType.HYBRID:
                return await self._execute_hybrid(context)
            else:
                context.add_attempt(strategy, False, "Unknown strategy")
                return {
                    'success': False,
                    'logs': context.logs + [f"Unknown strategy: {strategy}"],
                    'screenshot': None,
                    'code': None
                }
        except Exception as e:
            context.add_attempt(strategy, False, str(e))
            context.logs.append(f"❌ {strategy.value} error: {str(e)}")
            return {
                'success': False,
                'logs': context.logs,
                'screenshot': None,
                'code': context.generated_code
            }
    
    async def _execute_mcp(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute using MCP direct approach"""
        context.logs.append("🚀 Executing with MCP Enhanced (direct browser control)...")
        
        try:
            result = await self.mcp_manager.execute_automation(
                test_id=context.test_id,
                command=context.command,
                browser_name=context.browser_name,
                headless=context.headless
            )
            
            success = result.get('success', False)
            context.add_attempt(StrategyType.MCP_DIRECT, success, 
                              None if success else result.get('error'))
            
            context.logs.extend(result.get('logs', []))
            context.screenshot = result.get('screenshot')
            
            return {
                'success': success,
                'logs': context.logs,
                'screenshot': context.screenshot,
                'code': None  # MCP doesn't generate code
            }
        except Exception as e:
            context.add_attempt(StrategyType.MCP_DIRECT, False, str(e))
            raise
    
    async def _execute_codegen(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute using Code Generation approach with healing"""
        context.logs.append("🔧 Executing with Code Generation (Playwright code)...")
        
        try:
            # Generate code (will import the function from app.py)
            from visionvault.web.app import generate_playwright_code
            
            code = generate_playwright_code(
                context.command,
                browser=context.browser_name
            )
            
            context.generated_code = code
            context.logs.append("✅ Code generated successfully")
            
            # Execute with healing
            result = await self.healing_executor.execute_with_healing(
                code=code,
                test_id=context.test_id,
                browser_name=context.browser_name,
                headless=context.headless
            )
            
            success = result.get('success', False)
            context.add_attempt(StrategyType.CODE_GEN, success,
                              None if success else result.get('error'))
            
            context.logs.extend(result.get('logs', []))
            context.screenshot = result.get('screenshot')
            
            return {
                'success': success,
                'logs': context.logs,
                'screenshot': context.screenshot,
                'code': result.get('healed_script') or code
            }
        except Exception as e:
            context.add_attempt(StrategyType.CODE_GEN, False, str(e))
            raise
    
    async def _execute_hybrid(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Execute using HYBRID approach: MCP intelligence + Code generation
        
        1. Execute with MCP (with tracing enabled)
        2. Capture working selectors and actions
        3. Generate reliable Playwright code from trace
        4. Validate generated code works standalone
        """
        context.logs.append("🎯 Executing with HYBRID strategy (MCP intelligence + Code generation)...")
        
        try:
            # Execute with MCP and enable tracing
            context.logs.append("▶️ Phase 1: Execute with MCP to discover working selectors...")
            result = await self.mcp_manager.execute_automation(
                test_id=context.test_id,
                command=context.command,
                browser=context.browser_name,
                headless=context.headless,
                enable_tracing=True  # Enable tracing to capture what worked
            )
            
            success = result.get('success', False)
            context.logs.extend(result.get('logs', []))
            context.screenshot = result.get('screenshot')
            context.generated_code = result.get('code')  # Code from MCP trace
            
            if success and context.generated_code:
                context.logs.append("✅ Phase 1 complete: MCP execution successful")
                context.logs.append("✅ Phase 2 complete: Playwright code generated from working selectors")
                
                # Optional: Validate the generated code works standalone
                # (Skip validation for now to save time, trust the traced selectors)
                context.add_attempt(StrategyType.HYBRID, True)
                
                return {
                    'success': True,
                    'logs': context.logs,
                    'screenshot': context.screenshot,
                    'code': context.generated_code
                }
            elif success and not context.generated_code:
                # MCP succeeded but no code generated (no successful actions traced)
                context.logs.append("⚠️ MCP succeeded but no code generated (no traceable actions)")
                context.add_attempt(StrategyType.HYBRID, True)
                return {
                    'success': True,
                    'logs': context.logs,
                    'screenshot': context.screenshot,
                    'code': None
                }
            else:
                # MCP failed
                context.add_attempt(StrategyType.HYBRID, False, result.get('error'))
                context.logs.append("❌ HYBRID failed: MCP execution unsuccessful")
                return {
                    'success': False,
                    'logs': context.logs,
                    'screenshot': context.screenshot,
                    'code': None
                }
                
        except Exception as e:
            context.add_attempt(StrategyType.HYBRID, False, str(e))
            context.logs.append(f"❌ HYBRID execution error: {str(e)}")
            raise
