"""
Unit tests for agents - JSON parsing and graceful degradation.
"""

import pytest
from unittest.mock import Mock, patch

from src.agents.base_agent import BaseAgent, PromptEngine
from src.agents.interpreter import InterpreterAgent
from src.agents.planner import PlannerAgent
from src.orchestration.state import SharedState, ExecutionMode


class TestPromptEngine:
    """Test the PromptEngine utility class."""
    
    def test_variable_injection_simple(self):
        """Test simple variable injection."""
        template = "Hello {name}, you are {age} years old."
        variables = {"name": "Alice", "age": 30}
        
        result = PromptEngine.inject_variables(template, variables)
        assert result == "Hello Alice, you are 30 years old."
    
    def test_variable_injection_dict(self):
        """Test injecting dictionary variables."""
        template = "Data: {data}"
        variables = {"data": {"key": "value", "count": 42}}
        
        result = PromptEngine.inject_variables(template, variables)
        assert "key" in result
        assert "value" in result
    
    def test_extract_json_from_markdown(self):
        """Test extracting JSON from markdown code blocks."""
        response = '''
        Here's the JSON:
        ```json
        {"name": "test", "value": 123}
        ```
        '''
        
        result = PromptEngine.extract_json_from_response(response)
        assert result is not None
        assert result["name"] == "test"
        assert result["value"] == 123
    
    def test_extract_json_plain(self):
        """Test extracting plain JSON."""
        response = '{"name": "test", "value": 123}'
        
        result = PromptEngine.extract_json_from_response(response)
        assert result is not None
        assert result["name"] == "test"
    
    def test_extract_json_with_text(self):
        """Test extracting JSON embedded in text."""
        response = '''
        Some explanation text here.
        {"name": "test", "value": 123}
        More text after.
        '''
        
        result = PromptEngine.extract_json_from_response(response)
        assert result is not None
        assert result["name"] == "test"
    
    def test_extract_json_invalid(self):
        """Test that invalid JSON returns None."""
        response = "This is not JSON at all"
        
        result = PromptEngine.extract_json_from_response(response)
        assert result is None


class TestInterpreterAgent:
    """Test the Interpreter agent."""
    
    def test_initialization(self):
        """Test Interpreter initialization."""
        agent = InterpreterAgent()
        
        assert agent.name == "Interpreter"
        assert agent.model_name == "llama3.1:8b-instruct-q4_K_M"
        assert agent.vram_mb == 5000
        assert agent.max_questions == 5
    
    def test_prepare_prompt(self):
        """Test prompt preparation."""
        agent = InterpreterAgent()
        
        state = SharedState(
            user_brief="Test brief",
            execution_mode=ExecutionMode.RESEARCH
        )
        
        prompt = agent._prepare_prompt(state)
        
        assert "Test brief" in prompt
        assert "interpreter" in prompt.lower() or "input" in prompt.lower()
    
    def test_parse_valid_response(self):
        """Test parsing a valid response."""
        agent = InterpreterAgent()
        
        state = SharedState(
            user_brief="Test",
            execution_mode=ExecutionMode.RESEARCH
        )
        
        valid_response = '''
        {
            "intent": {
                "primary_goal": "Test goal",
                "domain": "testing",
                "output_type": "research_report",
                "scope": "narrow"
            },
            "extracted_requirements": ["Req 1"],
            "ambiguities": [],
            "clarifying_questions": [],
            "confidence": 0.8
        }
        '''
        
        result = agent._parse_response(valid_response, state)
        
        assert result is not None
        assert "intent" in result
        assert result["intent"]["primary_goal"] == "Test goal"
    
    def test_graceful_degradation(self):
        """Test graceful degradation when parsing fails."""
        agent = InterpreterAgent()
        
        state = SharedState(
            user_brief="Test brief",
            execution_mode=ExecutionMode.RESEARCH
        )
        
        fallback = agent._graceful_degradation(state)
        
        assert "intent" in fallback
        assert fallback["degraded"] == True
        assert "confidence" in fallback


class TestPlannerAgent:
    """Test the Planner agent."""
    
    def test_initialization(self):
        """Test Planner initialization."""
        agent = PlannerAgent()
        
        assert agent.name == "Planner"
        assert agent.model_name == "mistral-nemo:12b-instruct-q4_K_M"
        assert agent.max_research_questions == 5
    
    def test_parse_valid_response(self):
        """Test parsing a valid plan."""
        agent = PlannerAgent()
        
        state = SharedState(
            user_brief="Test",
            execution_mode=ExecutionMode.RESEARCH
        )
        
        valid_response = '''
        {
            "research_questions": [
                {
                    "id": "RQ1",
                    "question": "What is X?",
                    "type": "factual",
                    "priority": "high",
                    "estimated_time_minutes": 20,
                    "dependencies": []
                }
            ],
            "phases": [
                {
                    "name": "Phase 1",
                    "description": "First phase",
                    "rq_ids": ["RQ1"],
                    "parallel": false
                }
            ],
            "success_criteria": ["Criterion 1"],
            "estimated_total_time_minutes": 30
        }
        '''
        
        result = agent._parse_response(valid_response, state)
        
        assert result is not None
        assert "research_questions" in result
        assert len(result["research_questions"]) == 1
        assert "phases" in result


class TestBaseAgent:
    """Test the BaseAgent abstract class functionality."""
    
    def test_cannot_instantiate_directly(self):
        """Test that BaseAgent cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAgent(
                name="Test",
                model_name="test",
                vram_mb=1000
            )
