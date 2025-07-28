"""Cohere LLM provider implementation."""

from typing import Dict, Any, Optional
import cohere
from src.models.base_provider import BaseLLMProvider
from src.utils.logger import logger


class CohereProvider(BaseLLMProvider):
    """Cohere API provider."""
    
    def _initialize_client(self):
        """Initialize Cohere client."""
        self.client = cohere.AsyncClient(api_key=self.api_key)
        logger.info(f"Initialized Cohere client for model: {self.config.name}")
    
    async def _make_request(self, prompt: str) -> Dict[str, Any]:
        """Make a request to Cohere API."""
        kwargs = {
            "message": prompt,
            "model": self.config.name,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        
        # Add optional parameters
        if self.config.top_p is not None:
            kwargs["p"] = self.config.top_p
        if self.config.frequency_penalty is not None:
            kwargs["frequency_penalty"] = self.config.frequency_penalty
        if self.config.presence_penalty is not None:
            kwargs["presence_penalty"] = self.config.presence_penalty
        if self.config.stop_sequences:
            kwargs["stop_sequences"] = self.config.stop_sequences
            
        response = await self.client.chat(**kwargs)
        
        # Convert response to dict format
        return {
            "text": response.text,
            "generation_id": response.generation_id,
            "citations": response.citations,
            "documents": response.documents,
            "search_queries": response.search_queries,
            "search_results": response.search_results,
            "meta": {
                "tokens": {
                    "input_tokens": response.meta.tokens.input_tokens,
                    "output_tokens": response.meta.tokens.output_tokens
                }
            } if hasattr(response, 'meta') and hasattr(response.meta, 'tokens') else {}
        }
    
    def _extract_response_text(self, response: Dict[str, Any]) -> str:
        """Extract response text from Cohere response."""
        return response.get("text", "")
    
    def _extract_token_count(self, response: Dict[str, Any]) -> Optional[int]:
        """Extract token count from Cohere response."""
        try:
            meta = response.get("meta", {})
            tokens = meta.get("tokens", {})
            input_tokens = tokens.get("input_tokens", 0)
            output_tokens = tokens.get("output_tokens", 0)
            return input_tokens + output_tokens
        except Exception:
            return None
    
    def _extract_metadata(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from Cohere response."""
        metadata = {}
        
        try:
            metadata["generation_id"] = response.get("generation_id", "")
            
            meta = response.get("meta", {})
            tokens = meta.get("tokens", {})
            metadata["input_tokens"] = tokens.get("input_tokens", 0)
            metadata["output_tokens"] = tokens.get("output_tokens", 0)
            
            # Include citations if available
            if response.get("citations"):
                metadata["citations"] = response["citations"]
                
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            
        return metadata