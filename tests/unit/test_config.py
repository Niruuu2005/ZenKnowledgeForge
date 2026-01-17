"""
Unit tests for configuration loading and validation.
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from src.orchestration.config import ConfigLoader, AgentsYamlConfig, HardwareYamlConfig


class TestConfigLoader:
    """Test the ConfigLoader class."""
    
    def test_load_agents_config(self):
        """Test loading agents configuration."""
        config_loader = ConfigLoader()
        agents_config = config_loader.load_agents_config()
        
        assert isinstance(agents_config, AgentsYamlConfig)
        assert "interpreter" in agents_config.agents
        assert "judge" in agents_config.agents
        
        # Check interpreter configuration
        interpreter = agents_config.agents["interpreter"]
        assert interpreter.name == "Interpreter"
        assert interpreter.vram_mb == 5000
        assert interpreter.temperature == 0.3
    
    def test_load_hardware_config(self):
        """Test loading hardware configuration."""
        config_loader = ConfigLoader()
        hardware_config = config_loader.load_hardware_config()
        
        assert isinstance(hardware_config, HardwareYamlConfig)
        
        gpu = hardware_config.gpu
        assert gpu.max_model_vram_mb == 5500
        
        constraints = hardware_config.constraints
        assert constraints.max_concurrent_models == 1
        assert constraints.ollama_keep_alive == 0
    
    def test_validate_hardware_compatibility(self):
        """Test hardware compatibility validation."""
        config_loader = ConfigLoader()
        
        # Should pass with default configuration
        assert config_loader.validate_hardware_compatibility() == True
    
    def test_get_environment_variables(self):
        """Test environment variable getters."""
        config_loader = ConfigLoader()
        
        ollama_url = config_loader.get_ollama_base_url()
        assert "localhost" in ollama_url or "ollama" in ollama_url
        
        log_level = config_loader.get_log_level()
        assert log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        default_mode = config_loader.get_default_mode()
        assert default_mode in ["research", "project", "learn"]


class TestConfigValidation:
    """Test Pydantic model validation."""
    
    def test_invalid_agents_config(self):
        """Test that invalid agent config raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "agents.yaml"
            
            # Missing required field
            invalid_config = {
                "agents": {
                    "interpreter": {
                        "name": "Interpreter"
                        # Missing 'model', 'vram_mb', 'role'
                    }
                },
                "pipelines": {}
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(invalid_config, f)
            
            config_loader = ConfigLoader(config_dir=tmpdir)
            
            with pytest.raises(Exception):
                config_loader.load_agents_config()
