"""Tests for the offshore leaks MCP server."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from offshore_leaks_mcp import Config, OffshoreLeaksServer, load_config
from offshore_leaks_mcp.config import Neo4jConfig, ServerConfig
from offshore_leaks_mcp.database import ConnectionError, QueryError
from offshore_leaks_mcp.models import HealthStatus, SearchResult


@pytest.fixture
def mock_config() -> Config:
    """Create a mock configuration for testing."""
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
def server(mock_config: Config) -> OffshoreLeaksServer:
    """Create a server instance for testing."""
    return OffshoreLeaksServer(mock_config)


@pytest.mark.asyncio
async def test_server_initialization(mock_config: Config) -> None:
    """Test server initialization."""
    server = OffshoreLeaksServer(mock_config)

    assert server.config == mock_config
    assert not server.is_running
    assert server.database is not None


@pytest.mark.asyncio
async def test_server_start_success(server: OffshoreLeaksServer) -> None:
    """Test successful server startup."""
    with patch.object(
        server.database, "connect", new_callable=AsyncMock
    ) as mock_connect:
        mock_connect.return_value = None

        await server.start()

        assert server._running
        mock_connect.assert_called_once()


@pytest.mark.asyncio
async def test_server_start_failure(server: OffshoreLeaksServer) -> None:
    """Test server startup failure."""
    with patch.object(
        server.database, "connect", new_callable=AsyncMock
    ) as mock_connect:
        mock_connect.side_effect = ConnectionError("Connection failed")

        with pytest.raises(ConnectionError):
            await server.start()

        assert not server._running


@pytest.mark.asyncio
async def test_server_stop(server: OffshoreLeaksServer) -> None:
    """Test server shutdown."""
    server._running = True

    with patch.object(
        server.database, "disconnect", new_callable=AsyncMock
    ) as mock_disconnect:
        mock_disconnect.return_value = None

        await server.stop()

        assert not server._running
        mock_disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_health_check_healthy(server: OffshoreLeaksServer) -> None:
    """Test health check when database is healthy."""
    mock_db_health = {
        "status": "healthy",
        "database": "test_db",
        "uri": "bolt://localhost:7687",
        "connected": True,
    }

    with (
        patch.object(server.database, "_connected", True),
        patch.object(server.database, "_driver", MagicMock()),
        patch.object(
            server.database, "health_check", new_callable=AsyncMock
        ) as mock_health,
    ):
        mock_health.return_value = mock_db_health

        health = await server.health_check()

        assert isinstance(health, HealthStatus)
        assert health.status == "healthy"
        assert health.database_connected is True
        assert health.version == "0.1.0"
        assert health.details == mock_db_health


@pytest.mark.asyncio
async def test_health_check_unhealthy(server: OffshoreLeaksServer) -> None:
    """Test health check when database is unhealthy."""
    with (
        patch.object(server.database, "_connected", False),
        patch.object(server.database, "_driver", None),
    ):
        health = await server.health_check()

        assert isinstance(health, HealthStatus)
        assert health.status == "unhealthy"
        assert health.database_connected is False
        assert health.version == "0.1.0"
        assert health.details is not None and "error" in health.details


@pytest.mark.asyncio
async def test_search_entities_success(server: OffshoreLeaksServer) -> None:
    """Test successful entity search."""
    mock_query_result = MagicMock()
    mock_query_result.records = [
        {"e": {"node_id": "1", "name": "Test Entity 1"}},
        {"e": {"node_id": "2", "name": "Test Entity 2"}},
    ]
    mock_query_result.query_time_ms = 150

    mock_count_result = MagicMock()
    mock_count_result.records = [{"total": 2}]

    with patch.object(
        server.database, "execute_query", new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.side_effect = [mock_query_result, mock_count_result]

        result = await server.search_entities(name="Test", limit=10)

        assert isinstance(result, SearchResult)
        assert result.total_count == 2
        assert result.returned_count == 2
        assert result.limit == 10
        assert result.offset == 0
        assert len(result.results) == 2
        assert result.query_time_ms == 150


@pytest.mark.asyncio
async def test_search_entities_invalid_params(server: OffshoreLeaksServer) -> None:
    """Test entity search with invalid parameters."""
    with pytest.raises(ValueError, match="Invalid parameters"):
        await server.search_entities(limit=1000)  # Exceeds max limit


@pytest.mark.asyncio
async def test_search_entities_database_error(server: OffshoreLeaksServer) -> None:
    """Test entity search with database error."""
    with patch.object(
        server.database, "execute_query", new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.side_effect = QueryError("Query failed")

        with pytest.raises(QueryError):
            await server.search_entities(name="Test")


@pytest.mark.asyncio
async def test_search_officers_success(server: OffshoreLeaksServer) -> None:
    """Test successful officer search."""
    mock_query_result = MagicMock()
    mock_query_result.records = [
        {"o": {"node_id": "1", "name": "John Doe"}},
    ]
    mock_query_result.query_time_ms = 100

    mock_count_result = MagicMock()
    mock_count_result.records = [{"total": 1}]

    with patch.object(
        server.database, "execute_query", new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.side_effect = [mock_query_result, mock_count_result]

        result = await server.search_officers(name="John")

        assert isinstance(result, SearchResult)
        assert result.total_count == 1
        assert result.returned_count == 1
        assert len(result.results) == 1
        assert result.results[0]["name"] == "John Doe"


@pytest.mark.asyncio
async def test_get_connections_success(server: OffshoreLeaksServer) -> None:
    """Test successful connection exploration."""
    mock_query_result = MagicMock()
    mock_query_result.records = [
        {
            "connected": {"node_id": "2", "name": "Connected Entity"},
            "distance": 1,
            "first_relationship": {"type": "officer_of"},
        }
    ]
    mock_query_result.query_time_ms = 200

    with patch.object(
        server.database, "execute_query", new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.return_value = mock_query_result

        result = await server.get_connections(start_node_id="1", max_depth=2)

        assert isinstance(result, SearchResult)
        assert result.total_count == 1
        assert result.returned_count == 1
        assert len(result.results) == 1

        connection = result.results[0]
        assert connection["node"]["name"] == "Connected Entity"
        assert connection["distance"] == 1


@pytest.mark.asyncio
async def test_get_statistics_success(server: OffshoreLeaksServer) -> None:
    """Test successful statistics retrieval."""
    mock_query_result = MagicMock()
    mock_query_result.records = [
        {
            "entity_count": 1000,
            "officer_count": 500,
            "intermediary_count": 100,
            "address_count": 300,
            "relationship_count": 2000,
        }
    ]
    mock_query_result.query_time_ms = 50

    with patch.object(
        server.database, "execute_query", new_callable=AsyncMock
    ) as mock_execute:
        mock_execute.return_value = mock_query_result

        result = await server.get_statistics("overview")

        assert result["stat_type"] == "overview"
        assert result["query_time_ms"] == 50
        assert len(result["results"]) == 1
        assert result["results"][0]["entity_count"] == 1000


@pytest.mark.asyncio
async def test_is_running_property(server: OffshoreLeaksServer) -> None:
    """Test is_running property."""
    # Initially not running
    assert not server.is_running

    # Set running but database not connected
    server._running = True
    with (
        patch.object(server.database, "_connected", False),
        patch.object(server.database, "_driver", None),
    ):
        assert not server.is_running

    # Both running and database connected
    with (
        patch.object(server.database, "_connected", True),
        patch.object(server.database, "_driver", MagicMock()),
    ):
        assert server.is_running


def test_load_config() -> None:
    """Test configuration loading."""
    with patch.dict(
        "os.environ",
        {
            "NEO4J_URI": "bolt://test:7687",
            "NEO4J_PASSWORD": "test_pass",
            "DEBUG": "true",
        },
    ):
        config = load_config()

        assert config.neo4j.uri == "bolt://test:7687"
        assert config.neo4j.password == "test_pass"
        assert config.server.debug is True
