# ZenKnowledgeForge Development Plan

## Project Overview

**Goal**: Build a complete local-first deliberative multi-agent LLM system that transforms vague ideas into structured knowledge artifacts.

**Timeline**: 10-week development cycle (flexible based on contributor availability)

**Hardware Constraint**: NVIDIA RTX 3050 (6GB VRAM), requiring sequential model execution

## Development Phases

### Phase 1: Foundation (Weeks 1-2) ✓ COMPLETED

**Objective**: Establish core infrastructure and configuration

#### Week 1: Project Setup
- [x] Repository initialization
- [x] Project structure creation
- [x] Configuration files (agents.yaml, hardware.yaml)
- [x] Docker Compose setup (Ollama, Neo4j, ComfyUI)
- [x] Environment configuration (.env.example)
- [x] Model download script

#### Week 2: Core Orchestration
- [x] ConfigLoader with Pydantic validation
- [x] ModelManager with VRAM locking
- [x] SharedState context object
- [x] PipelineEngine for sequential execution
- [x] Logging configuration with Rich

**Deliverables**: ✓
- Working configuration system
- Model manager with one-at-a-time guarantee
- Pipeline execution framework

---

### Phase 2: Agent Intelligence (Weeks 3-4) ✓ COMPLETED

**Objective**: Implement all six agents with prompting strategies

#### Week 3: Base Agent & Thinkers
- [x] BaseAgent abstract class
- [x] PromptEngine for variable injection
- [x] JSON parsing with retry logic
- [x] Interpreter agent (Llama 3.1 8B)
- [x] Planner agent (Mistral Nemo 12B)
- [x] Grounder agent (Qwen 2.5 7B)

#### Week 4: Evaluators & Judge
- [x] Auditor agent (Gemma 2 9B)
- [x] Visualizer agent (Phi-3.5 Mini)
- [x] Judge agent (Qwen 2.5 14B)
- [x] Consensus scoring algorithm
- [x] Prompt templates for all agents

**Deliverables**: ✓
- Six working agents with chain-of-thought prompts
- Graceful degradation on errors
- Deliberation loop control

---

### Phase 3: User Experience (Week 5) ✓ COMPLETED

**Objective**: Build CLI and rendering system

#### Tasks
- [x] Argument parser with all flags
- [x] Interactive mode for clarifying questions
- [x] Rich UI components (spinners, progress bars)
- [x] Jinja2 template rendering
- [x] Markdown artifact generation
- [x] Entry point (__main__.py)

**Deliverables**: ✓
- Fully functional CLI
- Beautiful terminal UI
- Three output templates (research, project, learn)

---

### Phase 4: Memory Systems (Weeks 6-7) - PENDING

**Objective**: Add persistence and knowledge retention

#### Week 6: Vector Store & Sessions
- [ ] ChromaDB wrapper with persistent storage
- [ ] ONNX embedding generation (all-MiniLM-L6-v2)
- [ ] Session state serialization
- [ ] SQLite session store
- [ ] Batch embedding (size=32)

#### Week 7: Knowledge Graph
- [ ] Neo4j async driver wrapper
- [ ] Schema definition (Concepts, Artifacts, Sources)
- [ ] Cypher query builder
- [ ] Cross-session knowledge retention
- [ ] Graph visualization (optional)

**Deliverables**:
- Session recovery functionality
- Long-term knowledge graph
- Semantic search capabilities

---

### Phase 5: Tools & Integration (Weeks 8-9) - PENDING

**Objective**: Add external data gathering and generation

#### Week 8: Browser & Research
- [ ] Playwright async browser automation
- [ ] HTML to Markdown converter
- [ ] Anti-detection (user agent rotation)
- [ ] Async research worker pool
- [ ] Map-Reduce pattern for parallel scraping
- [ ] Error isolation and timeout handling

#### Week 9: Content Generation
- [ ] Chart generation (Matplotlib/Seaborn)
- [ ] Image generation via ComfyUI API
- [ ] BibTeX citation generator
- [ ] LaTeX export (optional)
- [ ] File writing utilities

**Deliverables**:
- Real web research capability
- Visual content generation
- Professional citation handling

---

### Phase 6: Testing & Polish (Week 10) - PENDING

**Objective**: Ensure reliability and completeness

#### Tasks
- [ ] Unit tests for ModelManager (lock behavior)
- [ ] Unit tests for agents (JSON parsing)
- [ ] Integration tests (full pipeline)
- [ ] VRAM/RAM usage monitoring tests
- [ ] Documentation completion
- [ ] Example outputs and demos
- [ ] Performance profiling

**Deliverables**:
- Test coverage >80% for core modules
- Comprehensive documentation
- Demo video/screenshots
- Performance benchmarks

---

## Module Dependencies

```
Phase 1 (Foundation)
  ↓
Phase 2 (Agents) ← depends on Phase 1
  ↓
Phase 3 (UX) ← depends on Phases 1 & 2
  ↓
Phase 4 (Memory) ← can start after Phase 1
  ↓
Phase 5 (Tools) ← can start after Phase 1
  ↓
Phase 6 (Testing) ← depends on all phases
```

## Current Status (v0.1.0)

### Completed ✓
- ✅ Project structure and configuration
- ✅ Core orchestration (config, model manager, state, engine)
- ✅ All six agents (Interpreter, Planner, Grounder, Auditor, Visualizer, Judge)
- ✅ CLI with Rich UI
- ✅ Markdown rendering with Jinja2 templates
- ✅ Main entry point
- ✅ Basic documentation

### In Progress 🔄
- None currently (Phase 3 complete)

### Pending 📋
- Memory systems (ChromaDB, Neo4j, sessions)
- Tools (browser, search, image generation)
- Comprehensive testing
- Advanced features (RAG, GraphRAG)

## Technical Debt & Known Issues

### Current Limitations
1. **No actual web research**: Grounder uses placeholder content
2. **No RAG**: Vector store not integrated
3. **No knowledge graph**: Neo4j not utilized
4. **Limited error recovery**: Some agents may fail on edge cases
5. **No session persistence**: Can't resume interrupted sessions

### Planned Improvements
1. Implement real browser scraping (Playwright)
2. Add ChromaDB for semantic search
3. Integrate Neo4j for cross-session knowledge
4. Improve prompt engineering based on testing
5. Add session checkpointing

## Testing Strategy

### Unit Tests
- **ConfigLoader**: YAML parsing, validation
- **ModelManager**: Lock behavior, VRAM constraints, retries
- **Agents**: JSON parsing, graceful degradation
- **PromptEngine**: Variable injection, JSON extraction

### Integration Tests
- **Full pipeline**: End-to-end execution for each mode
- **Error scenarios**: Agent failures, timeouts, invalid inputs
- **Resource usage**: VRAM/RAM monitoring during execution

### Performance Tests
- Model swap timing (target: <30s per swap)
- Pipeline execution time (target: <10min for research mode)
- Memory consumption (target: stay within 6GB VRAM + 12GB RAM)

## Release Milestones

### v0.1.0 (Current) - MVP
- Core orchestration working
- All agents implemented
- Basic CLI functional
- Simple outputs generated

### v0.2.0 (Target: +2 weeks)
- Memory systems integrated
- Session persistence
- ChromaDB vector store

### v0.3.0 (Target: +4 weeks)
- Real web research
- Browser automation
- Improved grounding

### v0.4.0 (Target: +6 weeks)
- Neo4j knowledge graph
- Cross-session learning
- Visual content generation

### v1.0.0 (Target: +10 weeks)
- Production-ready
- Comprehensive tests
- Full documentation
- Example library

## Contribution Guidelines

### For New Contributors
1. Start with Phase 4 or Phase 5 tasks (memory or tools)
2. Each task should be in a separate PR
3. Include tests with new features
4. Update documentation

### Code Standards
- **Type hints**: Use typing annotations
- **Docstrings**: Google style for all public methods
- **Logging**: Use logger, not print()
- **Error handling**: Graceful degradation, not crashes
- **Testing**: Unit tests for new functionality

### Review Process
1. Self-review checklist:
   - Tests pass
   - Linting clean (ruff, black, mypy)
   - Documentation updated
   - No secrets committed
2. Peer review by maintainer
3. Manual testing on target hardware (RTX 3050)

## Resources

### Documentation
- [USER_GUIDE.md](USER_GUIDE.md) - Installation and usage
- [MODULE_SPECIFICATIONS.md](MODULE_SPECIFICATIONS.md) - Detailed module specs
- [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) - This file

### External References
- Ollama API: https://github.com/ollama/ollama/blob/main/docs/api.md
- ChromaDB: https://docs.trychroma.com/
- Neo4j Python Driver: https://neo4j.com/docs/python-manual/current/
- Playwright: https://playwright.dev/python/

## Questions & Discussions

For questions about the development plan:
- Open a GitHub Discussion
- Tag with `development-plan` label
- Reference specific phase/task

## License

MIT License - Open source, contributions welcome
