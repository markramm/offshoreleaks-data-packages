"""Output formatters for the CLI tool."""

import json
from typing import Any, Optional

from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree


class CLIFormatter:
    """Base formatter for CLI output."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize the formatter."""
        self.console = console or Console()

    def format_json(self, data: Any, title: Optional[str] = None) -> None:
        """Format data as JSON."""
        if title:
            self.console.print(f"\n[bold cyan]{title}[/bold cyan]")

        json_text = JSON(json.dumps(data, indent=2, default=str))
        self.console.print(json_text)

    def format_table(
        self,
        data: list[dict[str, Any]],
        title: Optional[str] = None,
        columns: Optional[list[str]] = None,
    ) -> None:
        """Format data as a table."""
        if not data:
            self.console.print("[yellow]No results found[/yellow]")
            return

        if not columns:
            # Auto-detect columns from first row
            columns = list(data[0].keys())

        table = Table(title=title, show_header=True, header_style="bold magenta")

        # Add columns
        for column in columns:
            table.add_column(
                column.replace("_", " ").title(), style="cyan", no_wrap=False
            )

        # Add rows
        for row in data:
            values = []
            for column in columns:
                value = row.get(column, "")
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, default=str)
                elif value is None:
                    value = ""
                values.append(str(value))
            table.add_row(*values)

        self.console.print(table)

    def format_entity_results(self, results: dict[str, Any]) -> None:
        """Format entity search results."""
        pagination = results.get("pagination", {})
        entities = results.get("results", [])

        # Summary
        total = pagination.get("total_count", 0)
        returned = pagination.get("returned_count", 0)
        offset = pagination.get("offset", 0)

        summary = f"Found {total} entities, showing {returned} (offset: {offset})"
        self.console.print(f"\n[bold green]{summary}[/bold green]")

        if not entities:
            return

        # Format as table with key columns
        columns = ["node_id", "name", "jurisdiction", "status", "sourceID"]
        self.format_table(entities, title="Entity Search Results", columns=columns)

        # Show query time if available
        query_time = results.get("query_time_ms")
        if query_time:
            self.console.print(f"\n[dim]Query completed in {query_time}ms[/dim]")

    def format_officer_results(self, results: dict[str, Any]) -> None:
        """Format officer search results."""
        pagination = results.get("pagination", {})
        officers = results.get("results", [])

        # Summary
        total = pagination.get("total_count", 0)
        returned = pagination.get("returned_count", 0)
        offset = pagination.get("offset", 0)

        summary = f"Found {total} officers, showing {returned} (offset: {offset})"
        self.console.print(f"\n[bold green]{summary}[/bold green]")

        if not officers:
            return

        # Format as table with key columns
        columns = ["node_id", "name", "countries", "sourceID"]
        self.format_table(officers, title="Officer Search Results", columns=columns)

        # Show query time if available
        query_time = results.get("query_time_ms")
        if query_time:
            self.console.print(f"\n[dim]Query completed in {query_time}ms[/dim]")

    def format_connections_graph(self, results: dict[str, Any]) -> None:
        """Format connections as ASCII graph."""
        connections = results.get("results", [])

        if not connections:
            self.console.print("[yellow]No connections found[/yellow]")
            return

        total = results.get("pagination", {}).get("total_count", len(connections))
        self.console.print(f"\n[bold green]Found {total} connections[/bold green]")

        # Create tree structure
        tree = Tree("[bold cyan]Connection Graph[/bold cyan]")

        # Group connections by distance
        by_distance = {}
        for conn in connections:
            distance = conn.get("distance", 0)
            if distance not in by_distance:
                by_distance[distance] = []
            by_distance[distance].append(conn)

        # Build tree
        for distance in sorted(by_distance.keys()):
            distance_branch = tree.add(f"[yellow]Distance {distance}[/yellow]")

            for conn in by_distance[distance]:
                node = conn.get("node", {})
                rel_type = conn.get("first_relationship", {}).get("type", "CONNECTED")

                node_name = node.get("name", node.get("node_id", "Unknown"))
                node_type = "Entity" if "jurisdiction" in node else "Officer"

                connection_text = f"[cyan]{node_name}[/cyan] ([dim]{node_type}[/dim]) via [green]{rel_type}[/green]"
                distance_branch.add(connection_text)

        self.console.print(tree)

        # Show query time if available
        query_time = results.get("query_time_ms")
        if query_time:
            self.console.print(f"\n[dim]Query completed in {query_time}ms[/dim]")

    def format_connections_table(self, results: dict[str, Any]) -> None:
        """Format connections as table."""
        connections = results.get("results", [])

        if not connections:
            self.console.print("[yellow]No connections found[/yellow]")
            return

        total = results.get("pagination", {}).get("total_count", len(connections))
        self.console.print(f"\n[bold green]Found {total} connections[/bold green]")

        # Flatten connection data for table display
        table_data = []
        for conn in connections:
            node = conn.get("node", {})
            rel = conn.get("first_relationship", {})

            table_data.append(
                {
                    "distance": conn.get("distance", 0),
                    "node_id": node.get("node_id", ""),
                    "name": node.get("name", ""),
                    "node_type": "Entity" if "jurisdiction" in node else "Officer",
                    "relationship": rel.get("type", ""),
                    "jurisdiction": node.get("jurisdiction", node.get("countries", "")),
                }
            )

        columns = ["distance", "name", "node_type", "relationship", "jurisdiction"]
        self.format_table(table_data, title="Connection Results", columns=columns)

        # Show query time if available
        query_time = results.get("query_time_ms")
        if query_time:
            self.console.print(f"\n[dim]Query completed in {query_time}ms[/dim]")

    def format_entity_detail(self, entity: dict[str, Any]) -> None:
        """Format detailed entity information."""
        panel_content = []

        # Basic information
        panel_content.append(
            f"[bold cyan]Name:[/bold cyan] {entity.get('name', 'N/A')}"
        )
        panel_content.append(
            f"[bold cyan]Node ID:[/bold cyan] {entity.get('node_id', 'N/A')}"
        )
        panel_content.append(
            f"[bold cyan]Jurisdiction:[/bold cyan] {entity.get('jurisdiction', 'N/A')}"
        )
        panel_content.append(
            f"[bold cyan]Status:[/bold cyan] {entity.get('status', 'N/A')}"
        )
        panel_content.append(
            f"[bold cyan]Source:[/bold cyan] {entity.get('sourceID', 'N/A')}"
        )

        # Additional fields
        if entity.get("incorporation_date"):
            panel_content.append(
                f"[bold cyan]Incorporation Date:[/bold cyan] {entity['incorporation_date']}"
            )

        if entity.get("company_type"):
            panel_content.append(
                f"[bold cyan]Company Type:[/bold cyan] {entity['company_type']}"
            )

        # Create panel
        panel = Panel(
            "\n".join(panel_content),
            title="[bold magenta]Entity Details[/bold magenta]",
            border_style="cyan",
        )

        self.console.print(panel)

    def format_officer_detail(self, officer: dict[str, Any]) -> None:
        """Format detailed officer information."""
        panel_content = []

        # Basic information
        panel_content.append(
            f"[bold cyan]Name:[/bold cyan] {officer.get('name', 'N/A')}"
        )
        panel_content.append(
            f"[bold cyan]Node ID:[/bold cyan] {officer.get('node_id', 'N/A')}"
        )
        panel_content.append(
            f"[bold cyan]Countries:[/bold cyan] {officer.get('countries', 'N/A')}"
        )
        panel_content.append(
            f"[bold cyan]Source:[/bold cyan] {officer.get('sourceID', 'N/A')}"
        )

        # Additional fields
        if officer.get("country_codes"):
            panel_content.append(
                f"[bold cyan]Country Codes:[/bold cyan] {officer['country_codes']}"
            )

        # Create panel
        panel = Panel(
            "\n".join(panel_content),
            title="[bold magenta]Officer Details[/bold magenta]",
            border_style="cyan",
        )

        self.console.print(panel)

    def format_statistics(self, stats: dict[str, Any]) -> None:
        """Format database statistics."""
        stat_type = stats.get("stat_type", "overview")
        results = stats.get("results", [])

        self.console.print(
            f"\n[bold green]Database Statistics ({stat_type})[/bold green]"
        )

        if not results:
            self.console.print("[yellow]No statistics available[/yellow]")
            return

        # Format as table
        self.format_table(results, title=f"Statistics - {stat_type.title()}")

        # Show query time if available
        query_time = stats.get("query_time_ms")
        if query_time:
            self.console.print(f"\n[dim]Query completed in {query_time}ms[/dim]")

    def format_health_check(self, health: dict[str, Any]) -> None:
        """Format health check results."""
        status = health.get("status", "unknown")
        db_connected = health.get("database_connected", False)

        # Status indicator
        if status == "healthy":
            status_text = "[bold green]✓ Healthy[/bold green]"
        else:
            status_text = "[bold red]✗ Unhealthy[/bold red]"

        # Database status
        if db_connected:
            db_text = "[bold green]✓ Connected[/bold green]"
        else:
            db_text = "[bold red]✗ Disconnected[/bold red]"

        panel_content = [
            f"[bold cyan]API Status:[/bold cyan] {status_text}",
            f"[bold cyan]Database:[/bold cyan] {db_text}",
        ]

        if health.get("timestamp"):
            panel_content.append(
                f"[bold cyan]Timestamp:[/bold cyan] {health['timestamp']}"
            )

        panel = Panel(
            "\n".join(panel_content),
            title="[bold magenta]Health Check[/bold magenta]",
            border_style="green" if status == "healthy" else "red",
        )

        self.console.print(panel)

    def format_analysis_results(
        self, results: dict[str, Any], analysis_type: str
    ) -> None:
        """Format analysis results."""
        data = results.get(
            f"{analysis_type}_analysis",
            results.get("patterns", results.get("paths", [])),
        )

        if not data:
            self.console.print(
                f"[yellow]No {analysis_type} analysis results found[/yellow]"
            )
            return

        total = results.get("total_count", len(data))
        self.console.print(
            f"\n[bold green]{analysis_type.title()} Analysis - Found {total} results[/bold green]"
        )

        # Format as table or JSON depending on complexity
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Try to format as table if data structure is simple
            columns = list(data[0].keys())
            if len(columns) <= 6:  # Simple enough for table
                self.format_table(
                    data, title=f"{analysis_type.title()} Analysis Results"
                )
            else:
                self.format_json(data, f"{analysis_type.title()} Analysis Results")
        else:
            self.format_json(data, f"{analysis_type.title()} Analysis Results")

        # Show query time if available
        query_time = results.get("query_time_ms")
        if query_time:
            self.console.print(f"\n[dim]Query completed in {query_time}ms[/dim]")

    def format_export_results(self, export_result: dict[str, Any]) -> None:
        """Format export operation results."""
        if export_result.get("success"):
            export_path = export_result.get("export_path")
            format_type = export_result.get("format")
            record_count = export_result.get(
                "record_count", export_result.get("node_count", 0)
            )

            self.console.print("\n[bold green]✓ Export successful![/bold green]")
            self.console.print(f"[cyan]Format:[/cyan] {format_type}")
            self.console.print(f"[cyan]File:[/cyan] {export_path}")
            self.console.print(f"[cyan]Records:[/cyan] {record_count}")
        else:
            error = export_result.get("error", "Unknown error")
            self.console.print(f"\n[bold red]✗ Export failed:[/bold red] {error}")

    def print_error(self, message: str) -> None:
        """Print error message."""
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message."""
        self.console.print(f"[bold yellow]Warning:[/bold yellow] {message}")

    def print_info(self, message: str) -> None:
        """Print info message."""
        self.console.print(f"[bold blue]Info:[/bold blue] {message}")

    def print_success(self, message: str) -> None:
        """Print success message."""
        self.console.print(f"[bold green]Success:[/bold green] {message}")

    def create_progress(self, description: str) -> Progress:
        """Create a progress indicator."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        )
