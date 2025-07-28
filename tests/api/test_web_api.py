"""Integration tests for MASB API endpoints."""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

from src.web.app import MASBWebApp
from src.models.data_models import BatchEvaluationResult, Language, Category


class TestWebAPI:
    """Test cases for web API endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application."""
        config = {
            'secret_key': 'test-secret-key',
            'testing': True
        }
        
        with patch('src.web.app.db_manager.initialize'):
            webapp = MASBWebApp(config)
            webapp.app.config['TESTING'] = True
            return webapp.app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    @pytest.fixture
    def mock_batch_result(self):
        """Mock batch evaluation result."""
        return BatchEvaluationResult(
            batch_id="test-batch-1",
            model_name="test-model",
            language=Language.EN,
            category=Category.HALLUCINATION,
            total_prompts=10,
            completed_prompts=10,
            failed_prompts=0,
            results=[],
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration=30.0,
            status="completed",
            config={},
            metadata={},
            summary={"hallucination": {"mean": 0.8, "pass_rate": 0.9}}
        )
    
    def test_index_page(self, client):
        """Test index page."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'MASB' in response.data
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_api_models_endpoint(self, client):
        """Test models API endpoint."""
        response = client.get('/api/models')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, dict)
        # Should contain model configurations
    
    def test_api_languages_endpoint(self, client):
        """Test languages API endpoint."""
        response = client.get('/api/languages')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'en' in data
        assert data['en'] == 'English'
    
    @patch('src.web.app.db_manager.get_evaluation_statistics')
    def test_api_statistics_endpoint(self, mock_stats, client):
        """Test statistics API endpoint."""
        mock_stats.return_value = {
            'total_batches': 5,
            'total_prompts': 50,
            'completed_prompts': 45,
            'completion_rate': 0.9
        }
        
        response = client.get('/api/statistics')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['total_batches'] == 5
        assert data['completion_rate'] == 0.9
    
    @patch('src.web.app.db_manager.get_evaluation_statistics')
    def test_api_statistics_with_filters(self, mock_stats, client):
        """Test statistics API endpoint with filters."""
        mock_stats.return_value = {'total_batches': 2}
        
        response = client.get('/api/statistics?model=gpt-4&language=en&days=7')
        assert response.status_code == 200
        
        # Verify filters were passed to database manager
        mock_stats.assert_called_once_with(
            model_name='gpt-4',
            language='en',
            days=7
        )
    
    @patch('src.web.app.db_manager.list_batch_results')
    def test_api_results_endpoint(self, mock_results, client, mock_batch_result):
        """Test results API endpoint."""
        mock_results.return_value = [mock_batch_result]
        
        response = client.get('/api/results')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['batch_id'] == 'test-batch-1'
        assert data[0]['model_name'] == 'test-model'
    
    @patch('src.web.app.db_manager.list_batch_results')
    def test_api_results_with_filters(self, mock_results, client):
        """Test results API endpoint with filters."""
        mock_results.return_value = []
        
        response = client.get('/api/results?model=gpt-4&language=en&limit=10')
        assert response.status_code == 200
        
        # Verify filters were passed
        mock_results.assert_called_once_with(
            model_name='gpt-4',
            language='en',
            category=None,
            limit=10
        )
    
    @patch('src.web.app.db_manager.delete_batch_result')
    def test_api_delete_result_success(self, mock_delete, client):
        """Test deleting result via API."""
        mock_delete.return_value = True
        
        response = client.delete('/api/results/test-batch-1/delete')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'message' in data
        mock_delete.assert_called_once_with('test-batch-1')
    
    @patch('src.web.app.db_manager.delete_batch_result')
    def test_api_delete_result_not_found(self, mock_delete, client):
        """Test deleting non-existent result via API."""
        mock_delete.return_value = False
        
        response = client.delete('/api/results/non-existent/delete')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_evaluate_page_get(self, client):
        """Test evaluation page GET request."""
        response = client.get('/evaluate')
        assert response.status_code == 200
        assert b'Start New Evaluation' in response.data
    
    def test_evaluate_page_post_invalid_model(self, client):
        """Test evaluation page POST with invalid model."""
        response = client.post('/evaluate', data={
            'model': 'invalid-model',
            'language': 'en',
            'max_prompts': '10'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid model selected' in response.data
    
    def test_evaluate_page_post_invalid_language(self, client):
        """Test evaluation page POST with invalid language."""
        response = client.post('/evaluate', data={
            'model': 'gpt-3.5-turbo',
            'language': 'invalid-lang',
            'max_prompts': '10'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid language selected' in response.data
    
    @patch('src.web.app.db_manager.list_batch_results')
    def test_results_page(self, mock_results, client, mock_batch_result):
        """Test results page."""
        mock_results.return_value = [mock_batch_result]
        
        response = client.get('/results')
        assert response.status_code == 200
        assert b'Evaluation Results' in response.data
    
    @patch('src.web.app.db_manager.get_batch_result')
    def test_result_detail_page(self, mock_get_result, client, mock_batch_result):
        """Test result detail page."""
        mock_get_result.return_value = mock_batch_result
        
        with patch('src.web.app.MetricsReporter.generate_comprehensive_report') as mock_report:
            mock_report.return_value = {'summary': {}}
            
            response = client.get('/results/test-batch-1')
            assert response.status_code == 200
    
    @patch('src.web.app.db_manager.get_batch_result')
    def test_result_detail_page_not_found(self, mock_get_result, client):
        """Test result detail page with non-existent result."""
        mock_get_result.return_value = None
        
        response = client.get('/results/non-existent', follow_redirects=True)
        assert response.status_code == 200
        assert b'Result not found' in response.data
    
    def test_settings_page_get(self, client):
        """Test settings page GET request."""
        response = client.get('/settings')
        assert response.status_code == 200
        assert b'Settings' in response.data
    
    def test_settings_page_post(self, client):
        """Test settings page POST request."""
        response = client.post('/settings', data={
            'batch_size': '20',
            'concurrent_requests': '10',
            'max_retries': '5'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Settings updated successfully' in response.data
    
    @patch('src.web.app.db_manager.list_batch_results')
    def test_analysis_page(self, mock_results, client, mock_batch_result):
        """Test analysis page."""
        mock_results.return_value = [mock_batch_result]
        
        with patch('src.web.app.MetricsReporter.generate_comprehensive_report') as mock_report:
            mock_report.return_value = {'summary': {}}
            
            response = client.get('/analysis')
            assert response.status_code == 200
            assert b'Analysis and comparison' in response.data or b'Analysis' in response.data


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment."""
    import os
    os.environ['MASB_ENVIRONMENT'] = 'testing'
    os.environ['FLASK_ENV'] = 'testing'