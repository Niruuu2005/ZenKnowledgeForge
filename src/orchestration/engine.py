"""
Pipeline Engine - Main execution loop for agent orchestration.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import uuid

from .config import ConfigLoader
from .model_manager import ModelManager
from .state import SharedState, ExecutionMode


logger = logging.getLogger(__name__)


class PipelineEngine:
    """
    Main execution engine for running agent pipelines.
    
    Coordinates agents based on the selected execution mode (research, project, learn).
    """
    
    def __init__(
        self,
        config_loader: Optional[ConfigLoader] = None,
        model_manager: Optional[ModelManager] = None
    ):
        """
        Initialize the pipeline engine.
        
        Args:
            config_loader: Configuration loader instance
            model_manager: Model manager instance
        """
        self.config_loader = config_loader or ConfigLoader()
        
        # Load configurations
        self.agents_config = self.config_loader.load_agents_config()
        self.hardware_config = self.config_loader.load_hardware_config()
        
        # Validate hardware compatibility
        self.config_loader.validate_hardware_compatibility()
        
        # Initialize model manager
        if model_manager is None:
            ollama_url = self.config_loader.get_ollama_base_url()
            constraints = self.hardware_config.constraints
            
            model_manager = ModelManager(
                ollama_base_url=ollama_url,
                max_concurrent_models=constraints.max_concurrent_models,
                model_swap_timeout=constraints.model_swap_timeout_seconds,
                max_retries=constraints.model_load_retries
            )
        
        self.model_manager = model_manager
        
        # Agent registry (will be populated when agents are imported)
        self._agent_registry: Dict[str, Any] = {}
        
        logger.info("PipelineEngine initialized")
    
    def register_agent(self, agent_name: str, agent_instance: Any):
        """
        Register an agent with the engine.
        
        Args:
            agent_name: Name of the agent (e.g., 'interpreter')
            agent_instance: Agent instance
        """
        self._agent_registry[agent_name] = agent_instance
        logger.debug(f"Registered agent: {agent_name}")
    
    def get_pipeline_steps(self, mode: ExecutionMode) -> List[str]:
        """
        Get the list of agent names for a pipeline mode.
        
        Args:
            mode: Execution mode
        
        Returns:
            List of agent names in execution order
        """
        mode_str = mode.value if isinstance(mode, ExecutionMode) else mode
        
        if mode_str not in self.agents_config.pipelines:
            raise ValueError(f"Unknown pipeline mode: {mode_str}")
        
        pipeline = self.agents_config.pipelines[mode_str]
        return [step.agent for step in pipeline.steps]
    
    def execute_pipeline(
        self,
        user_brief: str,
        mode: ExecutionMode = ExecutionMode.RESEARCH,
        clarifications: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> SharedState:
        """
        Execute a full pipeline for the given mode.
        
        Args:
            user_brief: User's input brief
            mode: Execution mode (research, project, learn)
            clarifications: Optional clarifications from interactive mode
            session_id: Optional session ID for tracking
        
        Returns:
            Final SharedState after pipeline execution
        """
        # Generate session ID if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        logger.info(f"Starting pipeline execution: mode={mode}, session={session_id}")
        
        # Initialize shared state
        state = SharedState(
            user_brief=user_brief,
            execution_mode=mode,
            clarifications=clarifications or {},
            session_id=session_id
        )
        
        # Get pipeline steps
        agent_names = self.get_pipeline_steps(mode)
        logger.info(f"Pipeline steps: {' -> '.join(agent_names)}")
        
        # Execute each agent in sequence
        for agent_name in agent_names:
            try:
                logger.info(f"Executing agent: {agent_name}")
                
                # Get agent instance
                if agent_name not in self._agent_registry:
                    raise ValueError(f"Agent not registered: {agent_name}")
                
                agent = self._agent_registry[agent_name]
                
                # Execute agent
                agent_output = agent.think(state, self.model_manager)
                
                # Validate agent output
                if agent_output is None or (isinstance(agent_output, dict) and len(agent_output) == 0):
                    logger.warning(
                        f"Agent {agent_name} produced empty output. "
                        f"This may cause issues for downstream agents."
                    )
                
                # Update state with agent output
                state.add_agent_output(agent_name, agent_output)
                
                # Agent-specific state updates
                self._update_state_from_agent(state, agent_name, agent_output)
                
                logger.info(f"Agent {agent_name} completed successfully")
                
            except Exception as e:
                error_msg = f"Error in agent {agent_name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                state.add_error(agent_name, error_msg)
                
                # Decide whether to continue or abort
                # For now, we'll continue with other agents
                continue
        
        # Mark completion
        from datetime import datetime
        state.completed_at = datetime.now()
        
        logger.info(f"Pipeline execution completed: session={session_id}")
        
        return state
    
    def _update_state_from_agent(
        self,
        state: SharedState,
        agent_name: str,
        agent_output: Dict[str, Any]
    ):
        """
        Update shared state based on agent output.
        
        Args:
            state: Current shared state
            agent_name: Name of the agent
            agent_output: Output from the agent
        """
        if agent_name == "interpreter":
            state.intent = agent_output.get("intent")
        
        elif agent_name == "planner":
            state.plan = agent_output
        
        elif agent_name == "grounder":
            # Grounder may be called multiple times (for each research question)
            if isinstance(agent_output, list):
                state.research_findings.extend(agent_output)
            else:
                state.research_findings.append(agent_output)
        
        elif agent_name == "auditor":
            state.audit_report = agent_output
        
        elif agent_name == "visualizer":
            state.visualizations = agent_output
        
        elif agent_name == "judge":
            state.final_artifact = agent_output.get("final_artifact")
            
            # Extract consensus score
            consensus = agent_output.get("consensus_score", {})
            state.consensus_score = consensus.get("overall")
            
            # Check if we need another deliberation round
            if agent_output.get("decision") == "needs_revision":
                state.deliberation_round += 1
                
                if state.should_continue_deliberation():
                    logger.info(
                        f"Judge requested revision. "
                        f"Starting deliberation round {state.deliberation_round}"
                    )
                    # In a full implementation, we would re-run parts of the pipeline
                else:
                    logger.warning(
                        f"Judge requested revision but max rounds reached "
                        f"({state.deliberation_round}/{state.max_deliberation_rounds})"
                    )
    
    def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up PipelineEngine")
        if self.model_manager:
            self.model_manager.cleanup()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
