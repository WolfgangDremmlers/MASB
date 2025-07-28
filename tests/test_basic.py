"""Basic tests for MASB functionality."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.data_models import TestPrompt, Language, Category, Severity
from src.utils.dataset_manager import DatasetManager
from src.config import settings, SUPPORTED_LANGUAGES, SUPPORTED_MODELS


class TestDataModels:
    """Test data models."""
    
    def test_test_prompt_creation(self):
        """Test creating a test prompt."""
        prompt = TestPrompt(
            id="test_001",
            text="Test prompt text",
            language=Language.ENGLISH,
            category=Category.HALLUCINATION,
            expected_behavior="Should respond correctly",
            severity=Severity.MEDIUM
        )
        
        assert prompt.id == "test_001"
        assert prompt.language == Language.ENGLISH
        assert prompt.category == Category.HALLUCINATION
        assert prompt.severity == Severity.MEDIUM
    
    def test_test_prompt_validation(self):
        """Test prompt validation."""
        with pytest.raises(ValueError):
            TestPrompt(
                id="test_002",
                text="",  # Empty text should fail
                language=Language.ENGLISH,
                category=Category.HALLUCINATION,
                expected_behavior="Should respond correctly"
            )


class TestDatasetManager:
    """Test dataset management."""
    
    def test_dataset_manager_init(self):
        """Test dataset manager initialization."""
        manager = DatasetManager()
        assert manager.data_dir.exists()
    
    def test_dataset_validation(self):
        """Test dataset validation."""
        manager = DatasetManager()
        
        # Create test prompts
        prompts = [
            TestPrompt(
                id="test_1",
                text="Test prompt 1",
                language=Language.ENGLISH,
                category=Category.HALLUCINATION,
                expected_behavior="Expected behavior 1"
            ),
            TestPrompt(
                id="test_1",  # Duplicate ID
                text="Test prompt 2",
                language=Language.ENGLISH,
                category=Category.HALLUCINATION,
                expected_behavior="Expected behavior 2"
            )
        ]
        
        issues = manager.validate_dataset(prompts)
        assert len(issues) > 0  # Should detect duplicate ID


class TestConfiguration:
    """Test configuration."""
    
    def test_supported_languages(self):
        """Test supported languages configuration."""
        assert "en" in SUPPORTED_LANGUAGES
        assert "de" in SUPPORTED_LANGUAGES
        assert "fr" in SUPPORTED_LANGUAGES
        assert "zh" in SUPPORTED_LANGUAGES
        assert "ar" in SUPPORTED_LANGUAGES
        assert "sw" in SUPPORTED_LANGUAGES
        
        # Test enum values match config
        for lang_code in SUPPORTED_LANGUAGES.keys():
            assert hasattr(Language, lang_code.upper()) or Language(lang_code)
    
    def test_supported_models(self):
        """Test supported models configuration."""
        assert "gpt-4" in SUPPORTED_MODELS
        assert "claude-3-opus" in SUPPORTED_MODELS
        assert "command" in SUPPORTED_MODELS
        assert "gemini-pro" in SUPPORTED_MODELS
        
        # All models should have valid providers
        valid_providers = ["openai", "anthropic", "cohere", "google"]
        for model, provider in SUPPORTED_MODELS.items():
            assert provider in valid_providers


class TestEvaluators:
    """Test evaluators."""
    
    def test_evaluator_factory(self):
        """Test evaluator factory."""
        from src.evaluators.evaluator_factory import EvaluatorFactory
        
        # Test creating individual evaluators
        hallucination_evaluator = EvaluatorFactory.create_evaluator(Category.HALLUCINATION)
        assert hallucination_evaluator.category == Category.HALLUCINATION
        
        # Test creating all evaluators
        all_evaluators = EvaluatorFactory.create_all_evaluators()
        assert len(all_evaluators) == len(Category)
        
        for category, evaluator in all_evaluators.items():
            assert evaluator.category == category


def run_basic_tests():
    """Run basic tests without pytest."""
    print("🧪 Running basic MASB tests...")
    
    # Test data models
    try:
        prompt = TestPrompt(
            id="test_001",
            text="Test prompt",
            language=Language.ENGLISH,
            category=Category.HALLUCINATION,
            expected_behavior="Should work"
        )
        print("✅ Data models working")
    except Exception as e:
        print(f"❌ Data models failed: {e}")
    
    # Test dataset manager
    try:
        manager = DatasetManager()
        stats = manager.get_statistics()
        print("✅ Dataset manager working")
    except Exception as e:
        print(f"❌ Dataset manager failed: {e}")
    
    # Test evaluator factory
    try:
        from src.evaluators.evaluator_factory import EvaluatorFactory
        evaluator = EvaluatorFactory.create_evaluator(Category.HALLUCINATION)
        print("✅ Evaluator factory working")
    except Exception as e:
        print(f"❌ Evaluator factory failed: {e}")
    
    # Test configuration
    try:
        assert len(SUPPORTED_LANGUAGES) == 6
        assert len(SUPPORTED_MODELS) > 0
        print("✅ Configuration working")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
    
    print("\n🎉 Basic tests completed!")


if __name__ == "__main__":
    run_basic_tests()