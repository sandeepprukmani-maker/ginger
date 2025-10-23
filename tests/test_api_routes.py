"""
Tests for API Routes
"""
import unittest
import json
from unittest.mock import Mock, patch
from app import create_app


class TestAPIRoutes(unittest.TestCase):
    """Test cases for API routes"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_index_route(self):
        """Test that index route returns HTML"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AI Browser Automation', response.data)
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('engines', data)
    
    def test_execute_empty_instruction(self):
        """Test that empty instruction returns 400 error"""
        response = self.client.post('/api/execute',
                                   json={'instruction': '', 'engine': 'hybrid'})
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('provide an instruction', data['error'])
    
    def test_execute_missing_instruction(self):
        """Test that missing instruction key returns 400 error"""
        response = self.client.post('/api/execute',
                                   json={'engine': 'hybrid'})
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
    
    @patch('app.services.engine_orchestrator.EngineOrchestrator.execute_instruction')
    def test_execute_success(self, mock_execute):
        """Test successful execution"""
        mock_execute.return_value = {
            'success': True,
            'message': 'Task completed',
            'iterations': 3,
            'steps': []
        }
        
        response = self.client.post('/api/execute',
                                   json={
                                       'instruction': 'Go to google.com',
                                       'engine': 'hybrid',
                                       'headless': True
                                   })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['iterations'], 3)
    
    def test_reset_agent(self):
        """Test reset agent endpoint"""
        response = self.client.post('/api/reset',
                                   json={'engine': 'hybrid'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('reset successfully', data['message'])


if __name__ == '__main__':
    unittest.main()
