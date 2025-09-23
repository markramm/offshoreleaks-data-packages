"""Main CLI interface for offshore leaks tool."""

import asyncio
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.prompt import Prompt

from .client import APIError, OffshoreLeaksClient, create_client
from .formatters import CLIFormatter

# Create Typer app
app = typer.Typer(
    name="offshore-cli",
    help="CLI tool for querying offshore leaks database",
    add_completion=False,
    rich_markup_mode="rich",
)

# Global console and formatter
console = Console()
formatter = CLIFormatter(console)

# Global client settings
DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 30


def version_callback(value: bool):
    """Show version information."""
    if value:
        console.print("offshore-cli version 1.0.0")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version", callback=version_callback, help="Show version information"
        ),
    ] = None,
    api_url: Annotated[
        str, typer.Option("--api-url", help="API server URL")
    ] = DEFAULT_API_URL,
    timeout: Annotated[
        int, typer.Option("--timeout", help="Request timeout in seconds")
    ] = DEFAULT_TIMEOUT,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
):
    """Offshore Leaks CLI - Query the offshore leaks database."""
    # Store settings in context
    ctx.ensure_object(dict)
    ctx.obj["api_url"] = api_url
    ctx.obj["timeout"] = timeout
    ctx.obj["verbose"] = verbose


async def run_with_client(ctx: typer.Context, func, *args, **kwargs):
    """Run an async function with API client."""
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    if verbose:
        formatter.print_info(f"Connecting to API at {api_url}")

    try:
        async with create_client(api_url, timeout) as client:
            return await func(client, *args, **kwargs)
    except APIError as e:
        formatter.print_error(f"API Error: {e}")
        if e.status_code:
            formatter.print_error(f"Status Code: {e.status_code}")
        raise typer.Exit(1) from e
    except Exception as e:
        formatter.print_error(f"Unexpected error: {e}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1) from e


@app.command()
def health(ctx: typer.Context):
    """Check API server health."""

    async def check_health(client: OffshoreLeaksClient):
        health_data = await client.health_check()
        formatter.format_health_check(health_data)

    asyncio.run(run_with_client(ctx, check_health))


@app.command()
def stats(
    ctx: typer.Context,
    stat_type: Annotated[
        str, typer.Option("--type", help="Type of statistics to retrieve")
    ] = "overview",
    format: Annotated[
        str, typer.Option("--format", help="Output format (table/json)")
    ] = "table",
):
    """Get database statistics."""

    async def get_stats(client: OffshoreLeaksClient):
        stats_data = await client.get_statistics(stat_type)

        if format == "json":
            formatter.format_json(stats_data, "Database Statistics")
        else:
            formatter.format_statistics(stats_data)

    asyncio.run(run_with_client(ctx, get_stats))


# Search commands
search_app = typer.Typer(name="search", help="Search entities and officers")
app.add_typer(search_app)


@search_app.command("entities")
def search_entities(
    ctx: typer.Context,
    name: Annotated[
        Optional[str], typer.Option("--name", "-n", help="Entity name to search for")
    ] = None,
    jurisdiction: Annotated[
        Optional[str], typer.Option("--jurisdiction", "-j", help="Jurisdiction filter")
    ] = None,
    status: Annotated[
        Optional[str], typer.Option("--status", "-s", help="Entity status filter")
    ] = None,
    country_codes: Annotated[
        Optional[str], typer.Option("--country-codes", help="Country codes filter")
    ] = None,
    company_type: Annotated[
        Optional[str], typer.Option("--company-type", help="Company type filter")
    ] = None,
    source: Annotated[
        Optional[str], typer.Option("--source", help="Data source filter")
    ] = None,
    limit: Annotated[
        int, typer.Option("--limit", "-l", help="Maximum number of results")
    ] = 20,
    offset: Annotated[
        int, typer.Option("--offset", help="Result offset for pagination")
    ] = 0,
    format: Annotated[
        str, typer.Option("--format", help="Output format (table/json)")
    ] = "table",
    export: Annotated[
        Optional[str], typer.Option("--export", help="Export format (json/csv)")
    ] = None,
    output: Annotated[
        Optional[str], typer.Option("--output", "-o", help="Output file path")
    ] = None,
):
    """Search for offshore entities."""

    if not any([name, jurisdiction, status, country_codes, company_type, source]):
        formatter.print_error("At least one search parameter is required")
        raise typer.Exit(1) from e

    async def search(client: OffshoreLeaksClient):
        results = await client.search_entities(
            name=name,
            jurisdiction=jurisdiction,
            status=status,
            country_codes=country_codes,
            company_type=company_type,
            source=source,
            limit=limit,
            offset=offset,
        )

        if format == "json":
            formatter.format_json(results, "Entity Search Results")
        else:
            formatter.format_entity_results(results)

        # Handle export
        if export and results.get("results"):
            if not output:
                output_file = f"entities_export.{export}"
            else:
                output_file = output

            try:
                export_result = await client.export_search_results(
                    results, format=export, filename=output_file
                )
                formatter.format_export_results(export_result)
            except Exception as e:
                formatter.print_error(f"Export failed: {e}")

    asyncio.run(run_with_client(ctx, search))


@search_app.command("officers")
def search_officers(
    ctx: typer.Context,
    name: Annotated[
        Optional[str], typer.Option("--name", "-n", help="Officer name to search for")
    ] = None,
    countries: Annotated[
        Optional[str], typer.Option("--countries", "-c", help="Countries filter")
    ] = None,
    country_codes: Annotated[
        Optional[str], typer.Option("--country-codes", help="Country codes filter")
    ] = None,
    source: Annotated[
        Optional[str], typer.Option("--source", help="Data source filter")
    ] = None,
    limit: Annotated[
        int, typer.Option("--limit", "-l", help="Maximum number of results")
    ] = 20,
    offset: Annotated[
        int, typer.Option("--offset", help="Result offset for pagination")
    ] = 0,
    format: Annotated[
        str, typer.Option("--format", help="Output format (table/json)")
    ] = "table",
    export: Annotated[
        Optional[str], typer.Option("--export", help="Export format (json/csv)")
    ] = None,
    output: Annotated[
        Optional[str], typer.Option("--output", "-o", help="Output file path")
    ] = None,
):
    """Search for officers."""

    if not any([name, countries, country_codes, source]):
        formatter.print_error("At least one search parameter is required")
        raise typer.Exit(1) from e

    async def search(client: OffshoreLeaksClient):
        results = await client.search_officers(
            name=name,
            countries=countries,
            country_codes=country_codes,
            source=source,
            limit=limit,
            offset=offset,
        )

        if format == "json":
            formatter.format_json(results, "Officer Search Results")
        else:
            formatter.format_officer_results(results)

        # Handle export
        if export and results.get("results"):
            if not output:
                output_file = f"officers_export.{export}"
            else:
                output_file = output

            try:
                export_result = await client.export_search_results(
                    results, format=export, filename=output_file
                )
                formatter.format_export_results(export_result)
            except Exception as e:
                formatter.print_error(f"Export failed: {e}")

    asyncio.run(run_with_client(ctx, search))


# Connection commands
@app.command()
def connections(
    ctx: typer.Context,
    start_node: Annotated[
        str, typer.Argument(help="Starting node ID for connection exploration")
    ],
    max_depth: Annotated[
        int, typer.Option("--max-depth", "-d", help="Maximum depth for exploration")
    ] = 2,
    limit: Annotated[
        int, typer.Option("--limit", "-l", help="Maximum number of results")
    ] = 20,
    relationship_types: Annotated[
        Optional[str],
        typer.Option("--rel-types", help="Comma-separated relationship types"),
    ] = None,
    node_types: Annotated[
        Optional[str], typer.Option("--node-types", help="Comma-separated node types")
    ] = None,
    format: Annotated[
        str, typer.Option("--format", help="Output format (graph/table/json)")
    ] = "graph",
    export: Annotated[
        Optional[str], typer.Option("--export", help="Export format (json/d3/gexf)")
    ] = None,
    output: Annotated[
        Optional[str], typer.Option("--output", "-o", help="Output file path")
    ] = None,
):
    """Explore connections from a starting node."""

    async def explore(client: OffshoreLeaksClient):
        # Parse comma-separated lists
        rel_types_list = relationship_types.split(",") if relationship_types else None
        node_types_list = node_types.split(",") if node_types else None

        results = await client.get_connections(
            start_node_id=start_node,
            max_depth=max_depth,
            limit=limit,
            relationship_types=rel_types_list,
            node_types=node_types_list,
        )

        if format == "json":
            formatter.format_json(results, "Connection Results")
        elif format == "table":
            formatter.format_connections_table(results)
        else:  # graph
            formatter.format_connections_graph(results)

        # Handle export
        if export and results.get("results"):
            if not output:
                output_file = f"connections_export.{export}"
            else:
                output_file = output

            try:
                export_result = await client.export_network_visualization(
                    results, format=export, filename=output_file
                )
                formatter.format_export_results(export_result)
            except Exception as e:
                formatter.print_error(f"Export failed: {e}")

    asyncio.run(run_with_client(ctx, explore))


# Analysis commands
analysis_app = typer.Typer(name="analysis", help="Advanced network analysis")
app.add_typer(analysis_app)


@analysis_app.command("paths")
def shortest_paths(
    ctx: typer.Context,
    start_node: Annotated[str, typer.Argument(help="Starting node ID")],
    end_node: Annotated[str, typer.Argument(help="Ending node ID")],
    max_depth: Annotated[
        int, typer.Option("--max-depth", "-d", help="Maximum path depth")
    ] = 6,
    limit: Annotated[
        int, typer.Option("--limit", "-l", help="Maximum number of paths")
    ] = 10,
    relationship_types: Annotated[
        Optional[str],
        typer.Option("--rel-types", help="Comma-separated relationship types"),
    ] = None,
    format: Annotated[
        str, typer.Option("--format", help="Output format (table/json)")
    ] = "table",
):
    """Find shortest paths between two nodes."""

    async def find_paths(client: OffshoreLeaksClient):
        rel_types_list = relationship_types.split(",") if relationship_types else None

        results = await client.find_shortest_paths(
            start_node_id=start_node,
            end_node_id=end_node,
            max_depth=max_depth,
            limit=limit,
            relationship_types=rel_types_list,
        )

        formatter.format_analysis_results(results, "path")

    asyncio.run(run_with_client(ctx, find_paths))


@analysis_app.command("patterns")
def network_patterns(
    ctx: typer.Context,
    node_id: Annotated[str, typer.Argument(help="Node ID to analyze")],
    pattern_type: Annotated[
        str, typer.Option("--type", help="Pattern type (hub/bridge/cluster)")
    ] = "hub",
    max_depth: Annotated[
        int, typer.Option("--max-depth", "-d", help="Maximum analysis depth")
    ] = 3,
    min_connections: Annotated[
        int, typer.Option("--min-connections", help="Minimum connections threshold")
    ] = 5,
    limit: Annotated[
        int, typer.Option("--limit", "-l", help="Maximum number of results")
    ] = 20,
):
    """Analyze network patterns around a node."""

    if pattern_type not in ["hub", "bridge", "cluster"]:
        formatter.print_error("Pattern type must be one of: hub, bridge, cluster")
        raise typer.Exit(1) from e

    async def analyze_patterns(client: OffshoreLeaksClient):
        results = await client.analyze_network_patterns(
            node_id=node_id,
            pattern_type=pattern_type,
            max_depth=max_depth,
            min_connections=min_connections,
            limit=limit,
        )

        formatter.format_analysis_results(results, "pattern")

    asyncio.run(run_with_client(ctx, analyze_patterns))


# Detail commands
@app.command()
def entity(
    ctx: typer.Context,
    entity_id: Annotated[str, typer.Argument(help="Entity ID to retrieve")],
    format: Annotated[
        str, typer.Option("--format", help="Output format (detail/json)")
    ] = "detail",
):
    """Get detailed entity information."""

    async def get_entity(client: OffshoreLeaksClient):
        entity_data = await client.get_entity(entity_id)

        if format == "json":
            formatter.format_json(entity_data, "Entity Details")
        else:
            formatter.format_entity_detail(entity_data)

    asyncio.run(run_with_client(ctx, get_entity))


@app.command()
def officer(
    ctx: typer.Context,
    officer_id: Annotated[str, typer.Argument(help="Officer ID to retrieve")],
    format: Annotated[
        str, typer.Option("--format", help="Output format (detail/json)")
    ] = "detail",
):
    """Get detailed officer information."""

    async def get_officer(client: OffshoreLeaksClient):
        officer_data = await client.get_officer(officer_id)

        if format == "json":
            formatter.format_json(officer_data, "Officer Details")
        else:
            formatter.format_officer_detail(officer_data)

    asyncio.run(run_with_client(ctx, get_officer))


# Interactive mode
@app.command()
def interactive(ctx: typer.Context):
    """Start interactive mode for exploratory analysis."""

    async def interactive_session(client: OffshoreLeaksClient):
        formatter.print_success(
            "Starting interactive mode. Type 'help' for commands or 'exit' to quit."
        )

        while True:
            try:
                command = Prompt.ask(
                    "\n[bold cyan]offshore-cli>[/bold cyan]", default="help"
                )

                if command.lower() in ["exit", "quit", "q"]:
                    formatter.print_info("Goodbye!")
                    break
                elif command.lower() == "help":
                    show_interactive_help()
                elif command.lower() == "health":
                    health_data = await client.health_check()
                    formatter.format_health_check(health_data)
                elif command.lower().startswith("search entities"):
                    formatter.print_info(
                        "Interactive entity search not implemented yet"
                    )
                elif command.lower().startswith("search officers"):
                    formatter.print_info(
                        "Interactive officer search not implemented yet"
                    )
                else:
                    formatter.print_warning(f"Unknown command: {command}")
                    formatter.print_info("Type 'help' for available commands")

            except KeyboardInterrupt:
                formatter.print_info("\nUse 'exit' to quit")
            except EOFError:
                formatter.print_info("\nGoodbye!")
                break

    def show_interactive_help():
        help_text = """
[bold cyan]Available Commands:[/bold cyan]

[yellow]health[/yellow]           - Check API server health
[yellow]search entities[/yellow]  - Search for entities (interactive)
[yellow]search officers[/yellow]  - Search for officers (interactive)
[yellow]help[/yellow]             - Show this help message
[yellow]exit[/yellow]             - Exit interactive mode

[dim]Note: Interactive search commands are not fully implemented yet.
Use the regular CLI commands for full functionality.[/dim]
        """
        console.print(help_text)

    asyncio.run(run_with_client(ctx, interactive_session))


if __name__ == "__main__":
    app()
