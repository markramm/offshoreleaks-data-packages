"""Shared test fixtures and configuration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from offshore_leaks_mcp.config import Config, Neo4jConfig, ServerConfig
from offshore_leaks_mcp.database import Neo4jDatabase
from offshore_leaks_mcp.service import OffshoreLeaksService


@pytest.fixture
def mock_config():
    """Create a mock config for testing."""
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
def mock_database():
    """Create a mock database for testing."""
    database = MagicMock(spec=Neo4jDatabase)
    database.is_connected = True

    # Mock async methods
    async def async_connect():
        database.is_connected = True

    async def async_disconnect():
        database.is_connected = False

    database.connect = AsyncMock(side_effect=async_connect)
    database.disconnect = AsyncMock(side_effect=async_disconnect)

    return database


@pytest.fixture
def mock_service(mock_database):
    """Create a mock service for testing."""
    service = MagicMock(spec=OffshoreLeaksService)
    service.database = mock_database
    return service


@pytest.fixture
def mock_load_config(mock_config):
    """Mock the load_config function to return test config."""
    with patch('offshore_leaks_mcp.api.load_config', return_value=mock_config):
        yield mock_config


@pytest.fixture
def mock_neo4j_init(mock_database):
    """Mock Neo4jDatabase initialization to return mock database."""
    with patch('offshore_leaks_mcp.api.Neo4jDatabase', return_value=mock_database):
        yield mock_database


@pytest.fixture
def mock_service_init(mock_service):
    """Mock OffshoreLeaksService initialization to return mock service."""
    with patch('offshore_leaks_mcp.api.OffshoreLeaksService', return_value=mock_service):
        yield mock_service


@pytest.fixture
def no_resilience(monkeypatch):
    """Disable resilience mechanisms (retries, circuit breakers) for testing."""
    from offshore_leaks_mcp.resilience import RetryConfig, CircuitBreakerConfig

    # Patch retry config to disable retries
    monkeypatch.setattr('offshore_leaks_mcp.resilience.RetryConfig.__init__',
                       lambda self, **kwargs: object.__setattr__(self, '__dict__', {
                           'max_attempts': 1,
                           'base_delay': 0.0,
                           'max_delay': 0.0,
                           'exponential_base': 1.0,
                           'jitter': False,
                           'backoff_strategy': 'fixed'
                       }))

    # Patch circuit breaker config to be very tolerant
    monkeypatch.setattr('offshore_leaks_mcp.resilience.CircuitBreakerConfig.__init__',
                       lambda self, **kwargs: object.__setattr__(self, '__dict__', {
                           'failure_threshold': 999,
                           'recovery_timeout': 0.1,
                           'expected_exception': Exception
                       }))

    yield
