# Running ZenKnowledgeForge - Complete Guide

**Status as of January 17, 2026**: Application is fully installed and configured, but requires Docker services and LLM models to run the full pipeline.

---

## 🚀 Prerequisites Check

### ✅ What's Already Ready
- Python 3.13.1 environment
- All 47+ dependencies installed
- Package installed in editable mode
- CLI interface functional
- Configuration files validated

### ⏳ What's Needed to Run Full Pipeline

To actually execute the multi-agent knowledge synthesis pipeline, you need:

1. **Docker & Docker Compose** - For Ollama, Neo4j services
2. **LLM Models** - 6 quantized models (~35GB total)
3. **NVIDIA GPU** - With CUDA drivers and 6GB+ VRAM

---

## 🔧 Step 1: Start Docker Services

### Check Docker Installation
```powershell
docker --version
docker-compose --version
```

If Docker is not installed:
- **Windows**: Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
- **Install** and restart your system
- Ensure WSL2 backend is enabled

### Start Services
```powershell
cd d:\Dream\ZenKnowledgeForge\ZenKnowledgeForge
docker-compose up -d
```

**Expected output**:
```
[+] Running 3/3
 ✔ Container zen_ollama started
 ✔ Container zen_neo4j started
 ✔ Container zen_comfyui started
```

### Verify Services Running
```powershell
docker ps
# Should show: zen_ollama, zen_neo4j, zen_comfyui

curl http://localhost:11434/api/tags
# Should return: {"models":[...]}
```

---

## 📥 Step 2: Download LLM Models

The system requires 6 quantized language models (~35GB total). These are downloaded to Ollama's storage.

### Automatic Download (Recommended)
```powershell
bash scripts/pull_models.sh
```

This script downloads:
1. `llama3.1:8b-instruct-q4_K_M` (~5.0 GB)
2. `mistral-nemo:12b-instruct-q4_K_M` (~7.5 GB)
3. `qwen2.5:7b-instruct-q4_K_M` (~4.5 GB)
4. `gemma2:9b-instruct-q4_K_M` (~5.5 GB)
5. `phi3.5:3.8b-mini-instruct-q4_K_M` (~2.5 GB)
6. `qwen2.5:14b-instruct-q4_K_M` (~9.0 GB)

**Total**: ~34 GB (takes 30-60 minutes on fast connection)

### Manual Download (If Script Fails)
```powershell
# Pull each model individually
ollama pull llama3.1:8b-instruct-q4_K_M
ollama pull mistral-nemo:12b-instruct-q4_K_M
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull gemma2:9b-instruct-q4_K_M
ollama pull phi3.5:3.8b-mini-instruct-q4_K_M
ollama pull qwen2.5:14b-instruct-q4_K_M
```

### Verify Models Loaded
```powershell
curl http://localhost:11434/api/tags
```

Should show all 6 models in the output.

---

## 🎯 Step 3: Run the Application

### Run Your First Query (Research Mode)
```powershell
cd d:\Dream\ZenKnowledgeForge\ZenKnowledgeForge
python -m src "Explain how neural networks learn"
```

**What happens**:
1. Interpreter loads and analyzes the question
2. Planner creates a research strategy
3. Grounder gathers evidence
4. Auditor assesses feasibility
5. Visualizer creates diagram specs
6. Judge synthesizes everything
7. Output saved to `./outputs/`

**Expected time**: 2-3 minutes

**Output location**: `./outputs/research_report_*.md`

---

## 📝 Usage Examples

### Example 1: Research Report (Detailed)
```powershell
python -m src "How do blockchain consensus mechanisms work?" --mode research -v
```
- Verbose logging
- ~2.5 minutes
- 5-10 page report with citations
- Quality metrics included

### Example 2: Project Specification
```powershell
python -m src "Design a real-time chat application with WebSockets" --mode project
```
- ~2.5 minutes
- Architecture diagrams (as text specs)
- Implementation phases
- Risk assessment

### Example 3: Learning Path
```powershell
python -m src "Learn Rust programming from scratch" --mode learn
```
- ~2 minutes (skips Grounder)
- Progressive curriculum
- Concepts → Examples → Exercises
- Knowledge gap identification

### Example 4: Interactive Mode (Get Clarifications)
```powershell
python -m src --interactive --mode research
```
- System asks follow-up questions
- Refines understanding before processing
- More targeted results

### Example 5: Verbose Output
```powershell
python -m src "Your topic here" -v
```
- DEBUG level logging
- Real-time progress
- Agent-by-agent execution tracking
- Saved to `./logs/zen_*.log`

---

## 📊 Monitoring Execution

### Watch GPU Usage
```powershell
# Real-time GPU monitoring
nvidia-smi --loop=1

# Or one-time check
nvidia-smi
```

**Expected pattern**:
- Model loads → VRAM spikes to 5-9 GB
- Agent thinks → GPU utilization increases
- Model unloads → VRAM drops back to ~1 GB
- Next model loads → Cycle repeats

### Monitor Memory
```powershell
# Check system RAM usage
Get-WmiObject Win32_OperatingSystem | Select-Object @{
  Expression={$_.TotalVisibleMemorySize}; Label="Total RAM (KB)"
}, @{
  Expression={$_.FreePhysicalMemory}; Label="Free RAM (KB)"
}
```

**Expected**: Peak usage ~13 GB during Judge phase (with spillage)

### Check Logs
```powershell
# Tail last 30 lines of latest log
Get-Content (Get-ChildItem logs/zen_*.log | Sort-Object LastWriteTime -Desc | Select-Object -First 1) -Tail 30
```

---

## 🎯 Output Structure

### Generated Files
```
outputs/
├── research_report_20260117_143022.md
├── project_spec_20260117_144015.md
└── learning_path_20260117_145030.md

logs/
├── zen_20260117_140500.log
├── zen_20260117_141200.log
└── zen_20260117_142100.log
```

### Report Contents
```markdown
# Research Report: [Your Topic]

> Generated by ZenKnowledgeForge
> Consensus Score: 0.87

## Executive Summary
[Synthesized overview]

## Key Findings
[From Grounder - evidence-based]

## Analysis
[From Auditor - risk assessment]

## Visualizations
[From Visualizer - diagram specs]

## Quality Metrics
| Metric | Score |
|--------|-------|
| Groundedness | 0.92 |
| Coherence | 0.88 |
| Completeness | 0.85 |

## References
[Citations with sources]
```

---

## ⚠️ Troubleshooting

### Problem: "Connection refused" (Ollama)
**Cause**: Docker services not running
**Fix**:
```powershell
docker-compose up -d
docker ps  # Verify running
```

### Problem: "Model not found" Error
**Cause**: Models not downloaded
**Fix**:
```powershell
bash scripts/pull_models.sh
# or pull individually:
ollama pull llama3.1:8b-instruct-q4_K_M
```

### Problem: "Out of memory" Error
**Cause**: GPU doesn't have enough VRAM
**Solutions**:
- Close other GPU-intensive applications
- Reduce max_context_tokens in `config/hardware.yaml` (default 4096 → 2048)
- Upgrade GPU (system requires RTX 3050 or better)

### Problem: Slow Inference (Takes >5 minutes)
**Cause**: Models spilling to system RAM
**Note**: This is normal for Planner (12B) and Judge (14B) models
**Expect**: ~2-3 minutes per query (140s average)

### Problem: "No module named zen"
**Cause**: Package not installed properly
**Fix**:
```powershell
pip install -e .
```

### Problem: Docker Command Not Found
**Cause**: Docker not in PATH or not installed
**Fix**:
- Install Docker Desktop for Windows
- Restart PowerShell
- Run: `docker --version`

---

## 🔍 Advanced Options

### Save Session (Resume Later)
```powershell
python -m src "Your query" --save-session
# Returns: Session ID: abc123def456

# Resume later:
python -m src --session-id abc123def456
```

### Custom Output Directory
```powershell
python -m src "Your query" --output-dir my_outputs
```

### Disable Rich Formatting
```powershell
python -m src "Your query" --no-rich
```

### Dry Run (Validate Without Executing)
```powershell
python -m src "test" --dry-run -v
```

---

## 📋 Full Setup Checklist

- [ ] Docker Desktop installed
- [ ] Docker running: `docker ps` works
- [ ] `docker-compose` available
- [ ] Models downloaded: `ollama pull ...` (all 6)
- [ ] Verify models: `curl http://localhost:11434/api/tags`
- [ ] NVIDIA driver installed
- [ ] CUDA available: `nvidia-smi` works
- [ ] Python venv active
- [ ] Package installed: `python -m src --help` works
- [ ] Ready to run: `python -m src "test query"`

---

## 📈 Expected Performance

| Stage | Agent | Time | Notes |
|-------|-------|------|-------|
| Load & Parse | Interpreter | ~20s | Model load + think + unload |
| Planning | Planner | ~45s | Larger model + RAM spillage |
| Evidence | Grounder | ~30s | Medium model |
| Assessment | Auditor | ~30s | Medium model |
| Diagrams | Visualizer | ~15s | Small, fast model |
| Synthesis | Judge | ~50s | Largest model + RAM spillage |
| **Total** | - | **~190s** | ~3.2 minutes average |

---

## 🎓 Understanding the Pipeline

**Sequential Execution** (One model at a time):
1. Model A loads (5 sec)
2. Thinks (20-40 sec)
3. Unloads (2 sec)
4. Model B loads (5 sec)
5. Thinks (20-40 sec)
6. Unloads (2 sec)
... and so on

**Why Sequential?**
- GPU has only 6GB VRAM
- Largest model (14B) needs 9GB
- Sequential execution is the only way to fit all agents

**Benefit**: Clear audit trail, easy debugging, stable execution

---

## 📞 Getting Help

### Check Documentation
- See **QUICK_REFERENCE.md** for common commands
- See **SYSTEM_ANALYSIS.md** for deep technical details
- See **EXECUTION_REPORT.md** for setup verification

### Debug Logging
```powershell
# Enable debug logging
python -m src "Your query" -v

# Saves to logs/zen_*.log with timestamps
cat logs/zen_*.log | tail -50
```

### Monitor Execution
```powershell
# In another PowerShell window:
nvidia-smi --loop=1

# Watch real-time VRAM usage and GPU utilization
```

---

## ✅ Summary

**To run the application:**

1. **Start services**:
   ```powershell
   docker-compose up -d
   ```

2. **Download models**:
   ```powershell
   bash scripts/pull_models.sh
   ```

3. **Run a query**:
   ```powershell
   python -m src "Your topic here"
   ```

4. **Check output**:
   - Artifacts: `./outputs/`
   - Logs: `./logs/`

**Time required:**
- Setup: 30-60 minutes (one-time, mostly download time)
- Per query: 2-3 minutes

**System requirements:**
- NVIDIA GPU (6GB+ VRAM)
- 16GB+ RAM
- ~37GB disk space
- Docker Desktop

Once set up, you can run unlimited knowledge synthesis queries!

---

*Running ZenKnowledgeForge - Execution Guide*  
*Version 0.1.0 - MVP*
