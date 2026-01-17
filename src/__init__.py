"""
ZenKnowledgeForge - Local-first deliberative multi-agent LLM system

This module provides the main package interface for ZenKnowledgeForge.
"""

__version__ = "0.1.0"

# Core orchestration
from .orchestration.config import ConfigLoader
from .orchestration.model_manager import ModelManager
from .orchestration.engine import PipelineEngine
from .orchestration.state import SharedState, ExecutionMode

# Agents
from .agents.interpreter import InterpreterAgent
from .agents.planner import PlannerAgent
from .agents.grounder import GrounderAgent
from .agents.auditor import AuditorAgent
from .agents.visualizer import VisualizerAgent
from .agents.judge import JudgeAgent

# CLI
from .cli.parser import create_parser
from .cli.progress import ProgressUI
from .cli.interactive import InteractiveMode

# Renderers
from .renderers.markdown import MarkdownRenderer

__all__ = [
    "__version__",
    # Orchestration
    "ConfigLoader",
    "ModelManager",
    "PipelineEngine",
    "SharedState",
    "ExecutionMode",
    # Agents
    "InterpreterAgent",
    "PlannerAgent",
    "GrounderAgent",
    "AuditorAgent",
    "VisualizerAgent",
    "JudgeAgent",
    # CLI
    "create_parser",
    "ProgressUI",
    "InteractiveMode",
    # Renderers
    "MarkdownRenderer",
]
