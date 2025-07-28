"""Unit tests for MASB evaluation engine."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.evaluation_engine import EvaluationEngine
from src.models.data_models import TestPrompt, ModelResponse, Language, Category, Severity, ModelConfig
from src.utils.logger import logger


class TestEvaluationEngine:
    """Test cases for EvaluationEngine."""
    
    @pytest.fixture
    def mock_provider(self):
        """Mock LLM provider."""
        provider = Mock()
        provider.generate_response = AsyncMock(return_value=ModelResponse(
            response_text="This is a test response",
            model_name="test-model",
            timestamp=datetime.utcnow(),
            metadata={}
        ))
        return provider
    
    @pytest.fixture
    def test_prompt(self):
        """Test prompt fixture."""
        return TestPrompt(
            id="test-prompt-1",
            text="What is the capital of France?",
            language=Language.EN,
            category=Category.HALLUCINATION,
            expected_behavior="Should provide accurate information",
            severity=Severity.MEDIUM
        )
    
    @pytest.fixture
    def evaluation_engine(self, mock_provider):
        """Evaluation engine with mocked provider."""
        with patch('src.evaluation_engine.ProviderFactory.create_provider', return_value=mock_provider):
            with patch('src.evaluation_engine.db_manager.initialize'):
                engine = EvaluationEngine("test-model", use_database=False)
                return engine
    
    @pytest.mark.asyncio
    async def test_evaluate_prompt_success(self, evaluation_engine, test_prompt):
        """Test successful prompt evaluation."""
        # Mock evaluator
        mock_evaluator = Mock()
        mock_score = Mock()
        mock_score.category = Category.HALLUCINATION
        mock_score.score = 0.8
        mock_score.reasoning = "Test reasoning"
        mock_evaluator.evaluate = AsyncMock(return_value=mock_score)
        
        evaluation_engine.evaluators = {Category.HALLUCINATION: mock_evaluator}
        
        result = await evaluation_engine.evaluate_prompt(test_prompt)
        
        assert result is not None
        assert result.prompt == test_prompt
        assert len(result.scores) == 1
        assert result.scores[0] == mock_score
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_evaluate_prompt_no_evaluator(self, evaluation_engine, test_prompt):
        """Test prompt evaluation with no evaluator."""
        evaluation_engine.evaluators = {}
        
        result = await evaluation_engine.evaluate_prompt(test_prompt)
        
        assert result is not None
        assert result.prompt == test_prompt
        assert len(result.scores) == 0
    
    @pytest.mark.asyncio
    async def test_evaluate_dataset_empty(self, evaluation_engine):
        """Test dataset evaluation with no prompts."""
        with patch.object(evaluation_engine.dataset_manager, 'load_dataset', return_value=[]):
            result = await evaluation_engine.evaluate_dataset(Language.EN)
            
            assert result.total_prompts == 0
            assert result.completed_prompts == 0
            assert result.failed_prompts == 0
            assert len(result.results) == 0
    
    @pytest.mark.asyncio
    async def test_evaluate_dataset_with_prompts(self, evaluation_engine, test_prompt):
        """Test dataset evaluation with prompts."""
        prompts = [test_prompt]
        
        # Mock evaluator
        mock_evaluator = Mock()
        mock_score = Mock()
        mock_score.category = Category.HALLUCINATION
        mock_score.score = 0.8
        mock_evaluator.evaluate = AsyncMock(return_value=mock_score)
        evaluation_engine.evaluators = {Category.HALLUCINATION: mock_evaluator}
        
        with patch.object(evaluation_engine.dataset_manager, 'load_dataset', return_value=prompts):
            with patch.object(evaluation_engine, '_save_batch_result', new_callable=AsyncMock):
                result = await evaluation_engine.evaluate_dataset(Language.EN, max_prompts=1)
                
                assert result.total_prompts == 1
                assert result.completed_prompts == 1
                assert result.failed_prompts == 0
                assert len(result.results) == 1
    
    @pytest.mark.asyncio
    async def test_evaluate_prompt_with_cache(self, evaluation_engine, test_prompt):
        """Test prompt evaluation with caching."""
        # Mock cache manager
        mock_cache = Mock()
        cached_result = Mock()
        mock_cache.get = AsyncMock(return_value=cached_result)
        mock_cache.set = AsyncMock()
        evaluation_engine.cache_manager = mock_cache
        
        result = await evaluation_engine.evaluate_prompt(test_prompt)
        
        assert result == cached_result
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_not_called()
    
    def test_get_batch_result_from_database_no_db(self, evaluation_engine):
        """Test getting batch result when database is disabled."""
        evaluation_engine.use_database = False
        
        result = evaluation_engine.get_batch_result_from_database("test-id")
        
        assert result is None
    
    def test_list_batch_results_from_database_no_db(self, evaluation_engine):
        """Test listing batch results when database is disabled."""
        evaluation_engine.use_database = False
        
        results = evaluation_engine.list_batch_results_from_database()
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_evaluate_multiple_languages(self, evaluation_engine, test_prompt):
        """Test evaluation of multiple languages."""
        languages = [Language.EN, Language.DE]
        
        with patch.object(evaluation_engine, 'evaluate_dataset', new_callable=AsyncMock) as mock_eval:
            mock_result = Mock()
            mock_eval.return_value = mock_result
            
            results = await evaluation_engine.evaluate_multiple_languages(languages)
            
            assert len(results) == 2
            assert "en" in results
            assert "de" in results
            assert mock_eval.call_count == 2


class TestEvaluationEngineIntegration:
    """Integration tests for EvaluationEngine."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_evaluation_workflow(self):
        """Test complete evaluation workflow."""
        # This would require actual API keys and should be run in integration environment
        pytest.skip("Requires API keys and integration environment")
    
    @pytest.mark.integration
    def test_database_integration(self):
        """Test database integration."""
        pytest.skip("Requires database setup")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()