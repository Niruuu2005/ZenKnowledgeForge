# ZenKnowledgeForge - Quick Reference Guide

## 🚀 Getting Started (5 Minutes)

### 1. Start Services
```bash
cd d:\Dream\ZenKnowledgeForge\ZenKnowledgeForge
docker-compose up -d
```

### 2. Download Models (~35GB, one-time)
```bash
bash scripts/pull_models.sh
```

### 3. Run Your First Query
```bash
python -m src "Explain blockchain consensus mechanisms"
```

**Output**: Generated in `./outputs/` directory as markdown file

---

## 📝 Common Commands

### Research Mode (Comprehensive Reports)
```bash
python -m src "How do neural networks learn?" --mode research
```
**Pipeline**: Interpreter → Planner → Grounder → Auditor → Judge  
**Best for**: Deep dives, citations, evidence

### Project Mode (Technical Specs)
```bash
python -m src "Build a real-time chat API" --mode project
```
**Pipeline**: Interpreter → Planner → Auditor → Visualizer → Judge  
**Best for**: Architecture, phases, diagrams

### Learn Mode (Learning Paths)
```bash
python -m src "Learn Rust programming" --mode learn
```
**Pipeline**: Interpreter → Planner → Grounder → Judge  
**Best for**: Progressive learning, resources

### Interactive Mode (Get Clarifications)
```bash
python -m src --interactive --mode research
```
**Effect**: System asks follow-up questions before processing

### Verbose Logging
```bash
python -m src "Your query" -v
```
**Output**: DEBUG level logs to console and `logs/` directory

### Dry Run (Test Config Without Running)
```bash
python -m src "test" --dry-run
```
**Output**: Validates configuration and exits

---

## ⚙️ Configuration Files

### agents.yaml - Agent Definitions
**Location**: `config/agents.yaml`  
**Edit**: Model names, temperatures, max questions/sources

```yaml
interpreter:
  model: "llama3.1:8b-instruct-q4_K_M"
  temperature: 0.3          # Lower = more precise
  max_questions: 5          # Max clarifying questions
```

**Temperature Guide**:
- `0.2` = Highly factual, consistent
- `0.3-0.4` = Balanced
- `0.5+` = Creative, varied

### hardware.yaml - Resource Constraints
**Location**: `config/hardware.yaml`  
**Edit**: VRAM limits, timeouts, batch sizes

```yaml
gpu:
  vram_mb: 6144        # Total VRAM
  max_model_vram_mb: 5500  # Reserve 500MB for system
constraints:
  max_concurrent_models: 1  # Must be 1 (sequential only)
  model_swap_timeout_seconds: 30
  model_load_retries: 3
```

### Prompt Templates
**Location**: `config/prompts/`  
**Files**:
- `interpreter.md` - Intent extraction
- `planner.md` - Research decomposition
- `grounder.md` - Evidence gathering
- `auditor.md` - Risk assessment
- `visualizer.md` - Diagram specs
- `judge.md` - Synthesis & consensus

**Edit**: Customize prompting strategy for each agent

### Output Templates
**Location**: `config/templates/`  
**Files**:
- `research_report.md.j2` - Research output format
- `project_overview.md.j2` - Project spec format
- `learning_path.md.j2` - Learning curriculum format

**Variables**: `{{ brief }}`, `{{ agent_outputs }}`, `{{ consensus_score }}`

---

## 🔍 Monitoring & Debugging

### Check Ollama Status
```bash
curl http://localhost:11434/api/tags
```
**Output**: List of downloaded models with sizes

### Monitor GPU Usage
```bash
nvidia-smi --loop=1  # Updates every second
```
**Watch**: Memory usage, utilization percentage

### Check Logs
```bash
cat logs/zen_*.log
```
**Contains**: Full execution trace with timestamps

### Verify Configuration
```bash
python -m src "test" --dry-run -v
```
**Output**: Configuration table and validation results

---

## 📊 The Six Agents at a Glance

| Agent | Role | Model | Speed | VRAM |
|-------|------|-------|-------|------|
| **Interpreter** | Parse intent | Llama 8B | Fast | 5.0 GB |
| **Planner** | Create plan | Mistral 12B | Slow* | 7.5 GB |
| **Grounder** | Gather evidence | Qwen 7B | Fast | 4.5 GB |
| **Auditor** | Assess risks | Gemma 9B | Medium | 5.5 GB |
| **Visualizer** | Create specs | Phi-3.5 | Fast | 2.5 GB |
| **Judge** | Synthesize | Qwen 14B | Slow* | 9.0 GB |

*Spillage to system RAM

---

## 🎯 Use Cases by Mode

### Research Mode
**When to use**: Learning, academic work, deep investigation  
**Expect**: 
- Structured report with sections
- Citations and evidence quality scores
- Risk assessment summary
- ~2.5 minutes execution
- ~5-10 page output

### Project Mode
**When to use**: Building, engineering, architecture  
**Expect**:
- Technical specifications
- Architecture diagrams (as text specs)
- Implementation phases
- Risk & feasibility assessment
- ~2.5 minutes execution
- ~8-12 page output

### Learn Mode
**When to use**: Skill development, teaching, curriculum  
**Expect**:
- Progressive learning path
- Concept explanations
- Resources and exercises
- Knowledge gaps identified
- ~2 minutes execution (no Grounder)
- ~4-6 page output

---

## 🛠️ Troubleshooting Quick Tips

| Problem | Quick Fix |
|---------|-----------|
| "Connection refused" | `docker-compose up -d` |
| Out of memory | Close other GPU apps or lower `max_context_tokens` |
| Slow processing | Normal (2-3 min); models loading/unloading |
| No output files | Check `./outputs/` directory created |
| Model not found | Run `bash scripts/pull_models.sh` |
| Rich formatting issues | Add `--no-rich` flag |

---

## 📂 Output Structure

**Location**: `./outputs/`

```
outputs/
├── research_report_20260117_143022.md
├── project_spec_20260117_144015.md
└── learning_path_20260117_145030.md
```

**Filename Format**: `{mode}_{YYYYMMDD}_{HHMMSS}.md`

**Contents**:
- Title and metadata
- Agent-by-agent analysis
- Consensus score (0-1)
- Final artifact with sections
- Quality metrics table

---

## 🔒 Privacy & Security

✅ **All local** - No cloud APIs, no external calls  
✅ **Offline capable** - After models downloaded, no internet needed  
✅ **Private data** - All queries stay on your machine  
✅ **No telemetry** - No tracking or logging to external services  

---

## 💾 Advanced Usage

### Save Session for Later
```bash
python -m src "Your brief" --save-session
```
**Creates**: Session state file with ID

### Resume Saved Session
```bash
python -m src --session-id <SESSION_ID>
```
**Effect**: Skips already-completed agents, resumes from next

### Custom Output Directory
```bash
python -m src "Query" --output-dir my_outputs
```
**Creates**: `my_outputs/` instead of `outputs/`

### Custom Configuration
```bash
python -m src "Query" --config-dir custom_config
```
**Loads**: Custom agents.yaml and hardware.yaml

---

## 🚨 Performance Optimization

### For Slower Hardware
1. Lower `max_context_tokens` in hardware.yaml (default 4096 → 2048)
2. Reduce `max_questions` in agents.yaml
3. Increase `model_swap_timeout_seconds` (for slow disk I/O)

### For Faster Execution
1. Increase `max_context_tokens` (more VRAM available)
2. Lower agent temperatures slightly (less variance)
3. Ensure OLLAMA_KEEP_ALIVE=0 (immediate unload)

### For Better Quality
1. Increase temperatures slightly (more creative)
2. Increase `max_research_questions` in Planner
3. Increase `max_deliberation_rounds` for Judge (max 7)
4. Lower `consensus_threshold` for more iterations

---

## 📚 Documentation

- **README.md** - Project overview and features
- **SYSTEM_ANALYSIS.md** - Deep technical analysis
- **EXECUTION_REPORT.md** - Setup completion report
- **USER_GUIDE.md** - Detailed usage instructions
- **DEVELOPMENT_PLAN.md** - Roadmap and milestones
- **MODULE_SPECIFICATIONS.md** - Technical specifications
- **QUICK_REFERENCE.md** - This file

---

## 🎓 How It Works (Simplified)

```
User Brief
    ↓
Interpreter: "What does the user want?"
    ↓
Planner: "How should we approach this?"
    ↓
Grounder: "What evidence supports each part?"
    ↓
Auditor: "What could go wrong?"
    ↓
Visualizer: "How should we show this?"
    ↓
Judge: "Does everything make sense? Score: X/100"
    ↓
Output: Structured markdown artifact
```

Each agent loads its model, thinks, unloads (sequential).  
Final artifact combines all perspectives into one coherent output.

---

## 🎉 You're Ready!

The application is fully set up. Next steps:

1. **Start Docker**: `docker-compose up -d`
2. **Get models**: `bash scripts/pull_models.sh` (one-time, takes a while)
3. **Run**: `python -m src "Your question"`
4. **Read output**: Check `./outputs/` for markdown file
5. **Customize**: Edit `config/` files to tune behavior

Enjoy knowledge synthesis! 🧘

---

*Quick Reference for ZenKnowledgeForge v0.1.0*
