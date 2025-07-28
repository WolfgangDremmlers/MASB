"""Data models for MASB."""

from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class Language(str, Enum):
    """Supported languages."""
    ENGLISH = "en"
    GERMAN = "de"
    FRENCH = "fr"
    CHINESE = "zh"
    ARABIC = "ar"
    SWAHILI = "sw"


class Category(str, Enum):
    """Evaluation categories."""
    HALLUCINATION = "hallucination"
    HARMFUL_CONTENT = "harmful_content"
    BIAS = "bias"
    REFUSAL_CONSISTENCY = "refusal_consistency"
    PRIVACY_LEAK = "privacy_leak"
    INSTRUCTION_FOLLOWING = "instruction_following"


class Severity(str, Enum):
    """Severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TestPrompt(BaseModel):
    """Model for test prompts."""
    id: str
    text: str
    language: Language
    category: Category
    expected_behavior: str
    severity: Severity = Severity.MEDIUM
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    
    @validator('text')
    def text_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Prompt text cannot be empty')
        return v


class ModelResponse(BaseModel):
    """Model for LLM responses."""
    prompt_id: str
    model_name: str
    provider: str
    response_text: str
    response_time: float  # in seconds
    tokens_used: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvaluationScore(BaseModel):
    """Model for evaluation scores."""
    category: Category
    score: float  # 0.0 to 1.0
    passed: bool
    details: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('score')
    def score_in_range(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Score must be between 0 and 1')
        return v


class EvaluationResult(BaseModel):
    """Model for complete evaluation results."""
    id: str
    prompt: TestPrompt
    response: ModelResponse
    scores: List[EvaluationScore]
    overall_score: float
    passed: bool
    flags: List[str] = Field(default_factory=list)
    evaluator_version: str = "1.0.0"
    
    @validator('overall_score')
    def overall_score_in_range(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Overall score must be between 0 and 1')
        return v


class BatchEvaluationResult(BaseModel):
    """Model for batch evaluation results."""
    batch_id: str
    model_name: str
    language: Language
    total_prompts: int
    completed_prompts: int
    failed_prompts: int
    results: List[EvaluationResult]
    summary: Dict[Category, Dict[str, float]] = Field(default_factory=dict)
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # in seconds
    
    def calculate_summary(self):
        """Calculate summary statistics."""
        if not self.results:
            return
            
        category_scores = {cat: [] for cat in Category}
        
        for result in self.results:
            for score in result.scores:
                category_scores[score.category].append(score.score)
        
        self.summary = {}
        for category, scores in category_scores.items():
            if scores:
                self.summary[category] = {
                    "mean": sum(scores) / len(scores),
                    "min": min(scores),
                    "max": max(scores),
                    "pass_rate": sum(1 for s in scores if s >= 0.5) / len(scores)
                }


class ModelConfig(BaseModel):
    """Configuration for a specific model."""
    name: str
    provider: str
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop_sequences: List[str] = Field(default_factory=list)
    custom_params: Dict[str, Any] = Field(default_factory=dict)