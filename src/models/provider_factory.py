"""Factory for creating LLM providers."""

from typing import Dict, Type, Optional
from src.models.base_provider import BaseLLMProvider
from src.models.openai_provider import OpenAIProvider
from src.models.anthropic_provider import AnthropicProvider
from src.models.cohere_provider import CohereProvider
from src.models.google_provider import GoogleProvider
from src.models.data_models import ModelConfig
from src.config import settings, SUPPORTED_MODELS
from src.utils.logger import logger


class ProviderFactory:
    """Factory class for creating LLM providers."""
    
    _providers: Dict[str, Type[BaseLLMProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "cohere": CohereProvider,
        "google": GoogleProvider,
    }
    
    @classmethod
    def create_provider(cls, model_name: str, config: Optional[ModelConfig] = None) -> BaseLLMProvider:
        """Create a provider instance for the given model.
        
        Args:
            model_name: Name of the model
            config: Optional model configuration
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If model is not supported or API key is missing
        """
        # Check if model is supported
        if model_name not in SUPPORTED_MODELS:
            raise ValueError(
                f"Model '{model_name}' is not supported. "
                f"Supported models: {list(SUPPORTED_MODELS.keys())}"
            )
        
        provider_name = SUPPORTED_MODELS[model_name]
        
        # Get API key
        api_key = settings.get_api_key(provider_name)
        if not api_key:
            raise ValueError(
                f"API key for {provider_name} not found. "
                f"Please set {provider_name.upper()}_API_KEY in your .env file"
            )
        
        # Create default config if not provided
        if config is None:
            config = ModelConfig(
                name=model_name,
                provider=provider_name,
                temperature=settings.default_temperature,
                max_tokens=settings.default_max_tokens,
                custom_params={
                    "timeout": settings.request_timeout,
                    "max_retries": settings.max_retries
                }
            )
        
        # Get provider class
        provider_class = cls._providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Provider '{provider_name}' is not implemented")
        
        # Create and return provider instance
        logger.info(f"Creating {provider_name} provider for model {model_name}")
        return provider_class(api_key=api_key, config=config)
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseLLMProvider]):
        """Register a new provider class.
        
        Args:
            name: Provider name
            provider_class: Provider class
        """
        cls._providers[name] = provider_class
        logger.info(f"Registered provider: {name}")
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered providers."""
        return list(cls._providers.keys())
    
    @classmethod
    def list_models(cls) -> Dict[str, str]:
        """List all supported models with their providers."""
        return SUPPORTED_MODELS.copy()