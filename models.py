from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime

class TestStep(BaseModel):
    action: Literal["navigate", "click", "type", "snapshot", "wait", "handle_alert", "switch_tab", "wait_for_new_tab", "close_tab", "get_alert_text"]
    description: str
    target: Optional[str] = None
    value: Optional[str] = None
    timeout: Optional[int] = 5000
    alert_action: Optional[Literal["accept", "dismiss"]] = "accept"
    tab_index: Optional[int] = None

class TestPlan(BaseModel):
    id: str
    name: str
    description: str
    steps: List[TestStep]
    browser: Optional[str] = "chrome"
    headless: Optional[bool] = False

class LocatorCandidate(BaseModel):
    element_id: str
    role: Optional[str] = None
    text: Optional[str] = None
    aria_label: Optional[str] = None
    placeholder: Optional[str] = None
    tag_name: str
    confidence_score: float
    xpath: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    parent_path: str = ""

class ExecutionStep(BaseModel):
    step_number: int
    action: str
    description: str
    status: Literal["pending", "running", "success", "failed", "retrying"]
    locator_used: Optional[str] = None
    locator_confidence: Optional[float] = None
    candidates_analyzed: int = 0
    retry_count: int = 0
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ExecutionReport(BaseModel):
    execution_id: str
    test_plan_id: str
    test_plan_name: str
    status: Literal["running", "completed", "failed"]
    start_time: datetime
    end_time: Optional[datetime] = None
    steps: List[ExecutionStep] = Field(default_factory=list)
    mcp_tool_calls: Dict[str, int] = Field(default_factory=dict)
    dom_elements_analyzed: int = 0
    locators_corrected: int = 0
    total_retries: int = 0
    screenshots_captured: int = 0
    error_summary: List[str] = Field(default_factory=list)

class DOMElement(BaseModel):
    id: str
    tag_name: str
    role: Optional[str] = None
    text: Optional[str] = None
    aria_label: Optional[str] = None
    placeholder: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    xpath: str
    parent_id: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    depth: int = 0
