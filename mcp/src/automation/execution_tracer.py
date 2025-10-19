"""
Execution Tracer for MCP Actions
Captures what MCP actually did during execution to generate reliable Playwright code.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class ExecutionTrace:
    """Represents a single action performed by MCP"""
    
    def __init__(self, action_type: str, tool_name: str, arguments: Dict[str, Any]):
        self.action_type = action_type
        self.tool_name = tool_name
        self.arguments = arguments
        self.result: Optional[Any] = None
        self.success: bool = False
        self.error: Optional[str] = None
        self.timestamp = datetime.now().isoformat()
        self.metadata: Dict[str, Any] = {}
        
    def mark_success(self, result: Any, metadata: Optional[Dict[str, Any]] = None):
        """Mark action as successful and store result"""
        self.success = True
        self.result = result
        if metadata:
            self.metadata.update(metadata)
    
    def mark_failure(self, error: str):
        """Mark action as failed"""
        self.success = False
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'action_type': self.action_type,
            'tool_name': self.tool_name,
            'arguments': self.arguments,
            'result': self.result,
            'success': self.success,
            'error': self.error,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


class ExecutionTracer:
    """
    Tracks MCP execution to capture what actually worked.
    Used to generate reliable Playwright code from successful MCP runs.
    """
    
    def __init__(self):
        self.traces: List[ExecutionTrace] = []
        self.enabled = False
        self.current_url: Optional[str] = None
        
    def start_tracing(self):
        """Enable execution tracing"""
        self.enabled = True
        self.traces = []
        
    def stop_tracing(self) -> List[ExecutionTrace]:
        """Disable tracing and return captured traces"""
        self.enabled = False
        return self.traces
    
    def is_tracing(self) -> bool:
        """Check if tracing is currently enabled"""
        return self.enabled
    
    def record_action(self, action_type: str, tool_name: str, arguments: Dict[str, Any]) -> ExecutionTrace:
        """Record a new action"""
        trace = ExecutionTrace(action_type, tool_name, arguments)
        if self.enabled:
            self.traces.append(trace)
        return trace
    
    def record_navigation(self, url: str) -> ExecutionTrace:
        """Record a page navigation"""
        self.current_url = url
        return self.record_action('navigate', 'browser_navigate', {'url': url})
    
    def record_click(self, selector: str) -> ExecutionTrace:
        """Record a click action"""
        return self.record_action('click', 'browser_click', {'selector': selector})
    
    def record_fill(self, selector: str, value: str) -> ExecutionTrace:
        """Record filling a form field"""
        return self.record_action('fill', 'browser_fill_form', {'selector': selector, 'value': value})
    
    def record_type(self, selector: str, text: str, delay: int = 50) -> ExecutionTrace:
        """Record typing text"""
        return self.record_action('type', 'browser_type', {'selector': selector, 'text': text, 'delay': delay})
    
    def record_select(self, selector: str, value: str) -> ExecutionTrace:
        """Record selecting dropdown option"""
        return self.record_action('select', 'browser_select_option', {'selector': selector, 'value': value})
    
    def record_wait(self, selector: str, timeout: int = 30000) -> ExecutionTrace:
        """Record waiting for selector"""
        return self.record_action('wait', 'browser_wait_for', {'selector': selector, 'timeout': timeout})
    
    def record_assertion(self, assertion_type: str, details: Dict[str, Any]) -> ExecutionTrace:
        """Record an assertion/verification"""
        return self.record_action('assert', f'assertion_{assertion_type}', details)
    
    def get_successful_traces(self) -> List[ExecutionTrace]:
        """Get only successful traces"""
        return [t for t in self.traces if t.success]
    
    def get_trace_summary(self) -> Dict[str, Any]:
        """Get summary of execution trace"""
        successful = self.get_successful_traces()
        return {
            'total_actions': len(self.traces),
            'successful_actions': len(successful),
            'failed_actions': len(self.traces) - len(successful),
            'current_url': self.current_url,
            'traces': [t.to_dict() for t in self.traces]
        }
    
    def export_to_json(self, filepath: str):
        """Export traces to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.get_trace_summary(), f, indent=2)
