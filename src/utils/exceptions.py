"""Custom exceptions for MASB."""

from typing import Optional, Dict, Any


class MASBException(Exception):
    """Base exception for all MASB-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize MASB exception.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class ConfigurationError(MASBException):
    """Raised when there's a configuration error."""
    pass


class APIError(MASBException):
    """Base class for API-related errors."""
    
    def __init__(self, message: str, provider: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.provider = provider
        self.status_code = status_code


class APIKeyError(APIError):
    """Raised when API key is missing or invalid."""
    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, message: str, provider: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, provider, **kwargs)
        self.retry_after = retry_after


class ModelNotSupportedError(MASBException):
    """Raised when a model is not supported."""
    
    def __init__(self, model_name: str, supported_models: list):
        message = f"Model '{model_name}' is not supported. Supported models: {supported_models}"
        super().__init__(message, {"model_name": model_name, "supported_models": supported_models})
        self.model_name = model_name
        self.supported_models = supported_models


class LanguageNotSupportedError(MASBException):
    """Raised when a language is not supported."""
    
    def __init__(self, language: str, supported_languages: list):
        message = f"Language '{language}' is not supported. Supported languages: {supported_languages}"
        super().__init__(message, {"language": language, "supported_languages": supported_languages})
        self.language = language
        self.supported_languages = supported_languages


class EvaluationError(MASBException):
    """Raised when evaluation fails."""
    
    def __init__(self, message: str, prompt_id: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.prompt_id = prompt_id


class DatasetError(MASBException):
    """Raised when there's an issue with dataset operations."""
    pass


class ValidationError(MASBException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None, **kwargs):
        super().__init__(message, **kwargs)
        self.field = field
        self.value = value


class CacheError(MASBException):
    """Raised when cache operations fail."""
    pass


class AnalysisError(MASBException):
    """Raised when analysis operations fail."""
    pass


class TimeoutError(MASBException):
    """Raised when operations timeout."""
    
    def __init__(self, message: str, timeout_duration: Optional[float] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.timeout_duration = timeout_duration


class ResourceError(MASBException):
    """Raised when resource operations fail."""
    pass


class ProviderError(MASBException):
    """Raised when provider operations fail."""
    
    def __init__(self, message: str, provider: str, **kwargs):
        super().__init__(message, **kwargs)
        self.provider = provider