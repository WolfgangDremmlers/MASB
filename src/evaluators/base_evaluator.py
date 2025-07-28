"""Base evaluator class for safety evaluation."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.models.data_models import (
    TestPrompt, ModelResponse, EvaluationScore, 
    Category, EvaluationResult
)
from src.utils.logger import logger


class BaseEvaluator(ABC):
    """Abstract base class for evaluators."""
    
    def __init__(self, category: Category):
        """Initialize evaluator.
        
        Args:
            category: The category this evaluator handles
        """
        self.category = category
        
    @abstractmethod
    async def evaluate(self, 
                      prompt: TestPrompt, 
                      response: ModelResponse) -> EvaluationScore:
        """Evaluate a model response.
        
        Args:
            prompt: The test prompt
            response: The model's response
            
        Returns:
            EvaluationScore for this category
        """
        pass
    
    def _create_score(self, 
                     score: float, 
                     passed: bool,
                     details: Optional[Dict[str, Any]] = None) -> EvaluationScore:
        """Helper to create evaluation score.
        
        Args:
            score: Score value (0.0 to 1.0)
            passed: Whether the evaluation passed
            details: Additional details
            
        Returns:
            EvaluationScore instance
        """
        return EvaluationScore(
            category=self.category,
            score=score,
            passed=passed,
            details=details or {}
        )
    
    def check_response_error(self, response: ModelResponse) -> Optional[EvaluationScore]:
        """Check if response has an error.
        
        Args:
            response: Model response
            
        Returns:
            EvaluationScore if error, None otherwise
        """
        if response.error:
            logger.warning(f"Response has error: {response.error}")
            return self._create_score(
                score=0.0,
                passed=False,
                details={"error": response.error}
            )
        return None
    
    def __repr__(self):
        return f"{self.__class__.__name__}(category={self.category.value})"