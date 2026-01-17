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

# Add src to path as a package location
# Since src contains modules with relative imports, we need Python to see them
# as part of a package. We'll use an import hook to handle this.

# Simpler approach: temporarily symlink or modify sys.modules
src_dir = repo_root / "src"

# Add the parent of src so Python can find modules
sys.path.insert(0, str(repo_root))

# Now when we import from src, Python will use the structure in src/
if __name__ == "__main__":
    # Change directory to repo root for relative paths in config
    os.chdir(repo_root)
    
    # Now import and run, using 'src' as the package prefix
    import src.__main__
    sys.exit(src.__main__.main())
