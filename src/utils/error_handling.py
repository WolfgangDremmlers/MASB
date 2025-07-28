"""Error handling utilities and retry mechanisms for MASB."""

import asyncio
import functools
import time
from typing import Any, Callable, Optional, Type, Union, List
from tenacity import (
    retry, stop_after_attempt, wait_exponential, 
    retry_if_exception_type, before_sleep_log
)
import aiohttp
import openai
import anthropic

from src.utils.exceptions import (
    MASBException, APIError, RateLimitError, TimeoutError,
    APIKeyError, ProviderError
)
from src.utils.logger import logger


class ErrorHandler:
    """Central error handler for MASB operations."""
    
    def __init__(self):
        """Initialize error handler."""
        self.error_counts = {}
        self.last_errors = {}
    
    def handle_api_error(self, error: Exception, provider: str) -> MASBException:
        """Convert API errors to MASB exceptions.
        
        Args:
            error: Original exception
            provider: Provider name
            
        Returns:
            Converted MASB exception
        """
        # Track error
        self._track_error(provider, error)
        
        # Convert based on provider and error type
        if provider == "openai":
            return self._handle_openai_error(error)
        elif provider == "anthropic":
            return self._handle_anthropic_error(error)
        elif provider == "cohere":
            return self._handle_cohere_error(error)
        elif provider == "google":
            return self._handle_google_error(error)
        else:
            return self._handle_generic_error(error, provider)
    
    def _handle_openai_error(self, error: Exception) -> MASBException:
        """Handle OpenAI-specific errors."""
        if isinstance(error, openai.AuthenticationError):
            return APIKeyError(
                "Invalid OpenAI API key",
                provider="openai",
                details={"original_error": str(error)}
            )
        elif isinstance(error, openai.RateLimitError):
            retry_after = getattr(error, 'retry_after', None)
            return RateLimitError(
                "OpenAI rate limit exceeded",
                provider="openai",
                retry_after=retry_after,
                details={"original_error": str(error)}
            )
        elif isinstance(error, openai.APITimeoutError):
            return TimeoutError(
                "OpenAI API timeout",
                details={"provider": "openai", "original_error": str(error)}
            )
        elif isinstance(error, openai.BadRequestError):
            return APIError(
                f"OpenAI bad request: {error}",
                provider="openai",
                status_code=400,
                details={"original_error": str(error)}
            )
        else:
            return ProviderError(
                f"OpenAI error: {error}",
                provider="openai",
                details={"original_error": str(error)}
            )
    
    def _handle_anthropic_error(self, error: Exception) -> MASBException:
        """Handle Anthropic-specific errors."""
        if isinstance(error, anthropic.AuthenticationError):
            return APIKeyError(
                "Invalid Anthropic API key",
                provider="anthropic",
                details={"original_error": str(error)}
            )
        elif isinstance(error, anthropic.RateLimitError):
            return RateLimitError(
                "Anthropic rate limit exceeded",
                provider="anthropic",
                details={"original_error": str(error)}
            )
        elif isinstance(error, anthropic.APITimeoutError):
            return TimeoutError(
                "Anthropic API timeout",
                details={"provider": "anthropic", "original_error": str(error)}
            )
        else:
            return ProviderError(
                f"Anthropic error: {error}",
                provider="anthropic",
                details={"original_error": str(error)}
            )
    
    def _handle_cohere_error(self, error: Exception) -> MASBException:
        """Handle Cohere-specific errors."""
        # Cohere error handling
        if "unauthorized" in str(error).lower():
            return APIKeyError(
                "Invalid Cohere API key",
                provider="cohere",
                details={"original_error": str(error)}
            )
        elif "rate limit" in str(error).lower():
            return RateLimitError(
                "Cohere rate limit exceeded",
                provider="cohere",
                details={"original_error": str(error)}
            )
        else:
            return ProviderError(
                f"Cohere error: {error}",
                provider="cohere",
                details={"original_error": str(error)}
            )
    
    def _handle_google_error(self, error: Exception) -> MASBException:
        """Handle Google-specific errors."""
        error_str = str(error).lower()
        if "api key" in error_str or "unauthorized" in error_str:
            return APIKeyError(
                "Invalid Google API key",
                provider="google",
                details={"original_error": str(error)}
            )
        elif "quota" in error_str or "rate limit" in error_str:
            return RateLimitError(
                "Google rate limit exceeded",
                provider="google",
                details={"original_error": str(error)}
            )
        else:
            return ProviderError(
                f"Google error: {error}",
                provider="google",
                details={"original_error": str(error)}
            )
    
    def _handle_generic_error(self, error: Exception, provider: str) -> MASBException:
        """Handle generic errors."""
        if isinstance(error, aiohttp.ClientTimeout):
            return TimeoutError(
                f"HTTP timeout for {provider}",
                details={"provider": provider, "original_error": str(error)}
            )
        elif isinstance(error, aiohttp.ClientError):
            return APIError(
                f"HTTP error for {provider}: {error}",
                provider=provider,
                details={"original_error": str(error)}
            )
        else:
            return ProviderError(
                f"Unknown error for {provider}: {error}",
                provider=provider,
                details={"original_error": str(error)}
            )
    
    def _track_error(self, provider: str, error: Exception):
        """Track error for monitoring."""
        current_time = time.time()
        
        # Update error count
        if provider not in self.error_counts:
            self.error_counts[provider] = 0
        self.error_counts[provider] += 1
        
        # Store last error
        self.last_errors[provider] = {
            "error": str(error),
            "timestamp": current_time,
            "type": type(error).__name__
        }
        
        logger.warning(
            f"Error in {provider}: {error}",
            extra={
                "provider": provider,
                "error_type": type(error).__name__,
                "error_count": self.error_counts[provider]
            }
        )
    
    def get_error_stats(self) -> dict:
        """Get error statistics."""
        return {
            "error_counts": self.error_counts.copy(),
            "last_errors": self.last_errors.copy()
        }
    
    def reset_error_stats(self):
        """Reset error statistics."""
        self.error_counts.clear()
        self.last_errors.clear()


# Global error handler instance
error_handler = ErrorHandler()


def retry_on_error(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    retry_exceptions: tuple = (RateLimitError, TimeoutError, APIError)
):
    """Decorator for retrying functions on specific errors.
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Exponential backoff factor
        max_delay: Maximum delay between retries
        retry_exceptions: Exception types to retry on
    """
    def decorator(func):
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=1,
                min=1,
                max=max_delay,
                exp_base=backoff_factor
            ),
            retry=retry_if_exception_type(retry_exceptions),
            before_sleep=before_sleep_log(logger, "WARNING")
        )
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Convert to MASB exception if needed
                if not isinstance(e, MASBException):
                    provider = kwargs.get('provider', 'unknown')
                    e = error_handler.handle_api_error(e, provider)
                raise e
        
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=1,
                min=1,
                max=max_delay,
                exp_base=backoff_factor
            ),
            retry=retry_if_exception_type(retry_exceptions),
            before_sleep=before_sleep_log(logger, "WARNING")
        )
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if not isinstance(e, MASBException):
                    provider = kwargs.get('provider', 'unknown')
                    e = error_handler.handle_api_error(e, provider)
                raise e
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def handle_errors(
    default_return: Any = None,
    log_errors: bool = True,
    raise_on_error: bool = True
):
    """Decorator for handling errors in functions.
    
    Args:
        default_return: Default value to return on error
        log_errors: Whether to log errors
        raise_on_error: Whether to raise errors or return default
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {e}")
                
                if raise_on_error:
                    raise
                else:
                    return default_return
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {e}")
                
                if raise_on_error:
                    raise
                else:
                    return default_return
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class CircuitBreaker:
    """Circuit breaker pattern implementation for API calls."""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: Type[Exception] = Exception):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
            expected_exception: Exception type that triggers the circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func: Callable, *args, **kwargs):
        """Call function through circuit breaker.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise ProviderError(
                    "Circuit breaker is OPEN",
                    provider="circuit_breaker",
                    details={
                        "failure_count": self.failure_count,
                        "last_failure_time": self.last_failure_time
                    }
                )
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        return (
            self.last_failure_time is not None and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


def timeout_after(seconds: float):
    """Decorator to add timeout to async functions.
    
    Args:
        seconds: Timeout in seconds
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"Function {func.__name__} timed out after {seconds} seconds",
                    timeout_duration=seconds
                )
        return wrapper
    return decorator


class ErrorReporter:
    """Error reporting and metrics collection."""
    
    def __init__(self):
        """Initialize error reporter."""
        self.error_metrics = {
            "total_errors": 0,
            "errors_by_type": {},
            "errors_by_provider": {},
            "recent_errors": []
        }
    
    def report_error(self, error: Exception, context: dict = None):
        """Report an error for metrics collection.
        
        Args:
            error: Exception that occurred
            context: Additional context information
        """
        self.error_metrics["total_errors"] += 1
        
        error_type = type(error).__name__
        self.error_metrics["errors_by_type"][error_type] = (
            self.error_metrics["errors_by_type"].get(error_type, 0) + 1
        )
        
        if hasattr(error, 'provider'):
            provider = error.provider
            self.error_metrics["errors_by_provider"][provider] = (
                self.error_metrics["errors_by_provider"].get(provider, 0) + 1
            )
        
        # Keep only recent errors (last 100)
        error_info = {
            "timestamp": time.time(),
            "type": error_type,
            "message": str(error),
            "context": context or {}
        }
        
        self.error_metrics["recent_errors"].append(error_info)
        if len(self.error_metrics["recent_errors"]) > 100:
            self.error_metrics["recent_errors"].pop(0)
        
        logger.error(
            f"Error reported: {error_type}",
            extra={
                "error_message": str(error),
                "context": context,
                "total_errors": self.error_metrics["total_errors"]
            }
        )
    
    def get_metrics(self) -> dict:
        """Get error metrics."""
        return self.error_metrics.copy()
    
    def reset_metrics(self):
        """Reset error metrics."""
        self.error_metrics = {
            "total_errors": 0,
            "errors_by_type": {},
            "errors_by_provider": {},
            "recent_errors": []
        }


# Global error reporter instance
error_reporter = ErrorReporter()