"""Tests for the database module."""

from unittest.mock import MagicMock, patch

import pytest

from offshore_leaks_mcp.config import Neo4jConfig
from offshore_leaks_mcp.database import Neo4jDatabase


@pytest.fixture
def neo4j_config() -> Neo4jConfig:
    """Create a Neo4j configuration for testing."""
    return Neo4jConfig(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="test_password",
        database="test_db",
    )


@pytest.fixture
def database(neo4j_config: Neo4jConfig) -> Neo4jDatabase:
    """Create a database instance for testing."""
    return Neo4jDatabase(neo4j_config)


@pytest.mark.asyncio
async def test_database_initialization(neo4j_config: Neo4jConfig) -> None:
    """Test database initialization."""
    db = Neo4jDatabase(neo4j_config)

    assert db.config == neo4j_config
    assert db._driver is None
    assert not db._connected
    assert not db.is_connected


@pytest.mark.asyncio
async def test_connect_success(database: Neo4jDatabase) -> None:
    """Test successful database connection."""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_record = MagicMock()
    mock_record.__getitem__.return_value = 1

    mock_result.single.return_value = mock_record
    mock_session.__enter__.return_value.run.return_value = mock_result
    mock_driver.session.return_value = mock_session

    with patch("offshore_leaks_mcp.database.GraphDatabase.driver") as mock_graph_driver:
        mock_graph_driver.return_value = mock_driver

        await database.connect()

        assert database._driver == mock_driver
        assert database._connected
        assert database.is_connected


@pytest.mark.asyncio
async def test_connect_failure(database: Neo4jDatabase, no_resilience) -> None:
    """Test database connection failure."""
    with patch("offshore_leaks_mcp.database.GraphDatabase.driver") as mock_graph_driver:
        mock_graph_driver.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            await database.connect()

        assert database._driver is None
        assert not database._connected


@pytest.mark.asyncio
async def test_disconnect(database: Neo4jDatabase) -> None:
    """Test database disconnection."""
    mock_driver = MagicMock()
    database._driver = mock_driver
    database._connected = True

    await database.disconnect()

    mock_driver.close.assert_called_once()
    assert database._driver is None
    assert not database._connected


@pytest.mark.asyncio
async def test_health_check_success(database: Neo4jDatabase, no_resilience) -> None:
    """Test successful health check."""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_record = MagicMock()
    mock_record.__getitem__.return_value = 1

    mock_result.single.return_value = mock_record
    mock_session.__enter__.return_value.run.return_value = mock_result
    mock_driver.session.return_value = mock_session

    database._driver = mock_driver

    health = await database.health_check()

    assert health["status"] == "healthy"
    assert health["database"] == "test_db"
    assert health["connected"] is True


@pytest.mark.asyncio
async def test_health_check_no_driver(database: Neo4jDatabase, no_resilience) -> None:
    """Test health check without driver."""
    with pytest.raises(Exception, match="Database not connected"):
        await database.health_check()


@pytest.mark.asyncio
async def test_execute_query_success(database: Neo4jDatabase, no_resilience) -> None:
    """Test successful query execution."""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_summary = MagicMock()

    # Mock result records
    mock_record1 = MagicMock()
    mock_record1.data.return_value = {"name": "Entity 1"}
    mock_record2 = MagicMock()
    mock_record2.data.return_value = {"name": "Entity 2"}

    mock_result.__iter__.return_value = [mock_record1, mock_record2]
    mock_result.summary.return_value = mock_summary
    mock_summary.query_type = "r"
    mock_summary.counters = {}
    mock_summary.result_available_after = 10
    mock_summary.result_consumed_after = 20

    mock_session.__enter__.return_value.run.return_value = mock_result
    mock_driver.session.return_value = mock_session

    database._driver = mock_driver

    result = await database.execute_query("MATCH (n) RETURN n", {"param": "value"})

    assert len(result.records) == 2
    assert result.records[0]["name"] == "Entity 1"
    assert result.records[1]["name"] == "Entity 2"
    assert result.summary["query_type"] == "r"
    assert result.query_time_ms is not None


@pytest.mark.asyncio
async def test_execute_query_no_driver(database: Neo4jDatabase, no_resilience) -> None:
    """Test query execution without driver."""
    with pytest.raises(Exception, match="Database not connected"):
        await database.execute_query("MATCH (n) RETURN n")


@pytest.mark.asyncio
async def test_execute_query_failure(database: Neo4jDatabase, no_resilience) -> None:
    """Test query execution failure."""
    mock_driver = MagicMock()
    mock_session = MagicMock()

    mock_session.__enter__.return_value.run.side_effect = Exception("Query failed")
    mock_driver.session.return_value = mock_session

    database._driver = mock_driver

    with pytest.raises(Exception, match="Query.*failed"):
        await database.execute_query("INVALID QUERY")


@pytest.mark.asyncio
async def test_get_database_info(database: Neo4jDatabase) -> None:
    """Test database info retrieval."""
    mock_driver = MagicMock()
    database._driver = mock_driver

    # Mock multiple query executions
    async def mock_execute_query(query: str) -> MagicMock:
        mock_result = MagicMock()
        if "labels(n)" in query:
            mock_result.records = [{"labels": ["Entity"], "count": 100}]
        elif "type(r)" in query:
            mock_result.records = [{"relationship_type": "officer_of", "count": 50}]
        else:
            mock_result.records = [{"total_size_bytes": 1000000}]
        return mock_result

    with patch.object(database, "execute_query", side_effect=mock_execute_query):
        info = await database.get_database_info()

        assert "node_counts" in info
        assert "relationship_counts" in info
        assert "database_size" in info
        assert len(info["node_counts"]) == 1
        assert info["node_counts"][0]["count"] == 100
