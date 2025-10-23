"""
Tests for Engine Orchestrator
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from app.services.engine_orchestrator import EngineOrchestrator


class TestEngineOrchestrator(unittest.TestCase):
    """Test cases for EngineOrchestrator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.orchestrator = EngineOrchestrator()
    
    def test_initialization(self):
        """Test orchestrator initializes with empty caches"""
        self.assertEqual(self.orchestrator.playwright_engines, {})
        self.assertEqual(self.orchestrator.browser_use_engines, {})
        self.assertEqual(self.orchestrator.hybrid_engines, {})
    
    @patch('app.services.engine_orchestrator.browser_use_codebase')
    def test_browser_use_engine_caching(self, mock_browser_use):
        """Test that Browser-Use engines are cached per headless mode"""
        mock_engine = Mock()
        mock_browser_use.create_engine.return_value = mock_engine
        
        # First call should create engine
        engine1 = self.orchestrator.get_browser_use_engine(headless=True)
        self.assertEqual(mock_browser_use.create_engine.call_count, 1)
        
        # Second call with same headless should return cached engine
        engine2 = self.orchestrator.get_browser_use_engine(headless=True)
        self.assertEqual(mock_browser_use.create_engine.call_count, 1)
        self.assertIs(engine1, engine2)
        
        # Call with different headless should create new engine
        engine3 = self.orchestrator.get_browser_use_engine(headless=False)
        self.assertEqual(mock_browser_use.create_engine.call_count, 2)
        self.assertIsNot(engine1, engine3)
    
    @patch('app.services.engine_orchestrator.hybrid_engine')
    def test_hybrid_engine_caching(self, mock_hybrid):
        """Test that Hybrid engines are cached per headless mode"""
        mock_engine = Mock()
        mock_hybrid.create_engine.return_value = mock_engine
        
        # First call should create engine
        engine1 = self.orchestrator.get_hybrid_engine(headless=True)
        self.assertEqual(mock_hybrid.create_engine.call_count, 1)
        
        # Second call should return cached engine
        engine2 = self.orchestrator.get_hybrid_engine(headless=True)
        self.assertEqual(mock_hybrid.create_engine.call_count, 1)
        self.assertIs(engine1, engine2)
    
    def test_execute_instruction_invalid_engine(self):
        """Test that invalid engine type raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.orchestrator.execute_instruction(
                "test instruction",
                "invalid_engine",
                headless=True
            )
        self.assertIn("Unknown engine type", str(context.exception))
    
    @patch('app.services.engine_orchestrator.browser_use_codebase')
    def test_execute_instruction_browser_use(self, mock_browser_use):
        """Test executing instruction with Browser-Use engine"""
        mock_engine = Mock()
        mock_engine.execute_instruction_sync.return_value = {
            'success': True,
            'message': 'Task completed',
            'iterations': 5
        }
        mock_browser_use.create_engine.return_value = mock_engine
        
        result = self.orchestrator.execute_instruction(
            "Go to google.com",
            "browser_use",
            headless=True
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['engine'], 'browser_use')
        self.assertTrue(result['headless'])
        mock_engine.execute_instruction_sync.assert_called_once_with("Go to google.com")


if __name__ == '__main__':
    unittest.main()
