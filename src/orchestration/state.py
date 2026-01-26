"""
Shared State - Context passed between pipeline steps.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ExecutionMode(str, Enum):
    """Execution mode for the pipeline."""
    RESEARCH = "research"
    PROJECT = "project"
    LEARN = "learn"


class SharedState(BaseModel):
    """
    State object passed between agents in the pipeline.
    
    This accumulates context and results from each agent.
    """
    
    # Original user input
    user_brief: str
    execution_mode: ExecutionMode
    
    # Clarifications (from interactive mode or interpreter)
    clarifications: Dict[str, Any] = Field(default_factory=dict)
    
    # Intent (from interpreter)
    intent: Optional[Dict[str, Any]] = None
    
    # Plan (from planner)
    plan: Optional[Dict[str, Any]] = None
    
    # Evidence (retrieved by grounder for research questions)
    evidence: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    
    # Research findings (from grounder)
    research_findings: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Audit report (from auditor)
    audit_report: Optional[Dict[str, Any]] = None
    
    # Visualizations (from visualizer)
    visualizations: Optional[Dict[str, Any]] = None
    
    # Final artifact (from judge)
    final_artifact: Optional[Dict[str, Any]] = None
    
    # Consensus score
    consensus_score: Optional[float] = None
    
    # Deliberation tracking
    deliberation_round: int = 0
    max_deliberation_rounds: int = 7
    consensus_threshold: float = 0.85
    
    # Execution metadata
    session_id: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Agent outputs (raw)
    agent_outputs: Dict[str, Any] = Field(default_factory=dict)
    
    # Errors encountered
    errors: List[Dict[str, str]] = Field(default_factory=list)
    
    class Config:
        """Pydantic config."""
        use_enum_values = True
    
    def add_agent_output(self, agent_name: str, output: Dict[str, Any]):
        """
        Add output from an agent.
        
        Args:
            agent_name: Name of the agent
            output: Agent's output dictionary
        """
        self.agent_outputs[agent_name] = output
    
    def add_error(self, agent_name: str, error: str):
        """
        Record an error.
        
        Args:
            agent_name: Name of the agent that encountered the error
            error: Error message
        """
        self.errors.append({
            "agent": agent_name,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    def should_continue_deliberation(self) -> bool:
        """
        Determine if deliberation should continue.
        
        Returns:
            True if another round is needed
        """
        if self.consensus_score is None:
            return True
        
        if self.consensus_score >= self.consensus_threshold:
            return False
        
        if self.deliberation_round >= self.max_deliberation_rounds:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SharedState":
        """Create from dictionary."""
        return cls(**data)
