"""
Agent Orchestrator - Coordinates Planner, Generator, and Healer agents
Implements the complete automation workflow
"""
import logging
from typing import Dict, Any, Optional, Tuple
from app.agents.planner import PlannerAgent
from app.agents.generator import GeneratorAgent
from app.agents.healer import HealerAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the three-agent workflow: Plan → Generate → Execute → Heal (if needed)
    
    This implements the exact Playwright Agents pattern:
    1. Planner explores and creates execution plan
    2. Generator converts plan to Python Playwright code
    3. If execution fails, Healer fixes the code
    4. On subsequent runs, uses healed version if available
    """
    
    def __init__(self, engine):
        """
        Initialize the orchestrator with an automation engine
        
        Args:
            engine: Playwright MCP or Browser-Use engine instance
        """
        self.engine = engine
        self.planner = PlannerAgent(engine)
        self.generator = GeneratorAgent(engine)
        self.healer = HealerAgent(engine)
        
    async def create_automation_script(self, 
                                     instruction: str, 
                                     context: Optional[Dict[str, Any]] = None,
                                     headless: bool = False) -> Tuple[str, Dict[str, Any]]:
        """
        Create an automation script using the Planner → Generator workflow
        
        Args:
            instruction: Natural language automation task
            context: Optional context (URL, etc.)
            headless: Whether to run in headless mode
            
        Returns:
            Tuple of (generated_script, plan_metadata)
        """
        logger.info(f"🎭 Starting automation script creation for: {instruction}")
        
        # Step 1: Planner creates execution plan
        logger.info("   Step 1/2: Planning...")
        plan = await self.planner.create_plan(instruction, context or {})
        
        # Step 2: Generator converts plan to code
        logger.info("   Step 2/2: Generating code...")
        script = await self.generator.generate_code(plan, headless)
        
        logger.info(f"✅ Automation script created ({len(script)} characters)")
        
        return script, plan
    
    async def heal_failed_script(self,
                                failed_script: str,
                                error_message: str,
                                execution_logs: str = "") -> str:
        """
        Heal a failed automation script
        
        Args:
            failed_script: The script that failed
            error_message: Error message from the failure
            execution_logs: Optional execution logs
            
        Returns:
            Healed script
        """
        logger.info("🎭 Starting script healing process")
        
        healed_script = await self.healer.heal_script(
            original_script=failed_script,
            error_message=error_message,
            execution_logs=execution_logs
        )
        
        logger.info(f"✅ Script healed ({len(healed_script)} characters)")
        
        return healed_script
    
    def determine_script_to_execute(self, 
                                   generated_script: Optional[str],
                                   healed_script: Optional[str]) -> Tuple[Optional[str], str]:
        """
        Determine which script to execute based on availability
        
        Logic:
        - If both exist: use healed_script (it's the most recent fixed version)
        - If only generated exists: use generated_script
        - If neither exists: return None
        
        Args:
            generated_script: The originally generated script
            healed_script: The healed version (if any)
            
        Returns:
            Tuple of (script_to_execute, script_type)
        """
        if healed_script:
            logger.info("   Using HEALED script (most recent fixed version)")
            return healed_script, "healed"
        elif generated_script:
            logger.info("   Using GENERATED script (original version)")
            return generated_script, "generated"
        else:
            logger.warning("   No script available to execute")
            return None, "none"
