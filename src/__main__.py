"""
ZenKnowledgeForge - Main entry point.

This module provides the CLI interface for running the deliberative multi-agent system.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging

from .cli.parser import create_parser, validate_args, get_log_level
from .cli.progress import ProgressUI
from .cli.interactive import InteractiveMode
from .orchestration.config import ConfigLoader
from .orchestration.model_manager import ModelManager
from .orchestration.engine import PipelineEngine
from .orchestration.state import ExecutionMode
from .orchestration.logging_config import setup_logging
from .agents.interpreter import InterpreterAgent
from .agents.planner import PlannerAgent
from .agents.grounder import GrounderAgent
from .agents.auditor import AuditorAgent
from .agents.visualizer import VisualizerAgent
from .agents.judge import JudgeAgent
from .renderers.markdown import MarkdownRenderer


logger = logging.getLogger(__name__)


def main():
    """Main entry point for ZenKnowledgeForge CLI."""
    
    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate arguments
    if not validate_args(args):
        parser.print_help()
        return 1
    
    # Determine log level
    log_level = get_log_level(args)
    
    # Setup logging
    log_file = None
    if not args.quiet:
        log_file = Path("logs") / f"zen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    setup_logging(
        level=log_level,
        log_file=log_file,
        rich_formatting=not args.no_rich
    )
    
    # Initialize UI
    ui = ProgressUI(use_rich=not args.no_rich)
    
    try:
        # Show banner
        ui.show_banner()
        
        # Load configuration
        logger.info("Loading configuration...")
        config_loader = ConfigLoader(config_dir=args.config_dir)
        
        # Validate hardware compatibility
        try:
            config_loader.validate_hardware_compatibility()
        except ValueError as e:
            ui.show_error(f"Hardware incompatibility: {e}")
            return 1
        
        # Dry run - just validate and exit
        if args.dry_run:
            ui.show_config_summary({
                "Mode": args.mode,
                "Ollama URL": config_loader.get_ollama_base_url(),
                "Output Dir": args.output_dir or config_loader.get_output_dir(),
                "Log Level": log_level
            })
            print("\n✓ Configuration valid")
            return 0
        
        # Get user brief
        if args.interactive:
            interactive = InteractiveMode(use_rich=not args.no_rich)
            user_brief = args.brief or interactive.get_brief()
        else:
            user_brief = args.brief
        
        if not user_brief:
            ui.show_error("No brief provided")
            return 1
        
        # Show configuration
        ui.show_config_summary({
            "Mode": args.mode,
            "Brief": user_brief[:50] + "..." if len(user_brief) > 50 else user_brief,
            "Interactive": "Yes" if args.interactive else "No"
        })
        
        # Initialize engine
        logger.info("Initializing pipeline engine...")
        
        with PipelineEngine(config_loader=config_loader) as engine:
            
            # Load agent configurations
            agents_config = config_loader.load_agents_config()
            
            # Register agents
            logger.info("Registering agents...")
            
            # Create and register each agent
            interpreter_cfg = agents_config.agents["interpreter"]
            engine.register_agent(
                "interpreter",
                InterpreterAgent(
                    model_name=interpreter_cfg.model,
                    vram_mb=interpreter_cfg.vram_mb,
                    temperature=interpreter_cfg.temperature,
                    max_questions=interpreter_cfg.max_questions or 5
                )
            )
            
            planner_cfg = agents_config.agents["planner"]
            engine.register_agent(
                "planner",
                PlannerAgent(
                    model_name=planner_cfg.model,
                    vram_mb=planner_cfg.vram_mb,
                    temperature=planner_cfg.temperature,
                    max_research_questions=planner_cfg.max_research_questions or 5
                )
            )
            
            grounder_cfg = agents_config.agents["grounder"]
            engine.register_agent(
                "grounder",
                GrounderAgent(
                    model_name=grounder_cfg.model,
                    vram_mb=grounder_cfg.vram_mb,
                    temperature=grounder_cfg.temperature,
                    max_sources=grounder_cfg.max_sources or 10
                )
            )
            
            auditor_cfg = agents_config.agents["auditor"]
            engine.register_agent(
                "auditor",
                AuditorAgent(
                    model_name=auditor_cfg.model,
                    vram_mb=auditor_cfg.vram_mb,
                    temperature=auditor_cfg.temperature
                )
            )
            
            visualizer_cfg = agents_config.agents["visualizer"]
            engine.register_agent(
                "visualizer",
                VisualizerAgent(
                    model_name=visualizer_cfg.model,
                    vram_mb=visualizer_cfg.vram_mb,
                    temperature=visualizer_cfg.temperature
                )
            )
            
            judge_cfg = agents_config.agents["judge"]
            engine.register_agent(
                "judge",
                JudgeAgent(
                    model_name=judge_cfg.model,
                    vram_mb=judge_cfg.vram_mb,
                    temperature=judge_cfg.temperature,
                    consensus_threshold=judge_cfg.consensus_threshold or 0.85,
                    max_deliberation_rounds=judge_cfg.max_deliberation_rounds or 7
                )
            )
            
            # Get pipeline steps for the mode
            mode = ExecutionMode(args.mode)
            pipeline_steps = engine.get_pipeline_steps(mode)
            
            logger.info(f"Pipeline: {' -> '.join(pipeline_steps)}")
            
            # Execute pipeline
            logger.info("Starting pipeline execution...")
            
            # Show pipeline progress
            ui.show_pipeline_progress(pipeline_steps, 0)
            
            # Execute the pipeline
            state = engine.execute_pipeline(
                user_brief=user_brief,
                mode=mode,
                session_id=args.session_id
            )
            
            # Check for errors
            if state.errors:
                ui.show_warning(f"Pipeline completed with {len(state.errors)} errors")
                for error in state.errors:
                    logger.error(f"Agent {error['agent']}: {error['error']}")
            
            # Get final artifact
            final_artifact = state.final_artifact
            
            if not final_artifact:
                ui.show_error("No final artifact generated")
                return 1
            
            # Render the artifact
            logger.info("Rendering final artifact...")
            
            renderer = MarkdownRenderer()
            
            # Determine output path
            if args.output:
                output_path = args.output
            else:
                output_dir = args.output_dir or config_loader.get_output_dir()
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{args.mode}_{timestamp}.md"
                output_path = output_dir / filename
            
            # Render and save
            content = renderer.render(
                artifact=final_artifact,
                mode=args.mode,
                output_path=output_path
            )
            
            # Show success
            ui.show_final_artifact(final_artifact, str(output_path))
            
            logger.info("Pipeline execution completed successfully")
            
            return 0
    
    except KeyboardInterrupt:
        ui.show_warning("Interrupted by user")
        return 130
    
    except Exception as e:
        logger.exception("Fatal error during execution")
        ui.show_error(f"Fatal error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
