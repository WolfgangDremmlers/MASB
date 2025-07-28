"""Google (Gemini) LLM provider implementation."""

from typing import Dict, Any, Optional
import google.generativeai as genai
from src.models.base_provider import BaseLLMProvider
from src.utils.logger import logger
import asyncio


class GoogleProvider(BaseLLMProvider):
    """Google API provider for Gemini models."""
    
    def _initialize_client(self):
        """Initialize Google Generative AI client."""
        genai.configure(api_key=self.api_key)
        
        # Map model names
        model_map = {
            "gemini-pro": "gemini-pro",
            "gemini-1.5-pro": "gemini-1.5-pro",
            "gemini-pro-vision": "gemini-pro-vision"
        }
        
        model_name = model_map.get(self.config.name, self.config.name)
        self.client = genai.GenerativeModel(model_name)
        logger.info(f"Initialized Google client for model: {model_name}")
    
    async def _make_request(self, prompt: str) -> Dict[str, Any]:
        """Make a request to Google API."""
        generation_config = genai.GenerationConfig(
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens,
            top_p=self.config.top_p if self.config.top_p is not None else 0.95,
            stop_sequences=self.config.stop_sequences if self.config.stop_sequences else None
        )
        
        # Run synchronous call in executor to make it async
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.generate_content(
                prompt,
                generation_config=generation_config
            )
        )
        
        # Convert response to dict format
        result = {
            "text": "",
            "candidates": [],
            "prompt_feedback": {}
        }
        
        # Extract text from response
        if response.text:
            result["text"] = response.text
            
        # Extract candidates
        if hasattr(response, 'candidates'):
            for candidate in response.candidates:
                candidate_data = {
                    "content": "",
                    "finish_reason": str(candidate.finish_reason) if hasattr(candidate, 'finish_reason') else "",
                    "safety_ratings": []
                }
                
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    candidate_data["content"] = ' '.join([part.text for part in candidate.content.parts if hasattr(part, 'text')])
                
                if hasattr(candidate, 'safety_ratings'):
                    candidate_data["safety_ratings"] = [
                        {
                            "category": str(rating.category),
                            "probability": str(rating.probability)
                        }
                        for rating in candidate.safety_ratings
                    ]
                
                result["candidates"].append(candidate_data)
        
        # Extract prompt feedback
        if hasattr(response, 'prompt_feedback'):
            result["prompt_feedback"] = {
                "safety_ratings": [
                    {
                        "category": str(rating.category),
                        "probability": str(rating.probability)
                    }
                    for rating in response.prompt_feedback.safety_ratings
                ] if hasattr(response.prompt_feedback, 'safety_ratings') else []
            }
        
        return result
    
    def _extract_response_text(self, response: Dict[str, Any]) -> str:
        """Extract response text from Google response."""
        # Try to get text directly
        if response.get("text"):
            return response["text"]
        
        # Fall back to candidates
        candidates = response.get("candidates", [])
        if candidates and candidates[0].get("content"):
            return candidates[0]["content"]
        
        return ""
    
    def _extract_token_count(self, response: Dict[str, Any]) -> Optional[int]:
        """Extract token count from Google response."""
        # Google doesn't provide token counts in the same way
        # Would need to estimate or use a tokenizer
        return None
    
    def _extract_metadata(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from Google response."""
        metadata = {}
        
        try:
            # Extract safety ratings
            prompt_feedback = response.get("prompt_feedback", {})
            if prompt_feedback.get("safety_ratings"):
                metadata["prompt_safety_ratings"] = prompt_feedback["safety_ratings"]
            
            # Extract candidate information
            candidates = response.get("candidates", [])
            if candidates:
                candidate = candidates[0]
                metadata["finish_reason"] = candidate.get("finish_reason", "")
                if candidate.get("safety_ratings"):
                    metadata["response_safety_ratings"] = candidate["safety_ratings"]
                    
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            
        return metadata