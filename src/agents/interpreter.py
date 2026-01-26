"""
Interpreter Agent - Parses user brief and extracts intent.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from .base_agent import BaseAgent, PromptEngine
from ..orchestration.state import SharedState


logger = logging.getLogger(__name__)


class InterpreterAgent(BaseAgent):
    """
    The Interpreter agent parses the user's brief, extracts intent,
    and generates clarifying questions.
    
    Model: Llama 3.1 8B
    """
    
    def __init__(
        self,
        model_name: str = "llama3.1:8b-instruct-q4_K_M",
        vram_mb: int = 5000,
        temperature: float = 0.3,
        max_questions: int = 5
    ):
        """
        Initialize the Interpreter agent.
        
        Args:
            model_name: Ollama model name
            vram_mb: Expected VRAM usage
            temperature: Sampling temperature
            max_questions: Maximum clarifying questions
        """
        super().__init__(
            name="Interpreter",
            model_name=model_name,
            vram_mb=vram_mb,
            temperature=temperature
        )
        
        self.max_questions = max_questions
        
        # Load prompt template
        config_dir = Path(__file__).parent.parent.parent / "config"
        template_path = config_dir / "prompts" / "interpreter.md"
        self.prompt_template = self.load_prompt_template(str(template_path))
    
    def _prepare_prompt(self, state: SharedState) -> str:
        """
        Prepare the prompt for the Interpreter.
        
        Args:
            state: Current shared state
        
        Returns:
            Formatted prompt
        """
        # Prepare input JSON
        input_json = {
            "user_brief": state.user_brief,
            "context": ""
        }
        
        # If there are clarifications, add them to context
        if state.clarifications:
            input_json["context"] = str(state.clarifications)
        
        # Build the full prompt
        prompt = f"{self.prompt_template}\n\n"
        prompt += f"## Input\n\n"
        prompt += f"```json\n{self.prompt_engine.inject_variables('{input}', {'input': input_json})}\n```\n\n"
        prompt += f"## Your Response\n\n"
        prompt += f"Provide your response as valid JSON only:"
        
        return prompt
    
    def _parse_response(
        self,
        response: str,
        state: SharedState
    ) -> Optional[Dict[str, Any]]:
        """
        Parse the Interpreter's JSON response.
        
        Args:
            response: Raw LLM response
            state: Current shared state
        
        Returns:
            Parsed output dictionary or None
        """
        parsed = self.prompt_engine.extract_json_from_response(response)
        
        if parsed is None:
            logger.warning("Failed to extract JSON from Interpreter response")
            return None
        
        # Validate required fields
        required_fields = ["intent", "extracted_requirements"]
        
        for field in required_fields:
            if field not in parsed:
                logger.warning(f"Missing required field in Interpreter output: {field}")
                return None
        
        # Add default confidence if missing
        if "confidence" not in parsed:
            parsed["confidence"] = 0.7  # Default moderate confidence
        
        # Limit number of clarifying questions
        if "clarifying_questions" in parsed:
            parsed["clarifying_questions"] = parsed["clarifying_questions"][:self.max_questions]
        
        return parsed
    
    def _graceful_degradation(self, state: SharedState) -> Dict[str, Any]:
        """
        Provide fallback when Interpreter fails.
        
        Args:
            state: Current shared state
        
        Returns:
            Minimal valid output
        """
        # Handle execution_mode being either string or enum
        mode_value = (
            state.execution_mode.value 
            if hasattr(state.execution_mode, 'value') 
            else str(state.execution_mode)
        )
        
        return {
            "intent": {
                "primary_goal": state.user_brief,
                "domain": "unknown",
                "output_type": mode_value,
                "scope": "moderate"
            },
            "extracted_requirements": [state.user_brief],
            "ambiguities": [],
            "clarifying_questions": [],
            "confidence": 0.5,
            "degraded": True
        }
