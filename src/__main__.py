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


def _run_preflight_checks(ui, config_loader) -> bool:
    """
    Run pre-flight checks to ensure system is ready.
    
    Args:
        ui: Progress UI instance
        config_loader: Configuration loader
    
    Returns:
        True if all checks pass, False otherwise
    """
    import urllib.request
    import urllib.error
    
    print("\n[*] Running pre-flight checks...")
    
    # Check Ollama connectivity
    ollama_url = config_loader.get_ollama_base_url()
    
    try:
        req = urllib.request.Request(f"{ollama_url}/api/tags", method='GET')
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                print("  [OK] Ollama service is running")
                
                # Check if models are available
                import json
                data = json.loads(response.read())
                
                if 'models' in data and len(data['models']) > 0:
                    print(f"  [OK] Found {len(data['models'])} models")
                else:
                    print("  [!] No models found - first run may be slow")
                    print("    Tip: Run 'bash scripts/pull_models.sh' to download models")
                
                return True
    except urllib.error.URLError as e:
        print(f"  [X] Cannot connect to Ollama at {ollama_url}")
        print(f"    Error: {e.reason}")
        print("\n  Fix:")
        print("    1. Start Docker Desktop")
        print("    2. Run: docker-compose up -d")
        print("    3. Wait ~30 seconds for Ollama to start")
        return False
    except Exception as e:
        print(f"  [X] Unexpected error checking Ollama: {e}\")")
        return False



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
            print("\n[OK] Configuration valid")
            return 0
        
        # Pre-flight checks
        logger.info("Running pre-flight system checks...")
        if not _run_preflight_checks(ui, config_loader):
            ui.show_error("Pre-flight checks failed. Fix the issues above and try again.")
            print("\nTip: Run diagnosis_script.py for detailed diagnostics")
            print("Tip: Run scripts/start_services.ps1 to start Docker services")
            return 1
        
        # Single model mode - interactive selection
        single_model_name = None
        if args.single_model:
            from .cli.model_selector import select_model_interactive
            
            print("\\n[>>] SINGLE MODEL MODE - Faster execution, no model swapping")
            print("   All agents will use the same model.")
            print()
            
            single_model_name = select_model_interactive(config_loader.get_ollama_base_url())
            
            if not single_model_name:
                print("\\n[X] No model selected. Exiting.")
                return 1
            
            print(f"\\n[OK] Using {single_model_name} for all agents")
            print("   Expected execution time: 8-12 minutes (vs 15-25 with swapping)\n")
        
        # Fast mode - automatically use smallest model
        elif args.fast_mode:
            single_model_name = "phi3.5:3.8b-mini-instruct-q4_K_M"
            
            print("\n⚡ FAST MODE - Using smallest model for maximum speed")
            print(f"   Model: {single_model_name}")
            print("   Expected execution time: 6-10 minutes")
            print("   Quality: Good for most queries\n")
        
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
            
            # Determine VRAM estimate for single model mode
            if single_model_name:
                # Use a conservative estimate based on model name
                if "14b" in single_model_name or "13b" in single_model_name:
                    single_model_vram = 9000
                elif "9b" in single_model_name or "8b" in single_model_name:
                    single_model_vram = 5500
                elif "7b" in single_model_name:
                    single_model_vram = 4500
                else:
                    single_model_vram = 3000
            
            # Create and register each agent
            interpreter_cfg = agents_config.agents["interpreter"]
            engine.register_agent(
                "interpreter",
                InterpreterAgent(
                    model_name=single_model_name or interpreter_cfg.model,
                    vram_mb=single_model_vram if single_model_name else interpreter_cfg.vram_mb,
                    temperature=interpreter_cfg.temperature,
                    max_questions=interpreter_cfg.max_questions or 5
                )
            )
            
            planner_cfg = agents_config.agents["planner"]
            engine.register_agent(
                "planner",
                PlannerAgent(
                    model_name=single_model_name or planner_cfg.model,
                    vram_mb=single_model_vram if single_model_name else planner_cfg.vram_mb,
                    temperature=planner_cfg.temperature,
                    max_research_questions=planner_cfg.max_research_questions or 5
                )
            )
            
            grounder_cfg = agents_config.agents["grounder"]
            engine.register_agent(
                "grounder",
                GrounderAgent(
                    model_name=single_model_name or grounder_cfg.model,
                    vram_mb=single_model_vram if single_model_name else grounder_cfg.vram_mb,
                    temperature=grounder_cfg.temperature,
                    max_sources=grounder_cfg.max_sources or 10
                )
            )
            
            auditor_cfg = agents_config.agents["auditor"]
            engine.register_agent(
                "auditor",
                AuditorAgent(
                    model_name=single_model_name or auditor_cfg.model,
                    vram_mb=single_model_vram if single_model_name else auditor_cfg.vram_mb,
                    temperature=auditor_cfg.temperature
                )
            )
            
            visualizer_cfg = agents_config.agents["visualizer"]
            engine.register_agent(
                "visualizer",
                VisualizerAgent(
                    model_name=single_model_name or visualizer_cfg.model,
                    vram_mb=single_model_vram if single_model_name else visualizer_cfg.vram_mb,
                    temperature=visualizer_cfg.temperature
                )
            )
            
            judge_cfg = agents_config.agents["judge"]
            engine.register_agent(
                "judge",
                JudgeAgent(
                    model_name=single_model_name or judge_cfg.model,
                    vram_mb=single_model_vram if single_model_name else judge_cfg.vram_mb,
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
            
            # Try rendering with template, fallback to raw JSON if fails
            try:
                content = renderer.render(
                    artifact=final_artifact,
                    mode=args.mode,
                    output_path=output_path
                )
            except Exception as render_error:
                logger.warning(f"Template rendering failed: {render_error}")
                logger.info("Falling back to raw artifact save...")
                
                # Save raw artifact as JSON
                import json
                json_path = Path(output_path).with_suffix('.json')
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(final_artifact, f, indent=2, default=str)
                
                # Also create a simple markdown version
                simple_md = f"""# ZenKnowledgeForge Research Output

**Generated:** {datetime.now().isoformat()}
**Mode:** {args.mode}

## Summary

{final_artifact.get('synthesis', {}).get('executive_summary', 'No summary available.')}

## Raw Output

See: {json_path}
"""
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(simple_md)
                
                ui.show_warning(f"Template failed - Raw output saved to: {json_path}")
            
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
