# ZenKnowledgeForge - Module Specifications

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ZenKnowledgeForge v0.1.0                    │
│              Local-First Multi-Agent LLM System                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
              ┌─────▼─────┐          ┌─────▼─────┐
              │    CLI    │          │  Engine   │
              │  (Rich)   │          │ (Pipeline)│
              └─────┬─────┘          └─────┬─────┘
                    │                      │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Model Manager     │
                    │  (VRAM Guard)       │
                    │  threading.Lock     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
         ┌────▼────┐     ┌────▼────┐     ┌────▼────┐
         │ Agent 1 │     │ Agent 2 │ ... │ Agent 6 │
         │(Llama)  │     │(Mistral)│     │ (Qwen)  │
         └─────────┘     └─────────┘     └─────────┘
```

---

## MODULE 1: Core Orchestration (`src/orchestration/`)

### Purpose
The "operating system" of the council - manages lifecycle, configuration, and sequential execution.

### Components

#### 1.1 ConfigLoader (`config.py`)
**Responsibility**: Load and validate YAML configurations

**Key Classes**:
- `ConfigLoader`: Main configuration interface
- `AgentsYamlConfig`: Pydantic model for agents.yaml
- `HardwareYamlConfig`: Pydantic model for hardware.yaml
- `AgentConfig`, `PipelineConfig`, etc.: Nested configuration models

**Key Methods**:
```python
load_agents_config() -> AgentsYamlConfig
load_hardware_config() -> HardwareYamlConfig
validate_hardware_compatibility() -> bool
get_ollama_base_url() -> str
load_prompt_template(agent_name: str) -> str
```

**Design Decisions**:
- Uses Pydantic for validation (type safety + automatic validation)
- Lazy loading (configs loaded on first access)
- Environment variable support via python-dotenv
- Strict validation prevents runtime errors

---

#### 1.2 ModelManager (`model_manager.py`)
**Responsibility**: VRAM-safe model loading/unloading with strict locking

**Critical Constraints**:
- **ONLY ONE MODEL AT A TIME** (hardware limitation)
- Uses `threading.Lock` (not asyncio.Lock - Ollama is blocking)
- `OLLAMA_KEEP_ALIVE=0` enforced globally

**Key Methods**:
```python
load_model(model_name, vram_mb, agent_name) -> bool
unload_model(force=False) -> bool
generate(model_name, prompt, ...) -> str
is_model_loaded(model_name) -> bool
get_current_model() -> Optional[str]
```

**Lock Behavior**:
```python
with self._lock:
    # 1. Unload current model if any
    # 2. Wait for VRAM to free (sleep 2s)
    # 3. Load new model
    # 4. Update _current_model
```

**Retry Logic**:
- Max 3 retries with exponential backoff
- Timeout: 30 seconds per model load
- Graceful failure with RuntimeError

**Design Decisions**:
- `threading.Lock` for synchronization (httpx is blocking)
- Context manager support (`with ModelManager()`)
- Automatic cleanup on exit
- Detailed logging at each step

---

#### 1.3 SharedState (`state.py`)
**Responsibility**: Context object passed between pipeline steps

**Key Fields**:
```python
user_brief: str                    # Original input
execution_mode: ExecutionMode      # research/project/learn
clarifications: Dict               # From interactive mode
intent: Optional[Dict]             # From Interpreter
plan: Optional[Dict]               # From Planner
research_findings: List[Dict]      # From Grounder
audit_report: Optional[Dict]       # From Auditor
visualizations: Optional[Dict]     # From Visualizer
final_artifact: Optional[Dict]     # From Judge
consensus_score: Optional[float]   # Overall quality
deliberation_round: int            # Current round
agent_outputs: Dict[str, Any]      # Raw outputs
errors: List[Dict]                 # Error tracking
```

**Key Methods**:
```python
add_agent_output(agent_name, output)
add_error(agent_name, error)
should_continue_deliberation() -> bool
to_dict() -> Dict
from_dict(data) -> SharedState
```

**Design Decisions**:
- Pydantic model for validation
- Accumulates context (never loses information)
- Tracks deliberation rounds
- Serializable for session persistence (future)

---

#### 1.4 PipelineEngine (`engine.py`)
**Responsibility**: Main execution loop coordinating all agents

**Key Methods**:
```python
register_agent(agent_name, agent_instance)
get_pipeline_steps(mode) -> List[str]
execute_pipeline(user_brief, mode, ...) -> SharedState
_update_state_from_agent(state, agent_name, output)
```

**Execution Flow**:
```python
1. Initialize SharedState
2. Get pipeline steps for mode (e.g., research)
3. For each agent in sequence:
   a. Load agent
   b. Call agent.think(state, model_manager)
   c. Update SharedState with output
   d. Handle errors gracefully
4. Return final SharedState
```

**Error Handling**:
- Errors logged and added to state.errors
- Pipeline continues even if one agent fails
- Graceful degradation at final artifact level

**Design Decisions**:
- Sequential execution (hardware constraint)
- Agent registry for dynamic lookup
- Context manager support
- Separation of concerns (engine doesn't know agent internals)

---

#### 1.5 Logging Configuration (`logging_config.py`)
**Responsibility**: Setup logging with Rich formatting

**Features**:
- Console handler with Rich formatting
- Optional file handler
- Configurable log levels
- Traceback formatting with locals

**Usage**:
```python
setup_logging(level="INFO", log_file="./logs/zen.log")
logger = get_logger(__name__)
```

---

## MODULE 2: Agents (`src/agents/`)

### Architecture

```
BaseAgent (Abstract)
    │
    ├─ PromptEngine (Static utility)
    │
    ├─ InterpreterAgent (Llama 3.1 8B)
    ├─ PlannerAgent (Mistral Nemo 12B)
    ├─ GrounderAgent (Qwen 2.5 7B)
    ├─ AuditorAgent (Gemma 2 9B)
    ├─ VisualizerAgent (Phi-3.5 Mini)
    └─ JudgeAgent (Qwen 2.5 14B)
```

### Base Components

#### 2.1 BaseAgent (`base_agent.py`)
**Abstract class defining agent interface**

**Key Methods**:
```python
think(state, model_manager) -> Dict[str, Any]
_prepare_prompt(state) -> str  # Abstract
_parse_response(response, state) -> Optional[Dict]  # Abstract
_graceful_degradation(state) -> Dict  # Abstract
```

**Retry Logic**:
```python
for attempt in range(max_retries):
    response = model_manager.generate(...)
    parsed = _parse_response(response)
    if parsed is not None:
        return parsed
    # Add "return valid JSON" instruction to prompt
```

**Design Decisions**:
- Template method pattern
- Automatic retry with prompt refinement
- Mandatory graceful degradation
- Subclasses only implement domain logic

---

#### 2.2 PromptEngine (`base_agent.py`)
**Static utility for prompt manipulation**

**Key Methods**:
```python
inject_variables(template, variables) -> str
extract_json_from_response(response) -> Optional[Dict]
```

**JSON Extraction Strategy**:
1. Try markdown code blocks: ` ```json ... ``` `
2. Try plain JSON parse
3. Try finding `{...}` in text
4. Return None if all fail

**Design Decisions**:
- Handles common LLM output variations
- Robust to markdown wrapping
- No exceptions thrown (returns None)

---

### Agent Implementations

#### 2.3 InterpreterAgent
**Model**: Llama 3.1 8B (5GB VRAM)  
**Temperature**: 0.3 (factual)

**Input**:
```json
{
  "user_brief": "...",
  "context": "..."
}
```

**Output**:
```json
{
  "intent": {
    "primary_goal": "...",
    "domain": "...",
    "output_type": "research_report|project_spec|learning_path",
    "scope": "broad|moderate|narrow"
  },
  "extracted_requirements": [...],
  "ambiguities": [...],
  "clarifying_questions": [...],  // Max 5
  "confidence": 0.85
}
```

**Role**: Understand user intent and identify ambiguities

---

#### 2.4 PlannerAgent
**Model**: Mistral Nemo 12B (7.5GB VRAM - RAM spill)  
**Temperature**: 0.4 (creative)

**Input**: Intent + brief + clarifications

**Output**:
```json
{
  "research_questions": [
    {
      "id": "RQ1",
      "question": "...",
      "type": "factual|analytical|comparative|exploratory",
      "priority": "critical|high|medium|low",
      "estimated_time_minutes": 20,
      "dependencies": ["RQ0"]
    }
  ],
  "phases": [
    {
      "name": "...",
      "description": "...",
      "rq_ids": [...],
      "parallel": true|false
    }
  ],
  "success_criteria": [...],
  "estimated_total_time_minutes": 60
}
```

**Role**: Decompose into actionable research questions and phases

---

#### 2.5 GrounderAgent
**Model**: Qwen 2.5 7B (4.5GB VRAM)  
**Temperature**: 0.2 (precise)

**Input**: Research question + retrieved content

**Output**:
```json
{
  "answer": "...",
  "key_findings": [
    {
      "finding": "...",
      "evidence": [...],
      "confidence": 0.9
    }
  ],
  "contradictions": [...],
  "knowledge_gaps": [...],
  "overall_confidence": 0.85
}
```

**Role**: Ground claims in evidence, cite sources, assess confidence

**Current Limitation**: Uses placeholder content (no web search yet)

---

#### 2.6 AuditorAgent
**Model**: Gemma 2 9B (5.5GB VRAM)  
**Temperature**: 0.3 (balanced)

**Input**: Plan + findings + domain

**Output**:
```json
{
  "risk_assessment": {
    "overall_risk_level": "low|medium|high|critical",
    "risks": [...]
  },
  "dependencies": {
    "technical": [...],
    "knowledge": [...]
  },
  "security_concerns": [...],
  "feasibility_assessment": {
    "technical_feasibility": 0.85,
    "resource_feasibility": 0.70,
    "time_feasibility": 0.90,
    "overall_feasibility": 0.82,
    "blockers": [...]
  },
  "recommendations": [...]
}
```

**Role**: Identify risks, dependencies, security issues, feasibility

---

#### 2.7 VisualizerAgent
**Model**: Phi-3.5 Mini (2.5GB VRAM)  
**Temperature**: 0.5 (creative)

**Input**: Content + context

**Output**:
```json
{
  "visualizations": [
    {
      "id": "viz_1",
      "type": "chart|diagram|flowchart|architecture",
      "title": "...",
      "purpose": "...",
      "specification": {...}  // Detailed chart/diagram spec
    }
  ],
  "image_prompts": [...]
}
```

**Role**: Generate specifications for charts, diagrams, images

**Current Limitation**: Specs generated but not rendered (no chart_gen.py yet)

---

#### 2.8 JudgeAgent
**Model**: Qwen 2.5 14B (9GB VRAM - RAM spill)  
**Temperature**: 0.2 (precise)

**Input**: All agent outputs

**Output**:
```json
{
  "synthesis": {
    "executive_summary": "...",
    "key_insights": [...],
    "conflicts_resolved": [...]
  },
  "consensus_score": {
    "groundedness": 0.92,
    "coherence": 0.88,
    "completeness": 0.85,
    "overall": 0.88,
    "justification": "..."
  },
  "final_artifact": {
    "type": "research_report|project_spec|learning_path",
    "sections": [...],
    "metadata": {...}
  },
  "recommendations": [...],
  "decision": "accept|needs_revision",
  "revision_notes": "..."
}
```

**Role**: Synthesize all inputs, resolve conflicts, score consensus, produce final artifact

**Deliberation Control**:
- If `overall < 0.85` AND `rounds < 7`: Request revision
- Otherwise: Accept

---

## MODULE 5: User Experience (`src/cli/`)

### Components

#### 5.1 CLI Parser (`parser.py`)
**Responsibility**: Command-line argument handling

**Key Arguments**:
```bash
zen "brief" 
  --mode {research|project|learn}
  --interactive
  --output FILE
  --verbose / --quiet
  --config-dir DIR
  --session-id ID
  --no-rich
  --dry-run
```

**Validation**:
- Brief required unless --interactive or --dry-run
- Cannot be both --verbose and --quiet

---

#### 5.2 Progress UI (`progress.py`)
**Responsibility**: Rich terminal UI components

**Features**:
- Banner display
- Configuration summary table
- Agent thinking spinners
- Pipeline progress indicators
- Final artifact summary
- Error/warning panels

**Design Decisions**:
- Graceful fallback when --no-rich
- Minimal console output in quiet mode
- Color-coded status (green=done, yellow=current, dim=pending)

---

#### 5.3 Interactive Mode (`interactive.py`)
**Responsibility**: Interactive question/answer flow

**Flow**:
1. Get brief (if not provided)
2. Show clarifying questions from Interpreter
3. Collect answers
4. Show execution plan
5. Confirm to proceed

**Design Decisions**:
- Rich prompts with formatting
- Fallback to plain input without Rich
- Optional confirmation step

---

#### 5.4 Markdown Renderer (`renderers/markdown.py`)
**Responsibility**: Generate markdown artifacts from JSON

**Features**:
- Jinja2 template rendering
- Three templates (research, project, learn)
- Automatic metadata enhancement
- Fallback simple rendering

**Template Selection**:
```python
{
  "research": "research_report.md.j2",
  "project": "project_overview.md.j2",
  "learn": "learning_path.md.j2"
}
```

---

## Entry Point (`src/__main__.py`)

### Execution Flow

```python
1. Parse arguments
2. Setup logging (Rich or plain)
3. Load configuration
4. Validate hardware compatibility
5. Show banner and config summary
6. Get user brief (interactive or CLI)
7. Initialize PipelineEngine
8. Register all 6 agents
9. Execute pipeline
10. Render artifact to markdown
11. Save to file
12. Display summary
```

### Error Handling
- KeyboardInterrupt → Exit code 130
- Configuration errors → Exit code 1
- Execution errors → Logged, exit code 1

---

## Configuration Files

### agents.yaml
Defines each agent's model, VRAM, role, and hyperparameters.

### hardware.yaml
Defines VRAM limits, timeouts, performance settings.

### prompts/*.md
Detailed instruction templates for each agent with examples.

### templates/*.md.j2
Jinja2 templates for final artifact rendering.

---

## Design Patterns Used

1. **Template Method** (BaseAgent)
2. **Strategy Pattern** (Agent implementations)
3. **Context Manager** (ModelManager, PipelineEngine)
4. **Registry Pattern** (Agent registration)
5. **Pipeline Pattern** (Sequential agent execution)
6. **Builder Pattern** (SharedState accumulation)

---

## Key Technical Decisions

### Why threading.Lock instead of asyncio.Lock?
Ollama API calls via httpx are **blocking**, not async. Using threading.Lock is correct.

### Why Pydantic for configuration?
- Type safety
- Automatic validation
- Clear error messages
- IDE autocomplete

### Why sequential execution?
Hardware constraint: Only 6GB VRAM, models range from 5-9GB.

### Why graceful degradation?
Research quality > system crashes. Better to have partial results than none.

### Why Rich UI?
Developer experience matters. Beautiful terminals improve debugging.

---

## Future Enhancements (v0.2.0+)

### Memory Systems (v0.2.0)
- ChromaDB for semantic search
- Session persistence
- Context retrieval

### Tools (v0.3.0)
- Real web search (Playwright)
- Browser automation
- Actual RAG implementation

### Knowledge Graph (v0.4.0)
- Neo4j integration
- Cross-session learning
- Concept relationships

---

## Performance Characteristics

### Model Swap Time
- Cold start: 30-60 seconds
- Warm start: 10-20 seconds
- VRAM → RAM spill adds ~10s

### Pipeline Execution
- Research mode: ~8-12 minutes (6 agents)
- Project mode: ~6-10 minutes (5 agents)
- Learn mode: ~6-9 minutes (4 agents)

### Resource Usage
- Peak VRAM: ~5.5GB (Auditor)
- Peak RAM: ~12GB (Judge with RAM spill)
- Disk: ~35GB (models)

---

## Testing Strategy

### Unit Tests
- ConfigLoader: YAML validation
- ModelManager: Lock behavior, retries
- Agents: JSON parsing, graceful degradation
- PromptEngine: Variable injection

### Integration Tests (Planned)
- Full pipeline execution
- Error scenarios
- Resource monitoring

### Manual Tests
- Hardware compatibility
- Model swapping
- UI responsiveness

---

**End of Module Specifications**
