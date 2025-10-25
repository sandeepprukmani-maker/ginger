"""
Test Enhanced Playwright MCP Code Generator
Verifies selector validation, confidence scoring, and CI/CD-ready code generation
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.engines.playwright_mcp.mcp_code_generator import MCPCodeGenerator, ElementMetadata
from app.engines.playwright_mcp.selector_validator import SelectorValidator, SelectorConfidence


def test_selector_validator():
    """Test that brittle selectors are rejected"""
    print("\n=== Testing Selector Validator ===")
    
    test_cases = [
        ("button:nth-child(3)", SelectorConfidence.REJECTED, "nth-child should be rejected"),
        ("div:nth-of-type(2)", SelectorConfidence.REJECTED, "nth-of-type should be rejected"),
        (".css-a1b2c3", SelectorConfidence.REJECTED, "Hashed classes should be rejected"),
        ('[data-testid="submit-button"]', SelectorConfidence.HIGH, "data-testid should be HIGH"),
        ("#user-email", SelectorConfidence.MEDIUM, "ID selector should be MEDIUM"),
    ]
    
    for selector, expected_confidence, description in test_cases:
        confidence, reason = SelectorValidator.validate_selector(selector)
        status = "✅" if confidence == expected_confidence else "❌"
        print(f"{status} {description}: {selector} -> {confidence.value} ({reason})")
        assert confidence == expected_confidence, f"Expected {expected_confidence.value} for {selector}"
    
    print("✅ All selector validation tests passed!")


def test_confidence_scoring():
    """Test ElementMetadata confidence scoring"""
    print("\n=== Testing Confidence Scoring ===")
    
    high_confidence_meta = ElementMetadata(
        ref="e1",
        data_testid="submit-btn",
        role="button",
        name="Submit"
    )
    confidence, reason = high_confidence_meta.get_confidence()
    print(f"✅ data-testid selector: {confidence.value} - {reason}")
    assert confidence == SelectorConfidence.HIGH
    
    medium_confidence_meta = ElementMetadata(
        ref="e2",
        role="button",
        text="Click Me"
    )
    confidence, reason = medium_confidence_meta.get_confidence()
    print(f"⚠️  Role without name: {confidence.value} - {reason}")
    assert confidence == SelectorConfidence.MEDIUM
    
    print("✅ All confidence scoring tests passed!")


def test_code_generation_with_waits():
    """Test that generated code includes explicit waits"""
    print("\n=== Testing Code Generation with Explicit Waits ===")
    
    sample_steps = [
        {
            "tool": "browser_navigate_to",
            "arguments": {"url": "https://example.com"},
            "success": True
        },
        {
            "tool": "browser_snapshot",
            "arguments": {},
            "success": True,
            "result": {
                "content": [{
                    "type": "text",
                    "text": '[ref=e1] role=button name="Submit" data-testid="submit-btn"'
                }]
            }
        },
        {
            "tool": "browser_click",
            "arguments": {"ref": "e1"},
            "success": True
        }
    ]
    
    generator = MCPCodeGenerator(sample_steps, task_description="Test automation with waits")
    generated_code = generator.generate_python_code()
    
    checks = [
        ("expect(", "Should include expect() for visibility checks"),
        ("to_be_visible()", "Should check visibility before interactions"),
        ("get_by_test_id", "Should use data-testid when available"),
        ("wait_for_load_state", "Should wait for network idle after navigation"),
        ("Selector confidence: HIGH", "Should include confidence comments"),
    ]
    
    for check_string, description in checks:
        if check_string in generated_code:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            assert False, f"Generated code missing: {check_string}"
    
    print("\n--- Generated Code Sample ---")
    print(generated_code[:800])
    print("...\n")
    
    print("✅ All code generation tests passed!")


def test_confidence_warnings_in_code():
    """Test that low-confidence selectors get warnings in generated code"""
    print("\n=== Testing Confidence Warnings ===")
    
    sample_steps = [
        {
            "tool": "browser_navigate_to",
            "arguments": {"url": "https://example.com"},
            "success": True
        },
        {
            "tool": "browser_click",
            "arguments": {"selector": "button:nth-child(2)"},
            "success": True
        }
    ]
    
    generator = MCPCodeGenerator(sample_steps, task_description="Test with brittle selector")
    generated_code = generator.generate_python_code()
    
    if "WARNING: REJECTED" in generated_code:
        print("✅ Low-confidence selectors are flagged with warnings")
    else:
        print("❌ Low-confidence selectors should be flagged")
        assert False, "Missing confidence warnings for brittle selectors"
    
    print("✅ Confidence warning test passed!")


def test_brittle_selectors_not_in_code():
    """REGRESSION TEST: Ensure REJECTED selectors never appear in generated code"""
    print("\n=== Testing Brittle Selector Blocking (REGRESSION) ===")
    
    brittle_selectors = [
        "button:nth-child(2)",
        "div:nth-of-type(3)",
        ".css-abc123",
        "//div[@class='dynamic-abc123']"
    ]
    
    for brittle_selector in brittle_selectors:
        sample_steps = [
            {
                "tool": "browser_navigate_to",
                "arguments": {"url": "https://example.com"},
                "success": True
            },
            {
                "tool": "browser_click",
                "arguments": {"selector": brittle_selector},
                "success": True
            }
        ]
        
        generator = MCPCodeGenerator(sample_steps, task_description=f"Test blocking {brittle_selector}")
        generated_code = generator.generate_python_code()
        
        # Check that brittle selector doesn't appear in executable code (page.locator())
        escaped_selector = brittle_selector.replace('\\', '\\\\').replace('"', '\\"')
        locator_with_selector = f'page.locator("{escaped_selector}")'
        
        if locator_with_selector in generated_code:
            print(f"❌ CRITICAL: Brittle selector '{brittle_selector}' used in page.locator()!")
            print(f"Found: {locator_with_selector}")
            assert False, f"Brittle selector '{brittle_selector}' was not blocked in executable code!"
        else:
            print(f"✅ Brittle selector '{brittle_selector}' correctly blocked from executable code")
        
        if "REJECTED selector" not in generated_code:
            print(f"❌ Missing REJECTED warning for '{brittle_selector}'")
            assert False, "Should warn about rejected selector"
        
        if "TODO: Replace rejected selector" not in generated_code:
            print(f"❌ Missing TODO comment for '{brittle_selector}'")
            assert False, "Should have TODO comment instead of executable code for rejected selector"
    
    print("✅ All brittle selectors correctly blocked from generated code!")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ENHANCED PLAYWRIGHT MCP CODE GENERATOR TESTS")
    print("="*60)
    
    try:
        test_selector_validator()
        test_confidence_scoring()
        test_code_generation_with_waits()
        test_confidence_warnings_in_code()
        test_brittle_selectors_not_in_code()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\n✅ Playwright MCP engine is now generating CI/CD-ready code with:")
        print("   - Stable, semantic locators (data-testid, role-based)")
        print("   - Explicit visibility waits before interactions")
        print("   - Confidence scoring and warnings")
        print("   - Rejection of brittle selectors (nth-child, XPath indices)")
        print("   - Production-ready pytest structure")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
