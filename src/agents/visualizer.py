"""
Visualizer Agent - Generate image and chart specifications.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from .base_agent import BaseAgent, PromptEngine
from ..orchestration.state import SharedState


logger = logging.getLogger(__name__)


class VisualizerAgent(BaseAgent):
    """
    The Visualizer agent creates specifications for images, diagrams,
    and charts that enhance understanding.
    
    Model: Phi-3.5 Mini
    """
    
    def __init__(
        self,
        model_name: str = "phi3.5:3.8b-mini-instruct-q4_K_M",
        vram_mb: int = 2500,
        temperature: float = 0.5
    ):
        """
        Initialize the Visualizer agent.
        
        Args:
            model_name: Ollama model name
            vram_mb: Expected VRAM usage
            temperature: Sampling temperature
        """
        super().__init__(
            name="Visualizer",
            model_name=model_name,
            vram_mb=vram_mb,
            temperature=temperature
        )
        
        # Load prompt template
        config_dir = Path(__file__).parent.parent.parent / "config"
        template_path = config_dir / "prompts" / "visualizer.md"
        self.prompt_template = self.load_prompt_template(str(template_path))
    
    def _prepare_prompt(self, state: SharedState) -> str:
        """
        Prepare the prompt for the Visualizer.
        
        Args:
            state: Current shared state
        
        Returns:
            Formatted prompt
        """
        # Prepare input JSON
        content = ""
        if state.research_findings:
            content = str(state.research_findings[:2])  # First 2 findings
        elif state.plan:
            content = str(state.plan)
        else:
            content = state.user_brief
        
        input_json = {
            "content": content,
            "context": state.intent.get("domain", "general") if state.intent else "general"
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
        Parse the Visualizer's JSON response.
        
        Args:
            response: Raw LLM response
            state: Current shared state
        
        Returns:
            Parsed output dictionary or None
        """
        parsed = self.prompt_engine.extract_json_from_response(response)
        
        if parsed is None:
            logger.warning("Failed to extract JSON from Visualizer response")
            return None
        
        # Validate that at least one field exists
        if "visualizations" not in parsed and "image_prompts" not in parsed:
            logger.warning("Visualizer output missing both visualizations and image_prompts")
            return None
        
        return parsed
    
    def _graceful_degradation(self, state: SharedState) -> Dict[str, Any]:
        """
        Provide fallback when Visualizer fails.
        
        Args:
            state: Current shared state
        
        Returns:
            Minimal valid output
        """
        return {
            "visualizations": [],
            "image_prompts": [],
            "degraded": True
        }
