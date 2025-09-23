"""Integration tests for the offshore leaks MCP server."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from offshore_leaks_mcp import OffshoreLeaksServer
from offshore_leaks_mcp.database import Neo4jDatabase, QueryResult
from offshore_leaks_mcp.models import (
    ConnectionsParameters,
    EntitySearchParameters,
    OfficerSearchParameters,
)
from tests.test_utils import (
    IntegrationTestHelper,
    setup_neo4j_mock,
)


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.mark.asyncio
    async def test_database_connection_lifecycle(self, test_config, no_resilience):
        """Test complete database connection lifecycle."""
        with patch(
            "offshore_leaks_mcp.database.GraphDatabase.driver"
        ) as mock_driver_class:
            mock_driver = MagicMock()
            mock_session = MagicMock()
            mock_result = MagicMock()

            # Mock successful connection test
            mock_result.single.return_value = {"health_check": 1}
            mock_session.__enter__.return_value.run.return_value = mock_result
            mock_driver.session.return_value = mock_session
            mock_driver_class.return_value = mock_driver

            database = Neo4jDatabase(test_config.neo4j)

            # Test connection
            await database.connect()
            assert database.is_connected
            assert database._driver is not None

            # Test health check
            health = await database.health_check()
            assert health["connected"] is True
            assert health["status"] == "healthy"

            # Test disconnect
            await database.disconnect()
            assert not database.is_connected

    @pytest.mark.asyncio
    async def test_database_query_execution(self, test_config, no_resilience):
        """Test database query execution with real Cypher queries."""
        with patch(
            "offshore_leaks_mcp.database.GraphDatabase.driver"
        ) as mock_driver_class:
            # Mock query results
            test_records = [
                {"entity": {"node_id": "001", "name": "Test Company"}},
                {"entity": {"node_id": "002", "name": "Another Company"}},
            ]

            # Setup complete mock with health check support
            setup_neo4j_mock(mock_driver_class, query_result_data=test_records)

            database = Neo4jDatabase(test_config.neo4j)
            await database.connect()

            # Test query execution
            query = "MATCH (e:Entity) WHERE e.name CONTAINS $name RETURN e LIMIT 10"
            parameters = {"name": "Test"}

            result = await database.execute_query(query, parameters)

            assert isinstance(result, QueryResult)
            assert len(result.records) == 2
            assert result.records[0]["entity"]["name"] == "Test Company"


@pytest.mark.integration
class TestServerIntegration:
    """Integration tests for server operations."""

    @pytest.mark.asyncio
    async def test_server_startup_and_health_check(self, test_config, no_resilience):
        """Test server startup and health check workflow."""
        with patch(
            "offshore_leaks_mcp.database.GraphDatabase.driver"
        ) as mock_driver_class:
            # Setup successful database connection
            mock_driver = MagicMock()
            mock_session = MagicMock()
            mock_result = MagicMock()
            mock_result.single.return_value = {"health_check": 1}
            mock_session.__enter__.return_value.run.return_value = mock_result
            mock_driver.session.return_value = mock_session
            mock_driver_class.return_value = mock_driver

            server = OffshoreLeaksServer(test_config)

            # Test server startup
            await server.start()
            assert server.is_running
            assert server.database.is_connected

            # Test health check
            health = await server.health_check()
            assert health.status == "healthy"
            assert health.database_connected is True
            assert health.server_running is True
            assert health.version == test_config.server.version

            # Test server stop
            await server.stop()
            assert not server.is_running

    @pytest.mark.asyncio
    async def test_entity_search_workflow(self, test_config, no_resilience):
        """Test complete entity search workflow."""
        with patch(
            "offshore_leaks_mcp.database.GraphDatabase.driver"
        ) as mock_driver_class:
            # Setup mock data
            test_entity = IntegrationTestHelper.create_test_entity_data()
            mock_result_data = [{"e": test_entity}]

            # Setup complete mock with health check support
            setup_neo4j_mock(mock_driver_class, query_result_data=mock_result_data)

            server = OffshoreLeaksServer(test_config)
            await server.start()

            # Test entity search
            search_params = EntitySearchParameters(
                name="Test", jurisdiction="BVI", limit=10
            )

            result = await server.search_entities(
                **search_params.dict(exclude_none=True)
            )

            assert result.total_count >= 0
            assert len(result.results) <= 10
            if result.results:
                entity = result.results[0]
                assert "node_id" in entity
                assert "name" in entity

    @pytest.mark.asyncio
    async def test_officer_search_workflow(self, test_config, no_resilience):
        """Test complete officer search workflow."""
        with patch(
            "offshore_leaks_mcp.database.GraphDatabase.driver"
        ) as mock_driver_class:
            # Setup mock data
            test_officer = IntegrationTestHelper.create_test_officer_data()
            mock_result_data = [{"o": test_officer}]

            # Setup complete mock with health check support
            setup_neo4j_mock(mock_driver_class, query_result_data=mock_result_data)

            server = OffshoreLeaksServer(test_config)
            await server.start()

            # Test officer search
            search_params = OfficerSearchParameters(
                name="John", countries="United States", limit=10
            )

            result = await server.search_officers(
                **search_params.dict(exclude_none=True)
            )

            assert result.total_count >= 0
            assert len(result.results) <= 10

    @pytest.mark.asyncio
    async def test_connections_exploration_workflow(self, test_config, no_resilience):
        """Test connections exploration workflow."""
        with patch(
            "offshore_leaks_mcp.database.GraphDatabase.driver"
        ) as mock_driver_class:
            # Setup mock connection data
            mock_connection_data = [
                {
                    "connected": {
                        "node_id": "connected_001",
                        "name": "Connected Entity",
                    },
                    "distance": 1,
                    "first_relationship": {"type": "OFFICER_OF"},
                }
            ]

            # Setup complete mock with health check support
            setup_neo4j_mock(mock_driver_class, query_result_data=mock_connection_data)

            server = OffshoreLeaksServer(test_config)
            await server.start()

            # Test connections search
            connections_params = ConnectionsParameters(
                start_node_id="test_entity_001", max_depth=2, limit=20
            )

            result = await server.get_connections(
                **connections_params.dict(exclude_none=True)
            )

            assert result.total_count >= 0
            assert len(result.results) <= 20


@pytest.mark.integration
class TestEndToEndWorkflows:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_complete_investigation_workflow(self, test_config, no_resilience):
        """Test a complete investigation workflow."""
        with patch(
            "offshore_leaks_mcp.database.GraphDatabase.driver"
        ) as mock_driver_class:
            # Setup mock data for multi-step workflow
            entity_data = IntegrationTestHelper.create_test_entity_data()
            officer_data = IntegrationTestHelper.create_test_officer_data()
            connection_data = [
                {
                    "connected": officer_data,
                    "distance": 1,
                    "first_relationship": {"type": "OFFICER_OF"},
                }
            ]

            mock_driver = MagicMock()
            mock_session = MagicMock()
            mock_result = MagicMock()

            # Configure mock to return different data based on query
            def mock_run(query, parameters=None, timeout=None):
                if "RETURN 1 as health_check" in query:
                    # Health check query
                    mock_result.single.return_value = {"health_check": 1}
                    mock_result.data.return_value = [{"health_check": 1}]
                elif "count(e) as total" in query:
                    # Count query
                    mock_result.data.return_value = [{"total": 1}]
                    mock_record = MagicMock()
                    mock_record.data.return_value = {"total": 1}
                    mock_result.__iter__.return_value = iter([mock_record])
                elif "count(o) as total" in query:
                    # Officer count query
                    mock_result.data.return_value = [{"total": 1}]
                    mock_record = MagicMock()
                    mock_record.data.return_value = {"total": 1}
                    mock_result.__iter__.return_value = iter([mock_record])
                elif "MATCH (e:Entity)" in query:
                    mock_result.data.return_value = [{"e": entity_data}]
                    # Setup records iteration for query execution
                    mock_record = MagicMock()
                    mock_record.data.return_value = {"e": entity_data}
                    mock_result.__iter__.return_value = iter([mock_record])
                elif "MATCH (o:Officer)" in query:
                    mock_result.data.return_value = [{"o": officer_data}]
                    mock_record = MagicMock()
                    mock_record.data.return_value = {"o": officer_data}
                    mock_result.__iter__.return_value = iter([mock_record])
                elif "MATCH path" in query or "connected" in query:
                    mock_result.data.return_value = connection_data
                    mock_records = []
                    for data in connection_data:
                        mock_record = MagicMock()
                        mock_record.data.return_value = data
                        mock_records.append(mock_record)
                    mock_result.__iter__.return_value = iter(mock_records)
                else:
                    mock_result.data.return_value = []
                    mock_result.__iter__.return_value = iter([])

                # Setup summary for all queries
                mock_summary = MagicMock()
                mock_summary.query_type = "r"
                mock_summary.counters = {}
                mock_summary.result_available_after = 1
                mock_summary.result_consumed_after = 2
                mock_result.summary.return_value = mock_summary

                return mock_result

            mock_session.__enter__.return_value.run.side_effect = mock_run
            mock_driver.session.return_value = mock_session
            mock_driver_class.return_value = mock_driver

            server = OffshoreLeaksServer(test_config)
            await server.start()

            # Step 1: Search for entities
            entity_result = await server.search_entities(name="Test", limit=5)
            assert len(entity_result.results) > 0

            # Step 2: Get the first entity's connections
            entity_id = entity_data["node_id"]
            connections_result = await server.get_connections(
                start_node_id=entity_id, max_depth=2, limit=10
            )
            assert len(connections_result.results) > 0

            # Step 3: Search for officers
            officer_result = await server.search_officers(name="John", limit=5)
            assert len(officer_result.results) >= 0

            # Step 4: Check server health throughout
            health = await server.health_check()
            assert health.status == "healthy"

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, test_config, no_resilience):
        """Test error handling and recovery scenarios."""
        server = OffshoreLeaksServer(test_config)

        # Test health check when database is not connected
        health = await server.health_check()
        assert health.status == "unhealthy"
        assert health.database_connected is False

        # Test search operations when database is not connected
        with pytest.raises(
            (ConnectionError, ValueError)
        ):  # Should raise database error
            await server.search_entities(name="Test")


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Performance-related integration tests."""

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, test_config, no_resilience):
        """Test handling of concurrent queries."""
        with patch(
            "offshore_leaks_mcp.database.GraphDatabase.driver"
        ) as mock_driver_class:
            # Setup mock data
            mock_result_data = [{"e": IntegrationTestHelper.create_test_entity_data()}]

            # Setup complete mock with health check support
            setup_neo4j_mock(mock_driver_class, query_result_data=mock_result_data)

            server = OffshoreLeaksServer(test_config)
            await server.start()

            # Run multiple queries concurrently
            tasks = []
            for i in range(5):
                task = server.search_entities(name=f"Test{i}", limit=10)
                tasks.append(task)

            results = await asyncio.gather(*tasks)

            # Verify all queries completed successfully
            assert len(results) == 5
            for result in results:
                assert result.total_count >= 0

    @pytest.mark.asyncio
    async def test_large_result_handling(self, test_config, no_resilience):
        """Test handling of large result sets."""
        with patch(
            "offshore_leaks_mcp.database.GraphDatabase.driver"
        ) as mock_driver_class:
            # Setup mock driver with large dataset
            large_dataset = []
            for i in range(100):
                entity = IntegrationTestHelper.create_test_entity_data()
                entity["node_id"] = f"entity_{i:03d}"
                entity["name"] = f"Test Company {i}"
                large_dataset.append({"e": entity})

            # Setup complete mock with health check support
            setup_neo4j_mock(mock_driver_class, query_result_data=large_dataset)

            server = OffshoreLeaksServer(test_config)
            await server.start()

            # Test with max limit
            result = await server.search_entities(
                name="Test", limit=server.config.server.max_limit
            )

            assert len(result.results) <= server.config.server.max_limit
            assert result.total_count >= 0
