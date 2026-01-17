"""
Integration test for ZenKnowledgeForge v0.1.0

This test verifies that all components can be imported and initialized
without errors, even if Ollama is not running.
"""

import sys
from pathlib import Path

# Add repository root to path so 'src' package can be found
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing module imports...")
    
    try:
        # Core orchestration
        from src.orchestration.config import ConfigLoader
        from src.orchestration.model_manager import ModelManager
        from src.orchestration.engine import PipelineEngine
        from src.orchestration.state import SharedState, ExecutionMode
        from src.orchestration.logging_config import setup_logging
        
        # Agents
        from src.agents.interpreter import InterpreterAgent
        from src.agents.planner import PlannerAgent
        from src.agents.grounder import GrounderAgent
        from src.agents.auditor import AuditorAgent
        from src.agents.visualizer import VisualizerAgent
        from src.agents.judge import JudgeAgent
        from src.agents.base_agent import BaseAgent, PromptEngine
        
        # CLI
        from src.cli.parser import create_parser
        from src.cli.progress import ProgressUI
        from src.cli.interactive import InteractiveMode
        
        # Renderers
        from src.renderers.markdown import MarkdownRenderer
        
        print("✓ All modules imported successfully")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test configuration loading."""
    print("\nTesting configuration loading...")
    
    try:
        from src.orchestration.config import ConfigLoader
        
        config_loader = ConfigLoader()
        
        # Load configs
        agents_config = config_loader.load_agents_config()
        hardware_config = config_loader.load_hardware_config()
        
        # Check agents
        assert len(agents_config.agents) == 6, "Should have 6 agents"
        assert "interpreter" in agents_config.agents
        assert "planner" in agents_config.agents
        assert "grounder" in agents_config.agents
        assert "auditor" in agents_config.agents
        assert "visualizer" in agents_config.agents
        assert "judge" in agents_config.agents
        
        # Check pipelines
        assert len(agents_config.pipelines) == 3, "Should have 3 pipelines"
        assert "research" in agents_config.pipelines
        assert "project" in agents_config.pipelines
        assert "learn" in agents_config.pipelines
        
        print(f"✓ Configuration loaded: {len(agents_config.agents)} agents, {len(agents_config.pipelines)} pipelines")
        return True
        
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_initialization():
    """Test that agents can be initialized."""
    print("\nTesting agent initialization...")
    
    try:
        from src.agents.interpreter import InterpreterAgent
        from src.agents.planner import PlannerAgent
        from src.agents.grounder import GrounderAgent
        from src.agents.auditor import AuditorAgent
        from src.agents.visualizer import VisualizerAgent
        from src.agents.judge import JudgeAgent
        
        # Initialize each agent
        agents = {
            "Interpreter": InterpreterAgent(),
            "Planner": PlannerAgent(),
            "Grounder": GrounderAgent(),
            "Auditor": AuditorAgent(),
            "Visualizer": VisualizerAgent(),
            "Judge": JudgeAgent(),
        }
        
        for name, agent in agents.items():
            assert agent.name == name, f"Agent name mismatch: {agent.name} != {name}"
            assert agent.model_name, f"Agent {name} missing model_name"
            assert agent.vram_mb > 0, f"Agent {name} has invalid VRAM"
        
        print(f"✓ All {len(agents)} agents initialized successfully")
        return True
        
    except Exception as e:
        print(f"✗ Agent initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_management():
    """Test SharedState."""
    print("\nTesting state management...")
    
    try:
        from src.orchestration.state import SharedState, ExecutionMode
        
        state = SharedState(
            user_brief="Test brief",
            execution_mode=ExecutionMode.RESEARCH
        )
        
        # Test adding outputs
        state.add_agent_output("test_agent", {"result": "test"})
        assert "test_agent" in state.agent_outputs
        
        # Test error tracking
        state.add_error("test_agent", "test error")
        assert len(state.errors) == 1
        
        # Test serialization
        state_dict = state.to_dict()
        assert isinstance(state_dict, dict)
        assert state_dict["user_brief"] == "Test brief"
        
        # Test deserialization
        new_state = SharedState.from_dict(state_dict)
        assert new_state.user_brief == "Test brief"
        assert new_state.execution_mode == ExecutionMode.RESEARCH
        
        print("✓ State management working correctly")
        return True
        
    except Exception as e:
        print(f"✗ State management error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_engine():
    """Test PromptEngine utilities."""
    print("\nTesting prompt engine...")
    
    try:
        from src.agents.base_agent import PromptEngine
        
        # Test variable injection
        template = "Hello {name}, you are {age} years old."
        variables = {"name": "Alice", "age": 30}
        result = PromptEngine.inject_variables(template, variables)
        assert "Alice" in result
        assert "30" in result
        
        # Test JSON extraction from markdown
        response = '''
        Here's the result:
        ```json
        {"key": "value", "number": 42}
        ```
        '''
        parsed = PromptEngine.extract_json_from_response(response)
        assert parsed is not None
        assert parsed["key"] == "value"
        assert parsed["number"] == 42
        
        # Test plain JSON extraction
        plain_json = '{"test": true}'
        parsed = PromptEngine.extract_json_from_response(plain_json)
        assert parsed is not None
        assert parsed["test"] is True
        
        print("✓ Prompt engine working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Prompt engine error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_parser():
    """Test CLI argument parser."""
    print("\nTesting CLI parser...")
    
    try:
        from src.cli.parser import create_parser, validate_args
        
        parser = create_parser()
        
        # Test with valid arguments
        args = parser.parse_args(["test brief", "--mode", "research"])
        assert args.brief == "test brief"
        assert args.mode == "research"
        assert validate_args(args)
        
        # Test dry-run
        args = parser.parse_args(["--dry-run", "test"])
        assert args.dry_run
        assert validate_args(args)
        
        print("✓ CLI parser working correctly")
        return True
        
    except Exception as e:
        print(f"✗ CLI parser error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("ZenKnowledgeForge v0.1.0 Integration Test")
    print("=" * 70)
    
    tests = [
        test_imports,
        test_configuration,
        test_agent_initialization,
        test_state_management,
        test_prompt_engine,
        test_cli_parser,
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "=" * 70)
    print(f"Test Summary: {sum(results)}/{len(results)} tests passed")
    print("=" * 70)
    
    if all(results):
        print("\n✓ All tests passed! ZenKnowledgeForge v0.1.0 is ready.")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
