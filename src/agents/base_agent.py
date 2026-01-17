"""
Base Agent - Abstract class for all agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
import logging
import re

from ..orchestration.state import SharedState
from ..orchestration.model_manager import ModelManager


logger = logging.getLogger(__name__)


class PromptEngine:
    """
    Handles prompt template variable injection and formatting.
    """
    
    @staticmethod
    def inject_variables(template: str, variables: Dict[str, Any]) -> str:
        """
        Inject variables into a prompt template.
        
        Args:
            template: Prompt template with {variable} placeholders
            variables: Dictionary of variable values
        
        Returns:
            Formatted prompt
        """
        prompt = template
        
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            
            # Convert value to string appropriately
            if isinstance(value, dict) or isinstance(value, list):
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)
            
            prompt = prompt.replace(placeholder, value_str)
        
        return prompt
    
    @staticmethod
    def extract_json_from_response(response: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from an LLM response that may contain markdown or other text.
        
        Args:
            response: Raw LLM response
        
        Returns:
            Parsed JSON dictionary or None if parsing fails
        """
        # Try to find JSON in markdown code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass
        
        # Try to parse the entire response as JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON object in the text
        try:
            # Find the first { and last }
            start = response.find('{')
            end = response.rfind('}')
            
            if start != -1 and end != -1 and end > start:
                json_str = response[start:end+1]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError):
            pass
        
        return None


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Each agent must implement:
    - think(): Main reasoning method
    - _prepare_prompt(): Prepare the prompt for the LLM
    - _parse_response(): Parse the LLM's response
    """
    
    def __init__(
        self,
        name: str,
        model_name: str,
        vram_mb: int,
        temperature: float = 0.3,
        max_retries: int = 3
    ):
        """
        Initialize the agent.
        
        Args:
            name: Agent name (e.g., 'Interpreter')
            model_name: Ollama model name
            vram_mb: Expected VRAM usage in MB
            temperature: Sampling temperature
            max_retries: Maximum retries for JSON parsing
        """
        self.name = name
        self.model_name = model_name
        self.vram_mb = vram_mb
        self.temperature = temperature
        self.max_retries = max_retries
        
        self.prompt_engine = PromptEngine()
        
        logger.debug(f"Initialized {self.name} agent with model {self.model_name}")
    
    def think(
        self,
        state: SharedState,
        model_manager: ModelManager
    ) -> Dict[str, Any]:
        """
        Main reasoning method - execute the agent's thinking process.
        
        Args:
            state: Current shared state
            model_manager: Model manager for LLM access
        
        Returns:
            Agent's output as a dictionary
        """
        logger.info(f"{self.name} is thinking...")
        
        # Prepare the prompt
        prompt = self._prepare_prompt(state)
        
        # Generate response with retry logic
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"{self.name} generating response (attempt {attempt + 1})"
                )
                
                # Generate with the model
                response = model_manager.generate(
                    model_name=self.model_name,
                    prompt=prompt,
                    vram_mb=self.vram_mb,
                    agent_name=self.name.lower(),
                    temperature=self.temperature
                )
                
                logger.debug(f"{self.name} received response: {response[:200]}...")
                
                # Parse the response
                parsed = self._parse_response(response, state)
                
                if parsed is not None:
                    logger.info(f"{self.name} successfully produced output")
                    return parsed
                else:
                    logger.warning(
                        f"{self.name} failed to parse response (attempt {attempt + 1})"
                    )
                    
                    if attempt < self.max_retries - 1:
                        # Add instruction to return valid JSON
                        prompt = (
                            f"{prompt}\n\n"
                            f"IMPORTANT: Your previous response could not be parsed. "
                            f"Please respond with ONLY valid JSON, no markdown, "
                            f"no explanations."
                        )
                
            except Exception as e:
                logger.error(
                    f"{self.name} error during generation (attempt {attempt + 1}): {e}"
                )
                
                if attempt == self.max_retries - 1:
                    raise
        
        # If all retries failed, return a graceful degradation
        logger.error(f"{self.name} failed after {self.max_retries} attempts")
        return self._graceful_degradation(state)
    
    @abstractmethod
    def _prepare_prompt(self, state: SharedState) -> str:
        """
        Prepare the prompt for the LLM.
        
        Args:
            state: Current shared state
        
        Returns:
            Formatted prompt string
        """
        pass
    
    @abstractmethod
    def _parse_response(
        self,
        response: str,
        state: SharedState
    ) -> Optional[Dict[str, Any]]:
        """
        Parse the LLM's response into structured output.
        
        Args:
            response: Raw LLM response
            state: Current shared state
        
        Returns:
            Parsed output dictionary or None if parsing failed
        """
        pass
    
    def _graceful_degradation(self, state: SharedState) -> Dict[str, Any]:
        """
        Provide a fallback response when the agent fails.
        
        Args:
            state: Current shared state
        
        Returns:
            Minimal valid output
        """
        logger.warning(f"{self.name} using graceful degradation")
        
        return {
            "error": f"{self.name} failed to produce valid output",
            "degraded": True
        }
    
    def load_prompt_template(self, template_path: str) -> str:
        """
        Load a prompt template from file.
        
        Args:
            template_path: Path to the template file
        
        Returns:
            Template content
        """
        from pathlib import Path
        
        template_file = Path(template_path)
        if not template_file.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(template_file, 'r') as f:
            return f.read()
