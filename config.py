import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    FLASK_HOST = "0.0.0.0"
    FLASK_PORT = 5000
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    MCP_BROWSER = os.getenv("MCP_BROWSER", "chrome")
    MCP_HEADLESS = os.getenv("MCP_HEADLESS", "false").lower() == "true"
    MCP_DEVICE = os.getenv("MCP_DEVICE", "")
    
    LOGS_DIR = "logs"
    SCREENSHOTS_DIR = "screenshots"
    TEST_PLANS_DIR = "test_plans"
    REPORTS_DIR = "reports"
    
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = float(os.getenv("RETRY_DELAY", "2.0"))
    
    LOCATOR_CONFIDENCE_THRESHOLD = float(os.getenv("LOCATOR_CONFIDENCE_THRESHOLD", "0.7"))
