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
        # Get ALL research questions from the plan
        all_research_questions = []
        if state.plan and "research_questions" in state.plan:
            all_research_questions = state.plan["research_questions"]
        
        # If no plan, create from user brief
        if not all_research_questions:
            all_research_questions = [
                {
                    "id": "RQ1",
                    "question": state.user_brief,
                    "type": "exploratory"
                }
            ]
        
        # Prepare comprehensive input JSON with all questions
        input_json = {
            "user_brief": state.user_brief,
            "research_questions": all_research_questions,
            "instructions": """
CRITICAL DIRECTIVE: Provide comprehensive, high-quality answers for each research question.

For EACH research question, provide:
1. A clear, detailed answer (3-5 paragraphs, 300-500 words per question)
2. Technical analysis explaining key principles and mechanisms
3. Real-world examples (2-3) with specific use cases
4. Key findings with supporting evidence
5. Related concepts and interconnections
6. Implementation guidance and best practices
7. Common challenges and solutions
8. Future trends and directions

Focus on depth and accuracy over length.
Target: 2000-4000 words total for all questions combined.
Each answer should be informative and actionable.
Every claim must be substantiated with reasoning or evidence.
"""
        }
        
        # Build the full prompt
        prompt = f"{self.prompt_template}\n\n"
        prompt += f"## Input\n\n"
        prompt += f"```json\n{self.prompt_engine.inject_variables('{input}', {'input': input_json})}\n```\n\n"
        prompt += f"""## Content Requirements

**CRITICAL DIRECTIVE**: Provide comprehensive, accurate answers. Each research question requires:
- Clear explanation (3-5 paragraphs, 300-500 words)
- Technical analysis explaining key concepts and mechanisms
- Real-world examples (2-3) with specific use cases
- Implementation guidance: practical patterns and best practices
- Common challenges with solutions
- Future directions and emerging trends

TARGET: 2000-4000 words total for all questions combined.
Focus on clarity, accuracy, and practical value.
Every claim must be substantiated with evidence or reasoning.
Provide actionable insights that users can apply.

## Your Response

Provide your response as valid JSON only:"""
        
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
