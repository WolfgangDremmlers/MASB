"""OpenAI LLM provider implementation."""

from typing import Dict, Any, Optional
import openai
from openai import AsyncOpenAI
from src.models.base_provider import BaseLLMProvider
from src.utils.logger import logger


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider."""
    
    def _initialize_client(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(api_key=self.api_key)
        logger.info(f"Initialized OpenAI client for model: {self.config.name}")
    
    async def _make_request(self, prompt: str) -> Dict[str, Any]:
        """Make a request to OpenAI API."""
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": self.config.name,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "timeout": self.config.custom_params.get("timeout", 60)
        }
        
        # Add optional parameters
        if self.config.top_p is not None:
            kwargs["top_p"] = self.config.top_p
        if self.config.frequency_penalty is not None:
            kwargs["frequency_penalty"] = self.config.frequency_penalty
        if self.config.presence_penalty is not None:
            kwargs["presence_penalty"] = self.config.presence_penalty
        if self.config.stop_sequences:
            kwargs["stop"] = self.config.stop_sequences
            
        response = await self.client.chat.completions.create(**kwargs)
        return response.model_dump()
    
    def _extract_response_text(self, response: Dict[str, Any]) -> str:
        """Extract response text from OpenAI response."""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            logger.error(f"Failed to extract response text from: {response}")
            return ""
    
    def _extract_token_count(self, response: Dict[str, Any]) -> Optional[int]:
        """Extract token count from OpenAI response."""
        try:
            usage = response.get("usage", {})
            return usage.get("total_tokens")
        except Exception:
            return None
    
    def _extract_metadata(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from OpenAI response."""
        metadata = {}
        
        try:
            metadata["model"] = response.get("model", "")
            metadata["finish_reason"] = response["choices"][0].get("finish_reason", "")
            
            usage = response.get("usage", {})
            metadata["prompt_tokens"] = usage.get("prompt_tokens", 0)
            metadata["completion_tokens"] = usage.get("completion_tokens", 0)
            
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            
        return metadata