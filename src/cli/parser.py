"""
CLI Argument Parser - Command line interface setup.
"""

import argparse
from typing import Optional
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for ZenKnowledgeForge CLI.
    
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="zen",
        description="ZenKnowledgeForge - Local-first deliberative multi-agent LLM system",
        epilog="Example: zen \"Explain blockchain consensus mechanisms\" --mode research"
    )
    
    # Main argument: the brief
    parser.add_argument(
        "brief",
        nargs="?",
        help="Your brief or question (required unless using --interactive)"
    )
    
    # Execution mode
    parser.add_argument(
        "-m", "--mode",
        choices=["research", "project", "learn"],
        default="research",
        help="Execution mode (default: research)"
    )
    
    # Interactive mode
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Interactive mode - answer clarifying questions"
    )
    
    # Output options
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file path (default: auto-generated in ./outputs)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: ./outputs)"
    )
    
    # Verbosity
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output (DEBUG level logging)"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet output (WARNING level logging)"
    )
    
    # Configuration
    parser.add_argument(
        "--config-dir",
        type=Path,
        help="Configuration directory (default: ./config)"
    )
    
    # Session management
    parser.add_argument(
        "--session-id",
        help="Resume a previous session by ID"
    )
    
    parser.add_argument(
        "--save-session",
        action="store_true",
        help="Save session state for later resumption"
    )
    
    # Advanced options
    parser.add_argument(
        "--no-rich",
        action="store_true",
        help="Disable Rich formatting in console output"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and exit without execution"
    )
    
    parser.add_argument(
        "--single-model",
        action="store_true",
        help="Use a single model for all agents (interactive selection, faster)"
    )
    
    parser.add_argument(
        "--fast-mode",
        action="store_true",
        help="Fast mode: automatically use smallest model (phi3.5:3.8b) for all agents"
    )
    
    return parser


def validate_args(args: argparse.Namespace) -> bool:
    """
    Validate parsed arguments.
    
    Args:
        args: Parsed arguments
    
    Returns:
        True if valid, False otherwise
    """
    # Brief is required unless in interactive mode or dry run
    if not args.brief and not args.interactive and not args.dry_run:
        print("Error: brief is required (or use --interactive mode)")
        return False
    
    # Can't be both verbose and quiet
    if args.verbose and args.quiet:
        print("Error: Cannot use both --verbose and --quiet")
        return False
    
    # Can't use both single-model and fast-mode
    if args.single_model and args.fast_mode:
        print("Error: Cannot use both --single-model and --fast-mode")
        print("  --single-model: Interactive model selection")
        print("  --fast-mode: Automatic small model (phi3.5:3.8b)")
        return False
    
    return True


def get_log_level(args: argparse.Namespace) -> str:
    """
    Determine log level from arguments.
    
    Args:
        args: Parsed arguments
    
    Returns:
        Log level string (DEBUG, INFO, WARNING, etc.)
    """
    if args.verbose:
        return "DEBUG"
    elif args.quiet:
        return "WARNING"
    else:
        return "INFO"
