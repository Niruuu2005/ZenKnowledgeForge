"""
Planner Agent - Decomposes goals into research questions and phases.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from .base_agent import BaseAgent, PromptEngine
from ..orchestration.state import SharedState


logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """
    The Planner agent decomposes the user's goal into concrete
    Research Questions (RQs) and execution phases.
    
    Model: Mistral Nemo 12B
    """
    
    def __init__(
        self,
        model_name: str = "mistral-nemo:12b-instruct-q4_K_M",
        vram_mb: int = 7500,
        temperature: float = 0.5,
        max_research_questions: int = 15
    ):
        """
        Initialize the Planner agent.
        
        Args:
            model_name: Ollama model name
            vram_mb: Expected VRAM usage
            temperature: Sampling temperature
            max_research_questions: Maximum RQs to generate
        """
        super().__init__(
            name="Planner",
            model_name=model_name,
            vram_mb=vram_mb,
            temperature=temperature
        )
        
        self.max_research_questions = max_research_questions
        
        # Load prompt template
        config_dir = Path(__file__).parent.parent.parent / "config"
        template_path = config_dir / "prompts" / "planner.md"
        self.prompt_template = self.load_prompt_template(str(template_path))
    
    def _prepare_prompt(self, state: SharedState) -> str:
        """
        Prepare the prompt for the Planner.
        
        Args:
            state: Current shared state
        
        Returns:
            Formatted prompt
        """
        # Prepare input JSON
        input_json = {
            "intent": state.intent or {"primary_goal": state.user_brief},
            "user_brief": state.user_brief,
            "clarifications": state.clarifications
        }
        
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
        Parse the Planner's JSON response.
        
        Args:
            response: Raw LLM response
            state: Current shared state
        
        Returns:
            Parsed output dictionary or None
        """
        parsed = self.prompt_engine.extract_json_from_response(response)
        
        if parsed is None:
            logger.warning("Failed to extract JSON from Planner response")
            return None
        
        # Validate required fields
        required_fields = ["research_questions", "phases"]
        
        for field in required_fields:
            if field not in parsed:
                logger.warning(f"Missing required field in Planner output: {field}")
                return None
        
        # Limit number of research questions
        if len(parsed["research_questions"]) > self.max_research_questions:
            parsed["research_questions"] = parsed["research_questions"][:self.max_research_questions]
        
        return parsed
    
    def _graceful_degradation(self, state: SharedState) -> Dict[str, Any]:
        """
        Provide fallback when Planner fails.
        
        Args:
            state: Current shared state
        
        Returns:
            Minimal valid output
        """
        return {
            "research_questions": [
                {
                    "id": "RQ1",
                    "question": state.user_brief,
                    "type": "exploratory",
                    "priority": "critical",
                    "estimated_time_minutes": 30,
                    "dependencies": []
                }
            ],
            "phases": [
                {
                    "name": "Investigation",
                    "description": "Investigate the topic",
                    "rq_ids": ["RQ1"],
                    "parallel": False
                }
            ],
            "success_criteria": ["Address user's brief"],
            "estimated_total_time_minutes": 30,
            "degraded": True
        }
