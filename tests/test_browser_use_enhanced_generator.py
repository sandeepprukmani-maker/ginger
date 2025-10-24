"""
Test Enhanced Browser-Use Code Generator
Verifies selector validation, confidence scoring, and CI/CD-ready code generation
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.engines.browser_use.playwright_code_generator import PlaywrightCodeGenerator, PlaywrightAction
from app.engines.playwright_mcp.selector_validator import SelectorConfidence


def test_browser_use_selector_validation():
    """Test that Browser-Use generator validates and scores selectors"""
    print("\n=== Testing Browser-Use Selector Validation ===")
    
    # Simulate actions as they would come from _convert_model_action
    generator = PlaywrightCodeGenerator(task_description="Test with mixed selectors")
    
    # Manually call _convert_model_action to get properly validated actions
    brittle_action = generator._convert_model_action({
        'name': 'click_element',
        'params': {'selector': 'button:nth-child(2)'}
    })
    
    stable_action = generator._convert_model_action({
        'name': 'fill_element',
        'params': {'selector': '[data-testid="email-input"]', 'value': 'test@example.com'}
    })
    
    generator.actions = [brittle_action, stable_action]
    
    # Generate code
    code = generator.generate_python_code()
    
    # Check that brittle selector is blocked
    if 'button:nth-child(2)' in code and 'page.locator("button:nth-child(2)")' in code:
        print("❌ CRITICAL: Brittle selector 'button:nth-child(2)' used in executable code!")
        assert False, "Brittle selector should be blocked"
    else:
        print("✅ Brittle selector correctly blocked from executable code")
    
    # Check that stable selector is used
    if '[data-testid="email-input"]' in code:
        print("✅ Stable data-testid selector preserved")
    else:
        print("❌ Stable selector should be preserved")
        assert False, "Stable selector missing"
    
    # Check for confidence warnings
    if 'REJECTED selector' in code:
        print("✅ REJECTED warning present for brittle selector")
    else:
        print("❌ Missing REJECTED warning")
        assert False, "Should warn about rejected selector"
    
    print("✅ Browser-Use selector validation working correctly!")


def test_browser_use_explicit_waits():
    """Test that Browser-Use generator includes explicit waits"""
    print("\n=== Testing Browser-Use Explicit Waits ===")
    
    actions = [
        PlaywrightAction(
            action_type='navigate',
            url='https://example.com',
            comment='Navigate to site'
        ),
        PlaywrightAction(
            action_type='click',
            selector='[data-testid="submit"]',
            comment='Click submit',
            confidence=SelectorConfidence.HIGH,
            confidence_reason='Has data-testid'
        )
    ]
    
    generator = PlaywrightCodeGenerator(task_description="Test with waits")
    generator.actions = actions
    
    code = generator.generate_python_code()
    
    checks = [
        ("expect(", "Should include expect() for visibility checks"),
        ("to_be_visible()", "Should check visibility before interactions"),
        ("wait_for_load_state", "Should wait for network idle after navigation"),
        ("Selector confidence: HIGH", "Should include confidence comments"),
    ]
    
    for check_string, description in checks:
        if check_string in code:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            assert False, f"Missing: {check_string}"
    
    print("✅ Browser-Use explicit waits working correctly!")


def test_browser_use_pytest_format():
    """Test that Browser-Use generator can create pytest tests"""
    print("\n=== Testing Browser-Use pytest Format ===")
    
    actions = [
        PlaywrightAction(
            action_type='navigate',
            url='https://example.com'
        )
    ]
    
    generator = PlaywrightCodeGenerator(task_description="Test pytest format")
    generator.actions = actions
    
    code = generator.generate_python_code(test_framework=True)
    
    pytest_checks = [
        ("import pytest", "Should import pytest"),
        ("from playwright.sync_api import Page, expect", "Should import Page and expect"),
        ("def test_automation(page: Page):", "Should create pytest test function"),
        ("To run: pytest test_automation.py", "Should include pytest run instructions"),
    ]
    
    for check_string, description in pytest_checks:
        if check_string in code:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            assert False, f"Missing: {check_string}"
    
    print("✅ Browser-Use pytest format working correctly!")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ENHANCED BROWSER-USE CODE GENERATOR TESTS")
    print("="*60)
    
    try:
        test_browser_use_selector_validation()
        test_browser_use_explicit_waits()
        test_browser_use_pytest_format()
        
        print("\n" + "="*60)
        print("🎉 ALL BROWSER-USE TESTS PASSED!")
        print("="*60)
        print("\n✅ Browser-Use engine now generates CI/CD-ready code with:")
        print("   - Stable selector validation and blocking")
        print("   - Explicit visibility waits before interactions")
        print("   - Confidence scoring and warnings")
        print("   - pytest-compatible test structure")
        print("   - Network stability waits after navigation")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
