"""
Grounder Agent - RAG retrieval, evidence citation, confidence scoring.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from .base_agent import BaseAgent, PromptEngine
from ..orchestration.state import SharedState


logger = logging.getLogger(__name__)


class GrounderAgent(BaseAgent):
    """
    The Grounder agent retrieves evidence, cites sources,
    and provides confidence scores for claims.
    
    Model: Qwen 2.5 7B
    """
    
    def __init__(
        self,
        model_name: str = "qwen2.5:7b-instruct-q4_K_M",
        vram_mb: int = 4500,
        temperature: float = 0.2,
        max_sources: int = 10
    ):
        """
        Initialize the Grounder agent.
        
        Args:
            model_name: Ollama model name
            vram_mb: Expected VRAM usage
            temperature: Sampling temperature
            max_sources: Maximum sources to cite
        """
        super().__init__(
            name="Grounder",
            model_name=model_name,
            vram_mb=vram_mb,
            temperature=temperature
        )
        
        self.max_sources = max_sources
        
        # Load prompt template
        config_dir = Path(__file__).parent.parent.parent / "config"
        template_path = config_dir / "prompts" / "grounder.md"
        self.prompt_template = self.load_prompt_template(str(template_path))
    
    def _prepare_prompt(self, state: SharedState) -> str:
        """
        Prepare the prompt for the Grounder.
        
        Args:
            state: Current shared state
        
        Returns:
            Formatted prompt
        """
        # For now, we'll simulate retrieved content
        # In a full implementation, this would call the browser/search tools
        
        # Get the first research question from the plan
        research_question = "What is the topic?"
        if state.plan and "research_questions" in state.plan:
            rqs = state.plan["research_questions"]
            if rqs:
                research_question = rqs[0].get("question", research_question)
        
        # Prepare input JSON
        input_json = {
            "research_question": research_question,
            "retrieved_content": [
                {
                    "url": "https://example.com/placeholder",
                    "title": "Placeholder Content",
                    "content": f"This is placeholder content for: {research_question}"
                }
            ]
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
        Parse the Grounder's JSON response.
        
        Args:
            response: Raw LLM response
            state: Current shared state
        
        Returns:
            Parsed output dictionary or None
        """
        parsed = self.prompt_engine.extract_json_from_response(response)
        
        if parsed is None:
            logger.warning("Failed to extract JSON from Grounder response")
            return None
        
        # Validate required fields
        required_fields = ["answer", "key_findings", "overall_confidence"]
        
        for field in required_fields:
            if field not in parsed:
                logger.warning(f"Missing required field in Grounder output: {field}")
                return None
        
        return parsed
    
    def _graceful_degradation(self, state: SharedState) -> Dict[str, Any]:
        """
        Provide fallback when Grounder fails.
        
        Args:
            state: Current shared state
        
        Returns:
            Minimal valid output
        """
        return {
            "answer": "Unable to retrieve sufficient evidence",
            "key_findings": [],
            "contradictions": [],
            "knowledge_gaps": ["Insufficient data available"],
            "overall_confidence": 0.3,
            "degraded": True
        }
