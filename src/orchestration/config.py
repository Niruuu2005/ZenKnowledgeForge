"""
Configuration loader and validation using Pydantic models.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
from pydantic import BaseModel, Field, field_validator
import os
from dotenv import load_dotenv


class AgentConfig(BaseModel):
    """Configuration for a single agent."""
    name: str
    model: str
    vram_mb: int
    role: str
    temperature: float = 0.3
    max_questions: Optional[int] = None
    max_research_questions: Optional[int] = None
    max_sources: Optional[int] = None
    consensus_threshold: Optional[float] = None
    max_deliberation_rounds: Optional[int] = None


class PipelineStep(BaseModel):
    """A single step in a pipeline."""
    agent: str


class PipelineConfig(BaseModel):
    """Configuration for a pipeline mode."""
    steps: List[PipelineStep]


class AgentsYamlConfig(BaseModel):
    """Full agents.yaml configuration."""
    agents: Dict[str, AgentConfig]
    pipelines: Dict[str, PipelineConfig]


class GPUConfig(BaseModel):
    """GPU hardware configuration."""
    name: str
    vram_mb: int
    max_model_vram_mb: int


class CPUConfig(BaseModel):
    """CPU hardware configuration."""
    ram_mb: int
    max_model_ram_mb: int


class HardwareConstraints(BaseModel):
    """Hardware constraint settings."""
    max_concurrent_models: int
    ollama_keep_alive: int
    model_swap_timeout_seconds: int
    model_load_retries: int


class PerformanceConfig(BaseModel):
    """Performance tuning settings."""
    max_concurrent_browser_tabs: int
    research_timeout_seconds: int
    embedding_batch_size: int
    max_context_tokens: int


class HardwareYamlConfig(BaseModel):
    """Full hardware.yaml configuration."""
    hardware: Dict[str, Any]
    
    @property
    def gpu(self) -> GPUConfig:
        return GPUConfig(**self.hardware['gpu'])
    
    @property
    def cpu(self) -> CPUConfig:
        return CPUConfig(**self.hardware['cpu'])
    
    @property
    def constraints(self) -> HardwareConstraints:
        return HardwareConstraints(**self.hardware['constraints'])
    
    @property
    def performance(self) -> PerformanceConfig:
        return PerformanceConfig(**self.hardware['performance'])


class ConfigLoader:
    """
    Loads and validates configuration from YAML files and environment variables.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Path to configuration directory. Defaults to ./config
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config"
        
        self.config_dir = Path(config_dir)
        
        # Load environment variables
        env_file = Path.cwd() / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        
        self._agents_config: Optional[AgentsYamlConfig] = None
        self._hardware_config: Optional[HardwareYamlConfig] = None
    
    def load_agents_config(self) -> AgentsYamlConfig:
        """Load and validate agents.yaml configuration."""
        if self._agents_config is not None:
            return self._agents_config
        
        agents_file = self.config_dir / "agents.yaml"
        if not agents_file.exists():
            raise FileNotFoundError(f"agents.yaml not found at {agents_file}")
        
        with open(agents_file, 'r') as f:
            data = yaml.safe_load(f)
        
        self._agents_config = AgentsYamlConfig(**data)
        return self._agents_config
    
    def load_hardware_config(self) -> HardwareYamlConfig:
        """Load and validate hardware.yaml configuration."""
        if self._hardware_config is not None:
            return self._hardware_config
        
        hardware_file = self.config_dir / "hardware.yaml"
        if not hardware_file.exists():
            raise FileNotFoundError(f"hardware.yaml not found at {hardware_file}")
        
        with open(hardware_file, 'r') as f:
            data = yaml.safe_load(f)
        
        self._hardware_config = HardwareYamlConfig(**data)
        return self._hardware_config
    
    def validate_hardware_compatibility(self) -> bool:
        """
        Validate that the system meets hardware requirements.
        
        Returns:
            True if compatible, raises ValueError otherwise
        """
        hw_config = self.load_hardware_config()
        agents_config = self.load_agents_config()
        
        # Check that at least one agent can fit in VRAM
        max_vram = hw_config.gpu.max_model_vram_mb
        
        can_run = []
        for agent_name, agent in agents_config.agents.items():
            if agent.vram_mb <= max_vram:
                can_run.append(agent_name)
        
        if not can_run:
            raise ValueError(
                f"No agents can fit in available VRAM ({max_vram}MB). "
                f"Minimum required: {min(a.vram_mb for a in agents_config.agents.values())}MB"
            )
        
        return True
    
    def get_ollama_base_url(self) -> str:
        """Get Ollama base URL from environment."""
        return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    def get_neo4j_uri(self) -> str:
        """Get Neo4j URI from environment."""
        return os.getenv("NEO4J_URI", "bolt://localhost:7687")
    
    def get_neo4j_auth(self) -> tuple:
        """Get Neo4j authentication from environment."""
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "zenknowledge123")
        return (user, password)
    
    def get_chroma_persist_dir(self) -> Path:
        """Get ChromaDB persistence directory."""
        persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")
        return Path(persist_dir)
    
    def get_session_db_path(self) -> Path:
        """Get session database path."""
        db_path = os.getenv("SESSION_DB_PATH", "./data/sessions.db")
        return Path(db_path)
    
    def get_log_level(self) -> str:
        """Get logging level from environment."""
        return os.getenv("LOG_LEVEL", "INFO")
    
    def get_log_file(self) -> Optional[Path]:
        """Get log file path from environment."""
        log_file = os.getenv("LOG_FILE")
        return Path(log_file) if log_file else None
    
    def get_output_dir(self) -> Path:
        """Get default output directory."""
        output_dir = os.getenv("DEFAULT_OUTPUT_DIR", "./outputs")
        return Path(output_dir)
    
    def get_default_mode(self) -> str:
        """Get default execution mode."""
        return os.getenv("DEFAULT_MODE", "research")
    
    def load_prompt_template(self, agent_name: str) -> str:
        """
        Load prompt template for an agent.
        
        Args:
            agent_name: Name of the agent (e.g., 'interpreter')
        
        Returns:
            Prompt template as string
        """
        prompt_file = self.config_dir / "prompts" / f"{agent_name}.md"
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_file}")
        
        with open(prompt_file, 'r') as f:
            return f.read()
