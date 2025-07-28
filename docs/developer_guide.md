# MASB Developer Guide

This guide provides comprehensive information for developers who want to contribute to, extend, or integrate with MASB.

## Table of Contents
- [Development Setup](#development-setup)
- [Architecture Overview](#architecture-overview)
- [Contributing Guidelines](#contributing-guidelines)
- [Adding New Features](#adding-new-features)
- [Testing Strategy](#testing-strategy)
- [Code Style Guide](#code-style-guide)
- [Debugging and Troubleshooting](#debugging-and-troubleshooting)

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- API keys for testing (optional but recommended)

### Environment Setup

1. **Clone and setup development environment:**
   ```bash
   git clone https://github.com/WolfgangDremmler/MASB.git
   cd MASB
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If exists
   ```

2. **Setup pre-commit hooks:**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Development Dependencies

Create `requirements-dev.txt`:
```
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0
sphinx>=6.0.0
sphinx-rtd-theme>=1.0.0
jupyter>=1.0.0
```

## Architecture Overview

### Core Components

```
MASB Architecture
├── Evaluation Engine (Core orchestrator)
├── Providers (LLM API interfaces)
├── Evaluators (Safety assessment logic)
├── Data Models (Type definitions)
├── Dataset Manager (Data handling)
├── Analysis Tools (Result processing)
└── Utilities (Logging, caching, etc.)
```

### Data Flow

```
1. Load Prompts → 2. Generate Responses → 3. Evaluate → 4. Analyze → 5. Report
     ↓                      ↓                  ↓           ↓          ↓
DatasetManager      ProviderFactory    EvaluatorFactory  Analyzer  Reporter
```

### Module Dependencies

```python
# Core dependencies
src.config → All modules (settings)
src.models.data_models → All modules (types)
src.utils.logger → All modules (logging)

# Evaluation flow
EvaluationEngine ← ProviderFactory
EvaluationEngine ← EvaluatorFactory
EvaluationEngine ← DatasetManager

# Analysis flow
ResultAnalyzer ← EvaluationResults
```

## Contributing Guidelines

### Code Contribution Workflow

1. **Fork and Branch:**
   ```bash
   git fork https://github.com/WolfgangDremmler/MASB.git
   git checkout -b feature/new-evaluator
   ```

2. **Develop and Test:**
   ```bash
   # Make changes
   # Run tests
   pytest tests/
   
   # Check code style
   black src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

3. **Submit PR:**
   ```bash
   git add .
   git commit -m "feat: add custom evaluator support"
   git push origin feature/new-evaluator
   # Create PR on GitHub
   ```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: fix bug
docs: update documentation
style: formatting changes
refactor: code refactoring
test: add tests
chore: maintenance tasks
```

### Pull Request Guidelines

- **Title:** Clear, descriptive title
- **Description:** What, why, and how
- **Tests:** Include tests for new features
- **Documentation:** Update relevant docs
- **Breaking Changes:** Clearly marked

## Adding New Features

### Adding a New Evaluator

1. **Create evaluator class:**
   ```python
   # src/evaluators/custom_evaluator.py
   from src.evaluators.base_evaluator import BaseEvaluator
   from src.models.data_models import Category, EvaluationScore
   
   class CustomEvaluator(BaseEvaluator):
       def __init__(self):
           super().__init__(Category.CUSTOM)
       
       async def evaluate(self, prompt, response):
           # Implementation
           return self._create_score(score=0.8, passed=True)
   ```

2. **Register evaluator:**
   ```python
   # src/evaluators/__init__.py
   from src.evaluators.custom_evaluator import CustomEvaluator
   
   __all__ = [..., "CustomEvaluator"]
   ```

3. **Update factory:**
   ```python
   # src/evaluators/evaluator_factory.py
   from src.evaluators.custom_evaluator import CustomEvaluator
   
   _evaluators = {
       # ...existing evaluators...
       Category.CUSTOM: CustomEvaluator,
   }
   ```

4. **Add tests:**
   ```python
   # tests/test_custom_evaluator.py
   import pytest
   from src.evaluators.custom_evaluator import CustomEvaluator
   
   @pytest.mark.asyncio
   async def test_custom_evaluator():
       evaluator = CustomEvaluator()
       # Test implementation
   ```

### Adding a New Provider

1. **Implement provider:**
   ```python
   # src/models/custom_provider.py
   from src.models.base_provider import BaseLLMProvider
   
   class CustomProvider(BaseLLMProvider):
       def _initialize_client(self):
           # Initialize API client
           
       async def _make_request(self, prompt):
           # Make API request
           
       def _extract_response_text(self, response):
           # Extract response text
   ```

2. **Register in factory:**
   ```python
   # src/models/provider_factory.py
   from src.models.custom_provider import CustomProvider
   
   _providers = {
       # ...existing providers...
       "custom": CustomProvider,
   }
   ```

3. **Update configuration:**
   ```python
   # src/config.py
   SUPPORTED_MODELS = {
       # ...existing models...
       "custom-model": "custom",
   }
   ```

### Adding New Languages

1. **Update language enum:**
   ```python
   # src/models/data_models.py
   class Language(str, Enum):
       # ...existing languages...
       CUSTOM = "custom"
   ```

2. **Update configuration:**
   ```python
   # src/config.py
   SUPPORTED_LANGUAGES = {
       # ...existing languages...
       "custom": "Custom Language",
   }
   ```

3. **Add example prompts:**
   ```python
   # src/utils/generate_examples.py
   EXAMPLE_PROMPTS = {
       # ...existing languages...
       Language.CUSTOM: {
           Category.HALLUCINATION: [
               # Custom language prompts
           ]
       }
   }
   ```

## Testing Strategy

### Test Structure

```
tests/
├── unit/                 # Unit tests
│   ├── test_models.py
│   ├── test_evaluators.py
│   └── test_providers.py
├── integration/          # Integration tests
│   ├── test_evaluation_engine.py
│   └── test_end_to_end.py
├── fixtures/             # Test data
│   ├── sample_prompts.json
│   └── mock_responses.json
└── conftest.py          # Pytest configuration
```

### Writing Tests

#### Unit Tests

```python
# tests/unit/test_evaluators.py
import pytest
from src.evaluators.hallucination_evaluator import HallucinationEvaluator
from src.models.data_models import TestPrompt, ModelResponse

@pytest.fixture
def sample_prompt():
    return TestPrompt(
        id="test_001",
        text="Test prompt",
        language="en",
        category="hallucination",
        expected_behavior="Should respond correctly"
    )

@pytest.fixture
def sample_response():
    return ModelResponse(
        prompt_id="test_001",
        model_name="test_model",
        provider="test",
        response_text="Test response",
        response_time=1.0
    )

@pytest.mark.asyncio
async def test_hallucination_evaluator(sample_prompt, sample_response):
    evaluator = HallucinationEvaluator()
    score = await evaluator.evaluate(sample_prompt, sample_response)
    
    assert 0 <= score.score <= 1
    assert isinstance(score.passed, bool)
```

#### Integration Tests

```python
# tests/integration/test_evaluation_engine.py
import pytest
from src.evaluation_engine import EvaluationEngine

@pytest.mark.asyncio
async def test_full_evaluation_flow():
    # Use mock provider for testing
    engine = EvaluationEngine("mock_model")
    
    result = await engine.evaluate_dataset(
        language="en",
        max_prompts=5
    )
    
    assert result.total_prompts == 5
    assert result.completed_prompts <= result.total_prompts
```

#### Mock Objects

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.fixture
def mock_provider():
    provider = Mock()
    provider.generate_response = AsyncMock(return_value=Mock(
        response_text="Mock response",
        response_time=1.0,
        error=None
    ))
    return provider

@pytest.fixture
def mock_evaluator():
    evaluator = Mock()
    evaluator.evaluate = AsyncMock(return_value=Mock(
        score=0.8,
        passed=True,
        category="test"
    ))
    return evaluator
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_evaluators.py

# With coverage
pytest --cov=src --cov-report=html

# Async tests only
pytest -m asyncio

# Skip slow tests
pytest -m "not slow"
```

## Code Style Guide

### Python Style

Follow [PEP 8](https://pep8.org/) with these additions:

#### Import Organization

```python
# Standard library
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Optional

# Third-party
import pandas as pd
import numpy as np
from pydantic import BaseModel

# Local imports
from src.models.data_models import TestPrompt
from src.utils.logger import logger
```

#### Type Hints

Always use type hints:

```python
from typing import List, Dict, Optional, Union

def process_results(
    results: List[EvaluationResult],
    filter_passed: bool = True
) -> Dict[str, float]:
    """Process evaluation results and return summary statistics."""
    pass

async def evaluate_prompt(
    self,
    prompt: TestPrompt
) -> EvaluationResult:
    """Evaluate a single prompt asynchronously."""
    pass
```

#### Documentation

Use Google-style docstrings:

```python
def calculate_score(
    self,
    responses: List[str],
    expected: str
) -> float:
    """Calculate evaluation score based on responses.
    
    Args:
        responses: List of model responses to evaluate
        expected: Expected behavior description
        
    Returns:
        Score between 0.0 and 1.0, where 1.0 is perfect
        
    Raises:
        ValueError: If responses list is empty
        
    Example:
        >>> evaluator = CustomEvaluator()
        >>> score = evaluator.calculate_score(["good response"], "helpful")
        >>> assert 0 <= score <= 1
    """
    pass
```

#### Error Handling

```python
# Specific exceptions
try:
    result = await provider.generate_response(prompt)
except APIError as e:
    logger.error(f"API error: {e}")
    raise
except RateLimitError as e:
    logger.warning(f"Rate limited, retrying: {e}")
    await asyncio.sleep(1)
    # Retry logic
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise EvaluationError(f"Failed to evaluate prompt: {e}") from e
```

#### Async/Await Best Practices

```python
# Use async/await properly
async def process_batch(self, prompts: List[TestPrompt]) -> List[EvaluationResult]:
    """Process prompts concurrently with proper resource management."""
    semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def process_single(prompt):
        async with semaphore:
            return await self.evaluate_prompt(prompt)
    
    tasks = [process_single(prompt) for prompt in prompts]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

### Configuration Management

```python
# Use pydantic for configuration
from pydantic_settings import BaseSettings

class EvaluatorConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EVALUATOR_")
    
    threshold: float = 0.7
    max_retries: int = 3
    timeout: int = 60
    
    @validator('threshold')
    def validate_threshold(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Threshold must be between 0 and 1')
        return v
```

## Debugging and Troubleshooting

### Logging Best Practices

```python
from src.utils.logger import logger

# Different log levels
logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error")

# Structured logging
logger.info(
    "Evaluation completed",
    extra={
        "model": "gpt-4",
        "language": "en",
        "prompts": 100,
        "duration": 45.2
    }
)
```

### Performance Profiling

```python
import cProfile
import time
from functools import wraps

def profile_async(func):
    """Decorator to profile async functions."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time
        logger.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper

@profile_async
async def evaluate_dataset(self, language: str):
    # Implementation
    pass
```

### Memory Management

```python
import gc
import psutil
import tracemalloc

def monitor_memory():
    """Monitor memory usage during evaluation."""
    process = psutil.Process()
    memory_info = process.memory_info()
    logger.info(f"Memory usage: {memory_info.rss / 1024 / 1024:.1f} MB")

# Track memory allocations
tracemalloc.start()

# Your code here

current, peak = tracemalloc.get_traced_memory()
logger.info(f"Current memory: {current / 1024 / 1024:.1f} MB")
logger.info(f"Peak memory: {peak / 1024 / 1024:.1f} MB")
tracemalloc.stop()
```

### Common Issues and Solutions

#### 1. API Rate Limiting

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def make_api_request(self, prompt: str):
    """Make API request with exponential backoff retry."""
    try:
        response = await self.client.generate(prompt)
        return response
    except RateLimitError:
        logger.warning("Rate limited, retrying...")
        raise
```

#### 2. Memory Issues with Large Datasets

```python
async def process_large_dataset(self, prompts: List[TestPrompt]):
    """Process large datasets in chunks to manage memory."""
    chunk_size = 50
    results = []
    
    for i in range(0, len(prompts), chunk_size):
        chunk = prompts[i:i + chunk_size]
        chunk_results = await self.process_batch(chunk)
        results.extend(chunk_results)
        
        # Clear memory periodically
        if i % 500 == 0:
            gc.collect()
    
    return results
```

#### 3. Async Context Manager for Resources

```python
class EvaluationContext:
    """Context manager for evaluation resources."""
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self.initialize_providers()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
        await self.cleanup_resources()

# Usage
async with EvaluationContext() as ctx:
    results = await ctx.evaluate_dataset(prompts)
```

### Development Tools

#### Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
```

#### VS Code Configuration

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

This developer guide provides comprehensive information for contributing to and extending MASB. For questions or clarifications, please open an issue on GitHub.