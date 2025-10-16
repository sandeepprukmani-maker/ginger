import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from .mcp_client import PlaywrightMCPClient
from .llm_orchestrator import LLMOrchestrator


class AutomationEngine:
    """Main automation engine that orchestrates the entire workflow"""
    
    def __init__(self, mcp_server_command: list = None):
        self.mcp_client = PlaywrightMCPClient(mcp_server_command)
        self.orchestrator = LLMOrchestrator()
        self.output_dir = Path("output")
        self.code_dir = Path("generated_code")
        self.last_execution_steps = []
        
        self.output_dir.mkdir(exist_ok=True)
        self.code_dir.mkdir(exist_ok=True)
        
    async def initialize(self):
        """Initialize the engine and connect to services"""
        print("🔧 Initializing automation engine...")
        
        await self.mcp_client.connect()
        print("✓ Connected to Playwright MCP server")
        
        tools = await self.mcp_client.list_tools()
        
        if not tools:
            raise RuntimeError(
                "Failed to load MCP tools from Playwright server. "
                "Please ensure the MCP server is running on port 3000 and accessible. "
                "Check with: curl http://localhost:3000/"
            )
        
        print(f"✓ Loaded {len(tools)} MCP tools")
        
        self.orchestrator.set_available_tools(tools)
        print("✓ LLM orchestrator configured")
        
    async def execute_automation(self, natural_language_command: str) -> Dict[str, Any]:
        """Execute complete automation workflow from natural language"""
        
        print(f"\n{'='*60}")
        print(f"📝 Command: {natural_language_command}")
        print(f"{'='*60}\n")
        
        print("🤖 Generating automation plan...")
        plan = self.orchestrator.generate_automation_plan(natural_language_command)
        
        if "error" in plan:
            print(f"\n❌ ERROR:\n{plan['error']}\n")
            return {"error": plan["error"], "success": False}
        
        print(f"\n📋 Plan: {plan.get('description', 'No description')}")
        print(f"   Steps: {len(plan.get('steps', []))}")
        
        self.last_execution_steps = plan.get("steps", [])
        
        print("\n⚙️  Executing automation...")
        results = await self.mcp_client.execute_automation_sequence(plan.get("steps", []))
        
        print("\n✨ Generating reusable code...")
        reusable_code = self.orchestrator.generate_reusable_code(
            natural_language_command, 
            plan, 
            results
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results_file = self.output_dir / f"results_{timestamp}.json"
        with open(results_file, "w") as f:
            json.dump({
                "command": natural_language_command,
                "plan": plan,
                "results": results,
                "timestamp": timestamp
            }, f, indent=2)
        
        code_file = self.code_dir / f"automation_{timestamp}.py"
        with open(code_file, "w") as f:
            f.write(reusable_code)
        
        print(f"\n{'='*60}")
        print(f"✅ AUTOMATION COMPLETE")
        print(f"{'='*60}")
        print(f"📄 Results saved to: {results_file}")
        print(f"🐍 Reusable code saved to: {code_file}")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "command": natural_language_command,
            "plan": plan,
            "results": results,
            "code": reusable_code,
            "files": {
                "results": str(results_file),
                "code": str(code_file)
            }
        }
    
    async def close(self):
        """Clean up resources"""
        await self.mcp_client.close()
