"""Factory for creating evaluators."""

from typing import Dict, Type, List
from src.evaluators.base_evaluator import BaseEvaluator
from src.evaluators.hallucination_evaluator import HallucinationEvaluator
from src.evaluators.harmful_content_evaluator import HarmfulContentEvaluator
from src.evaluators.bias_evaluator import BiasEvaluator
from src.evaluators.refusal_consistency_evaluator import RefusalConsistencyEvaluator
from src.evaluators.privacy_leak_evaluator import PrivacyLeakEvaluator
from src.evaluators.instruction_following_evaluator import InstructionFollowingEvaluator
from src.models.data_models import Category
from src.utils.logger import logger


class EvaluatorFactory:
    """Factory class for creating evaluators."""
    
    _evaluators: Dict[Category, Type[BaseEvaluator]] = {
        Category.HALLUCINATION: HallucinationEvaluator,
        Category.HARMFUL_CONTENT: HarmfulContentEvaluator,
        Category.BIAS: BiasEvaluator,
        Category.REFUSAL_CONSISTENCY: RefusalConsistencyEvaluator,
        Category.PRIVACY_LEAK: PrivacyLeakEvaluator,
        Category.INSTRUCTION_FOLLOWING: InstructionFollowingEvaluator,
    }
    
    @classmethod
    def create_evaluator(cls, category: Category) -> BaseEvaluator:
        """Create an evaluator for a specific category.
        
        Args:
            category: Evaluation category
            
        Returns:
            Evaluator instance
            
        Raises:
            ValueError: If category is not supported
        """
        evaluator_class = cls._evaluators.get(category)
        if not evaluator_class:
            raise ValueError(f"No evaluator found for category: {category.value}")
        
        logger.info(f"Creating evaluator for category: {category.value}")
        return evaluator_class()
    
    @classmethod
    def create_all_evaluators(cls) -> Dict[Category, BaseEvaluator]:
        """Create evaluators for all categories.
        
        Returns:
            Dictionary mapping categories to evaluator instances
        """
        evaluators = {}
        for category in Category:
            try:
                evaluators[category] = cls.create_evaluator(category)
            except ValueError as e:
                logger.warning(f"Failed to create evaluator: {e}")
        
        return evaluators
    
    @classmethod
    def get_evaluator_for_prompt(cls, prompt_category: Category) -> BaseEvaluator:
        """Get the appropriate evaluator for a prompt's category.
        
        Args:
            prompt_category: The category of the prompt
            
        Returns:
            Evaluator instance
        """
        return cls.create_evaluator(prompt_category)
    
    @classmethod
    def register_evaluator(cls, category: Category, evaluator_class: Type[BaseEvaluator]):
        """Register a new evaluator class.
        
        Args:
            category: Category for the evaluator
            evaluator_class: Evaluator class
        """
        cls._evaluators[category] = evaluator_class
        logger.info(f"Registered evaluator for category: {category.value}")
    
    @classmethod
    def list_categories(cls) -> List[Category]:
        """List all supported categories."""
        return list(cls._evaluators.keys())