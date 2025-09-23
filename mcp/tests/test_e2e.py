"""End-to-end tests with real database for offshore leaks system.

These tests require a real Neo4j database with offshore leaks data.
They test the entire stack from database to CLI/API to ensure everything works together.
"""

import asyncio
import os
import subprocess

import httpx
import pytest

from offshore_leaks_mcp import Config, OffshoreLeaksServer
from offshore_leaks_mcp.cli.client import OffshoreLeaksClient
from offshore_leaks_mcp.database import Neo4jDatabase

# Configuration for E2E tests
E2E_NEO4J_URI = os.getenv("E2E_NEO4J_URI", "bolt://localhost:7687")
E2E_NEO4J_USER = os.getenv("E2E_NEO4J_USER", "neo4j")
E2E_NEO4J_PASSWORD = os.getenv("E2E_NEO4J_PASSWORD", "password")
E2E_NEO4J_DATABASE = os.getenv("E2E_NEO4J_DATABASE", "neo4j")
E2E_API_URL = os.getenv("E2E_API_URL", "http://localhost:8000")

# Skip E2E tests if database is not available
pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_E2E_TESTS"),
    reason="E2E tests require RUN_E2E_TESTS=1 and a real Neo4j database",
)


@pytest.fixture(scope="session")
async def e2e_config() -> Config:
    """Create configuration for E2E tests."""
    from offshore_leaks_mcp.config import Neo4jConfig, ServerConfig

    neo4j_config = Neo4jConfig(
        uri=E2E_NEO4J_URI,
        user=E2E_NEO4J_USER,
        password=E2E_NEO4J_PASSWORD,
        database=E2E_NEO4J_DATABASE,
    )
    server_config = ServerConfig(
        name="e2e-test-server",
        version="0.1.0",
        debug=True,
        query_timeout=30,
    )
    return Config(neo4j=neo4j_config, server=server_config)


@pytest.fixture(scope="session")
async def e2e_database(e2e_config: Config) -> Neo4jDatabase:
    """Create database connection for E2E tests."""
    database = Neo4jDatabase(e2e_config.neo4j)
    await database.connect()

    # Verify database has data
    result = await database.execute_query(
        "MATCH (n) RETURN count(n) as total_nodes LIMIT 1"
    )

    if not result.records or result.records[0]["total_nodes"] == 0:
        pytest.skip("E2E database appears to be empty - no nodes found")

    yield database
    await database.disconnect()


@pytest.fixture(scope="session")
async def e2e_server(
    e2e_config: Config, e2e_database: Neo4jDatabase
) -> OffshoreLeaksServer:
    """Create and start server for E2E tests."""
    server = OffshoreLeaksServer(e2e_config)
    # Use the already connected database
    server.database = e2e_database
    server._running = True
    yield server
    await server.stop()


@pytest.mark.asyncio
@pytest.mark.e2e
class TestDatabaseConnectivity:
    """Test basic database connectivity and data availability."""

    async def test_database_connection(self, e2e_database: Neo4jDatabase):
        """Test that we can connect to the database."""
        assert e2e_database.is_connected

        health = await e2e_database.health_check()
        assert health["status"] == "healthy"
        assert health["connected"] is True

    async def test_database_has_entities(self, e2e_database: Neo4jDatabase):
        """Test that database contains Entity nodes."""
        result = await e2e_database.execute_query(
            "MATCH (e:Entity) RETURN count(e) as entity_count LIMIT 1"
        )

        assert result.records
        entity_count = result.records[0]["entity_count"]
        assert entity_count > 0, "Database should contain Entity nodes"

    async def test_database_has_officers(self, e2e_database: Neo4jDatabase):
        """Test that database contains Officer nodes."""
        result = await e2e_database.execute_query(
            "MATCH (o:Officer) RETURN count(o) as officer_count LIMIT 1"
        )

        assert result.records
        officer_count = result.records[0]["officer_count"]
        assert officer_count > 0, "Database should contain Officer nodes"

    async def test_database_has_relationships(self, e2e_database: Neo4jDatabase):
        """Test that database contains relationships."""
        result = await e2e_database.execute_query(
            "MATCH ()-[r]->() RETURN count(r) as rel_count LIMIT 1"
        )

        assert result.records
        rel_count = result.records[0]["rel_count"]
        assert rel_count > 0, "Database should contain relationships"


@pytest.mark.asyncio
@pytest.mark.e2e
class TestServerE2E:
    """Test the MCP server with real data."""

    async def test_server_health_check(self, e2e_server: OffshoreLeaksServer):
        """Test server health check with real database."""
        health = await e2e_server.health_check()

        assert health.status == "healthy"
        assert health.database_connected is True
        assert health.version == "0.1.0"
        assert health.details is not None

    async def test_entity_search_with_real_data(self, e2e_server: OffshoreLeaksServer):
        """Test entity search returns real results."""
        # Search for entities with a common name pattern
        results = await e2e_server.search_entities(
            name="COMPANY",
            limit=5,  # Common word in entity names
        )

        assert results.total_count > 0
        assert len(results.results) > 0
        assert results.returned_count <= 5

        # Verify result structure
        entity = results.results[0]
        assert "node_id" in entity
        assert "name" in entity

    async def test_officer_search_with_real_data(self, e2e_server: OffshoreLeaksServer):
        """Test officer search returns real results."""
        # Search for officers with a common name pattern
        results = await e2e_server.search_officers(
            name="JOHN",
            limit=5,  # Common first name
        )

        # Note: Might be 0 if no officers match, which is OK
        assert results.total_count >= 0
        assert results.returned_count >= 0

        if results.total_count > 0:
            officer = results.results[0]
            assert "node_id" in officer
            assert "name" in officer

    async def test_get_statistics_with_real_data(self, e2e_server: OffshoreLeaksServer):
        """Test statistics with real data."""
        stats = await e2e_server.get_statistics("overview")

        assert "stat_type" in stats
        assert stats["stat_type"] == "overview"
        assert "results" in stats
        assert len(stats["results"]) > 0

        # Check that we have actual counts
        overview = stats["results"][0]
        assert "entity_count" in overview
        assert overview["entity_count"] > 0

    async def test_connections_with_real_data(self, e2e_server: OffshoreLeaksServer):
        """Test connection exploration with real data."""
        # First find an entity to explore from
        entities = await e2e_server.search_entities(limit=1)

        if entities.total_count == 0:
            pytest.skip("No entities found for connection test")

        start_entity = entities.results[0]
        start_node_id = start_entity["node_id"]

        # Explore connections
        connections = await e2e_server.get_connections(
            start_node_id=start_node_id, max_depth=2, limit=10
        )

        # May be 0 connections, which is valid
        assert connections.total_count >= 0
        assert connections.returned_count >= 0


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.slow
class TestCLIE2E:
    """Test the CLI tool end-to-end with real API."""

    @pytest.fixture
    async def api_process(self):
        """Start the API server for CLI testing."""
        # Start API server in background
        env = os.environ.copy()
        env.update(
            {
                "NEO4J_URI": E2E_NEO4J_URI,
                "NEO4J_USER": E2E_NEO4J_USER,
                "NEO4J_PASSWORD": E2E_NEO4J_PASSWORD,
                "NEO4J_DATABASE": E2E_NEO4J_DATABASE,
            }
        )

        process = subprocess.Popen(
            ["python", "-m", "offshore_leaks_mcp.api"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for API to start
        await asyncio.sleep(3)

        # Verify API is running
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{E2E_API_URL}/health", timeout=5)
                if response.status_code != 200:
                    process.terminate()
                    pytest.skip("API server failed to start properly")
        except Exception:
            process.terminate()
            pytest.skip("Could not connect to API server")

        yield process

        # Cleanup
        process.terminate()
        process.wait()

    async def test_cli_health_check(self, api_process):
        """Test CLI health check command."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "offshore_leaks_mcp.cli.main",
                "--api-url",
                E2E_API_URL,
                "health",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0
        assert "healthy" in result.stdout.lower()

    async def test_cli_search_entities(self, api_process):
        """Test CLI entity search."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "offshore_leaks_mcp.cli.main",
                "--api-url",
                E2E_API_URL,
                "search",
                "entities",
                "--name",
                "COMPANY",
                "--limit",
                "5",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should succeed even if no results
        assert result.returncode == 0
        # Should contain some output indicating search completion
        assert "Found" in result.stdout or "No results" in result.stdout

    async def test_cli_get_statistics(self, api_process):
        """Test CLI statistics command."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "offshore_leaks_mcp.cli.main",
                "--api-url",
                E2E_API_URL,
                "stats",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )

        assert result.returncode == 0
        # Should show some statistics
        assert (
            "entities" in result.stdout.lower() or "statistics" in result.stdout.lower()
        )


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.slow
class TestAPIE2E:
    """Test the REST API end-to-end."""

    @pytest.fixture
    async def api_client(self):
        """Create API client for testing."""
        async with OffshoreLeaksClient(E2E_API_URL) as client:
            yield client

    async def test_api_health_endpoint(self, api_client: OffshoreLeaksClient):
        """Test API health endpoint."""
        health = await api_client.health_check()

        assert health["success"] is True
        assert health["data"]["status"] == "healthy"
        assert health["data"]["database_connected"] is True

    async def test_api_entity_search(self, api_client: OffshoreLeaksClient):
        """Test API entity search endpoint."""
        results = await api_client.search_entities(name="COMPANY", limit=5)

        assert "success" in results
        assert "data" in results
        assert "pagination" in results["data"]
        assert results["data"]["pagination"]["limit"] == 5

    async def test_api_statistics(self, api_client: OffshoreLeaksClient):
        """Test API statistics endpoint."""
        stats = await api_client.get_statistics("overview")

        assert "success" in stats
        assert "data" in stats
        assert stats["data"]["stat_type"] == "overview"


@pytest.mark.asyncio
@pytest.mark.e2e
class TestDataIntegrity:
    """Test data integrity and consistency."""

    async def test_entity_officer_relationships(self, e2e_database: Neo4jDatabase):
        """Test that entity-officer relationships are valid."""
        result = await e2e_database.execute_query(
            """
            MATCH (e:Entity)-[r]-(o:Officer)
            RETURN type(r) as rel_type, count(*) as count
            LIMIT 10
        """
        )

        # Should have some relationships if data is loaded
        if result.records:
            for record in result.records:
                assert record["rel_type"] is not None
                assert record["count"] > 0

    async def test_node_properties_consistency(self, e2e_database: Neo4jDatabase):
        """Test that nodes have expected properties."""
        # Test entities have required properties
        result = await e2e_database.execute_query(
            """
            MATCH (e:Entity)
            WHERE e.node_id IS NOT NULL AND e.name IS NOT NULL
            RETURN count(e) as valid_entities
            LIMIT 1
        """
        )

        if result.records:
            valid_count = result.records[0]["valid_entities"]
            assert valid_count > 0, "Entities should have node_id and name properties"


@pytest.mark.asyncio
@pytest.mark.e2e
@pytest.mark.slow
class TestPerformanceE2E:
    """Test performance with real data."""

    async def test_search_performance(self, e2e_server: OffshoreLeaksServer):
        """Test that searches complete within reasonable time."""
        import time

        start_time = time.time()
        results = await e2e_server.search_entities(name="COMPANY", limit=100)
        end_time = time.time()

        # Should complete within 30 seconds
        assert (end_time - start_time) < 30
        assert results.query_time_ms is not None
        # Query should complete within 10 seconds at database level
        assert results.query_time_ms < 10000

    async def test_statistics_performance(self, e2e_server: OffshoreLeaksServer):
        """Test that statistics queries perform reasonably."""
        import time

        start_time = time.time()
        stats = await e2e_server.get_statistics("overview")
        end_time = time.time()

        # Should complete within 60 seconds (stats can be slow)
        assert (end_time - start_time) < 60
        assert "query_time_ms" in stats
        # Allow up to 30 seconds for complex statistics
        assert stats["query_time_ms"] < 30000


# Helper function to setup test data (if needed)
async def setup_test_data(database: Neo4jDatabase) -> None:
    """Setup minimal test data if database is empty."""
    # Check if we need to create test data
    result = await database.execute_query("MATCH (n) RETURN count(n) as total")

    if result.records and result.records[0]["total"] == 0:
        # Create minimal test data
        await database.execute_query(
            """
            CREATE (e1:Entity {node_id: "test_entity_1", name: "Test Company Ltd"})
            CREATE (o1:Officer {node_id: "test_officer_1", name: "John Test"})
            CREATE (e1)-[:officer_of]->(o1)
        """
        )


# Configuration helpers
def get_e2e_config_help() -> str:
    """Get help text for E2E test configuration."""
    return """
To run E2E tests, you need:

1. A running Neo4j database with offshore leaks data
2. Environment variables:
   - RUN_E2E_TESTS=1 (required to enable tests)
   - E2E_NEO4J_URI (default: bolt://localhost:7687)
   - E2E_NEO4J_USER (default: neo4j)
   - E2E_NEO4J_PASSWORD (default: password)
   - E2E_NEO4J_DATABASE (default: neo4j)
   - E2E_API_URL (default: http://localhost:8000)

Example:
    export RUN_E2E_TESTS=1
    export E2E_NEO4J_PASSWORD=your_password
    pytest tests/test_e2e.py -v
"""


if __name__ == "__main__":
    print(get_e2e_config_help())
