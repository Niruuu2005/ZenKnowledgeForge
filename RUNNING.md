# ZenKnowledgeForge - Running from Source

## Quick Start (Development Mode)

If you want to run ZenKnowledgeForge from source without installing it:

```bash
# 1. Install dependencies
pip install pydantic pyyaml httpx rich jinja2 python-dotenv

# 2. Run using the development runner
python run_zen.py --help
python run_zen.py --dry-run "test query"

# Example: Run in research mode
python run_zen.py "Explain blockchain consensus" --mode research
```

## Installation (Production Mode)

For proper installation:

```bash
# Install with all dependencies
pip install -e .

# Or use the zen command directly (after installation)
zen "Your query here" --mode research
```

## Requirements

- Python 3.10+
- Dependencies listed in pyproject.toml
- Ollama running locally (for actual execution)
- NVIDIA GPU with 6GB+ VRAM (recommended)

## Configuration

The system uses configuration files in `config/`:
- `agents.yaml` - Agent model configurations
- `hardware.yaml` - Hardware constraints
- `prompts/*.md` - Agent prompt templates
- `templates/*.md.j2` - Output templates

## Modes

- `research` - Generate research reports
- `project` - Create project specifications  
- `learn` - Build learning paths

## Options

- `--dry-run` - Validate configuration without execution
- `--interactive` - Interactive mode with clarifying questions
- `--verbose` - Debug logging
- `--no-rich` - Disable terminal UI formatting

See `README.md` for full documentation.
