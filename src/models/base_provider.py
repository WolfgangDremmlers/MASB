"""Base interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import asyncio
import time
from src.models.data_models import ModelResponse, ModelConfig
from src.utils.logger import logger


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str, config: ModelConfig):
        """Initialize the provider.
        
        Args:
            api_key: API key for the provider
            config: Model configuration
        """
        self.api_key = api_key
        self.config = config
        self.client = None
        self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self):
        """Initialize the API client."""
        pass
    
    @abstractmethod
    async def _make_request(self, prompt: str) -> Dict[str, Any]:
        """Make a request to the API.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Raw API response
        """
        pass
    
    async def generate_response(self, prompt_id: str, prompt_text: str) -> ModelResponse:
        """Generate a response for a prompt.
        
        Args:
            prompt_id: ID of the prompt
            prompt_text: The prompt text
            
        Returns:
            ModelResponse object
        """
        start_time = time.time()
        
        try:
            # Retry logic
            for attempt in range(self.config.custom_params.get("max_retries", 3)):
                try:
                    response = await self._make_request(prompt_text)
                    
                    # Extract response text and tokens
                    response_text = self._extract_response_text(response)
                    tokens_used = self._extract_token_count(response)
                    
                    return ModelResponse(
                        prompt_id=prompt_id,
                        model_name=self.config.name,
                        provider=self.config.provider,
                        response_text=response_text,
                        response_time=time.time() - start_time,
                        tokens_used=tokens_used,
                        metadata=self._extract_metadata(response)
                    )
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt == self.config.custom_params.get("max_retries", 3) - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return ModelResponse(
                prompt_id=prompt_id,
                model_name=self.config.name,
                provider=self.config.provider,
                response_text="",
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    @abstractmethod
    def _extract_response_text(self, response: Dict[str, Any]) -> str:
        """Extract response text from API response."""
        pass
    
    @abstractmethod
    def _extract_token_count(self, response: Dict[str, Any]) -> Optional[int]:
        """Extract token count from API response."""
        pass
    
    def _extract_metadata(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract additional metadata from API response."""
        return {}
    
    async def batch_generate(self, prompts: List[tuple[str, str]], 
                           max_concurrent: int = 5) -> List[ModelResponse]:
        """Generate responses for multiple prompts.
        
        Args:
            prompts: List of (prompt_id, prompt_text) tuples
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of ModelResponse objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(prompt_id: str, prompt_text: str):
            async with semaphore:
                return await self.generate_response(prompt_id, prompt_text)
        
        tasks = [
            generate_with_semaphore(prompt_id, prompt_text)
            for prompt_id, prompt_text in prompts
        ]
        
        return await asyncio.gather(*tasks)
    
    def __repr__(self):
        return f"{self.__class__.__name__}(model={self.config.name})"