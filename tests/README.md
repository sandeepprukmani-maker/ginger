# Tests

This directory contains unit tests for the AI Browser Automation application.

## Running Tests

Run all tests:
```bash
python -m pytest tests/
```

Run specific test file:
```bash
python -m pytest tests/test_engine_orchestrator.py
```

Run with coverage:
```bash
python -m pytest --cov=app tests/
```

## Test Structure

- `test_engine_orchestrator.py` - Tests for engine coordination and caching
- `test_api_routes.py` - Tests for Flask API endpoints

## Writing New Tests

1. Create a new file starting with `test_`
2. Import `unittest` and create a class inheriting from `unittest.TestCase`
3. Add test methods starting with `test_`
4. Use mocks for external dependencies (browsers, OpenAI API, etc.)
