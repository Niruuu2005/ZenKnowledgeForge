#!/usr/bin/env python3
"""
Development runner for ZenKnowledgeForge.

This script runs ZenKnowledgeForge from source by temporarily creating
a proper package structure in memory.
"""

import sys
import os
from pathlib import Path

# Get the repository root
repo_root = Path(__file__).parent.absolute()

# Validate that src directory exists
src_dir = repo_root / "src"
if not src_dir.exists():
    print(f"Error: Could not find src directory at {src_dir}", file=sys.stderr)
    print("Please run this script from the repository root.", file=sys.stderr)
    sys.exit(1)

# Add the parent of src so Python can find modules
sys.path.insert(0, str(repo_root))

# Now when we import from src, Python will use the structure in src/
if __name__ == "__main__":
    # Change directory to repo root for relative paths in config
    os.chdir(repo_root)
    
    # Now import and run, using 'src' as the package prefix
    try:
        import src.__main__
    except ImportError as e:
        print(f"Error importing src.__main__: {e}", file=sys.stderr)
        print("Please ensure all dependencies are installed.", file=sys.stderr)
        print("Run: pip install pydantic pyyaml httpx rich jinja2 python-dotenv", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(src.__main__.main())
