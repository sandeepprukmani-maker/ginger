"""
Unit tests for security middleware
"""
import pytest
from app.middleware.security import (
    validate_engine_type,
    validate_instruction,
    sanitize_error_message
)


def test_validate_engine_type():
    """Test engine type validation"""
    # Valid engines
    assert validate_engine_type('browser_use')[0] is True
    assert validate_engine_type('playwright_mcp')[0] is True
    
    # Invalid engine
    is_valid, error = validate_engine_type('invalid_engine')
    assert is_valid is False
    assert 'invalid_engine' in error.lower()


def test_validate_instruction():
    """Test instruction validation"""
    # Valid instruction
    assert validate_instruction('Navigate to Google')[0] is True
    
    # Empty instruction
    assert validate_instruction('')[0] is False
    assert validate_instruction('   ')[0] is False
    
    # Too long instruction
    long_instruction = 'a' * 5001
    is_valid, error = validate_instruction(long_instruction)
    assert is_valid is False
    assert 'too long' in error.lower()


def test_sanitize_error_message():
    """Test error message sanitization"""
    # OpenAI error
    error = Exception("OpenAI API key invalid")
    sanitized = sanitize_error_message(error)
    assert 'api key' not in sanitized.lower()
    assert 'service error' in sanitized.lower()
    
    # Timeout error
    error = Exception("Operation timeout after 300 seconds")
    sanitized = sanitize_error_message(error)
    assert 'timeout' in sanitized.lower()
