"""
Pytest configuration and fixtures for tests
"""
import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_instruction():
    """Sample instruction for testing"""
    return "Navigate to example.com"


@pytest.fixture
def mock_openai_key(monkeypatch):
    """Mock OpenAI API key for tests"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
