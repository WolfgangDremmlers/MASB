# Contributing to MASB

Thank you for your interest in contributing to MASB (Multilingual Adversarial Safety Benchmark)! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Style Guidelines](#style-guidelines)
- [Review Process](#review-process)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Docker (optional but recommended)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/MASB.git
   cd MASB
   ```

## Development Setup

### Local Development

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. Initialize the database:
   ```bash
   python init_database.py
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

### Docker Development

1. Build and start development environment:
   ```bash
   ./docker/manage.sh start dev
   ```

2. The application will be available at http://localhost:8080

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-evaluator`
- `bugfix/fix-database-connection`
- `docs/update-api-documentation`
- `refactor/improve-error-handling`

### Commit Messages

Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (no logic changes)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(evaluator): add bias detection evaluator

fix(database): resolve connection timeout issues

docs(api): update endpoint documentation
```

## Testing

### Running Tests

```bash
# Run all tests
python run_tests.py --type all --coverage

# Run specific test types
python run_tests.py --type unit
python run_tests.py --type integration
python run_tests.py --type api

# Run code quality checks
python run_tests.py --type quality
```

### Writing Tests

1. **Unit Tests**: Test individual components in isolation
   - Location: `tests/unit/`
   - Mock external dependencies
   - Fast execution

2. **Integration Tests**: Test component interactions
   - Location: `tests/integration/`
   - Use test databases
   - May be slower

3. **API Tests**: Test web endpoints
   - Location: `tests/api/`
   - Test request/response cycles
   - Verify error handling

### Test Guidelines

- Write tests for new features and bug fixes
- Maintain or improve test coverage
- Use descriptive test names
- Include both positive and negative test cases
- Mock external services (LLM APIs)

## Submitting Changes

### Pull Request Process

1. **Create a Pull Request**:
   - Use the provided PR template
   - Include a clear description of changes
   - Link related issues

2. **PR Requirements**:
   - All tests must pass
   - Code coverage should not decrease
   - Documentation updated if needed
   - No merge conflicts

3. **Review Process**:
   - At least one maintainer review required
   - Address review feedback
   - Squash commits if requested

### Before Submitting

Run the pre-submission checklist:

```bash
# Code formatting
black .

# Linting
flake8 src tests

# Type checking
mypy src

# Security scan
bandit -r src

# Tests
python run_tests.py --type all --coverage
```

## Style Guidelines

### Python Code Style

- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use meaningful variable and function names
- Add type hints for function parameters and return values
- Write docstrings for public functions and classes

### Code Organization

```python
"""Module docstring."""

# Standard library imports
import os
import sys

# Third-party imports
import pandas as pd
import pytest

# Local imports
from src.models.data_models import TestPrompt
from src.utils.logger import logger


class MyClass:
    """Class docstring."""
    
    def __init__(self, param: str):
        """Initialize with parameter."""
        self.param = param
    
    def public_method(self, arg: int) -> str:
        """Public method with clear docstring."""
        return self._private_method(arg)
    
    def _private_method(self, arg: int) -> str:
        """Private method."""
        return f"{self.param}_{arg}"
```

### Documentation

- Use clear, concise language
- Include code examples
- Update docstrings when changing function signatures
- Add comments for complex logic

## Review Process

### What Reviewers Look For

1. **Correctness**: Does the code work as intended?
2. **Testing**: Are there adequate tests?
3. **Performance**: Any performance implications?
4. **Security**: Are there security considerations?
5. **Maintainability**: Is the code readable and well-structured?
6. **Documentation**: Is it properly documented?

### Responding to Reviews

- Be responsive to feedback
- Ask questions if feedback is unclear
- Make requested changes promptly
- Thank reviewers for their time

## Development Guidelines

### Adding New Features

1. **LLM Providers**:
   - Extend `BaseProvider` class
   - Implement async methods
   - Add comprehensive error handling
   - Include rate limiting

2. **Evaluators**:
   - Extend `BaseEvaluator` class
   - Support multiple languages
   - Include confidence scores
   - Add detailed reasoning

3. **Web Interface**:
   - Follow existing UI patterns
   - Add responsive design
   - Include error states
   - Test accessibility

### Database Changes

1. Create Alembic migrations for schema changes
2. Test migrations on sample data
3. Update model classes
4. Add corresponding tests

### Configuration

- Add new settings to `src/config.py`
- Update environment variable documentation
- Provide sensible defaults
- Validate configuration values

## Performance Considerations

- Profile code for performance bottlenecks
- Use async/await for I/O operations
- Implement caching where appropriate
- Consider memory usage for large datasets
- Add performance tests for critical paths

## Security Guidelines

- Never commit API keys or secrets
- Validate all user inputs
- Use parameterized database queries
- Implement proper authentication/authorization
- Follow security best practices for web applications

## Getting Help

- Check existing issues and documentation
- Ask questions in GitHub discussions
- Join our community channels
- Reach out to maintainers

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Project documentation

Thank you for contributing to MASB! 🚀