"""Tests for the offshore leaks service layer."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from offshore_leaks_mcp.database import (
    DatabaseError,
    Neo4jDatabase,
    QueryError,
    QueryResult,
)
from offshore_leaks_mcp.models import (
    SearchResult,
)
from offshore_leaks_mcp.service import OffshoreLeaksService


@pytest.fixture
def mock_database():
    """Create a mock database for testing."""
    database = MagicMock(spec=Neo4jDatabase)
    database.is_connected = True
    return database


@pytest.fixture
def service(mock_database):
    """Create a service instance for testing."""
    return OffshoreLeaksService(mock_database, query_timeout=30)


@pytest.mark.unit
class TestServiceInitialization:
    """Test service initialization."""

    def test_service_init(self, mock_database):
        """Test service initialization."""
        service = OffshoreLeaksService(mock_database, query_timeout=60)

        assert service.database == mock_database
        assert service.query_timeout == 60

    def test_service_init_default_timeout(self, mock_database):
        """Test service initialization with default timeout."""
        service = OffshoreLeaksService(mock_database)

        assert service.query_timeout == 30  # Default value


@pytest.mark.unit
@pytest.mark.asyncio
class TestEntitySearch:
    """Test entity search functionality."""

    async def test_search_entities_success(self, service, mock_database, no_resilience):
        """Test successful entity search."""
        # Mock query result
        mock_records = [
            {
                "e": {
                    "node_id": "entity_001",
                    "name": "Test Company",
                    "jurisdiction": "BVI",
                }
            },
            {
                "e": {
                    "node_id": "entity_002",
                    "name": "Another Company",
                    "jurisdiction": "Cayman",
                }
            },
        ]

        # Mock count result
        mock_count_records = [{"total": 50}]

        # Setup database mocks
        mock_database.execute_query.side_effect = [
            QueryResult(records=mock_records, query_time_ms=45, summary={}),
            QueryResult(records=mock_count_records, query_time_ms=10, summary={}),
        ]

        # Execute search
        result = await service.search_entities(name="Test", limit=10, offset=0)

        # Verify result
        assert isinstance(result, SearchResult)
        assert result.total_count == 50
        assert result.returned_count == 2
        assert result.limit == 10
        assert result.offset == 0
        assert len(result.results) == 2
        assert result.results[0]["node_id"] == "entity_001"
        assert result.query_time_ms == 45

        # Verify database calls
        assert mock_database.execute_query.call_count == 2

    async def test_search_entities_validation_error(
        self, service, mock_database, no_resilience
    ):
        """Test entity search with validation error."""
        with pytest.raises(ValueError, match="Invalid parameters"):
            await service.search_entities(limit=-1)  # Invalid limit

    async def test_search_entities_database_error(
        self, service, mock_database, no_resilience
    ):
        """Test entity search with database error."""
        mock_database.execute_query.side_effect = DatabaseError("Connection failed")

        with pytest.raises(DatabaseError):
            await service.search_entities(name="Test")

    async def test_search_entities_empty_result(
        self, service, mock_database, no_resilience
    ):
        """Test entity search with empty results."""
        # Mock empty results
        mock_database.execute_query.side_effect = [
            QueryResult(records=[], query_time_ms=25, summary={}),
            QueryResult(records=[{"total": 0}], query_time_ms=5, summary={}),
        ]

        result = await service.search_entities(name="NonExistent")

        assert result.total_count == 0
        assert result.returned_count == 0
        assert len(result.results) == 0


@pytest.mark.unit
@pytest.mark.asyncio
class TestOfficerSearch:
    """Test officer search functionality."""

    async def test_search_officers_success(self, service, mock_database, no_resilience):
        """Test successful officer search."""
        # Mock query result
        mock_records = [
            {"o": {"node_id": "officer_001", "name": "John Smith", "countries": "USA"}},
            {"o": {"node_id": "officer_002", "name": "Jane Doe", "countries": "UK"}},
        ]

        # Mock count result
        mock_count_records = [{"total": 25}]

        # Setup database mocks
        mock_database.execute_query.side_effect = [
            QueryResult(records=mock_records, query_time_ms=30, summary={}),
            QueryResult(records=mock_count_records, query_time_ms=8, summary={}),
        ]

        # Execute search
        result = await service.search_officers(name="John", limit=5)

        # Verify result
        assert isinstance(result, SearchResult)
        assert result.total_count == 25
        assert result.returned_count == 2
        assert len(result.results) == 2
        assert result.results[0]["node_id"] == "officer_001"

    async def test_search_officers_validation_error(
        self, service, mock_database, no_resilience
    ):
        """Test officer search with validation error."""
        with pytest.raises(ValueError):
            await service.search_officers(limit=0)  # Invalid limit


@pytest.mark.unit
@pytest.mark.asyncio
class TestConnectionsSearch:
    """Test connections search functionality."""

    async def test_get_connections_success(self, service, mock_database, no_resilience):
        """Test successful connections search."""
        # Mock query result
        mock_records = [
            {
                "connected": {"node_id": "entity_002", "name": "Connected Entity"},
                "distance": 1,
                "first_relationship": {"type": "OFFICER_OF"},
            },
            {
                "connected": {"node_id": "officer_003", "name": "Connected Officer"},
                "distance": 2,
                "first_relationship": {"type": "OWNS"},
            },
        ]

        # Setup database mock
        mock_database.execute_query.return_value = QueryResult(
            records=mock_records, query_time_ms=60, summary={}
        )

        # Execute search
        result = await service.get_connections(
            start_node_id="entity_001", max_depth=2, limit=20
        )

        # Verify result
        assert isinstance(result, SearchResult)
        assert result.total_count == 2
        assert result.returned_count == 2
        assert len(result.results) == 2

        # Verify connection format
        connection = result.results[0]
        assert "node" in connection
        assert "distance" in connection
        assert "first_relationship" in connection
        assert connection["node"]["node_id"] == "entity_002"

    async def test_get_connections_validation_error(
        self, service, mock_database, no_resilience
    ):
        """Test connections search with validation error."""
        with pytest.raises(ValueError):
            await service.get_connections(max_depth=-1)  # Invalid depth


@pytest.mark.unit
@pytest.mark.asyncio
class TestStatistics:
    """Test statistics functionality."""

    async def test_get_statistics_success(self, service, mock_database, no_resilience):
        """Test successful statistics retrieval."""
        # Mock query result
        mock_records = [
            {"metric": "total_entities", "value": 100000},
            {"metric": "total_officers", "value": 50000},
        ]

        mock_database.execute_query.return_value = QueryResult(
            records=mock_records, query_time_ms=15, summary={}
        )

        # Execute request
        result = await service.get_statistics("overview")

        # Verify result
        assert result["stat_type"] == "overview"
        assert result["results"] == mock_records
        assert result["query_time_ms"] == 15

    async def test_get_statistics_database_error(
        self, service, mock_database, no_resilience
    ):
        """Test statistics with database error."""
        mock_database.execute_query.side_effect = DatabaseError("Query failed")

        with pytest.raises(DatabaseError):
            await service.get_statistics("overview")


@pytest.mark.unit
@pytest.mark.asyncio
class TestAdvancedAnalysis:
    """Test advanced analysis functionality."""

    async def test_find_shortest_paths_success(
        self, service, mock_database, no_resilience
    ):
        """Test successful shortest paths analysis."""
        # Mock query result
        mock_records = [
            {
                "path_length": 3,
                "relationship_types": ["OFFICER_OF", "OWNS"],
                "path_nodes": [
                    {"node_id": "entity_001", "name": "Start"},
                    {"node_id": "officer_001", "name": "Middle"},
                    {"node_id": "entity_002", "name": "End"},
                ],
            }
        ]

        mock_database.execute_query.return_value = QueryResult(
            records=mock_records, query_time_ms=120, summary={}
        )

        # Execute request
        result = await service.find_shortest_paths(
            start_node_id="entity_001", end_node_id="entity_002", max_depth=5
        )

        # Verify result
        assert isinstance(result, SearchResult)
        assert len(result.results) == 1
        assert result.results[0]["path_length"] == 3

    async def test_analyze_network_patterns_success(
        self, service, mock_database, no_resilience
    ):
        """Test successful network pattern analysis."""
        # Mock query result
        mock_records = [
            {
                "connected": {"node_id": "entity_hub", "name": "Hub Entity"},
                "connection_count": 25,
                "total_neighbors": 25,
                "relationship_types": ["OFFICER_OF", "OWNS"],
            }
        ]

        mock_database.execute_query.return_value = QueryResult(
            records=mock_records, query_time_ms=90, summary={}
        )

        # Execute request
        result = await service.analyze_network_patterns(
            node_id="entity_001", pattern_type="hub", max_depth=3
        )

        # Verify result
        assert isinstance(result, SearchResult)
        assert len(result.results) == 1
        pattern = result.results[0]
        assert pattern["connection_count"] == 25

    async def test_find_common_connections_success(
        self, service, mock_database, no_resilience
    ):
        """Test successful common connections analysis."""
        # Mock query result
        mock_records = [
            {
                "common": {"node_id": "officer_common", "name": "Common Officer"},
                "connected_sources": ["entity_001", "entity_002"],
                "connection_count": 2,
                "total_neighbors": 10,
                "relationship_types": ["OFFICER_OF"],
            }
        ]

        mock_database.execute_query.return_value = QueryResult(
            records=mock_records, query_time_ms=75, summary={}
        )

        # Execute request
        result = await service.find_common_connections(
            node_ids=["entity_001", "entity_002"], max_depth=2
        )

        # Verify result
        assert isinstance(result, SearchResult)
        assert len(result.results) == 1
        connection = result.results[0]
        assert connection["connection_count"] == 2

    async def test_temporal_analysis_success(
        self, service, mock_database, no_resilience
    ):
        """Test successful temporal analysis."""
        # Mock query result
        mock_records = [
            {
                "related": {"node_id": "entity_temporal", "name": "Related Entity"},
                "related_date": "2015-06-15",
                "day_diff": 14,
                "node_types": ["Entity"],
                "temporal_relationship": "same_period",
            }
        ]

        mock_database.execute_query.return_value = QueryResult(
            records=mock_records, query_time_ms=55, summary={}
        )

        # Execute request
        result = await service.temporal_analysis(
            node_id="entity_001", date_field="incorporation_date", time_window_days=365
        )

        # Verify result
        assert isinstance(result, SearchResult)
        assert len(result.results) == 1
        temporal = result.results[0]
        assert temporal["day_difference"] == 14

    async def test_compliance_risk_analysis_success(
        self, service, mock_database, no_resilience
    ):
        """Test successful compliance risk analysis."""
        # Mock query result
        mock_records = [
            {
                "risky": {"node_id": "entity_risky", "name": "Risky Entity"},
                "distance": 2,
                "risk_level": "high",
                "jurisdiction": "British Virgin Islands",
                "connection_count": 5,
                "relationship_types": ["OFFICER_OF", "OWNS"],
                "connected_types": ["Entity", "Officer"],
            }
        ]

        mock_database.execute_query.return_value = QueryResult(
            records=mock_records, query_time_ms=95, summary={}
        )

        # Execute request
        result = await service.compliance_risk_analysis(
            node_id="entity_001",
            risk_jurisdictions=["British Virgin Islands"],
            max_depth=3,
        )

        # Verify result
        assert isinstance(result, SearchResult)
        assert len(result.results) == 1
        risk = result.results[0]
        assert risk["risk_level"] == "high"


@pytest.mark.unit
@pytest.mark.asyncio
class TestExportFunctions:
    """Test export functionality."""

    async def test_export_results_success(self, service, mock_database, no_resilience):
        """Test successful export of results."""
        test_data = {
            "results": [{"node_id": "entity_001", "name": "Test Entity"}],
            "total_count": 1,
        }

        with patch("offshore_leaks_mcp.exporters.DataExporter") as mock_exporter_class:
            mock_exporter = MagicMock()
            mock_exporter.export_to_json.return_value = "/path/to/export.json"
            mock_exporter_class.return_value = mock_exporter

            result = await service.export_results(
                data=test_data, format="json", filename="test_export.json"
            )

            assert result["success"] is True
            assert result["export_path"] == "/path/to/export.json"
            assert result["format"] == "json"
            assert result["record_count"] == 1

    async def test_export_results_failure(self, service, mock_database, no_resilience):
        """Test export failure."""
        test_data = {"results": []}

        with patch("offshore_leaks_mcp.exporters.DataExporter") as mock_exporter_class:
            mock_exporter = MagicMock()
            mock_exporter.export_to_json.side_effect = Exception("Export failed")
            mock_exporter_class.return_value = mock_exporter

            result = await service.export_results(data=test_data, format="json")

            assert result["success"] is False
            assert "Export failed" in result["error"]

    async def test_export_network_visualization_success(
        self, service, mock_database, no_resilience
    ):
        """Test successful network export."""
        connections_data = {
            "results": [
                {
                    "node": {"node_id": "entity_001", "name": "Test Entity"},
                    "distance": 1,
                    "first_relationship": {"type": "OFFICER_OF"},
                }
            ]
        }

        with (
            patch("offshore_leaks_mcp.exporters.NetworkVisualizer") as mock_viz_class,
            patch("offshore_leaks_mcp.exporters.DataExporter") as mock_exporter_class,
        ):
            mock_visualizer = MagicMock()
            mock_visualizer.prepare_network_data.return_value = {
                "nodes": [{"id": "entity_001", "name": "Test Entity"}],
                "edges": [],
            }
            mock_viz_class.return_value = mock_visualizer

            mock_exporter = MagicMock()
            mock_exporter.export_to_json.return_value = "/path/to/network.json"
            mock_exporter_class.return_value = mock_exporter

            result = await service.export_network_visualization(
                connections_data=connections_data, format="d3"
            )

            assert result["success"] is True
            assert result["export_path"] == "/path/to/network.json"
            assert result["format"] == "d3"
            assert result["node_count"] == 1

    async def test_create_investigation_report_success(
        self, service, mock_database, no_resilience
    ):
        """Test successful investigation report creation."""
        investigation_data = {
            "query_count": 5,
            "total_results": 100,
            "entities": [],
            "officers": [],
        }

        with patch("offshore_leaks_mcp.exporters.DataExporter") as mock_exporter_class:
            mock_exporter = MagicMock()
            mock_exporter.create_investigation_report.return_value = (
                "/path/to/report.html"
            )
            mock_exporter_class.return_value = mock_exporter

            result = await service.create_investigation_report(
                investigation_data=investigation_data,
                filename="investigation_report.html",
            )

            assert result["success"] is True
            assert result["report_path"] == "/path/to/report.html"
            assert result["total_queries"] == 5
            assert result["total_results"] == 100


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling in service layer."""

    @pytest.mark.asyncio
    async def test_search_entities_exception_handling(
        self, service, mock_database, no_resilience
    ):
        """Test exception handling in entity search."""
        mock_database.execute_query.side_effect = Exception("Unexpected error")

        with pytest.raises(Exception, match="Unexpected error"):
            await service.search_entities(name="Test")

    @pytest.mark.asyncio
    async def test_search_officers_exception_handling(
        self, service, mock_database, no_resilience
    ):
        """Test exception handling in officer search."""
        mock_database.execute_query.side_effect = QueryError("Query syntax error")

        with pytest.raises(QueryError):
            await service.search_officers(name="Test")

    @pytest.mark.asyncio
    async def test_get_connections_exception_handling(
        self, service, mock_database, no_resilience
    ):
        """Test exception handling in connections search."""
        mock_database.execute_query.side_effect = DatabaseError(
            "Database connection lost"
        )

        with pytest.raises(DatabaseError):
            await service.get_connections(start_node_id="entity_001")


@pytest.mark.integration
@pytest.mark.asyncio
class TestServiceIntegration:
    """Integration tests for service layer."""

    async def test_complete_search_workflow(self, test_config, no_resilience):
        """Test complete search workflow using service layer."""
        with patch("offshore_leaks_mcp.service.Neo4jDatabase") as mock_db_class:
            # Setup mock database
            mock_database = MagicMock()
            mock_database.is_connected = True
            mock_db_class.return_value = mock_database

            # Setup service
            service = OffshoreLeaksService(mock_database, query_timeout=30)

            # Mock entity search - use AsyncMock to return awaitable results
            entity_result = QueryResult(
                records=[{"e": {"node_id": "entity_001", "name": "Test Entity"}}],
                query_time_ms=45,
                summary={},
            )
            count_result = QueryResult(
                records=[{"total": 1}], query_time_ms=10, summary={}
            )
            mock_database.execute_query = AsyncMock(
                side_effect=[entity_result, count_result]
            )

            # Execute entity search
            entities = await service.search_entities(name="Test", limit=10)
            assert entities.total_count == 1
            assert len(entities.results) == 1

            # Reset mock for connections search
            connection_result = QueryResult(
                records=[
                    {
                        "connected": {"node_id": "officer_001", "name": "Test Officer"},
                        "distance": 1,
                        "first_relationship": {"type": "OFFICER_OF"},
                    }
                ],
                query_time_ms=60,
                summary={},
            )
            mock_database.execute_query = AsyncMock(return_value=connection_result)

            # Execute connections search
            connections = await service.get_connections(
                start_node_id="entity_001", max_depth=2
            )
            assert len(connections.results) == 1
