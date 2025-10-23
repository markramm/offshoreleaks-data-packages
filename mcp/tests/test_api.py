"""Tests for the offshore leaks FastAPI REST API."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from offshore_leaks_mcp.api import app, get_config, get_database, get_service
from offshore_leaks_mcp.database import DatabaseError, QueryError
from offshore_leaks_mcp.models import SearchResult


@pytest.fixture
def client(mock_service, mock_database, mock_config, mock_load_config, mock_neo4j_init, mock_service_init):
    """Create a test client with mocked dependencies."""

    def get_mock_service():
        return mock_service

    def get_mock_database():
        return mock_database

    def get_mock_config():
        return mock_config

    # Override dependencies
    app.dependency_overrides[get_service] = get_mock_service
    app.dependency_overrides[get_database] = get_mock_database
    app.dependency_overrides[get_config] = get_mock_config

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.mark.unit
class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_basic_health_check(self, client, mock_database):
        """Test basic health check endpoint."""
        mock_database.health_check.return_value = {"connected": True}

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "status" in data["data"]
        assert "database_connected" in data["data"]

    def test_api_health_check(self, client, mock_database):
        """Test API v1 health check endpoint."""
        mock_database.health_check.return_value = {"connected": True}

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["database_connected"] is True

    def test_health_check_database_disconnected(self, client, mock_database):
        """Test health check when database is disconnected."""
        mock_database.is_connected = False

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "unhealthy"
        assert data["data"]["database_connected"] is False

    def test_health_check_exception(self, client, mock_database):
        """Test health check with exception."""
        mock_database.health_check.side_effect = Exception("Database error")

        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data


@pytest.mark.unit
class TestStatisticsEndpoints:
    """Test statistics endpoints."""

    def test_get_statistics_default(self, client, mock_service):
        """Test get statistics with default parameters."""
        mock_service.get_statistics.return_value = {
            "stat_type": "overview",
            "results": [{"metric": "total_entities", "value": 100000}],
            "query_time_ms": 25,
        }

        response = client.get("/api/v1/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["stat_type"] == "overview"
        assert data["query_time_ms"] == 25
        mock_service.get_statistics.assert_called_once_with("overview")

    def test_get_statistics_custom_type(self, client, mock_service):
        """Test get statistics with custom type."""
        mock_service.get_statistics.return_value = {
            "stat_type": "entities",
            "results": [{"metric": "entity_count", "value": 50000}],
            "query_time_ms": 15,
        }

        response = client.get("/api/v1/stats?stat_type=entities")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["stat_type"] == "entities"
        mock_service.get_statistics.assert_called_once_with("entities")

    def test_get_statistics_service_error(self, client, mock_service):
        """Test get statistics with service error."""
        mock_service.get_statistics.side_effect = DatabaseError("Query failed")

        response = client.get("/api/v1/stats")

        assert response.status_code == 500


@pytest.mark.unit
class TestSearchEndpoints:
    """Test search endpoints."""

    def test_search_entities_success(self, client, mock_service):
        """Test successful entity search."""
        mock_result = SearchResult(
            total_count=100,
            returned_count=2,
            offset=0,
            limit=20,
            results=[
                {"node_id": "entity_001", "name": "Test Entity 1"},
                {"node_id": "entity_002", "name": "Test Entity 2"},
            ],
            query_time_ms=45,
        )
        mock_service.search_entities.return_value = mock_result

        payload = {
            "name": "Test Entity",
            "jurisdiction": "BVI",
            "limit": 20,
            "offset": 0,
        }

        response = client.post("/api/v1/search/entities", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["results"]) == 2
        assert data["data"]["pagination"]["total_count"] == 100
        assert data["query_time_ms"] == 45

        mock_service.search_entities.assert_called_once_with(
            name="Test Entity", jurisdiction="BVI", limit=20, offset=0
        )

    def test_search_entities_empty_request(self, client, mock_service):
        """Test entity search with empty request body."""
        mock_result = SearchResult(
            total_count=0,
            returned_count=0,
            offset=0,
            limit=20,
            results=[],
            query_time_ms=10,
        )
        mock_service.search_entities.return_value = mock_result

        response = client.post("/api/v1/search/entities", json={})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["results"]) == 0

    def test_search_officers_success(self, client, mock_service):
        """Test successful officer search."""
        mock_result = SearchResult(
            total_count=50,
            returned_count=1,
            offset=0,
            limit=20,
            results=[
                {"node_id": "officer_001", "name": "John Smith", "countries": "USA"}
            ],
            query_time_ms=30,
        )
        mock_service.search_officers.return_value = mock_result

        payload = {"name": "John Smith", "countries": "USA", "limit": 20}

        response = client.post("/api/v1/search/officers", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["results"]) == 1
        assert data["data"]["results"][0]["name"] == "John Smith"

        mock_service.search_officers.assert_called_once_with(
            limit=20, offset=0, name="John Smith", countries="USA"
        )

    def test_search_entities_validation_error(self, client, mock_service):
        """Test entity search with validation error."""
        mock_service.search_entities.side_effect = ValueError("Invalid parameters")

        payload = {"name": "Test", "limit": -1}  # Invalid limit

        response = client.post("/api/v1/search/entities", json=payload)

        assert response.status_code == 422

    def test_search_entities_database_error(self, client, mock_service):
        """Test entity search with database error."""
        mock_service.search_entities.side_effect = DatabaseError("Connection failed")

        payload = {"name": "Test"}

        response = client.post("/api/v1/search/entities", json=payload)

        assert response.status_code == 500


@pytest.mark.unit
class TestConnectionsEndpoints:
    """Test connections endpoints."""

    def test_explore_connections_success(self, client, mock_service):
        """Test successful connection exploration."""
        mock_result = SearchResult(
            total_count=5,
            returned_count=2,
            offset=0,
            limit=20,
            results=[
                {
                    "node": {"node_id": "entity_002", "name": "Connected Entity"},
                    "distance": 1,
                    "first_relationship": {"type": "OFFICER_OF"},
                },
                {
                    "node": {"node_id": "officer_003", "name": "Connected Officer"},
                    "distance": 2,
                    "first_relationship": {"type": "OWNS"},
                },
            ],
            query_time_ms=60,
        )
        mock_service.get_connections.return_value = mock_result

        payload = {"start_node_id": "entity_001", "max_depth": 2, "limit": 20}

        response = client.post("/api/v1/connections", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["results"]) == 2
        assert data["data"]["results"][0]["node"]["node_id"] == "entity_002"

        mock_service.get_connections.assert_called_once_with(
            start_node_id="entity_001", max_depth=2, limit=20
        )

    def test_explore_connections_missing_start_node(self, client, mock_service):
        """Test connection exploration without start node."""
        response = client.post("/api/v1/connections", json={})

        assert response.status_code == 422  # Validation error


@pytest.mark.unit
class TestIndividualLookups:
    """Test individual entity/officer lookup endpoints."""

    def test_get_entity_success(self, client, mock_service):
        """Test successful entity lookup."""
        mock_result = SearchResult(
            total_count=1,
            returned_count=1,
            offset=0,
            limit=1,
            results=[
                {
                    "node_id": "entity_001",
                    "name": "Test Entity",
                    "jurisdiction": "BVI",
                    "status": "Active",
                }
            ],
            query_time_ms=15,
        )
        mock_service.search_entities.return_value = mock_result

        response = client.get("/api/v1/entity/entity_001")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["node_id"] == "entity_001"
        assert data["data"]["name"] == "Test Entity"

        mock_service.search_entities.assert_called_once_with(
            node_id="entity_001", limit=1
        )

    def test_get_entity_not_found(self, client, mock_service):
        """Test entity lookup when entity not found."""
        mock_result = SearchResult(
            total_count=0,
            returned_count=0,
            offset=0,
            limit=1,
            results=[],
            query_time_ms=10,
        )
        mock_service.search_entities.return_value = mock_result

        response = client.get("/api/v1/entity/nonexistent")

        assert response.status_code == 404

    def test_get_officer_success(self, client, mock_service):
        """Test successful officer lookup."""
        mock_result = SearchResult(
            total_count=1,
            returned_count=1,
            offset=0,
            limit=1,
            results=[
                {"node_id": "officer_001", "name": "John Smith", "countries": "USA"}
            ],
            query_time_ms=12,
        )
        mock_service.search_officers.return_value = mock_result

        response = client.get("/api/v1/officer/officer_001")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["node_id"] == "officer_001"


@pytest.mark.unit
class TestAdvancedAnalysis:
    """Test advanced analysis endpoints."""

    def test_find_shortest_paths_success(self, client, mock_service):
        """Test successful shortest paths analysis."""
        mock_result = SearchResult(
            total_count=1,
            returned_count=1,
            offset=0,
            limit=10,
            results=[
                {
                    "path_length": 3,
                    "relationship_types": ["OFFICER_OF", "OWNS"],
                    "path_nodes": [
                        {"node_id": "entity_001", "name": "Start"},
                        {"node_id": "officer_001", "name": "Middle"},
                        {"node_id": "entity_002", "name": "End"},
                    ],
                }
            ],
            query_time_ms=150,
        )
        mock_service.find_shortest_paths.return_value = mock_result

        response = client.post(
            "/api/v1/analysis/paths?start_node_id=entity_001&end_node_id=entity_002&max_depth=6&limit=10",
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["paths"]) == 1
        assert data["data"]["paths"][0]["path_length"] == 3

    def test_analyze_network_patterns_success(self, client, mock_service):
        """Test successful network pattern analysis."""
        mock_result = SearchResult(
            total_count=1,
            returned_count=1,
            offset=0,
            limit=20,
            results=[
                {
                    "node": {"node_id": "entity_hub", "name": "Hub Entity"},
                    "connection_count": 25,
                    "total_neighbors": 25,
                }
            ],
            query_time_ms=90,
        )
        mock_service.analyze_network_patterns.return_value = mock_result

        response = client.post(
            "/api/v1/analysis/patterns?node_id=entity_001&pattern_type=hub&max_depth=3&limit=20"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["pattern_type"] == "hub"
        assert len(data["data"]["patterns"]) == 1

    def test_find_common_connections_success(self, client, mock_service):
        """Test successful common connections analysis."""
        mock_result = SearchResult(
            total_count=1,
            returned_count=1,
            offset=0,
            limit=20,
            results=[
                {
                    "common_node": {
                        "node_id": "officer_common",
                        "name": "Common Officer",
                    },
                    "connected_sources": ["entity_001", "entity_002"],
                    "connection_count": 2,
                }
            ],
            query_time_ms=75,
        )
        mock_service.find_common_connections.return_value = mock_result

        payload = {
            "node_ids": ["entity_001", "entity_002"],
            "relationship_types": ["OFFICER_OF"],
        }

        response = client.post(
            "/api/v1/analysis/common-connections?max_depth=2&limit=20", json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["common_connections"]) == 1

    def test_temporal_analysis_success(self, client, mock_service):
        """Test successful temporal analysis."""
        mock_result = SearchResult(
            total_count=1,
            returned_count=1,
            offset=0,
            limit=50,
            results=[
                {
                    "related_node": {
                        "node_id": "entity_temporal",
                        "name": "Related Entity",
                    },
                    "related_date": "2015-06-15",
                    "day_difference": 14,
                }
            ],
            query_time_ms=55,
        )
        mock_service.temporal_analysis.return_value = mock_result

        response = client.post(
            "/api/v1/analysis/temporal?node_id=entity_001&date_field=incorporation_date&time_window_days=365&limit=50"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["temporal_patterns"]) == 1

    def test_compliance_risk_analysis_success(self, client, mock_service):
        """Test successful compliance risk analysis."""
        mock_result = SearchResult(
            total_count=1,
            returned_count=1,
            offset=0,
            limit=30,
            results=[
                {
                    "risky_node": {"node_id": "entity_risky", "name": "Risky Entity"},
                    "distance": 2,
                    "risk_level": "high",
                }
            ],
            query_time_ms=95,
        )
        mock_service.compliance_risk_analysis.return_value = mock_result

        payload = {"risk_jurisdictions": ["British Virgin Islands"]}

        response = client.post(
            "/api/v1/analysis/compliance-risk?node_id=entity_001&max_depth=3&limit=30",
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["risk_analysis"]) == 1


@pytest.mark.unit
class TestExportEndpoints:
    """Test export endpoints."""

    def test_export_search_results_success(self, client, mock_service):
        """Test successful search results export."""
        mock_service.export_results.return_value = {
            "success": True,
            "export_path": "/exports/search_results.csv",
            "format": "csv",
            "record_count": 100,
        }

        payload = {
            "results": [{"node_id": "entity_001", "name": "Test Entity"}],
            "pagination": {"total_count": 100},
        }

        response = client.post(
            "/api/v1/export/search?format=csv&filename=test_export.csv&include_metadata=true",
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["format"] == "csv"
        assert data["data"]["record_count"] == 100

    def test_export_network_visualization_success(self, client, mock_service):
        """Test successful network export."""
        mock_service.export_network_visualization.return_value = {
            "success": True,
            "export_path": "/exports/network.json",
            "format": "d3",
            "node_count": 10,
            "edge_count": 15,
        }

        payload = {
            "results": [
                {
                    "node": {"node_id": "entity_001", "name": "Test Entity"},
                    "distance": 1,
                    "first_relationship": {"type": "OFFICER_OF"},
                }
            ]
        }

        response = client.post(
            "/api/v1/export/network?format=d3&filename=network.json", json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["format"] == "d3"
        assert data["data"]["node_count"] == 10

    def test_export_search_results_failure(self, client, mock_service):
        """Test export failure."""
        mock_service.export_results.side_effect = Exception("Export failed")

        payload = {"results": []}

        response = client.post("/api/v1/export/search?format=json", json=payload)

        assert response.status_code == 500


@pytest.mark.unit
class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "name" in data["data"]
        assert "version" in data["data"]
        assert "endpoints" in data["data"]


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling."""

    def test_database_error_handler(self, client, mock_service):
        """Test database error handling."""
        mock_service.search_entities.side_effect = DatabaseError("Connection failed")

        payload = {"name": "Test"}

        response = client.post("/api/v1/search/entities", json=payload)

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Database error" in data["error"]

    def test_query_error_handler(self, client, mock_service):
        """Test query error handling."""
        mock_service.search_entities.side_effect = QueryError("Invalid query")

        payload = {"name": "Test"}

        response = client.post("/api/v1/search/entities", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Query error" in data["error"]

    def test_validation_error_handler(self, client, mock_service):
        """Test validation error handling."""
        mock_service.search_entities.side_effect = ValueError("Invalid parameters")

        payload = {"name": "Test"}

        response = client.post("/api/v1/search/entities", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert "Validation error" in data["error"]


@pytest.mark.integration
@pytest.mark.asyncio
class TestAPIIntegration:
    """Integration tests for API endpoints."""

    async def test_full_api_workflow(self, mock_service, mock_database, mock_config, mock_load_config, mock_neo4j_init, mock_service_init):
        """Test full API workflow with async client."""

        # Setup mock dependencies
        def get_mock_service():
            return mock_service

        def get_mock_database():
            return mock_database

        def get_mock_config():
            return mock_config

        app.dependency_overrides[get_service] = get_mock_service
        app.dependency_overrides[get_database] = get_mock_database
        app.dependency_overrides[get_config] = get_mock_config

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # Test health check
                mock_database.health_check.return_value = {"connected": True}
                health_response = await client.get("/api/v1/health")
                assert health_response.status_code == 200

                # Test entity search
                mock_service.search_entities.return_value = SearchResult(
                    total_count=1,
                    returned_count=1,
                    offset=0,
                    limit=20,
                    results=[{"node_id": "entity_001", "name": "Test Entity"}],
                    query_time_ms=45,
                )

                search_response = await client.post(
                    "/api/v1/search/entities", json={"name": "Test Entity", "limit": 20}
                )
                assert search_response.status_code == 200
                search_data = search_response.json()
                assert len(search_data["data"]["results"]) == 1

                # Test connections
                mock_service.get_connections.return_value = SearchResult(
                    total_count=1,
                    returned_count=1,
                    offset=0,
                    limit=20,
                    results=[
                        {
                            "node": {
                                "node_id": "entity_002",
                                "name": "Connected Entity",
                            },
                            "distance": 1,
                            "first_relationship": {"type": "OFFICER_OF"},
                        }
                    ],
                    query_time_ms=60,
                )

                connections_response = await client.post(
                    "/api/v1/connections",
                    json={"start_node_id": "entity_001", "max_depth": 2},
                )
                assert connections_response.status_code == 200
                connections_data = connections_response.json()
                assert len(connections_data["data"]["results"]) == 1

        finally:
            # Clean up
            app.dependency_overrides.clear()
