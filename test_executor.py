import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from models import TestPlan, TestStep, ExecutionReport, ExecutionStep, LocatorCandidate
from mcp_client import MCPClient
from dom_analyzer import DOMAnalyzer
from locator_selector import LocatorSelector
from config import Config

logger = logging.getLogger(__name__)

class TestExecutor:
    def __init__(self):
        self.current_execution: Optional[ExecutionReport] = None
        self.mcp_client: Optional[MCPClient] = None
        self.dom_analyzer = DOMAnalyzer()
        self.locator_selector = LocatorSelector(
            self.dom_analyzer, 
            Config.LOCATOR_CONFIDENCE_THRESHOLD
        )
    
    def execute_test_plan(self, test_plan: TestPlan) -> ExecutionReport:
        execution_id = f"exec_{int(time.time() * 1000)}"
        
        self.current_execution = ExecutionReport(
            execution_id=execution_id,
            test_plan_id=test_plan.id,
            test_plan_name=test_plan.name,
            status="running",
            start_time=datetime.now(),
            mcp_tool_calls={}
        )
        
        self.mcp_client = MCPClient(
            browser=test_plan.browser or Config.MCP_BROWSER,
            headless=test_plan.headless if test_plan.headless is not None else Config.MCP_HEADLESS
        )
        
        try:
            if not self.mcp_client.start_server():
                raise RuntimeError("Failed to start MCP server")
            
            for idx, step in enumerate(test_plan.steps, start=1):
                self._execute_step(idx, step)
            
            self.current_execution.status = "completed"
            
        except Exception as e:
            logger.error(f"Execution failed: {str(e)}")
            self.current_execution.status = "failed"
            self.current_execution.error_summary.append(str(e))
        
        finally:
            if self.mcp_client:
                self.mcp_client.stop_server()
            
            self.current_execution.end_time = datetime.now()
            self._save_report()
        
        return self.current_execution
    
    def _execute_step(self, step_number: int, step: TestStep):
        exec_step = ExecutionStep(
            step_number=step_number,
            action=step.action,
            description=step.description,
            status="running"
        )
        
        self.current_execution.steps.append(exec_step)
        logger.info(f"Executing step {step_number}: {step.action} - {step.description}")
        
        try:
            if step.action == "navigate":
                self._execute_navigate(step, exec_step)
            
            elif step.action == "click":
                self._execute_click(step, exec_step)
            
            elif step.action == "type":
                self._execute_type(step, exec_step)
            
            elif step.action == "snapshot":
                self._execute_snapshot(step, exec_step)
            
            elif step.action == "wait":
                self._execute_wait(step, exec_step)
            
            elif step.action == "handle_alert":
                self._execute_handle_alert(step, exec_step)
            
            elif step.action == "get_alert_text":
                self._execute_get_alert_text(step, exec_step)
            
            elif step.action == "wait_for_new_tab":
                self._execute_wait_for_new_tab(step, exec_step)
            
            elif step.action == "switch_tab":
                self._execute_switch_tab(step, exec_step)
            
            elif step.action == "close_tab":
                self._execute_close_tab(step, exec_step)
            
            exec_step.status = "success"
            
        except Exception as e:
            logger.error(f"Step {step_number} failed: {str(e)}")
            exec_step.status = "failed"
            exec_step.error_message = str(e)
            self.current_execution.error_summary.append(f"Step {step_number}: {str(e)}")
            raise
    
    def _execute_navigate(self, step: TestStep, exec_step: ExecutionStep):
        if not step.target:
            raise ValueError("Navigate action requires a target URL")
        
        self._increment_tool_call("browser_navigate")
        response = self.mcp_client.navigate(step.target)
        
        time.sleep(1)
        
        snapshot = self.mcp_client.get_accessibility_snapshot()
        self._increment_tool_call("page_snapshot")
        
        elements_count = self.dom_analyzer.analyze_accessibility_tree(snapshot)
        self.current_execution.dom_elements_analyzed += elements_count
        
        exec_step.candidates_analyzed = elements_count
        logger.info(f"DOM analyzed: {elements_count} elements indexed")
    
    def _execute_click(self, step: TestStep, exec_step: ExecutionStep):
        if not step.target:
            raise ValueError("Click action requires a target element description")
        
        locator = self._find_element_with_retry(step.target, exec_step)
        
        if not locator:
            raise RuntimeError(f"Could not find element: {step.target}")
        
        locator_string = self._build_mcp_locator(locator)
        
        self._increment_tool_call("page_click")
        response = self.mcp_client.click(locator_string)
        
        exec_step.locator_used = locator_string
        exec_step.locator_confidence = locator.confidence_score
        
        time.sleep(0.5)
    
    def _execute_type(self, step: TestStep, exec_step: ExecutionStep):
        if not step.target or not step.value:
            raise ValueError("Type action requires target and value")
        
        locator = self._find_element_with_retry(step.target, exec_step)
        
        if not locator:
            raise RuntimeError(f"Could not find element: {step.target}")
        
        locator_string = self._build_mcp_locator(locator)
        
        self._increment_tool_call("page_type")
        response = self.mcp_client.type_text(locator_string, step.value)
        
        exec_step.locator_used = locator_string
        exec_step.locator_confidence = locator.confidence_score
        
        time.sleep(0.3)
    
    def _execute_snapshot(self, step: TestStep, exec_step: ExecutionStep):
        snapshot = self.mcp_client.get_accessibility_snapshot()
        self._increment_tool_call("page_snapshot")
        
        elements_count = self.dom_analyzer.analyze_accessibility_tree(snapshot)
        self.current_execution.dom_elements_analyzed += elements_count
        exec_step.candidates_analyzed = elements_count
        
        screenshot_path = self._take_screenshot(step.description)
        exec_step.screenshot_path = screenshot_path
    
    def _execute_wait(self, step: TestStep, exec_step: ExecutionStep):
        wait_time = step.timeout / 1000.0 if step.timeout else 1.0
        logger.info(f"Waiting for {wait_time} seconds")
        time.sleep(wait_time)
    
    def _execute_handle_alert(self, step: TestStep, exec_step: ExecutionStep):
        alert_action = step.alert_action or "accept"
        prompt_text = step.value or ""
        
        logger.info(f"Handling alert: {alert_action}")
        self._increment_tool_call("page_handle_dialog")
        response = self.mcp_client.handle_alert(alert_action, prompt_text)
        
        exec_step.locator_used = f"alert:{alert_action}"
        time.sleep(0.5)
    
    def _execute_get_alert_text(self, step: TestStep, exec_step: ExecutionStep):
        logger.info("Getting alert text")
        self._increment_tool_call("page_dialog_message")
        response = self.mcp_client.get_alert_text()
        
        if response and "result" in response:
            alert_text = response.get("result", "")
            logger.info(f"Alert text: {alert_text}")
            exec_step.locator_used = f"alert_text:{alert_text}"
    
    def _execute_wait_for_new_tab(self, step: TestStep, exec_step: ExecutionStep):
        logger.info("Waiting for new tab to open")
        self._increment_tool_call("context_wait_for_page")
        response = self.mcp_client.wait_for_new_tab()
        
        time.sleep(1)
        
        snapshot = self.mcp_client.get_accessibility_snapshot()
        self._increment_tool_call("page_snapshot")
        elements_count = self.dom_analyzer.analyze_accessibility_tree(snapshot)
        self.current_execution.dom_elements_analyzed += elements_count
        exec_step.candidates_analyzed = elements_count
        
        logger.info(f"New tab opened, DOM analyzed: {elements_count} elements")
    
    def _execute_switch_tab(self, step: TestStep, exec_step: ExecutionStep):
        tab_index = step.tab_index if step.tab_index is not None else 0
        
        logger.info(f"Switching to tab {tab_index}")
        self._increment_tool_call("page_bring_to_front")
        response = self.mcp_client.switch_tab(tab_index)
        
        time.sleep(0.5)
        
        snapshot = self.mcp_client.get_accessibility_snapshot()
        self._increment_tool_call("page_snapshot")
        elements_count = self.dom_analyzer.analyze_accessibility_tree(snapshot)
        self.current_execution.dom_elements_analyzed += elements_count
        exec_step.candidates_analyzed = elements_count
        
        logger.info(f"Switched to tab {tab_index}, DOM analyzed: {elements_count} elements")
    
    def _execute_close_tab(self, step: TestStep, exec_step: ExecutionStep):
        tab_index = step.tab_index
        
        logger.info(f"Closing tab {tab_index if tab_index is not None else 'current'}")
        self._increment_tool_call("page_close")
        response = self.mcp_client.close_tab(tab_index)
        
        time.sleep(0.5)
    
    def _find_element_with_retry(self, target: str, exec_step: ExecutionStep) -> Optional[LocatorCandidate]:
        for attempt in range(Config.MAX_RETRIES):
            if attempt > 0:
                exec_step.status = "retrying"
                exec_step.retry_count += 1
                self.current_execution.total_retries += 1
                logger.info(f"Retry attempt {attempt + 1} for: {target}")
                time.sleep(Config.RETRY_DELAY)
                
                snapshot = self.mcp_client.get_accessibility_snapshot()
                self._increment_tool_call("page_snapshot")
                self.dom_analyzer.analyze_accessibility_tree(snapshot)
            
            locator = self.locator_selector.find_best_locator(target)
            
            if locator and locator.confidence_score >= Config.LOCATOR_CONFIDENCE_THRESHOLD:
                if attempt > 0:
                    self.current_execution.locators_corrected += 1
                    logger.info(f"Locator found on retry {attempt + 1}")
                return locator
            
            if locator:
                fallbacks = self.locator_selector.get_fallback_locators(locator)
                exec_step.candidates_analyzed += len(fallbacks)
                
                for fallback in fallbacks:
                    if fallback.confidence_score >= Config.LOCATOR_CONFIDENCE_THRESHOLD * 0.8:
                        self.current_execution.locators_corrected += 1
                        logger.info(f"Using fallback locator: {fallback.role or fallback.tag_name}")
                        return fallback
        
        return None
    
    def _build_mcp_locator(self, candidate: LocatorCandidate) -> str:
        if candidate.aria_label:
            return f'[aria-label="{candidate.aria_label}"]'
        
        if candidate.text and len(candidate.text) < 50:
            return f'text="{candidate.text}"'
        
        if candidate.placeholder:
            return f'[placeholder="{candidate.placeholder}"]'
        
        if candidate.role:
            if candidate.text:
                return f'{candidate.role}[name="{candidate.text}"]'
            return f'role={candidate.role}'
        
        return candidate.xpath
    
    def _take_screenshot(self, description: str) -> str:
        timestamp = int(time.time() * 1000)
        filename = f"screenshot_{timestamp}_{description[:30].replace(' ', '_')}.png"
        filepath = Path(Config.SCREENSHOTS_DIR) / filename
        
        try:
            self.mcp_client.take_screenshot(str(filepath))
            self._increment_tool_call("page_screenshot")
            self.current_execution.screenshots_captured += 1
            logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Screenshot failed: {str(e)}")
            return ""
    
    def _increment_tool_call(self, tool_name: str):
        if tool_name not in self.current_execution.mcp_tool_calls:
            self.current_execution.mcp_tool_calls[tool_name] = 0
        self.current_execution.mcp_tool_calls[tool_name] += 1
    
    def _save_report(self):
        report_path = Path(Config.REPORTS_DIR) / f"{self.current_execution.execution_id}.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.current_execution.model_dump(mode='json'), f, indent=2, default=str)
        
        logger.info(f"Execution report saved: {report_path}")
