# Testing Guide

This directory contains comprehensive tests for the Offshore Leaks MCP Server.

## Test Structure

### Unit Tests
- `test_basic.py` - Basic package functionality and imports
- `test_queries.py` - Query builder and Cypher query generation
- `test_database.py` - Database connection and query execution (with resilience)
- `test_database_simple.py` - Simplified database tests (bypassing resilience)
- `test_server.py` - Server functionality and health checks

### Integration Tests
- `test_integration.py` - End-to-end workflows and integration scenarios

### Test Utilities
- `test_utils.py` - Fixtures, mocks, and test helpers

## Running Tests

### All Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

### Specific Test Categories
```bash
# Unit tests only
pytest -m "not integration"

# Integration tests only
pytest -m integration

# Slow tests (performance related)
pytest -m slow

# Specific test file
pytest tests/test_queries.py -v
```

### Test Configuration
The test configuration is defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
pythonpath = ["src"]
asyncio_mode = "auto"

[tool.pytest_asyncio]
asyncio_mode = "auto"
```

## Test Markers

- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.integration` - Integration tests requiring external dependencies
- `@pytest.mark.unit` - Unit tests (isolated functionality)
- `@pytest.mark.slow` - Performance tests that take longer to run

## Mocking Strategy

### Database Mocking
Tests use comprehensive mocking for Neo4j operations:

```python
from tests.test_utils import mock_database, reset_resilience

@pytest.mark.asyncio
async def test_database_operation(mock_database, reset_resilience):
    # Test database operations without real Neo4j connection
    result = await mock_database.execute_query("MATCH (n) RETURN n")
    assert result.records is not None
```

### Resilience Pattern Testing
The codebase includes sophisticated resilience patterns (circuit breakers, retries) that can interfere with tests. Use the `reset_resilience` fixture to reset state between tests:

```python
@pytest.mark.asyncio
async def test_with_resilience(database, reset_resilience):
    # Circuit breakers and error counters are reset
    await database.connect()
```

## Test Utilities

### `test_utils.py` Features
- **Mock Database**: Pre-configured Neo4j database mocks
- **Test Configuration**: Sample configurations for testing
- **Resilience Reset**: Fixtures to reset circuit breaker state
- **Integration Helpers**: Utilities for complex test scenarios
- **Mock Results**: Neo4j result mocking utilities

### Example Usage
```python
from tests.test_utils import (
    test_config,
    mock_database,
    reset_resilience,
    IntegrationTestHelper
)

@pytest.mark.asyncio
async def test_entity_search(test_config, mock_database, reset_resilience):
    server = OffshoreLeaksServer(test_config)
    server.database = mock_database

    result = await server.search_entities(name="Test Company")
    assert result.total_count >= 0
```

## Integration Test Strategy

Integration tests are designed to test complete workflows:

1. **Database Integration**: Connection lifecycle, query execution
2. **Server Integration**: Startup, health checks, API operations
3. **End-to-End Workflows**: Complete investigation scenarios
4. **Performance Testing**: Concurrent operations, large datasets

### Mock Data Strategy
Integration tests use realistic mock data:

```python
# Create test entity data
entity_data = IntegrationTestHelper.create_test_entity_data()
# Returns: {"node_id": "test_001", "name": "Test Company", ...}

# Create test relationship data
relationship_data = IntegrationTestHelper.create_test_relationship_data()
```

## Known Issues and Workarounds

### Circuit Breaker Interference
The resilience system's circuit breakers can remain open between tests, causing failures. Solutions:

1. **Use `reset_resilience` fixture** - Resets circuit breaker state
2. **Run tests in isolation** - Use pytest's `--forked` option if available
3. **Mock resilience decorators** - For tests that don't need resilience testing

### Async Test Configuration
Ensure async tests are properly configured:
- Use `@pytest.mark.asyncio` decorator
- Configure `asyncio_mode = "auto"` in pytest configuration
- Install `pytest-asyncio` package

## Test Data Management

### Environment Variables for Testing
```bash
# Required for integration tests with real database
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=test_password
export NEO4J_DATABASE=test_db
```

### Test Database Setup
For full integration testing:

1. Start Neo4j test instance (Docker recommended)
2. Load test data or use empty database
3. Run integration tests with proper environment variables
4. Clean up test data after tests

## Continuous Integration

The project includes GitHub Actions workflow (`.github/workflows/`):
- Multi-Python version testing (3.9, 3.10, 3.11, 3.12)
- Automated dependency installation
- Test execution with coverage reporting
- Security scanning integration

## Contributing to Tests

### Adding New Tests
1. Follow the existing naming convention (`test_*.py`)
2. Use appropriate test markers (`@pytest.mark.unit`, `@pytest.mark.integration`)
3. Include docstrings explaining test purpose
4. Use the test utilities and fixtures for consistency

### Test Development Best Practices
1. **Isolation**: Tests should not depend on each other
2. **Clarity**: Test names should clearly indicate what they test
3. **Coverage**: Aim for comprehensive coverage of both success and failure scenarios
4. **Performance**: Mark slow tests appropriately
5. **Documentation**: Include clear docstrings and comments

### Mock vs Real Dependencies
- **Unit Tests**: Always use mocks for external dependencies
- **Integration Tests**: Use real dependencies when testing integration points
- **Performance Tests**: Use mocks unless testing actual performance characteristics
