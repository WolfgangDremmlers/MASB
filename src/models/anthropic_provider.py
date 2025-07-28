"""Anthropic (Claude) LLM provider implementation."""

from typing import Dict, Any, Optional
import anthropic
from anthropic import AsyncAnthropic
from src.models.base_provider import BaseLLMProvider
from src.utils.logger import logger


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API provider for Claude models."""
    
    def _initialize_client(self):
        """Initialize Anthropic client."""
        self.client = AsyncAnthropic(api_key=self.api_key)
        logger.info(f"Initialized Anthropic client for model: {self.config.name}")
    
    async def _make_request(self, prompt: str) -> Dict[str, Any]:
        """Make a request to Anthropic API."""
        # Map model names to Anthropic's naming convention
        model_map = {
            "claude-3-opus": "claude-3-opus-20240229",
            "claude-3-sonnet": "claude-3-sonnet-20240229",
            "claude-3-haiku": "claude-3-haiku-20240307",
            "claude-2.1": "claude-2.1",
            "claude-2": "claude-2.0",
            "claude-instant": "claude-instant-1.2"
        }
        
        model_name = model_map.get(self.config.name, self.config.name)
        
        kwargs = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "timeout": self.config.custom_params.get("timeout", 60)
        }
        
        # Add optional parameters
        if self.config.top_p is not None:
            kwargs["top_p"] = self.config.top_p
        if self.config.stop_sequences:
            kwargs["stop_sequences"] = self.config.stop_sequences
            
        response = await self.client.messages.create(**kwargs)
        
        # Convert response to dict format
        return {
            "id": response.id,
            "model": response.model,
            "role": response.role,
            "content": [{"text": block.text} for block in response.content],
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }
    
    def _extract_response_text(self, response: Dict[str, Any]) -> str:
        """Extract response text from Anthropic response."""
        try:
            content = response.get("content", [])
            if content and isinstance(content, list):
                return content[0].get("text", "")
            return ""
        except Exception as e:
            logger.error(f"Failed to extract response text: {e}")
            return ""
    
    def _extract_token_count(self, response: Dict[str, Any]) -> Optional[int]:
        """Extract token count from Anthropic response."""
        try:
            usage = response.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            return input_tokens + output_tokens
        except Exception:
            return None
    
    def _extract_metadata(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from Anthropic response."""
        metadata = {}
        
        try:
            metadata["model"] = response.get("model", "")
            metadata["stop_reason"] = response.get("stop_reason", "")
            
            usage = response.get("usage", {})
            metadata["input_tokens"] = usage.get("input_tokens", 0)
            metadata["output_tokens"] = usage.get("output_tokens", 0)
            
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            
        return metadata