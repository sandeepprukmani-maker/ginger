import os
from datetime import datetime
from pathlib import Path

class OutputGenerator:
    def __init__(self, output_dir: str = "generated_scripts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def save_script(self, code: str, custom_path: str | None = None, command: str = "") -> str:
        if custom_path:
            output_path = Path(custom_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_command = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in command)
            safe_command = safe_command[:50].strip().replace(' ', '_')
            filename = f"automation_{safe_command}_{timestamp}.py" if safe_command else f"automation_{timestamp}.py"
            output_path = self.output_dir / filename
        
        full_script = self._generate_standalone_script(code, command)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(full_script)
        
        os.chmod(output_path, 0o755)
        
        return str(output_path)
    
    def _generate_standalone_script(self, automation_function: str, command: str) -> str:
        script_template = f'''#!/usr/bin/env python3
"""
Playwright Automation Script
Generated from natural language command: "{command}"
Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This script can be executed independently without OpenAI or MCP.
Usage: python {Path(self.output_dir).name}/script_name.py
"""

from playwright.sync_api import sync_playwright
import sys

{automation_function}

def main():
    """Main execution function"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            print("Starting automation...")
            run_automation(page)
            print("Automation completed successfully!")
            
            page.wait_for_timeout(2000)
            
            browser.close()
            
    except Exception as e:
        print(f"Error during automation: {{e}}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
        return script_template
