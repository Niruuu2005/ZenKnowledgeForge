# ZenKnowledgeForge User Guide

## Overview

ZenKnowledgeForge is a **local-first, deliberative multi-agent LLM system** that transforms vague ideas into structured, actionable knowledge artifacts. The system runs entirely on consumer hardware using sequential model execution.

## Hardware Requirements

### Minimum Requirements
- **GPU**: NVIDIA RTX 3050 (6GB VRAM) or equivalent
- **RAM**: 16GB DDR4
- **Storage**: ~40GB for models + workspace
- **OS**: Linux, Windows, or macOS with Docker support

### Important Constraints
- **Only ONE LLM model can be loaded at a time** (hardware limitation)
- Models are swapped sequentially during pipeline execution
- `OLLAMA_KEEP_ALIVE=0` is enforced globally to free VRAM immediately

## Installation

### Prerequisites

1. **Docker and Docker Compose**
   ```bash
   # Install Docker (example for Ubuntu)
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```

2. **NVIDIA Container Toolkit** (for GPU support)
   ```bash
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
       sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   ```

3. **Python 3.10+**
   ```bash
   python --version  # Should be 3.10 or higher
   ```

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/Niruuu2005/ZenKnowledgeForge.git
   cd ZenKnowledgeForge
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env if you need custom settings
   ```

5. **Start services**
   ```bash
   docker-compose up -d
   ```

6. **Pull models** (this will download ~35GB)
   ```bash
   bash scripts/pull_models.sh
   ```

7. **Verify installation**
   ```bash
   python -m zen --dry-run
   ```

## Usage

### Basic Command Structure

```bash
zen "your brief or question" [options]
```

### Execution Modes

ZenKnowledgeForge supports three execution modes:

#### 1. Research Mode (default)
Generates comprehensive research reports with citations and evidence.

```bash
zen "Explain blockchain consensus mechanisms" --mode research
```

**Output**: Academic-style research report with:
- Executive summary
- Detailed sections with citations
- Quality metrics (groundedness, coherence, completeness)
- Bibliography

#### 2. Project Mode
Creates detailed project specifications and implementation plans.

```bash
zen "Build a microservices e-commerce platform" --mode project
```

**Output**: Project specification with:
- Architecture overview
- Component definitions
- Implementation phases
- Risk assessment
- Technology recommendations

#### 3. Learn Mode
Generates personalized learning paths with progressive complexity.

```bash
zen "Learn machine learning from scratch" --mode learn
```

**Output**: Learning path with:
- Progressive modules
- Concept explanations with analogies
- Practice exercises
- Resources and next steps

### Interactive Mode

Use interactive mode to answer clarifying questions:

```bash
zen --interactive --mode research
```

The system will:
1. Ask for your brief
2. Analyze it with the Interpreter agent
3. Present clarifying questions
4. Refine the plan based on your answers
5. Execute the pipeline

### Command Line Options

```
usage: zen [-h] [-m {research,project,learn}] [-i] [-o OUTPUT]
           [--output-dir OUTPUT_DIR] [-v] [-q] [--config-dir CONFIG_DIR]
           [--session-id SESSION_ID] [--save-session] [--no-rich] [--dry-run]
           [brief]

Options:
  brief                     Your brief or question
  -m, --mode               Execution mode (research/project/learn)
  -i, --interactive        Interactive mode with clarifying questions
  -o, --output            Output file path
  --output-dir            Output directory (default: ./outputs)
  -v, --verbose           Verbose output (DEBUG logging)
  -q, --quiet             Quiet output (WARNING logging)
  --config-dir            Configuration directory
  --session-id            Resume a previous session
  --save-session          Save session for later resumption
  --no-rich               Disable Rich formatting
  --dry-run               Validate configuration and exit
```

### Examples

**Simple research query:**
```bash
zen "How does TCP/IP work?"
```

**Project with custom output:**
```bash
zen "Design a real-time chat application" \
    --mode project \
    --output ./my-project-spec.md
```

**Verbose interactive learning:**
```bash
zen --interactive --mode learn --verbose
```

**Save output to specific directory:**
```bash
zen "Analyze microservices vs monoliths" \
    --mode research \
    --output-dir ~/research-reports
```

## Pipeline Execution

### Agent Flow

The system uses a multi-agent deliberative process:

1. **Interpreter** (Llama 3.1 8B)
   - Parses your brief
   - Extracts intent
   - Generates clarifying questions

2. **Planner** (Mistral Nemo 12B)
   - Decomposes into Research Questions (RQs)
   - Creates execution phases
   - Estimates time and complexity

3. **Grounder** (Qwen 2.5 7B)
   - Retrieves evidence from sources
   - Cites references
   - Provides confidence scores

4. **Auditor** (Gemma 2 9B)
   - Assesses risks and dependencies
   - Checks security concerns
   - Evaluates feasibility

5. **Visualizer** (Phi-3.5 Mini) [Optional]
   - Creates chart specifications
   - Generates diagram layouts
   - Produces image prompts

6. **Judge** (Qwen 2.5 14B)
   - Synthesizes all inputs
   - Resolves conflicts
   - Scores consensus (groundedness, coherence, completeness)
   - Produces final artifact

### Model Swapping

Due to hardware constraints (6GB VRAM), models are loaded/unloaded sequentially:

```
[Load Interpreter] → Think → [Unload] → 
[Load Planner] → Think → [Unload] → 
[Load Grounder] → Think → [Unload] → 
...
```

This process is automatic and transparent. You'll see progress indicators in the CLI.

## Output Files

### Location
- Default: `./outputs/`
- Configurable via `--output-dir`
- Custom filename via `--output`

### Format
All outputs are generated as **Markdown** (.md) files with:
- Rich formatting (headers, lists, tables)
- Citations and references
- Metadata (agents used, consensus scores, timestamps)
- Structured sections

### Example Output Structure

```markdown
# Research Report Title

> Generated by ZenKnowledgeForge
> Consensus Score: 0.88

## Executive Summary
...

## Section 1: Introduction
...

## Section 2: Analysis
...

## References
[1] Source 1...
[2] Source 2...

## Quality Metrics
| Metric | Score |
|--------|-------|
| Groundedness | 0.92 |
| Coherence | 0.88 |
| Completeness | 0.85 |
```

## Configuration

### Environment Variables

Edit `.env` to customize:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_KEEP_ALIVE=0  # CRITICAL: Must be 0

# Neo4j (for knowledge graph - future feature)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=zenknowledge123

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/zenknowledgeforge.log

# Output
DEFAULT_OUTPUT_DIR=./outputs
DEFAULT_MODE=research
```

### Agent Configuration

Edit `config/agents.yaml` to:
- Change model versions
- Adjust temperatures
- Modify max questions/sources
- Set consensus thresholds

### Hardware Configuration

Edit `config/hardware.yaml` to:
- Specify VRAM limits
- Set timeout values
- Configure retry counts
- Adjust performance settings

## Troubleshooting

### "Model failed to load"
- Check Ollama is running: `docker ps | grep ollama`
- Verify models are downloaded: `docker exec -it zen_ollama ollama list`
- Check VRAM availability: `nvidia-smi`

### "Hardware incompatibility"
- Ensure `max_model_vram_mb` in `config/hardware.yaml` matches your GPU
- Reduce model sizes if needed (use smaller quantization)

### "Pipeline timeout"
- Increase `model_swap_timeout_seconds` in `config/hardware.yaml`
- Check network connectivity to Ollama
- Review logs in `./logs/`

### "JSON parsing failed"
- Some models may produce invalid JSON occasionally
- The system retries automatically (3 attempts)
- Check verbose logs with `-v` flag

## Performance Tips

1. **First Run**: Model loading takes longer initially (~2-5 minutes per model)
2. **Subsequent Runs**: Models are cached by Ollama, loading is faster
3. **Parallel Research**: The Grounder can use async workers (future feature)
4. **Hardware Monitoring**: Use `nvidia-smi -l 1` to watch VRAM usage

## Limitations

### Current Version (0.1.0)
- **No web search**: Grounder uses placeholder content (future feature)
- **No actual RAG**: ChromaDB and Neo4j integration pending
- **Limited visualization**: Chart/image generation not fully implemented
- **Sequential only**: No parallel agent execution (hardware constraint)

### By Design
- **One model at a time**: Required by 6GB VRAM limit
- **Local only**: No cloud API calls (privacy-first)
- **Manual model download**: ~35GB download required

## Next Steps

After installation:
1. Start with simple research queries to familiarize yourself
2. Try interactive mode to see clarifying questions
3. Experiment with different modes (research/project/learn)
4. Review generated outputs and provide feedback

## Support

- **Issues**: https://github.com/Niruuu2005/ZenKnowledgeForge/issues
- **Logs**: Check `./logs/` for detailed execution logs
- **Verbose Mode**: Run with `-v` for debugging

## License

MIT License - See LICENSE file for details
