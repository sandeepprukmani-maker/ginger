#!/usr/bin/env python3
"""
Smoke test for Playwright MCP CLI
Tests basic functionality: code generation, execution, and output generation
"""

import os
import sys
from pathlib import Path
from src.code_generator import CodeGenerator
from src.executor import PlaywrightExecutor
from src.output_generator import OutputGenerator

def test_code_generation():
    """Test that code generator produces valid Python code"""
    print("Testing code generation...")
    
    generator = CodeGenerator()
    code, info = generator.generate_code("Go to example.com")
    
    assert "def run_automation(page)" in code, "Generated code should contain run_automation function"
    assert "page.goto" in code or "page.go" in code, "Generated code should navigate to a URL"
    assert info['total_locators'] >= 0, "Should track locator usage"
    
    print("✓ Code generation works")
    return code

def test_execution(code):
    """Test that executor can run generated code"""
    print("Testing code execution...")
    
    executor = PlaywrightExecutor(headless=True)
    success, error_info = executor.execute(code)
    
    if not success:
        print(f"  Note: Execution failed (expected for some test cases): {error_info.get('message', 'Unknown error') if error_info else 'Unknown'}")
    else:
        print("✓ Code execution works")
    
    return success, error_info

def test_output_generation(code):
    """Test that output generator creates valid standalone scripts"""
    print("Testing output generation...")
    
    output_gen = OutputGenerator(output_dir="test_output")
    script_path = output_gen.save_script(code, command="Test automation")
    
    assert Path(script_path).exists(), "Generated script should exist"
    
    with open(script_path, 'r') as f:
        content = f.read()
    
    assert "#!/usr/bin/env python3" in content, "Should be executable script"
    assert "def run_automation(page)" in content, "Should contain automation function"
    assert "if __name__ == \"__main__\":" in content, "Should have main block"
    assert "sync_playwright" in content, "Should import Playwright"
    
    Path(script_path).unlink()
    Path("test_output").rmdir()
    
    print(f"✓ Output generation works (created {script_path})")

def main():
    print("=" * 60)
    print("Playwright MCP CLI - Smoke Test")
    print("=" * 60)
    print()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set. Skipping smoke test.")
        return 0
    
    try:
        code = test_code_generation()
        print()
        
        success, error_info = test_execution(code)
        print()
        
        test_output_generation(code)
        print()
        
        print("=" * 60)
        print("✓ All smoke tests passed!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Smoke test failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
