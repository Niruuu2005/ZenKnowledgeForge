"""
Progress indicators and Rich UI components.
"""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.markdown import Markdown
from typing import Optional, Dict, Any
import json


class ProgressUI:
    """
    Rich UI components for progress visualization.
    """
    
    def __init__(self, use_rich: bool = True):
        """
        Initialize the progress UI.
        
        Args:
            use_rich: Whether to use Rich formatting
        """
        self.use_rich = use_rich
        self.console = Console() if use_rich else None
    
    def show_banner(self):
        """Display the ZenKnowledgeForge banner."""
        if not self.use_rich:
            print("=== ZenKnowledgeForge ===")
            print("Local-first deliberative multi-agent LLM system")
            print()
            return
        
        banner = """
        ╔══════════════════════════════════════════════════════════╗
        ║           🧘 ZenKnowledgeForge 🧘                        ║
        ║   Local-first deliberative multi-agent LLM system        ║
        ╚══════════════════════════════════════════════════════════╝
        """
        
        self.console.print(Panel(banner, style="bold blue"))
    
    def show_config_summary(self, config_info: Dict[str, Any]):
        """
        Display configuration summary.
        
        Args:
            config_info: Configuration information
        """
        if not self.use_rich:
            print("Configuration:")
            for key, value in config_info.items():
                print(f"  {key}: {value}")
            print()
            return
        
        table = Table(title="Configuration", show_header=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in config_info.items():
            table.add_row(key, str(value))
        
        self.console.print(table)
    
    def agent_thinking(self, agent_name: str) -> Optional[Any]:
        """
        Show that an agent is thinking.
        
        Args:
            agent_name: Name of the agent
        
        Returns:
            Context manager for progress
        """
        if not self.use_rich:
            print(f"[{agent_name}] Thinking...")
            return None
        
        return self.console.status(
            f"[bold yellow]{agent_name}[/bold yellow] is thinking...",
            spinner="dots"
        )
    
    def show_agent_output(self, agent_name: str, output: Dict[str, Any]):
        """
        Display agent output.
        
        Args:
            agent_name: Name of the agent
            output: Agent's output dictionary
        """
        if not self.use_rich:
            print(f"\n[{agent_name}] Output:")
            print(json.dumps(output, indent=2))
            print()
            return
        
        self.console.print(f"\n[bold green]✓[/bold green] {agent_name} completed")
        
        # Show key information based on agent
        if agent_name == "Interpreter" and "intent" in output:
            intent = output["intent"]
            self.console.print(f"  Goal: {intent.get('primary_goal', 'N/A')}")
            self.console.print(f"  Domain: {intent.get('domain', 'N/A')}")
        
        elif agent_name == "Planner" and "research_questions" in output:
            rqs = output["research_questions"]
            self.console.print(f"  Research Questions: {len(rqs)}")
        
        elif agent_name == "Judge" and "consensus_score" in output:
            score = output["consensus_score"]
            overall = score.get("overall", 0)
            self.console.print(f"  Consensus Score: {overall:.2f}")
    
    def show_pipeline_progress(self, agents: list, current_index: int):
        """
        Show pipeline progress.
        
        Args:
            agents: List of agent names
            current_index: Index of current agent
        """
        if not self.use_rich:
            progress = f"Pipeline: {current_index + 1}/{len(agents)}"
            print(progress)
            return
        
        pipeline_str = " → ".join([
            f"[bold green]{a}[/bold green]" if i < current_index
            else f"[bold yellow]{a}[/bold yellow]" if i == current_index
            else f"[dim]{a}[/dim]"
            for i, a in enumerate(agents)
        ])
        
        self.console.print(f"\nPipeline: {pipeline_str}\n")
    
    def show_final_artifact(self, artifact: Dict[str, Any], output_file: Optional[str] = None):
        """
        Display final artifact summary.
        
        Args:
            artifact: Final artifact dictionary
            output_file: Path to output file if saved
        """
        if not self.use_rich:
            print("\n=== Final Artifact ===")
            print(json.dumps(artifact, indent=2))
            if output_file:
                print(f"\nSaved to: {output_file}")
            return
        
        self.console.print("\n")
        self.console.print(Panel(
            "[bold green]✓ Artifact Generated Successfully[/bold green]",
            style="green"
        ))
        
        # Show metadata
        metadata = artifact.get("metadata", {})
        self.console.print(f"\nType: {artifact.get('type', 'unknown')}")
        self.console.print(f"Sections: {len(artifact.get('sections', []))}")
        self.console.print(f"Agents: {', '.join(metadata.get('agents_consulted', []))}")
        
        if output_file:
            self.console.print(f"\n[bold cyan]Saved to:[/bold cyan] {output_file}")
    
    def show_error(self, message: str):
        """
        Display an error message.
        
        Args:
            message: Error message
        """
        if not self.use_rich:
            print(f"ERROR: {message}")
            return
        
        self.console.print(f"\n[bold red]✗ Error:[/bold red] {message}")
    
    def show_warning(self, message: str):
        """
        Display a warning message.
        
        Args:
            message: Warning message
        """
        if not self.use_rich:
            print(f"WARNING: {message}")
            return
        
        self.console.print(f"[bold yellow]⚠ Warning:[/bold yellow] {message}")
