"""
Markdown renderer - Generates markdown artifacts from final output.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class MarkdownRenderer:
    """
    Renders final artifacts as markdown using Jinja2 templates.
    """
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the markdown renderer.
        
        Args:
            template_dir: Path to template directory
        """
        if template_dir is None:
            template_dir = Path(__file__).parent.parent.parent / "config" / "templates"
        
        self.template_dir = Path(template_dir)
        
        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        logger.debug(f"MarkdownRenderer initialized with templates from {template_dir}")
    
    def render(
        self,
        artifact: Dict[str, Any],
        mode: str,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Render an artifact to markdown.
        
        Args:
            artifact: Final artifact dictionary from Judge
            mode: Execution mode (research, project, learn)
            output_path: Optional path to save the output
        
        Returns:
            Rendered markdown content
        """
        # Select template based on mode
        template_map = {
            "research": "research_report.md.j2",
            "project": "project_overview.md.j2",
            "learn": "learning_path.md.j2"
        }
        
        template_name = template_map.get(mode, "research_report.md.j2")
        
        try:
            template = self.env.get_template(template_name)
        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {e}")
            # Fallback to simple rendering
            return self._render_simple(artifact, mode)
        
        # Enhance artifact with additional metadata if missing
        artifact = self._enhance_artifact(artifact, mode)
        
        try:
            # Render the template
            content = template.render(artifact=artifact)
            
            # Save to file if path provided
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w') as f:
                    f.write(content)
                
                logger.info(f"Rendered artifact saved to {output_path}")
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to render template: {e}")
            return self._render_simple(artifact, mode)
    
    def _enhance_artifact(self, artifact: Dict[str, Any], mode: str) -> Dict[str, Any]:
        """
        Enhance artifact with default values for template rendering.
        
        Args:
            artifact: Original artifact
            mode: Execution mode
        
        Returns:
            Enhanced artifact
        """
        # Make a copy to avoid modifying original
        enhanced = artifact.copy()
        
        # Ensure metadata exists
        if "metadata" not in enhanced:
            enhanced["metadata"] = {}
        
        metadata = enhanced["metadata"]
        
        # Add defaults
        if "title" not in metadata:
            metadata["title"] = f"ZenKnowledgeForge {mode.title()} Output"
        
        if "created_at" not in metadata:
            metadata["created_at"] = datetime.now().isoformat()
        
        if "agents_consulted" not in metadata:
            metadata["agents_consulted"] = []
        
        if "sources" not in metadata:
            metadata["sources"] = []
        
        # Ensure consensus_score exists
        if "consensus_score" not in enhanced:
            enhanced["consensus_score"] = {
                "groundedness": 0.5,
                "coherence": 0.5,
                "completeness": 0.5,
                "overall": 0.5,
                "justification": "No consensus score available"
            }
        
        # Ensure synthesis exists
        if "synthesis" not in enhanced:
            enhanced["synthesis"] = {
                "executive_summary": "No synthesis available",
                "key_insights": [],
                "conflicts_resolved": [],
                "knowledge_gaps": []
            }
        
        # Ensure sections exist
        if "sections" not in enhanced:
            enhanced["sections"] = []
        
        return enhanced
    
    def _render_simple(self, artifact: Dict[str, Any], mode: str) -> str:
        """
        Fallback simple rendering without templates.
        
        Args:
            artifact: Final artifact
            mode: Execution mode
        
        Returns:
            Simple markdown content
        """
        lines = [
            f"# ZenKnowledgeForge {mode.title()} Output",
            "",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Artifact",
            ""
        ]
        
        # Add sections if available
        sections = artifact.get("sections", [])
        for section in sections:
            title = section.get("title", "Untitled")
            content = section.get("content", "")
            
            lines.append(f"### {title}")
            lines.append("")
            lines.append(content)
            lines.append("")
        
        # Add synthesis if available
        synthesis = artifact.get("synthesis", {})
        if synthesis.get("executive_summary"):
            lines.append("## Summary")
            lines.append("")
            lines.append(synthesis["executive_summary"])
            lines.append("")
        
        return "\n".join(lines)
