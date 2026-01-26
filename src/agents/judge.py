"""
Judge Agent - Final synthesis, conflict resolution, consensus scoring.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from .base_agent import BaseAgent, PromptEngine
from ..orchestration.state import SharedState


logger = logging.getLogger(__name__)


class JudgeAgent(BaseAgent):
    """
    The Judge agent synthesizes all inputs, resolves conflicts,
    assesses consensus quality, and produces the final artifact.
    
    Model: Qwen 2.5 14B
    """
    
    def __init__(
        self,
        model_name: str = "qwen2.5:14b-instruct-q4_K_M",
        vram_mb: int = 9000,
        temperature: float = 0.2,
        consensus_threshold: float = 0.85,
        max_deliberation_rounds: int = 7
    ):
        """
        Initialize the Judge agent.
        
        Args:
            model_name: Ollama model name
            vram_mb: Expected VRAM usage
            temperature: Sampling temperature
            consensus_threshold: Minimum consensus score to accept
            max_deliberation_rounds: Maximum deliberation rounds
        """
        super().__init__(
            name="Judge",
            model_name=model_name,
            vram_mb=vram_mb,
            temperature=temperature
        )
        
        self.consensus_threshold = consensus_threshold
        self.max_deliberation_rounds = max_deliberation_rounds
        
        # Load prompt template
        config_dir = Path(__file__).parent.parent.parent / "config"
        template_path = config_dir / "prompts" / "judge.md"
        self.prompt_template = self.load_prompt_template(str(template_path))
    
    def _prepare_prompt(self, state: SharedState) -> str:
        """
        Prepare the prompt for the Judge.
        
        Args:
            state: Current shared state
        
        Returns:
            Formatted prompt
        """
        # Prepare input JSON with all context
        input_json = {
            "user_brief": state.user_brief,
            "intent": state.intent or {},
            "plan": state.plan or {},
            "research_findings": state.research_findings or [],
            "audit_report": state.audit_report or {},
            "visualizations": state.visualizations or {}
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
        Parse the Judge's JSON response.
        
        Args:
            response: Raw LLM response
            state: Current shared state
        
        Returns:
            Parsed output dictionary or None
        """
        parsed = self.prompt_engine.extract_json_from_response(response)
        
        if parsed is None:
            logger.warning("Failed to extract JSON from Judge response")
            return None
        
        # Validate required fields
        required_fields = ["synthesis", "consensus_score", "final_artifact", "decision"]
        
        for field in required_fields:
            if field not in parsed:
                logger.warning(f"Missing required field in Judge output: {field}")
                return None
        
        # Validate consensus score structure
        consensus = parsed.get("consensus_score", {})
        if not isinstance(consensus, dict):
            logger.warning("Invalid consensus_score structure")
            return None
        
        required_scores = ["groundedness", "coherence", "completeness", "overall"]
        for score_field in required_scores:
            if score_field not in consensus:
                logger.warning(f"Missing score field: {score_field}")
                return None
        
        return parsed
    
    def _graceful_degradation(self, state: SharedState) -> Dict[str, Any]:
        """
        Provide fallback when Judge fails.
        
        Args:
            state: Current shared state
        
        Returns:
            Minimal valid output
        """
        # Create a basic artifact from available information
        sections = []
        
        if state.research_findings:
            sections.append({
                "title": "Findings",
                "content": str(state.research_findings),
                "confidence": 0.5
            })
        
        return {
            "synthesis": {
                "executive_summary": state.user_brief,
                "key_insights": [],
                "conflicts_resolved": []
            },
            "consensus_score": {
                "groundedness": 0.5,
                "coherence": 0.5,
                "completeness": 0.5,
                "overall": 0.5,
                "justification": "Degraded mode - unable to perform full synthesis"
            },
            "final_artifact": {
                "type": state.execution_mode.value if hasattr(state.execution_mode, 'value') else str(state.execution_mode),
                "sections": sections,
                "metadata": {
                    "created_at": state.started_at.isoformat(),
                    "agents_consulted": list(state.agent_outputs.keys()),
                    "total_sources": 0,
                    "deliberation_rounds": state.deliberation_round
                }
            },
            "recommendations": ["Review and refine manually"],
            "decision": "accept",
            "revision_notes": "",
            "degraded": True
        }
