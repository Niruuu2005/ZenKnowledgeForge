"""
Auditor Agent - Risk analysis, security assessment, dependency checking.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from .base_agent import BaseAgent, PromptEngine
from ..orchestration.state import SharedState


logger = logging.getLogger(__name__)


class AuditorAgent(BaseAgent):
    """
    The Auditor agent performs risk analysis, security assessment,
    and dependency checking.
    
    Model: Gemma 2 9B
    """
    
    def __init__(
        self,
        model_name: str = "gemma2:9b-instruct-q4_K_M",
        vram_mb: int = 5500,
        temperature: float = 0.3
    ):
        """
        Initialize the Auditor agent.
        
        Args:
            model_name: Ollama model name
            vram_mb: Expected VRAM usage
            temperature: Sampling temperature
        """
        super().__init__(
            name="Auditor",
            model_name=model_name,
            vram_mb=vram_mb,
            temperature=temperature
        )
        
        # Load prompt template
        config_dir = Path(__file__).parent.parent.parent / "config"
        template_path = config_dir / "prompts" / "auditor.md"
        self.prompt_template = self.load_prompt_template(str(template_path))
    
    def _prepare_prompt(self, state: SharedState) -> str:
        """
        Prepare the prompt for the Auditor.
        
        Args:
            state: Current shared state
        
        Returns:
            Formatted prompt
        """
        # Prepare input JSON
        input_json = {
            "plan": state.plan or {},
            "findings": state.research_findings or [],
            "domain": state.intent.get("domain", "unknown") if state.intent else "unknown"
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
        Parse the Auditor's JSON response.
        
        Args:
            response: Raw LLM response
            state: Current shared state
        
        Returns:
            Parsed output dictionary or None
        """
        parsed = self.prompt_engine.extract_json_from_response(response)
        
        if parsed is None:
            logger.warning("Failed to extract JSON from Auditor response")
            return None
        
        # Validate required fields
        required_fields = ["risk_assessment", "dependencies", "feasibility_assessment"]
        
        for field in required_fields:
            if field not in parsed:
                logger.warning(f"Missing required field in Auditor output: {field}")
                return None
        
        return parsed
    
    def _graceful_degradation(self, state: SharedState) -> Dict[str, Any]:
        """
        Provide fallback when Auditor fails.
        
        Args:
            state: Current shared state
        
        Returns:
            Minimal valid output
        """
        return {
            "risk_assessment": {
                "overall_risk_level": "medium",
                "risks": []
            },
            "dependencies": {
                "technical": [],
                "knowledge": []
            },
            "security_concerns": [],
            "feasibility_assessment": {
                "technical_feasibility": 0.7,
                "resource_feasibility": 0.7,
                "time_feasibility": 0.7,
                "overall_feasibility": 0.7,
                "blockers": []
            },
            "recommendations": ["Proceed with caution"],
            "degraded": True
        }
