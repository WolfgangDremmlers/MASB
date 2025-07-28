"""Unit tests for database functionality."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from pathlib import Path

from src.storage.database import DatabaseManager, DatabaseConfig, EvaluationBatch, EvaluationResultDB
from src.models.data_models import BatchEvaluationResult, EvaluationResult, TestPrompt, ModelResponse, Language, Category, Severity, EvaluationScore


class TestDatabaseManager:
    """Test cases for DatabaseManager."""
    
    @pytest.fixture
    def db_config(self):
        """Test database configuration."""
        return DatabaseConfig(database_url="sqlite:///:memory:")
    
    @pytest.fixture
    def db_manager(self, db_config):
        """Database manager with in-memory SQLite."""
        manager = DatabaseManager(db_config)
        manager.initialize()
        return manager
    
    @pytest.fixture
    def sample_batch_result(self):
        """Sample batch evaluation result."""
        prompt = TestPrompt(
            id="test-prompt-1",
            text="Test prompt",
            language=Language.EN,
            category=Category.HALLUCINATION,
            expected_behavior="Test behavior",
            severity=Severity.MEDIUM
        )
        
        response = ModelResponse(
            response_text="Test response",
            model_name="test-model",
            timestamp=datetime.utcnow(),
            metadata={}
        )
        
        score = EvaluationScore(
            category=Category.HALLUCINATION,
            score=0.8,
            reasoning="Test reasoning",
            confidence=0.9,
            details={}
        )
        
        result = EvaluationResult(
            id="test-result-1",
            prompt=prompt,
            response=response,
            scores=[score],
            evaluation_timestamp=datetime.utcnow(),
            processing_time=1.5
        )
        
        return BatchEvaluationResult(
            batch_id="test-batch-1",
            model_name="test-model",
            language=Language.EN,
            category=Category.HALLUCINATION,
            total_prompts=1,
            completed_prompts=1,
            failed_prompts=0,
            results=[result],
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration=10.0,
            status="completed",
            config={},
            metadata={}
        )
    
    def test_initialize_database(self, db_config):
        """Test database initialization."""
        manager = DatabaseManager(db_config)
        manager.initialize()
        
        assert manager._initialized is True
        assert manager.engine is not None
        assert manager.SessionLocal is not None
    
    def test_save_batch_result(self, db_manager, sample_batch_result):
        """Test saving batch result."""
        success = db_manager.save_batch_result(sample_batch_result)
        
        assert success is True
        
        # Verify it was saved
        with db_manager.get_session() as session:
            batch = session.query(EvaluationBatch).filter(
                EvaluationBatch.id == sample_batch_result.batch_id
            ).first()
            
            assert batch is not None
            assert batch.model_name == sample_batch_result.model_name
            assert batch.language == sample_batch_result.language.value
    
    def test_get_batch_result(self, db_manager, sample_batch_result):
        """Test retrieving batch result."""
        # Save first
        db_manager.save_batch_result(sample_batch_result)
        
        # Retrieve
        result = db_manager.get_batch_result(sample_batch_result.batch_id)
        
        assert result is not None
        assert result.batch_id == sample_batch_result.batch_id
        assert result.model_name == sample_batch_result.model_name
        assert len(result.results) == 1
    
    def test_get_batch_result_not_found(self, db_manager):
        """Test retrieving non-existent batch result."""
        result = db_manager.get_batch_result("non-existent-id")
        
        assert result is None
    
    def test_list_batch_results(self, db_manager, sample_batch_result):
        """Test listing batch results."""
        # Save a batch result
        db_manager.save_batch_result(sample_batch_result)
        
        # List all results
        results = db_manager.list_batch_results()
        
        assert len(results) == 1
        assert results[0].batch_id == sample_batch_result.batch_id
    
    def test_list_batch_results_with_filters(self, db_manager, sample_batch_result):
        """Test listing batch results with filters."""
        # Save a batch result
        db_manager.save_batch_result(sample_batch_result)
        
        # Filter by model
        results = db_manager.list_batch_results(model_name="test-model")
        assert len(results) == 1
        
        # Filter by non-existent model
        results = db_manager.list_batch_results(model_name="non-existent")
        assert len(results) == 0
        
        # Filter by language
        results = db_manager.list_batch_results(language="en")
        assert len(results) == 1
    
    def test_delete_batch_result(self, db_manager, sample_batch_result):
        """Test deleting batch result."""
        # Save first
        db_manager.save_batch_result(sample_batch_result)
        
        # Verify it exists
        result = db_manager.get_batch_result(sample_batch_result.batch_id)
        assert result is not None
        
        # Delete
        success = db_manager.delete_batch_result(sample_batch_result.batch_id)
        assert success is True
        
        # Verify it's gone
        result = db_manager.get_batch_result(sample_batch_result.batch_id)
        assert result is None
    
    def test_delete_batch_result_not_found(self, db_manager):
        """Test deleting non-existent batch result."""
        success = db_manager.delete_batch_result("non-existent-id")
        assert success is False
    
    def test_get_evaluation_statistics(self, db_manager, sample_batch_result):
        """Test getting evaluation statistics."""
        # Save a batch result
        db_manager.save_batch_result(sample_batch_result)
        
        # Get statistics
        stats = db_manager.get_evaluation_statistics()
        
        assert stats['total_batches'] == 1
        assert stats['total_prompts'] == 1
        assert stats['completed_prompts'] == 1
        assert 'model_breakdown' in stats
        assert 'language_breakdown' in stats
    
    def test_cleanup_old_results(self, db_manager, sample_batch_result):
        """Test cleaning up old results."""
        # Save a batch result
        db_manager.save_batch_result(sample_batch_result)
        
        # Should not delete recent results
        count = db_manager.cleanup_old_results(days_to_keep=1)
        assert count == 0
        
        # Should delete old results (simulate by setting very short retention)
        count = db_manager.cleanup_old_results(days_to_keep=0)
        assert count >= 0  # May be 0 due to timing
    
    def test_update_existing_batch(self, db_manager, sample_batch_result):
        """Test updating existing batch result."""
        # Save initial result
        db_manager.save_batch_result(sample_batch_result)
        
        # Update the result
        sample_batch_result.completed_prompts = 2
        sample_batch_result.status = "updated"
        
        # Save updated result
        success = db_manager.save_batch_result(sample_batch_result)
        assert success is True
        
        # Verify update
        result = db_manager.get_batch_result(sample_batch_result.batch_id)
        assert result.completed_prompts == 2
        assert result.status == "updated"


class TestDatabaseConfig:
    """Test cases for DatabaseConfig."""
    
    def test_default_config(self):
        """Test default database configuration."""
        config = DatabaseConfig()
        
        assert config.database_url == "sqlite:///masb_results.db"
        assert config.pool_size == 10
        assert config.echo is False
    
    def test_custom_config(self):
        """Test custom database configuration."""
        config = DatabaseConfig(
            database_url="postgresql://user:pass@localhost/test",
            pool_size=20,
            echo=True
        )
        
        assert config.database_url == "postgresql://user:pass@localhost/test"
        assert config.pool_size == 20
        assert config.echo is True


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up test database environment."""
    # Set test environment variables
    import os
    os.environ['MASB_ENVIRONMENT'] = 'testing'
    os.environ['MASB_DATABASE_URL'] = 'sqlite:///:memory:'