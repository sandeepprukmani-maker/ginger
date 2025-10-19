import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .logger import get_logger

logger = get_logger()


class SessionMemory:
    """
    Persistent storage for automation execution history.
    Tracks successful patterns and failures to improve future executions.
    """
    
    def __init__(self, session_dir: str = "sessions"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.memory_file = self.session_dir / "execution_memory.json"
        self.memory: Dict[str, Any] = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load execution memory from disk."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    logger.debug(f"Loaded {len(data.get('executions', []))} executions from memory")
                    return data
            except Exception as e:
                logger.error(f"Failed to load memory: {e}")
                return {"executions": [], "patterns": {}}
        return {"executions": [], "patterns": {}}
    
    def _save_memory(self):
        """Save execution memory to disk."""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
            logger.debug("Memory saved to disk")
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
    
    def record_execution(self, instruction: str, success: bool, 
                        steps: List[Dict[str, Any]], error: Optional[str] = None):
        """Record an execution attempt."""
        execution = {
            "instruction": instruction,
            "success": success,
            "steps": steps,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        self.memory["executions"].append(execution)
        
        if len(self.memory["executions"]) > 100:
            self.memory["executions"] = self.memory["executions"][-100:]
        
        if success:
            self._update_patterns(instruction, steps)
        
        self._save_memory()
        logger.info(f"Recorded {'successful' if success else 'failed'} execution")
    
    def _update_patterns(self, instruction: str, steps: List[Dict[str, Any]]):
        """Learn from successful patterns."""
        instruction_lower = instruction.lower()
        
        key_phrases = ["search", "login", "click", "fill", "navigate", "extract", "scrape"]
        
        for phrase in key_phrases:
            if phrase in instruction_lower:
                if phrase not in self.memory["patterns"]:
                    self.memory["patterns"][phrase] = []
                
                pattern = {
                    "instruction": instruction,
                    "steps": steps,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.memory["patterns"][phrase].append(pattern)
                
                if len(self.memory["patterns"][phrase]) > 5:
                    self.memory["patterns"][phrase] = self.memory["patterns"][phrase][-5:]
    
    def get_similar_patterns(self, instruction: str) -> List[Dict[str, Any]]:
        """Get similar successful patterns based on instruction."""
        instruction_lower = instruction.lower()
        similar = []
        
        for phrase, patterns in self.memory["patterns"].items():
            if phrase in instruction_lower:
                similar.extend(patterns)
        
        return similar
    
    def get_recent_successes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent successful executions."""
        successes = [e for e in self.memory["executions"] if e["success"]]
        return successes[-limit:]
    
    def get_recent_failures(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent failed executions."""
        failures = [e for e in self.memory["executions"] if not e["success"]]
        return failures[-limit:]
    
    def get_context_for_instruction(self, instruction: str) -> str:
        """Build context string for similar instructions."""
        similar = self.get_similar_patterns(instruction)
        
        if not similar:
            return ""
        
        context_parts = ["Similar successful patterns:"]
        for pattern in similar[-3:]:
            context_parts.append(f"- {pattern['instruction']}: {len(pattern['steps'])} steps")
        
        return "\n".join(context_parts)
    
    def clear_memory(self):
        """Clear all execution memory."""
        self.memory = {"executions": [], "patterns": {}}
        self._save_memory()
        logger.info("Memory cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about executions."""
        total = len(self.memory["executions"])
        successes = len([e for e in self.memory["executions"] if e["success"]])
        failures = total - successes
        
        return {
            "total_executions": total,
            "successes": successes,
            "failures": failures,
            "success_rate": (successes / total * 100) if total > 0 else 0,
            "learned_patterns": len(self.memory["patterns"])
        }
