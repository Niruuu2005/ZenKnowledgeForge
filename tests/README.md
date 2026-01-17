# ZenKnowledgeForge Tests

## Running Tests

### Integration Tests

Integration tests verify that all components work together:

```bash
# Run the basic functionality test
python tests/integration/test_basic_functionality.py
```

This test suite verifies:
- All modules can be imported
- Configuration files are valid
- Agents can be initialized
- State management works correctly
- Prompt engine functions properly
- CLI parser works as expected

### Unit Tests

Unit tests require pytest:

```bash
# Install pytest first
pip install pytest pytest-asyncio

# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_config.py -v
pytest tests/unit/test_agents.py -v
pytest tests/unit/test_model_manager.py -v
```

## Test Coverage

Current test coverage:

- **Unit Tests**: Core components (config, model manager, agents)
- **Integration Tests**: Basic functionality, imports, initialization
- **Manual Tests**: See RUNNING.md for manual testing procedures

## Adding New Tests

When adding new features:

1. Add unit tests to `tests/unit/test_<module>.py`
2. Update integration tests if needed
3. Follow existing test patterns
4. Ensure all tests pass before committing

## Known Limitations

- Most tests don't require Ollama to be running
- Tests that require actual LLM inference are marked as integration tests
- Some features (memory systems, tools) are not yet implemented per v0.1.0 scope
