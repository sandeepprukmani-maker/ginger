"""
Integration tests for API endpoints
"""
import pytest


def test_health_endpoint():
    """Test the health check endpoint"""
    from app import create_app
    
    app = create_app()
    client = app.test_client()
    
    response = client.get('/health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'browser_use' in data['engines']
    assert 'playwright_mcp' in data['engines']


def test_execute_endpoint_validation():
    """Test execute endpoint input validation"""
    from app import create_app
    
    app = create_app()
    client = app.test_client()
    
    # Empty instruction should fail
    response = client.post('/api/execute', json={'instruction': ''})
    assert response.status_code == 400
    
    # Invalid engine should fail
    response = client.post('/api/execute', json={
        'instruction': 'test',
        'engine': 'invalid_engine'
    })
    assert response.status_code == 400
