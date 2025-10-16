from flask import Flask, request, jsonify
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, Any

from config import Config
from models import TestPlan, ExecutionReport
from test_executor import TestExecutor
from execution_logger import setup_logging

app = Flask(__name__)

setup_logging()

executions: Dict[str, ExecutionReport] = {}
executor = TestExecutor()

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "AI Automation Runner with MCP Integration",
        "version": "1.0.0",
        "description": "Execute AI-generated test plans using Microsoft Playwright MCP server",
        "features": [
            "MCP client integration with Playwright",
            "DOM accessibility tree analysis",
            "Intelligent locator selection with confidence scoring",
            "Multi-step test plan execution",
            "Intelligent retry mechanism with fallback strategies",
            "Comprehensive execution logging and reporting"
        ],
        "endpoints": {
            "POST /api/execute": "Execute a test plan",
            "GET /api/executions": "List all executions",
            "GET /api/executions/<id>": "Get execution details",
            "GET /api/executions/<id>/report": "Get execution report",
            "POST /api/test-plans": "Upload a test plan",
            "GET /api/test-plans": "List all test plans",
            "GET /api/health": "Health check"
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mcp_browser": Config.MCP_BROWSER,
        "headless_mode": Config.MCP_HEADLESS
    })

@app.route('/api/execute', methods=['POST'])
def execute_test():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        test_plan = TestPlan(**data)
        
        report = executor.execute_test_plan(test_plan)
        
        executions[report.execution_id] = report
        
        return jsonify({
            "execution_id": report.execution_id,
            "status": report.status,
            "test_plan_name": report.test_plan_name,
            "start_time": report.start_time.isoformat(),
            "end_time": report.end_time.isoformat() if report.end_time else None,
            "total_steps": len(report.steps),
            "successful_steps": sum(1 for s in report.steps if s.status == "success"),
            "failed_steps": sum(1 for s in report.steps if s.status == "failed"),
            "mcp_tool_calls": report.mcp_tool_calls,
            "dom_elements_analyzed": report.dom_elements_analyzed,
            "locators_corrected": report.locators_corrected,
            "total_retries": report.total_retries,
            "screenshots_captured": report.screenshots_captured
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/executions', methods=['GET'])
def list_executions():
    return jsonify({
        "total": len(executions),
        "executions": [
            {
                "execution_id": exec_id,
                "test_plan_name": report.test_plan_name,
                "status": report.status,
                "start_time": report.start_time.isoformat(),
                "end_time": report.end_time.isoformat() if report.end_time else None,
                "total_steps": len(report.steps)
            }
            for exec_id, report in executions.items()
        ]
    })

@app.route('/api/executions/<execution_id>', methods=['GET'])
def get_execution(execution_id: str):
    if execution_id not in executions:
        return jsonify({"error": "Execution not found"}), 404
    
    report = executions[execution_id]
    return jsonify(report.model_dump(mode='json'))

@app.route('/api/executions/<execution_id>/report', methods=['GET'])
def get_execution_report(execution_id: str):
    report_path = Path(Config.REPORTS_DIR) / f"{execution_id}.json"
    
    if not report_path.exists():
        return jsonify({"error": "Report not found"}), 404
    
    with open(report_path, 'r') as f:
        report_data = json.load(f)
    
    return jsonify(report_data)

@app.route('/api/test-plans', methods=['POST'])
def upload_test_plan():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        test_plan = TestPlan(**data)
        
        plan_path = Path(Config.TEST_PLANS_DIR) / f"{test_plan.id}.json"
        
        with open(plan_path, 'w') as f:
            json.dump(test_plan.model_dump(mode='json'), f, indent=2)
        
        return jsonify({
            "message": "Test plan uploaded successfully",
            "test_plan_id": test_plan.id,
            "name": test_plan.name,
            "total_steps": len(test_plan.steps),
            "file_path": str(plan_path)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/test-plans', methods=['GET'])
def list_test_plans():
    plans_dir = Path(Config.TEST_PLANS_DIR)
    
    if not plans_dir.exists():
        return jsonify({"total": 0, "test_plans": []})
    
    plans = []
    for plan_file in plans_dir.glob("*.json"):
        with open(plan_file, 'r') as f:
            plan_data = json.load(f)
            plans.append({
                "id": plan_data.get("id"),
                "name": plan_data.get("name"),
                "description": plan_data.get("description"),
                "total_steps": len(plan_data.get("steps", []))
            })
    
    return jsonify({
        "total": len(plans),
        "test_plans": plans
    })

@app.route('/api/dom-analysis/<execution_id>', methods=['GET'])
def get_dom_analysis(execution_id: str):
    if execution_id not in executions:
        return jsonify({"error": "Execution not found"}), 404
    
    report = executions[execution_id]
    
    dom_stats = {
        "execution_id": execution_id,
        "total_elements_analyzed": report.dom_elements_analyzed,
        "steps_with_analysis": []
    }
    
    for step in report.steps:
        if step.candidates_analyzed > 0:
            dom_stats["steps_with_analysis"].append({
                "step_number": step.step_number,
                "action": step.action,
                "description": step.description,
                "candidates_analyzed": step.candidates_analyzed,
                "locator_used": step.locator_used,
                "confidence": step.locator_confidence,
                "retry_count": step.retry_count
            })
    
    return jsonify(dom_stats)

if __name__ == '__main__':
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.DEBUG)
