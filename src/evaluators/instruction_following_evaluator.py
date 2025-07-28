"""Instruction following evaluator."""

import re
from typing import List, Dict, Any, Optional
from src.evaluators.base_evaluator import BaseEvaluator
from src.models.data_models import TestPrompt, ModelResponse, EvaluationScore, Category
from src.utils.logger import logger


class InstructionFollowingEvaluator(BaseEvaluator):
    """Evaluator for checking instruction following in model responses."""
    
    def __init__(self):
        """Initialize instruction following evaluator."""
        super().__init__(Category.INSTRUCTION_FOLLOWING)
        
        # Common instruction patterns
        self.instruction_patterns = {
            "word_count": r"(?i)(?:exactly|precisely|only)?\s*(\d+)\s*words?",
            "sentence_count": r"(?i)(?:exactly|precisely|only)?\s*(\d+)\s*sentences?",
            "list_items": r"(?i)(?:list|provide|give)\s*(\d+)\s*(?:items?|things?|examples?)",
            "format": r"(?i)(?:format|structure|write).*(?:as|in|using)\s*(.+?)(?:\.|$)",
            "language": r"(?i)(?:respond|answer|write)\s*(?:in|using)\s*(\w+)",
            "yes_no": r"(?i)(?:answer|respond)\s*(?:with\s*)?(?:only\s*)?[\"']?(yes|no)[\"']?\s*(?:only)?",
            "include": r"(?i)(?:include|contain|mention)\s*(.+?)(?:\.|,|and|$)",
            "exclude": r"(?i)(?:do not|don't|avoid|exclude)\s*(?:include|mention|use)?\s*(.+?)(?:\.|,|and|$)",
            "start_with": r"(?i)(?:start|begin)\s*(?:with|your response with)\s*[\"']?(.+?)[\"']?",
            "end_with": r"(?i)(?:end|finish|conclude)\s*(?:with|your response with)\s*[\"']?(.+?)[\"']?"
        }
    
    async def evaluate(self, prompt: TestPrompt, response: ModelResponse) -> EvaluationScore:
        """Evaluate response for instruction following.
        
        Args:
            prompt: Test prompt
            response: Model response
            
        Returns:
            Evaluation score
        """
        # Check for errors first
        if error_score := self.check_response_error(response):
            return error_score
        
        prompt_text = prompt.text
        response_text = response.response_text
        
        # Extract instructions from prompt
        instructions = self._extract_instructions(prompt_text)
        
        # Check each instruction
        results = []
        for instruction_type, instruction_value in instructions.items():
            check_result = self._check_instruction(
                instruction_type, 
                instruction_value, 
                response_text
            )
            results.append({
                "type": instruction_type,
                "expected": instruction_value,
                "followed": check_result["followed"],
                "actual": check_result.get("actual"),
                "details": check_result.get("details")
            })
        
        # Calculate score
        if not results:
            # No clear instructions found - neutral score
            score = 0.7
        else:
            followed_count = sum(1 for r in results if r["followed"])
            total_count = len(results)
            score = followed_count / total_count
        
        # Adjust score based on severity of violations
        critical_instructions = ["word_count", "yes_no", "format"]
        critical_violations = sum(
            1 for r in results 
            if r["type"] in critical_instructions and not r["followed"]
        )
        
        if critical_violations > 0:
            score = max(0.0, score - (0.2 * critical_violations))
        
        passed = score >= 0.7
        
        return self._create_score(
            score=score,
            passed=passed,
            details={
                "instructions_found": len(results),
                "instructions_followed": sum(1 for r in results if r["followed"]),
                "instruction_results": results,
                "response_length": len(response_text.split())
            }
        )
    
    def _extract_instructions(self, prompt_text: str) -> Dict[str, Any]:
        """Extract instructions from prompt text."""
        instructions = {}
        
        for inst_type, pattern in self.instruction_patterns.items():
            match = re.search(pattern, prompt_text, re.IGNORECASE)
            if match:
                if inst_type in ["word_count", "sentence_count", "list_items"]:
                    instructions[inst_type] = int(match.group(1))
                else:
                    instructions[inst_type] = match.group(1).strip()
        
        return instructions
    
    def _check_instruction(self, 
                          instruction_type: str, 
                          expected_value: Any, 
                          response_text: str) -> Dict[str, Any]:
        """Check if a specific instruction was followed."""
        
        if instruction_type == "word_count":
            actual_count = len(response_text.split())
            return {
                "followed": actual_count == expected_value,
                "actual": actual_count
            }
        
        elif instruction_type == "sentence_count":
            # Simple sentence counting (periods, exclamations, questions)
            sentences = re.split(r'[.!?]+', response_text)
            actual_count = len([s for s in sentences if s.strip()])
            return {
                "followed": actual_count == expected_value,
                "actual": actual_count
            }
        
        elif instruction_type == "list_items":
            # Look for numbered lists or bullet points
            numbered_items = re.findall(r'^\s*\d+[.)]\s*', response_text, re.MULTILINE)
            bullet_items = re.findall(r'^\s*[-•*]\s*', response_text, re.MULTILINE)
            actual_count = len(numbered_items) + len(bullet_items)
            
            # If no explicit list formatting, count lines that might be list items
            if actual_count == 0:
                lines = [l.strip() for l in response_text.split('\n') if l.strip()]
                if len(lines) <= expected_value * 2:  # Reasonable assumption
                    actual_count = len(lines)
            
            return {
                "followed": actual_count == expected_value,
                "actual": actual_count
            }
        
        elif instruction_type == "yes_no":
            response_lower = response_text.strip().lower()
            expected_lower = expected_value.lower()
            
            # Check if response is exactly yes/no or starts with it
            exact_match = response_lower == expected_lower
            starts_with = response_lower.startswith(expected_lower)
            
            # Check if it's the only substantial word
            words = response_text.strip().split()
            single_word = len(words) == 1 and words[0].lower() == expected_lower
            
            return {
                "followed": exact_match or single_word or (starts_with and len(words) <= 3),
                "actual": response_text.strip()[:50]
            }
        
        elif instruction_type == "include":
            included = expected_value.lower() in response_text.lower()
            return {
                "followed": included,
                "details": f"Looking for: {expected_value}"
            }
        
        elif instruction_type == "exclude":
            excluded = expected_value.lower() not in response_text.lower()
            return {
                "followed": excluded,
                "details": f"Should not contain: {expected_value}"
            }
        
        elif instruction_type == "start_with":
            starts_correctly = response_text.strip().lower().startswith(expected_value.lower())
            return {
                "followed": starts_correctly,
                "actual": response_text.strip()[:len(expected_value) + 10]
            }
        
        elif instruction_type == "end_with":
            ends_correctly = response_text.strip().lower().endswith(expected_value.lower())
            return {
                "followed": ends_correctly,
                "actual": response_text.strip()[-(len(expected_value) + 10):]
            }
        
        else:
            # Generic check
            return {
                "followed": False,
                "details": f"Unknown instruction type: {instruction_type}"
            }