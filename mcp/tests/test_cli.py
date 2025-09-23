"""Tests for the offshore leaks CLI tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rich.console import Console
from typer.testing import CliRunner

from offshore_leaks_mcp.cli.client import APIError, OffshoreLeaksClient
from offshore_leaks_mcp.cli.formatters import CLIFormatter
from offshore_leaks_mcp.cli.main import app


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_client():
    """Create a mock API client."""
    client = MagicMock(spec=OffshoreLeaksClient)
    return client


@pytest.fixture
def mock_console():
    """Create a mock console for formatter testing."""
    return MagicMock(spec=Console)


@pytest.fixture
def formatter(mock_console):
    """Create a formatter with mock console."""
    return CLIFormatter(mock_console)


@pytest.mark.unit
class TestCLIBasicCommands:
    """Test basic CLI commands."""

    def test_version_option(self, runner):
        """Test --version option."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "offshore-cli version" in result.stdout

    def test_help_option(self, runner):
        """Test --help option."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "CLI tool for querying offshore leaks database" in result.stdout
        assert "Commands" in result.stdout

    def test_global_options(self, runner):
        """Test global options parsing."""
        # Test that global options are accepted (even if command fails)
        result = runner.invoke(
            app,
            ["--api-url", "http://test:8000", "--timeout", "60", "--verbose", "health"],
        )

        # Should attempt to run health command with custom options
        # (will fail due to no actual API server, but that's expected)
        assert "--api-url" not in result.stdout  # Options should be consumed


@pytest.mark.unit
class TestHealthCommand:
    """Test health command."""

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_health_command_success(self, mock_create_client, runner):
        """Test successful health check."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_client.health_check.return_value = {
            "status": "healthy",
            "database_connected": True,
            "timestamp": "2024-01-15T10:30:45Z",
        }

        # Setup async context manager
        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        async_context.__aexit__.return_value = None
        mock_create_client.return_value = async_context

        result = runner.invoke(app, ["health"])

        assert result.exit_code == 0
        mock_client.health_check.assert_called_once()

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_health_command_api_error(self, mock_create_client, runner):
        """Test health check with API error."""
        # Setup mock client with error
        mock_client = AsyncMock()
        mock_client.health_check.side_effect = APIError("Connection failed", 500)

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        result = runner.invoke(app, ["health"])

        assert result.exit_code == 1


@pytest.mark.unit
class TestStatsCommand:
    """Test stats command."""

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_stats_command_default(self, mock_create_client, runner):
        """Test stats command with default parameters."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_client.get_statistics.return_value = {
            "stat_type": "overview",
            "results": [
                {"metric": "total_entities", "value": 100000},
                {"metric": "total_officers", "value": 50000},
            ],
            "query_time_ms": 25,
        }

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        result = runner.invoke(app, ["stats"])

        assert result.exit_code == 0
        mock_client.get_statistics.assert_called_once_with("overview")

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_stats_command_custom_type(self, mock_create_client, runner):
        """Test stats command with custom type."""
        mock_client = AsyncMock()
        mock_client.get_statistics.return_value = {
            "stat_type": "entities",
            "results": [{"metric": "entity_count", "value": 50000}],
            "query_time_ms": 15,
        }

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        result = runner.invoke(app, ["stats", "--type", "entities"])

        assert result.exit_code == 0
        mock_client.get_statistics.assert_called_once_with("entities")

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_stats_command_json_format(self, mock_create_client, runner):
        """Test stats command with JSON format."""
        mock_client = AsyncMock()
        mock_client.get_statistics.return_value = {
            "stat_type": "overview",
            "results": [{"metric": "total_entities", "value": 100000}],
            "query_time_ms": 25,
        }

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        result = runner.invoke(app, ["stats", "--format", "json"])

        assert result.exit_code == 0


@pytest.mark.unit
class TestSearchCommands:
    """Test search commands."""

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_search_entities_basic(self, mock_create_client, runner):
        """Test basic entity search."""
        mock_client = AsyncMock()
        mock_client.search_entities.return_value = {
            "results": [
                {
                    "node_id": "entity_001",
                    "name": "Apple Inc BVI",
                    "jurisdiction": "BVI",
                }
            ],
            "pagination": {
                "total_count": 1,
                "returned_count": 1,
                "offset": 0,
                "limit": 20,
                "has_more": False,
            },
            "query_time_ms": 45,
        }

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        result = runner.invoke(app, ["search", "entities", "--name", "Apple"])

        assert result.exit_code == 0
        mock_client.search_entities.assert_called_once()
        args, kwargs = mock_client.search_entities.call_args
        assert kwargs["name"] == "Apple"

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_search_entities_with_options(self, mock_create_client, runner):
        """Test entity search with multiple options."""
        mock_client = AsyncMock()
        mock_client.search_entities.return_value = {
            "results": [],
            "pagination": {
                "total_count": 0,
                "returned_count": 0,
                "offset": 0,
                "limit": 10,
            },
            "query_time_ms": 20,
        }

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        result = runner.invoke(
            app,
            [
                "search",
                "entities",
                "--name",
                "Apple",
                "--jurisdiction",
                "BVI",
                "--status",
                "Active",
                "--limit",
                "10",
            ],
        )

        assert result.exit_code == 0
        args, kwargs = mock_client.search_entities.call_args
        assert kwargs["name"] == "Apple"
        assert kwargs["jurisdiction"] == "BVI"
        assert kwargs["status"] == "Active"
        assert kwargs["limit"] == 10

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_search_officers_basic(self, mock_create_client, runner):
        """Test basic officer search."""
        mock_client = AsyncMock()
        mock_client.search_officers.return_value = {
            "results": [
                {"node_id": "officer_001", "name": "John Smith", "countries": "USA"}
            ],
            "pagination": {
                "total_count": 1,
                "returned_count": 1,
                "offset": 0,
                "limit": 20,
            },
            "query_time_ms": 30,
        }

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        result = runner.invoke(app, ["search", "officers", "--name", "John Smith"])

        assert result.exit_code == 0
        mock_client.search_officers.assert_called_once()

    def test_search_entities_no_parameters(self, runner):
        """Test entity search without required parameters."""
        result = runner.invoke(app, ["search", "entities"])

        assert result.exit_code == 1
        assert "At least one search parameter is required" in result.stdout

    def test_search_officers_no_parameters(self, runner):
        """Test officer search without required parameters."""
        result = runner.invoke(app, ["search", "officers"])

        assert result.exit_code == 1
        assert "At least one search parameter is required" in result.stdout


@pytest.mark.unit
class TestConnectionsCommand:
    """Test connections command."""

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_connections_basic(self, mock_create_client, runner):
        """Test basic connections exploration."""
        mock_client = AsyncMock()
        mock_client.get_connections.return_value = {
            "results": [
                {
                    "node": {"node_id": "entity_002", "name": "Connected Entity"},
                    "distance": 1,
                    "first_relationship": {"type": "OFFICER_OF"},
                }
            ],
            "pagination": {
                "total_count": 1,
                "returned_count": 1,
                "offset": 0,
                "limit": 20,
            },
            "query_time_ms": 60,
        }

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        result = runner.invoke(app, ["connections", "entity_123"])

        assert result.exit_code == 0
        mock_client.get_connections.assert_called_once()
        args, kwargs = mock_client.get_connections.call_args
        assert kwargs["start_node_id"] == "entity_123"

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_connections_with_options(self, mock_create_client, runner):
        """Test connections with advanced options."""
        mock_client = AsyncMock()
        mock_client.get_connections.return_value = {
            "results": [],
            "pagination": {
                "total_count": 0,
                "returned_count": 0,
                "offset": 0,
                "limit": 50,
            },
            "query_time_ms": 40,
        }

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        result = runner.invoke(
            app,
            [
                "connections",
                "entity_123",
                "--max-depth",
                "3",
                "--limit",
                "50",
                "--rel-types",
                "OFFICER_OF,OWNS",
                "--format",
                "table",
            ],
        )

        assert result.exit_code == 0
        args, kwargs = mock_client.get_connections.call_args
        assert kwargs["max_depth"] == 3
        assert kwargs["limit"] == 50
        assert kwargs["relationship_types"] == ["OFFICER_OF", "OWNS"]


@pytest.mark.unit
class TestAnalysisCommands:
    """Test analysis commands."""

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_shortest_paths(self, mock_create_client, runner):
        """Test shortest paths analysis."""
        mock_client = AsyncMock()
        mock_client.find_shortest_paths.return_value = {
            "paths": [
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
            "total_count": 1,
            "query_time_ms": 150,
        }

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        result = runner.invoke(app, ["analysis", "paths", "entity_001", "entity_002"])

        assert result.exit_code == 0
        mock_client.find_shortest_paths.assert_called_once()

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_network_patterns_hub(self, mock_create_client, runner):
        """Test network patterns analysis for hubs."""
        mock_client = AsyncMock()
        mock_client.analyze_network_patterns.return_value = {
            "patterns": [
                {
                    "node": {"node_id": "entity_hub", "name": "Hub Entity"},
                    "connection_count": 25,
                    "total_neighbors": 25,
                }
            ],
            "pattern_type": "hub",
            "total_count": 1,
            "query_time_ms": 90,
        }

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        result = runner.invoke(
            app, ["analysis", "patterns", "entity_001", "--type", "hub"]
        )

        assert result.exit_code == 0
        mock_client.analyze_network_patterns.assert_called_once()

    def test_network_patterns_invalid_type(self, runner):
        """Test network patterns with invalid pattern type."""
        result = runner.invoke(
            app, ["analysis", "patterns", "entity_001", "--type", "invalid"]
        )

        assert result.exit_code == 1
        assert "Pattern type must be one of: hub, bridge, cluster" in result.stdout


@pytest.mark.unit
class TestEntityOfficerCommands:
    """Test individual entity/officer lookup commands."""

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_entity_lookup(self, mock_create_client, runner):
        """Test entity lookup command."""
        mock_client = AsyncMock()
        mock_client.get_entity.return_value = {
            "node_id": "entity_001",
            "name": "Test Entity",
            "jurisdiction": "BVI",
            "status": "Active",
        }

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        result = runner.invoke(app, ["entity", "entity_001"])

        assert result.exit_code == 0
        mock_client.get_entity.assert_called_once_with("entity_001")

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_officer_lookup(self, mock_create_client, runner):
        """Test officer lookup command."""
        mock_client = AsyncMock()
        mock_client.get_officer.return_value = {
            "node_id": "officer_001",
            "name": "John Smith",
            "countries": "USA",
        }

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        result = runner.invoke(app, ["officer", "officer_001"])

        assert result.exit_code == 0
        mock_client.get_officer.assert_called_once_with("officer_001")


@pytest.mark.unit
class TestInteractiveMode:
    """Test interactive mode."""

    @patch("offshore_leaks_mcp.cli.main.create_client")
    @patch("offshore_leaks_mcp.cli.main.Prompt.ask")
    def test_interactive_mode_help(self, mock_prompt, mock_create_client, runner):
        """Test interactive mode help command."""
        mock_client = AsyncMock()
        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        # Simulate user typing 'help' then 'exit'
        mock_prompt.side_effect = ["help", "exit"]

        result = runner.invoke(app, ["interactive"])

        assert result.exit_code == 0
        # Should call prompt twice (help + exit)
        assert mock_prompt.call_count == 2

    @patch("offshore_leaks_mcp.cli.main.create_client")
    @patch("offshore_leaks_mcp.cli.main.Prompt.ask")
    def test_interactive_mode_health(self, mock_prompt, mock_create_client, runner):
        """Test interactive mode health command."""
        mock_client = AsyncMock()
        mock_client.health_check.return_value = {
            "status": "healthy",
            "database_connected": True,
        }

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        # Simulate user typing 'health' then 'exit'
        mock_prompt.side_effect = ["health", "exit"]

        result = runner.invoke(app, ["interactive"])

        assert result.exit_code == 0
        mock_client.health_check.assert_called_once()


@pytest.mark.unit
class TestCLIClient:
    """Test CLI client functionality."""

    @pytest.mark.asyncio
    async def test_client_creation(self):
        """Test client creation."""
        from offshore_leaks_mcp.cli.client import create_client

        client = create_client("http://test:8000", timeout=60)

        assert isinstance(client, OffshoreLeaksClient)
        assert client.base_url == "http://test:8000"
        assert client.timeout == 60

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Test client as async context manager."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_httpx_instance = AsyncMock()
            mock_httpx.return_value = mock_httpx_instance

            client = OffshoreLeaksClient("http://test:8000")

            async with client as c:
                assert c == client
                assert client._client is not None

            # Should call aclose when exiting context
            mock_httpx_instance.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_api_error(self):
        """Test client API error handling."""
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.json.return_value = {"error": "Internal server error"}

            mock_httpx_instance = AsyncMock()
            mock_httpx_instance.request.return_value = mock_response
            mock_httpx.return_value = mock_httpx_instance

            client = OffshoreLeaksClient("http://test:8000")

            async with client:
                with pytest.raises(APIError) as exc_info:
                    await client._request("GET", "/test")

                assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_client_connection_error(self):
        """Test client connection error handling."""
        with patch("httpx.AsyncClient") as mock_httpx:
            from httpx import ConnectError

            mock_httpx_instance = AsyncMock()
            mock_httpx_instance.request.side_effect = ConnectError("Connection failed")
            mock_httpx.return_value = mock_httpx_instance

            client = OffshoreLeaksClient("http://test:8000")

            async with client:
                with pytest.raises(APIError, match="Failed to connect"):
                    await client._request("GET", "/test")


@pytest.mark.unit
class TestCLIFormatters:
    """Test CLI output formatters."""

    def test_format_json(self, formatter, mock_console):
        """Test JSON formatting."""
        test_data = {"test": "data", "number": 123}

        formatter.format_json(test_data, "Test Title")

        # Should print title and JSON
        assert mock_console.print.call_count == 2

    def test_format_table(self, formatter, mock_console):
        """Test table formatting."""
        test_data = [
            {"name": "Entity 1", "jurisdiction": "BVI"},
            {"name": "Entity 2", "jurisdiction": "Cayman"},
        ]

        formatter.format_table(test_data, "Test Table")

        # Should print table
        mock_console.print.assert_called_once()

    def test_format_table_empty(self, formatter, mock_console):
        """Test table formatting with empty data."""
        formatter.format_table([], "Empty Table")

        # Should print "No results found"
        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0]
        assert "No results found" in str(args[0])

    def test_format_entity_results(self, formatter, mock_console):
        """Test entity results formatting."""
        results = {
            "results": [
                {"node_id": "entity_001", "name": "Test Entity", "jurisdiction": "BVI"}
            ],
            "pagination": {"total_count": 100, "returned_count": 1, "offset": 0},
            "query_time_ms": 45,
        }

        formatter.format_entity_results(results)

        # Should print summary, table, and timing
        assert mock_console.print.call_count >= 2

    def test_format_connections_graph(self, formatter, mock_console):
        """Test connections graph formatting."""
        results = {
            "results": [
                {
                    "node": {"node_id": "entity_002", "name": "Connected Entity"},
                    "distance": 1,
                    "first_relationship": {"type": "OFFICER_OF"},
                }
            ],
            "pagination": {"total_count": 1},
            "query_time_ms": 60,
        }

        formatter.format_connections_graph(results)

        # Should print summary, tree, and timing
        assert mock_console.print.call_count >= 2

    def test_print_error(self, formatter, mock_console):
        """Test error message formatting."""
        formatter.print_error("Test error message")

        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0]
        assert "Error" in str(args[0])

    def test_print_success(self, formatter, mock_console):
        """Test success message formatting."""
        formatter.print_success("Test success message")

        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0]
        assert "Success" in str(args[0])


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests for CLI commands."""

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_full_cli_workflow(self, mock_create_client, runner):
        """Test full CLI workflow simulation."""
        mock_client = AsyncMock()

        # Setup health check
        mock_client.health_check.return_value = {
            "status": "healthy",
            "database_connected": True,
        }

        # Setup entity search
        mock_client.search_entities.return_value = {
            "results": [
                {
                    "node_id": "entity_001",
                    "name": "Apple Inc BVI",
                    "jurisdiction": "BVI",
                }
            ],
            "pagination": {
                "total_count": 1,
                "returned_count": 1,
                "offset": 0,
                "limit": 20,
            },
            "query_time_ms": 45,
        }

        # Setup connections
        mock_client.get_connections.return_value = {
            "results": [
                {
                    "node": {"node_id": "entity_002", "name": "Connected Entity"},
                    "distance": 1,
                    "first_relationship": {"type": "OFFICER_OF"},
                }
            ],
            "pagination": {
                "total_count": 1,
                "returned_count": 1,
                "offset": 0,
                "limit": 20,
            },
            "query_time_ms": 60,
        }

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        # Test sequence of commands
        commands = [
            ["health"],
            ["search", "entities", "--name", "Apple"],
            ["connections", "entity_001", "--max-depth", "2"],
        ]

        for command in commands:
            result = runner.invoke(app, command)
            assert result.exit_code == 0

        # Verify all expected calls were made
        mock_client.health_check.assert_called()
        mock_client.search_entities.assert_called()
        mock_client.get_connections.assert_called()


@pytest.mark.unit
class TestErrorScenarios:
    """Test error scenarios in CLI."""

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_api_connection_failure(self, mock_create_client, runner):
        """Test CLI behavior when API connection fails."""
        mock_create_client.side_effect = Exception("Connection refused")

        result = runner.invoke(app, ["health"])

        assert result.exit_code == 1

    @patch("offshore_leaks_mcp.cli.main.create_client")
    def test_api_timeout(self, mock_create_client, runner):
        """Test CLI behavior on API timeout."""
        mock_client = AsyncMock()
        mock_client.health_check.side_effect = APIError("Request timeout")

        async_context = AsyncMock()
        async_context.__aenter__.return_value = mock_client
        mock_create_client.return_value = async_context

        result = runner.invoke(app, ["health"])

        assert result.exit_code == 1

    def test_invalid_command_arguments(self, runner):
        """Test CLI with invalid command arguments."""
        # Test invalid limit
        result = runner.invoke(
            app, ["search", "entities", "--name", "Test", "--limit", "-1"]
        )

        # Should show validation error (exit code may vary based on typer behavior)
        assert "limit" in result.stdout.lower() or result.exit_code != 0
