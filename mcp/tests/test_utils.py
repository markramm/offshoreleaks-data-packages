"""Test utilities for the offshore leaks MCP server."""

import asyncio
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from offshore_leaks_mcp.config import Config, Neo4jConfig, ServerConfig
from offshore_leaks_mcp.database import Neo4jDatabase


class TestResilienceManager:
    """Test version of resilience manager that disables circuit breakers."""

    def __init__(self):
        self.disabled = True
        # Initialize empty error tracking to match interface
        from offshore_leaks_mcp.resilience import ErrorType

        self.error_counts = dict.fromkeys(ErrorType, 0)
        self.last_errors = {}
        self.circuit_breakers = {}  # No circuit breakers in test mode

    async def execute_with_resilience(
        self, func, error_type=None, circuit_breaker_name=None, *args, **kwargs
    ):
        """Execute function without resilience patterns during testing."""
        return await func(*args, **kwargs)

    def record_error(self, error, error_type=None):
        """No-op for testing."""
        pass

    def get_error_stats(self):
        """Return empty stats for testing."""
        return {
            "error_counts": {et.value: 0 for et in self.error_counts.keys()},
            "circuit_breaker_states": {},
            "last_errors": {},
        }


@pytest.fixture
def test_config() -> Config:
    """Create a test configuration."""
    neo4j_config = Neo4jConfig(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="test_password",
        database="test_db",
    )
    server_config = ServerConfig(
        name="test-server",
        version="0.1.0",
        debug=True,
    )
    return Config(neo4j=neo4j_config, server=server_config)


@pytest.fixture
def mock_neo4j_driver():
    """Create a mock Neo4j driver for testing."""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_record = MagicMock()

    # Configure the mock chain for health check
    health_check_record = {"health_check": 1}
    mock_record.__getitem__.side_effect = lambda key: health_check_record.get(key, 1)
    mock_record.__contains__.side_effect = lambda key: key in health_check_record
    mock_result.single.return_value = health_check_record
    mock_result.data.return_value = [{"test": "data"}]
    mock_session.__enter__.return_value.run.return_value = mock_result
    mock_session.__aenter__.return_value.run.return_value = mock_result
    mock_driver.session.return_value = mock_session

    return mock_driver


@pytest.fixture
def mock_database(test_config: Config, mock_neo4j_driver):
    """Create a mock database instance for testing."""
    db = Neo4jDatabase(test_config.neo4j)
    db._driver = mock_neo4j_driver
    db._connected = True
    return db


@asynccontextmanager
async def disable_resilience():
    """Context manager to completely replace resilience manager during testing."""
    import offshore_leaks_mcp.database
    import offshore_leaks_mcp.resilience
    import offshore_leaks_mcp.server

    # Store original resilience manager
    original_manager = offshore_leaks_mcp.resilience.resilience_manager

    # Create and install test manager
    test_manager = TestResilienceManager()
    offshore_leaks_mcp.resilience.resilience_manager = test_manager
    offshore_leaks_mcp.database.resilience_manager = test_manager
    offshore_leaks_mcp.server.resilience_manager = test_manager

    try:
        yield test_manager
    finally:
        # Restore original manager
        offshore_leaks_mcp.resilience.resilience_manager = original_manager
        offshore_leaks_mcp.database.resilience_manager = original_manager
        offshore_leaks_mcp.server.resilience_manager = original_manager


@pytest.fixture
def reset_resilience():
    """Fixture to create fresh resilience manager for each test."""
    import offshore_leaks_mcp.database
    import offshore_leaks_mcp.resilience
    import offshore_leaks_mcp.server
    from offshore_leaks_mcp.resilience import ResilienceManager

    # Store original resilience manager
    original_manager = offshore_leaks_mcp.resilience.resilience_manager

    # Create a fresh resilience manager for this test
    fresh_manager = ResilienceManager()

    # Install fresh manager in all modules
    offshore_leaks_mcp.resilience.resilience_manager = fresh_manager
    offshore_leaks_mcp.database.resilience_manager = fresh_manager
    offshore_leaks_mcp.server.resilience_manager = fresh_manager

    yield fresh_manager

    # Restore original manager after test
    offshore_leaks_mcp.resilience.resilience_manager = original_manager
    offshore_leaks_mcp.database.resilience_manager = original_manager
    offshore_leaks_mcp.server.resilience_manager = original_manager


@pytest.fixture
async def disabled_resilience():
    """Fixture to completely disable resilience patterns for tests."""
    async with disable_resilience() as manager:
        yield manager


@pytest.fixture
def no_resilience():
    """Fixture to replace resilience manager with test version (synchronous)."""
    import offshore_leaks_mcp.database
    import offshore_leaks_mcp.resilience
    import offshore_leaks_mcp.server

    # Store original resilience manager
    original_manager = offshore_leaks_mcp.resilience.resilience_manager

    # Create and install test manager that bypasses all resilience
    test_manager = TestResilienceManager()
    offshore_leaks_mcp.resilience.resilience_manager = test_manager
    offshore_leaks_mcp.database.resilience_manager = test_manager
    offshore_leaks_mcp.server.resilience_manager = test_manager

    yield test_manager

    # Restore original manager
    offshore_leaks_mcp.resilience.resilience_manager = original_manager
    offshore_leaks_mcp.database.resilience_manager = original_manager
    offshore_leaks_mcp.server.resilience_manager = original_manager


class MockNeo4jResult:
    """Mock Neo4j query result."""

    def __init__(self, records: list[dict[str, Any]]):
        self.records = records
        self._index = 0

    def __iter__(self):
        return iter(self.records)

    def __next__(self):
        if self._index >= len(self.records):
            raise StopIteration
        record = self.records[self._index]
        self._index += 1
        return record

    def single(self):
        """Return single record."""
        if len(self.records) != 1:
            raise ValueError("Expected exactly one record")
        return self.records[0]

    def data(self):
        """Return all records as list."""
        return self.records


def setup_neo4j_mock(
    mock_driver_class, query_result_data=None, health_check_success=True
):
    """Setup a complete Neo4j mock with proper health check and query handling."""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_result = MagicMock()

    # Setup health check mock (needed for connection)
    if health_check_success:
        health_check_record = {"health_check": 1}
        mock_result.single.return_value = health_check_record
    else:
        mock_result.single.side_effect = Exception("Health check failed")

    # Setup query result data if provided
    if query_result_data is not None:
        mock_result.data.return_value = query_result_data
        # Also setup the records iteration behavior
        mock_records = []
        for record_data in query_result_data:
            mock_record = MagicMock()
            mock_record.data.return_value = record_data
            mock_records.append(mock_record)
        mock_result.__iter__.return_value = iter(mock_records)

    # Setup mock summary
    mock_summary = MagicMock()
    mock_summary.query_type = "r"
    mock_summary.counters = {}
    mock_summary.result_available_after = 1
    mock_summary.result_consumed_after = 2
    mock_result.summary.return_value = mock_summary

    # Wire up the mock chain
    mock_session.__enter__.return_value.run.return_value = mock_result
    mock_driver.session.return_value = mock_session
    mock_driver_class.return_value = mock_driver

    return mock_driver, mock_session, mock_result


class IntegrationTestHelper:
    """Helper class for integration tests."""

    @staticmethod
    def create_test_entity_data() -> dict[str, Any]:
        """Create test entity data."""
        return {
            "node_id": "test_entity_001",
            "name": "Test Offshore Company",
            "jurisdiction": "BVI",
            "jurisdiction_description": "British Virgin Islands",
            "sourceID": "Paradise Papers",
            "valid_until": "2023-12-31",
            "status": "Active",
            "incorporation_date": "2015-06-01",
        }

    @staticmethod
    def create_test_officer_data() -> dict[str, Any]:
        """Create test officer data."""
        return {
            "node_id": "test_officer_001",
            "name": "John Test Officer",
            "countries": "United States",
            "country_codes": "USA",
            "sourceID": "Paradise Papers",
            "valid_until": "2023-12-31",
        }

    @staticmethod
    def create_test_relationship_data() -> dict[str, Any]:
        """Create test relationship data."""
        return {
            "relationship_type": "OFFICER_OF",
            "start_date": "2015-06-01",
            "end_date": None,
            "link": "test_link_001",
        }


# Async test decorators and utilities
def async_test(coro):
    """Decorator for async tests."""

    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))

    return wrapper


def with_mock_database(test_func):
    """Decorator to provide a mock database to test functions."""

    async def wrapper(*args, **kwargs):
        with patch("offshore_leaks_mcp.database.GraphDatabase.driver") as mock_driver:
            # Set up mock driver behavior
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data.return_value = []
            mock_session.run.return_value = mock_result
            mock_driver.return_value.session.return_value.__aenter__.return_value = (
                mock_session
            )

            return await test_func(*args, **kwargs)

    return wrapper
