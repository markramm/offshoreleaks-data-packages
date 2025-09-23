"""MCP protocol implementation for the offshore leaks server."""

import asyncio
import logging
import sys
from typing import Any, Dict, List, Optional

# Check if MCP is available (Python 3.10+)
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        EmbeddedResource,
        ImageContent,
        LoggingLevel,
        Resource,
        TextContent,
        Tool,
    )

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

    # Create placeholder classes for type hints
    class Server:
        pass

    class InitializationOptions:
        pass

    class Resource:
        pass

    class Tool:
        pass

    class TextContent:
        pass

    class ImageContent:
        pass

    class EmbeddedResource:
        pass

    class LoggingLevel:
        pass


from .config import load_config
from .server import OffshoreLeaksServer

logger = logging.getLogger(__name__)


class MCPOffshoreLeaksServer:
    """MCP server wrapper for offshore leaks functionality."""

    def __init__(self):
        """Initialize the MCP wrapper."""
        if not MCP_AVAILABLE:
            raise ImportError(
                "MCP is not available. Please install with Python 3.10+ and run: "
                "pip install -e '.[mcp]'"
            )

        self.app = Server("offshore-leaks-mcp-server")
        self.offshore_server: Optional[OffshoreLeaksServer] = None
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up MCP protocol handlers."""

        @self.app.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools for offshore leaks investigation."""
            return [
                Tool(
                    name="search_entities",
                    description="Search for offshore entities (companies, trusts, foundations) by name, jurisdiction, or other criteria",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Partial or full name of the entity to search for",
                            },
                            "jurisdiction": {
                                "type": "string",
                                "description": "Jurisdiction code or description where the entity is registered",
                            },
                            "country_codes": {
                                "type": "string",
                                "description": "ISO country codes associated with the entity",
                            },
                            "company_type": {
                                "type": "string",
                                "description": "Type of company (e.g., Corporation, LLC, Trust)",
                            },
                            "status": {
                                "type": "string",
                                "description": "Status of the entity (e.g., Active, Defaulted, Struck off)",
                            },
                            "source": {
                                "type": "string",
                                "enum": [
                                    "Paradise Papers",
                                    "Panama Papers",
                                    "Offshore Leaks",
                                    "Bahamas Leaks",
                                    "Pandora Papers",
                                ],
                                "description": "Filter by data source",
                            },
                            "limit": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 20,
                                "description": "Maximum number of results to return",
                            },
                        },
                    },
                ),
                Tool(
                    name="search_officers",
                    description="Search for officers (individuals) by name, country, or role in entities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Partial or full name of the officer to search for",
                            },
                            "countries": {
                                "type": "string",
                                "description": "Countries associated with the officer",
                            },
                            "country_codes": {
                                "type": "string",
                                "description": "ISO country codes associated with the officer",
                            },
                            "source": {
                                "type": "string",
                                "enum": [
                                    "Paradise Papers",
                                    "Panama Papers",
                                    "Offshore Leaks",
                                    "Bahamas Leaks",
                                    "Pandora Papers",
                                ],
                                "description": "Filter by data source",
                            },
                            "limit": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 20,
                                "description": "Maximum number of results to return",
                            },
                        },
                    },
                ),
                Tool(
                    name="get_connections",
                    description="Explore relationships between entities, officers, and intermediaries starting from a specific node",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "start_node_id": {
                                "type": "string",
                                "description": "Node ID to start the relationship exploration from",
                            },
                            "relationship_types": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": [
                                        "officer_of",
                                        "intermediary_of",
                                        "registered_address",
                                        "connected_to",
                                        "same_name_as",
                                        "same_id_as",
                                    ],
                                },
                                "description": "Types of relationships to follow",
                            },
                            "max_depth": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 5,
                                "default": 2,
                                "description": "Maximum number of relationship hops to explore",
                            },
                            "node_types": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": [
                                        "Entity",
                                        "Officer",
                                        "Intermediary",
                                        "Other",
                                        "Address",
                                    ],
                                },
                                "description": "Types of nodes to include in results",
                            },
                            "limit": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 200,
                                "default": 50,
                                "description": "Maximum number of connected nodes to return",
                            },
                        },
                        "required": ["start_node_id"],
                    },
                ),
                Tool(
                    name="get_statistics",
                    description="Get database statistics and metadata about the offshore leaks data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "stat_type": {
                                "type": "string",
                                "enum": [
                                    "overview",
                                    "by_source",
                                    "by_jurisdiction",
                                    "by_node_type",
                                    "relationship_counts",
                                ],
                                "default": "overview",
                                "description": "Type of statistics to retrieve",
                            }
                        },
                    },
                ),
                Tool(
                    name="analyze_network",
                    description="Analyze network patterns around a specific entity or officer",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "center_node_id": {
                                "type": "string",
                                "description": "Node ID to center the network analysis around",
                            },
                            "analysis_depth": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 4,
                                "default": 2,
                                "description": "Depth of network to analyze",
                            },
                            "include_summary": {
                                "type": "boolean",
                                "default": True,
                                "description": "Include summary statistics in the analysis",
                            },
                        },
                        "required": ["center_node_id"],
                    },
                ),
                Tool(
                    name="find_shortest_paths",
                    description="Find shortest paths between two nodes in the network",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "start_node_id": {
                                "type": "string",
                                "description": "Starting node ID",
                            },
                            "end_node_id": {
                                "type": "string",
                                "description": "Ending node ID",
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "Maximum path length to consider",
                                "default": 6,
                            },
                            "relationship_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filter by relationship types",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of paths to return",
                                "default": 10,
                            },
                        },
                        "required": ["start_node_id", "end_node_id"],
                    },
                ),
                Tool(
                    name="analyze_network_patterns",
                    description="Analyze specific network patterns (hubs, bridges, clusters)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node_id": {
                                "type": "string",
                                "description": "Central node ID for pattern analysis",
                            },
                            "pattern_type": {
                                "type": "string",
                                "enum": ["hub", "bridge", "cluster"],
                                "description": "Type of pattern to analyze",
                                "default": "hub",
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "Maximum depth for pattern detection",
                                "default": 3,
                            },
                            "min_connections": {
                                "type": "integer",
                                "description": "Minimum connections threshold",
                                "default": 5,
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum results to return",
                                "default": 20,
                            },
                        },
                        "required": ["node_id"],
                    },
                ),
                Tool(
                    name="find_common_connections",
                    description="Find common connections between multiple nodes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of node IDs to find common connections for",
                                "minItems": 2,
                            },
                            "relationship_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filter by relationship types",
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "Maximum connection depth",
                                "default": 2,
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum results to return",
                                "default": 20,
                            },
                        },
                        "required": ["node_ids"],
                    },
                ),
                Tool(
                    name="temporal_analysis",
                    description="Analyze temporal patterns in entity creation around a node",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node_id": {
                                "type": "string",
                                "description": "Central node ID for temporal analysis",
                            },
                            "date_field": {
                                "type": "string",
                                "description": "Date field to analyze",
                                "default": "incorporation_date",
                            },
                            "time_window_days": {
                                "type": "integer",
                                "description": "Time window in days around the central date",
                                "default": 365,
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum results to return",
                                "default": 50,
                            },
                        },
                        "required": ["node_id"],
                    },
                ),
                Tool(
                    name="compliance_risk_analysis",
                    description="Analyze compliance risks in entity networks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node_id": {
                                "type": "string",
                                "description": "Central node ID for risk analysis",
                            },
                            "risk_jurisdictions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of high-risk jurisdictions (defaults to common offshore havens)",
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "Maximum depth to search for risky connections",
                                "default": 3,
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum results to return",
                                "default": 30,
                            },
                        },
                        "required": ["node_id"],
                    },
                ),
                Tool(
                    name="export_results",
                    description="Export investigation results to various formats (JSON, CSV, Excel)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "object",
                                "description": "Results data to export (from previous queries)",
                            },
                            "format": {
                                "type": "string",
                                "enum": ["json", "csv", "excel"],
                                "description": "Export format",
                                "default": "json",
                            },
                            "filename": {
                                "type": "string",
                                "description": "Optional custom filename",
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "Output directory path",
                                "default": "exports",
                            },
                            "include_metadata": {
                                "type": "boolean",
                                "description": "Include export metadata",
                                "default": True,
                            },
                        },
                        "required": ["data"],
                    },
                ),
                Tool(
                    name="export_network_visualization",
                    description="Export network data for visualization tools (D3.js, Gephi, Cytoscape)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "connections_data": {
                                "type": "object",
                                "description": "Network connections data to export",
                            },
                            "format": {
                                "type": "string",
                                "enum": ["json", "d3", "gexf", "graphml"],
                                "description": "Visualization format",
                                "default": "json",
                            },
                            "filename": {
                                "type": "string",
                                "description": "Optional custom filename",
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "Output directory path",
                                "default": "exports",
                            },
                        },
                        "required": ["connections_data"],
                    },
                ),
                Tool(
                    name="create_investigation_report",
                    description="Create a comprehensive investigation report with all findings",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "investigation_data": {
                                "type": "object",
                                "description": "Investigation data including summary, findings, risks, etc.",
                            },
                            "filename": {
                                "type": "string",
                                "description": "Optional custom filename",
                            },
                            "output_dir": {
                                "type": "string",
                                "description": "Output directory path",
                                "default": "exports",
                            },
                        },
                        "required": ["investigation_data"],
                    },
                ),
                Tool(
                    name="get_health_status",
                    description="Get comprehensive system health status including error recovery information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_resilience_stats": {
                                "type": "boolean",
                                "description": "Include detailed resilience and error recovery statistics",
                                "default": True,
                            }
                        },
                        "required": [],
                    },
                ),
            ]

        @self.app.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> List[TextContent]:
            """Handle tool calls for offshore leaks investigation."""
            if not self.offshore_server:
                return [
                    TextContent(
                        type="text",
                        text="Error: Offshore leaks server not initialized. Please check your database connection.",
                    )
                ]

            try:
                if name == "search_entities":
                    result = await self.offshore_server.search_entities(**arguments)
                    return self._format_search_results("Entities", result)

                elif name == "search_officers":
                    result = await self.offshore_server.search_officers(**arguments)
                    return self._format_search_results("Officers", result)

                elif name == "get_connections":
                    result = await self.offshore_server.get_connections(**arguments)
                    return self._format_connections_results(result)

                elif name == "get_statistics":
                    result = await self.offshore_server.get_statistics(
                        arguments.get("stat_type", "overview")
                    )
                    return self._format_statistics_results(result)

                elif name == "analyze_network":
                    result = await self._analyze_network(**arguments)
                    return self._format_network_analysis(result)
                elif name == "find_shortest_paths":
                    result = await self._find_shortest_paths(**arguments)
                    return self._format_path_results(result)
                elif name == "analyze_network_patterns":
                    result = await self._analyze_network_patterns(**arguments)
                    return self._format_pattern_results(result)
                elif name == "find_common_connections":
                    result = await self._find_common_connections(**arguments)
                    return self._format_common_connections_results(result)
                elif name == "temporal_analysis":
                    result = await self._temporal_analysis(**arguments)
                    return self._format_temporal_results(result)
                elif name == "compliance_risk_analysis":
                    result = await self._compliance_risk_analysis(**arguments)
                    return self._format_risk_analysis_results(result)
                elif name == "export_results":
                    result = await self.offshore_server.export_results(**arguments)
                    return self._format_export_results(result)
                elif name == "export_network_visualization":
                    result = await self.offshore_server.export_network_visualization(
                        **arguments
                    )
                    return self._format_export_results(result)
                elif name == "create_investigation_report":
                    result = await self.offshore_server.create_investigation_report(
                        **arguments
                    )
                    return self._format_export_results(result)
                elif name == "get_health_status":
                    include_resilience = arguments.get("include_resilience_stats", True)
                    if include_resilience:
                        result = await self.offshore_server.get_enhanced_health_status()
                    else:
                        result = await self.offshore_server.health_check()
                    return self._format_health_status(result)

                else:
                    return [
                        TextContent(type="text", text=f"Error: Unknown tool '{name}'")
                    ]

            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [
                    TextContent(type="text", text=f"Error executing {name}: {str(e)}")
                ]

        @self.app.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available resources."""
            return [
                Resource(
                    uri="offshore://schema",
                    name="Database Schema",
                    description="Complete schema of the offshore leaks database including all node types and relationships",
                    mimeType="application/json",
                ),
                Resource(
                    uri="offshore://sources",
                    name="Data Sources",
                    description="Information about data sources (Paradise Papers, Panama Papers, etc.)",
                    mimeType="application/json",
                ),
                Resource(
                    uri="offshore://jurisdictions",
                    name="Jurisdictions",
                    description="List of all jurisdictions in the database with entity counts",
                    mimeType="application/json",
                ),
                Resource(
                    uri="offshore://help",
                    name="Investigation Guide",
                    description="Guide for investigating offshore financial networks using this database",
                    mimeType="text/markdown",
                ),
            ]

        @self.app.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Handle resource reading."""
            if uri == "offshore://schema":
                return await self._get_schema_resource()
            elif uri == "offshore://sources":
                return await self._get_sources_resource()
            elif uri == "offshore://jurisdictions":
                return await self._get_jurisdictions_resource()
            elif uri == "offshore://help":
                return await self._get_help_resource()
            else:
                raise ValueError(f"Unknown resource: {uri}")

    def _format_search_results(self, entity_type: str, result) -> List[TextContent]:
        """Format search results for display."""
        if result.returned_count == 0:
            return [
                TextContent(
                    type="text",
                    text=f"No {entity_type.lower()} found matching the search criteria.",
                )
            ]

        text = f"## {entity_type} Search Results\n\n"
        text += f"Found {result.total_count} total {entity_type.lower()}, showing {result.returned_count}:\n\n"

        for i, item in enumerate(result.results, 1):
            name = item.get("name", "Unknown")
            if entity_type == "Entities":
                jurisdiction = item.get(
                    "jurisdiction_description", item.get("jurisdiction", "N/A")
                )
                status = item.get("status", "N/A")
                text += f"{i}. **{name}**\n"
                text += f"   - Jurisdiction: {jurisdiction}\n"
                text += f"   - Status: {status}\n"
                text += f"   - Node ID: `{item.get('node_id', 'N/A')}`\n\n"
            else:  # Officers
                countries = item.get("countries", "N/A")
                text += f"{i}. **{name}**\n"
                text += f"   - Countries: {countries}\n"
                text += f"   - Node ID: `{item.get('node_id', 'N/A')}`\n\n"

        if result.query_time_ms:
            text += f"*Query completed in {result.query_time_ms}ms*"

        return [TextContent(type="text", text=text)]

    def _format_connections_results(self, result) -> List[TextContent]:
        """Format connection exploration results."""
        if result.returned_count == 0:
            return [
                TextContent(
                    type="text",
                    text="No connections found from the specified starting node.",
                )
            ]

        text = "## Network Connections\n\n"
        text += f"Found {result.returned_count} connected nodes:\n\n"

        for i, connection in enumerate(result.results, 1):
            node = connection["node"]
            distance = connection["distance"]
            rel_info = connection.get("first_relationship", {})

            name = node.get("name", "Unknown")
            node_type = rel_info.get("type", "connected_to")

            text += f"{i}. **{name}** (distance: {distance})\n"
            text += f"   - Connection: {node_type.replace('_', ' ').title()}\n"
            text += f"   - Node ID: `{node.get('node_id', 'N/A')}`\n\n"

        if result.query_time_ms:
            text += f"*Query completed in {result.query_time_ms}ms*"

        return [TextContent(type="text", text=text)]

    def _format_statistics_results(self, result) -> List[TextContent]:
        """Format statistics results."""
        text = f"## Database Statistics ({result['stat_type']})\n\n"

        if result["stat_type"] == "overview" and result["results"]:
            stats = result["results"][0]
            text += f"- **Entities**: {stats.get('entity_count', 0):,}\n"
            text += f"- **Officers**: {stats.get('officer_count', 0):,}\n"
            text += f"- **Intermediaries**: {stats.get('intermediary_count', 0):,}\n"
            text += f"- **Addresses**: {stats.get('address_count', 0):,}\n"
            text += f"- **Relationships**: {stats.get('relationship_count', 0):,}\n\n"
        else:
            for item in result["results"]:
                if "source" in item:
                    text += f"- **{item['source']}**: {item['count']:,} {item.get('node_type', 'items')}\n"
                elif "jurisdiction" in item:
                    text += f"- **{item['jurisdiction_description']}**: {item['entity_count']:,} entities\n"
                elif "relationship_type" in item:
                    text += f"- **{item['relationship_type']}**: {item['count']:,} relationships\n"

        if result["query_time_ms"]:
            text += f"\n*Query completed in {result['query_time_ms']}ms*"

        return [TextContent(type="text", text=text)]

    async def _analyze_network(
        self, center_node_id: str, analysis_depth: int = 2, include_summary: bool = True
    ) -> Dict[str, Any]:
        """Analyze network patterns around a specific node."""
        # Get connections at specified depth
        connections_result = await self.offshore_server.get_connections(
            start_node_id=center_node_id, max_depth=analysis_depth, limit=100
        )

        # Basic network analysis
        analysis = {
            "center_node_id": center_node_id,
            "analysis_depth": analysis_depth,
            "total_connections": connections_result.returned_count,
            "connections_by_distance": {},
            "node_types": {},
            "relationship_types": {},
        }

        for connection in connections_result.results:
            distance = connection["distance"]
            node = connection["node"]

            # Count by distance
            analysis["connections_by_distance"][distance] = (
                analysis["connections_by_distance"].get(distance, 0) + 1
            )

            # Count node types (inferred from properties)
            if "jurisdiction" in node:
                node_type = "Entity"
            elif "countries" in node and "jurisdiction" not in node:
                node_type = "Officer"
            else:
                node_type = "Other"

            analysis["node_types"][node_type] = (
                analysis["node_types"].get(node_type, 0) + 1
            )

            # Count relationship types
            rel_type = connection.get("first_relationship", {}).get("type", "unknown")
            analysis["relationship_types"][rel_type] = (
                analysis["relationship_types"].get(rel_type, 0) + 1
            )

        analysis["connections"] = connections_result.results
        return analysis

    def _format_network_analysis(self, analysis: Dict[str, Any]) -> List[TextContent]:
        """Format network analysis results."""
        text = "## Network Analysis\n\n"
        text += f"**Center Node**: `{analysis['center_node_id']}`\n"
        text += f"**Analysis Depth**: {analysis['analysis_depth']} hops\n"
        text += f"**Total Connections**: {analysis['total_connections']}\n\n"

        if analysis["connections_by_distance"]:
            text += "### Connections by Distance\n"
            for distance, count in sorted(analysis["connections_by_distance"].items()):
                text += f"- Distance {distance}: {count} nodes\n"
            text += "\n"

        if analysis["node_types"]:
            text += "### Node Types in Network\n"
            for node_type, count in analysis["node_types"].items():
                text += f"- {node_type}s: {count}\n"
            text += "\n"

        if analysis["relationship_types"]:
            text += "### Relationship Types\n"
            for rel_type, count in analysis["relationship_types"].items():
                formatted_type = rel_type.replace("_", " ").title()
                text += f"- {formatted_type}: {count}\n"
            text += "\n"

        # Show key connections
        if analysis["connections"]:
            text += "### Key Connections\n"
            for i, connection in enumerate(analysis["connections"][:5], 1):
                node = connection["node"]
                distance = connection["distance"]
                name = node.get("name", "Unknown")
                text += f"{i}. **{name}** (distance: {distance})\n"

            if len(analysis["connections"]) > 5:
                text += f"... and {len(analysis['connections']) - 5} more\n"

        return [TextContent(type="text", text=text)]

    async def _find_shortest_paths(self, **kwargs) -> Dict[str, Any]:
        """Find shortest paths between two nodes."""
        return await self.offshore_server.find_shortest_paths(**kwargs)

    async def _analyze_network_patterns(self, **kwargs) -> Dict[str, Any]:
        """Analyze network patterns around a node."""
        return await self.offshore_server.analyze_network_patterns(**kwargs)

    async def _find_common_connections(self, **kwargs) -> Dict[str, Any]:
        """Find common connections between multiple nodes."""
        return await self.offshore_server.find_common_connections(**kwargs)

    async def _temporal_analysis(self, **kwargs) -> Dict[str, Any]:
        """Analyze temporal patterns in entity creation."""
        return await self.offshore_server.temporal_analysis(**kwargs)

    async def _compliance_risk_analysis(self, **kwargs) -> Dict[str, Any]:
        """Analyze compliance risks in entity networks."""
        return await self.offshore_server.compliance_risk_analysis(**kwargs)

    def _format_path_results(self, result: Dict[str, Any]) -> List[TextContent]:
        """Format shortest path results."""
        text = "## Shortest Paths Analysis\n\n"
        text += f"**Total Paths Found**: {result.get('total_count', 0)}\n"
        text += f"**Query Time**: {result.get('query_time_ms', 0):.2f}ms\n\n"

        if result.get("results"):
            text += "### Paths\n"
            for i, path in enumerate(result["results"][:10], 1):
                text += f"\n**Path {i}** (Length: {path['path_length']})\n"

                if path.get("path_nodes"):
                    for j, node in enumerate(path["path_nodes"]):
                        name = node.get("name", "Unknown")
                        labels = ", ".join(node.get("labels", []))
                        text += f"  {j + 1}. {name} ({labels})\n"

                if path.get("relationship_types"):
                    rel_types = ", ".join(path["relationship_types"])
                    text += f"     Relationships: {rel_types}\n"

            if len(result["results"]) > 10:
                text += f"\n... and {len(result['results']) - 10} more paths\n"
        else:
            text += "No paths found between the specified nodes.\n"

        return [TextContent(type="text", text=text)]

    def _format_pattern_results(self, result: Dict[str, Any]) -> List[TextContent]:
        """Format network pattern analysis results."""
        text = "## Network Pattern Analysis\n\n"
        text += f"**Total Patterns Found**: {result.get('total_count', 0)}\n"
        text += f"**Query Time**: {result.get('query_time_ms', 0):.2f}ms\n\n"

        if result.get("results"):
            text += "### Detected Patterns\n"
            for i, pattern in enumerate(result["results"][:10], 1):
                if "cluster_nodes" in pattern:
                    # Cluster pattern
                    text += (
                        f"\n**Cluster {i}** (Strength: {pattern['cluster_strength']})\n"
                    )
                    for j, node in enumerate(pattern["cluster_nodes"]):
                        name = node.get("name", "Unknown")
                        text += f"  {j + 1}. {name}\n"
                    node_types = ", ".join(pattern.get("node_types", []))
                    text += f"     Node Types: {node_types}\n"
                else:
                    # Hub or bridge pattern
                    node = pattern.get("node")
                    if node:
                        name = node.get("name", "Unknown")
                        text += f"\n**Pattern {i}**: {name}\n"

                        if "connection_count" in pattern:
                            text += (
                                f"  Connection Count: {pattern['connection_count']}\n"
                            )
                        if "communities_connected" in pattern:
                            text += f"  Communities Connected: {pattern['communities_connected']}\n"
                        if "total_neighbors" in pattern:
                            text += f"  Total Neighbors: {pattern['total_neighbors']}\n"

                        if pattern.get("relationship_types"):
                            rel_types = ", ".join(pattern["relationship_types"])
                            text += f"  Relationship Types: {rel_types}\n"

            if len(result["results"]) > 10:
                text += f"\n... and {len(result['results']) - 10} more patterns\n"
        else:
            text += "No patterns found matching the specified criteria.\n"

        return [TextContent(type="text", text=text)]

    def _format_common_connections_results(
        self, result: Dict[str, Any]
    ) -> List[TextContent]:
        """Format common connections results."""
        text = "## Common Connections Analysis\n\n"
        text += f"**Total Common Connections**: {result.get('total_count', 0)}\n"
        text += f"**Query Time**: {result.get('query_time_ms', 0):.2f}ms\n\n"

        if result.get("results"):
            text += "### Common Connections\n"
            for i, connection in enumerate(result["results"][:10], 1):
                node = connection.get("common_node")
                if node:
                    name = node.get("name", "Unknown")
                    text += f"\n**{i}. {name}**\n"
                    text += f"  Connected to {connection['connection_count']} source nodes\n"
                    text += f"  Total Neighbors: {connection['total_neighbors']}\n"

                    if connection.get("connected_sources"):
                        sources = ", ".join(connection["connected_sources"])
                        text += f"  Source Nodes: {sources}\n"

                    if connection.get("relationship_types"):
                        rel_types = ", ".join(connection["relationship_types"])
                        text += f"  Relationship Types: {rel_types}\n"

            if len(result["results"]) > 10:
                text += f"\n... and {len(result['results']) - 10} more connections\n"
        else:
            text += "No common connections found between the specified nodes.\n"

        return [TextContent(type="text", text=text)]

    def _format_temporal_results(self, result: Dict[str, Any]) -> List[TextContent]:
        """Format temporal analysis results."""
        text = "## Temporal Analysis\n\n"
        text += f"**Total Related Entities**: {result.get('total_count', 0)}\n"
        text += f"**Query Time**: {result.get('query_time_ms', 0):.2f}ms\n\n"

        if result.get("results"):
            # Group by temporal relationship
            before = []
            after = []
            same_day = []

            for item in result["results"]:
                if item["temporal_relationship"] == "before":
                    before.append(item)
                elif item["temporal_relationship"] == "after":
                    after.append(item)
                else:
                    same_day.append(item)

            if before:
                text += f"### Entities Created Before ({len(before)})\n"
                for item in before[:5]:
                    node = item["related_node"]
                    name = node.get("name", "Unknown")
                    days = abs(item["day_difference"])
                    text += f"- **{name}** ({days} days before)\n"
                if len(before) > 5:
                    text += f"  ... and {len(before) - 5} more\n"
                text += "\n"

            if same_day:
                text += f"### Entities Created Same Day ({len(same_day)})\n"
                for item in same_day[:5]:
                    node = item["related_node"]
                    name = node.get("name", "Unknown")
                    text += f"- **{name}**\n"
                if len(same_day) > 5:
                    text += f"  ... and {len(same_day) - 5} more\n"
                text += "\n"

            if after:
                text += f"### Entities Created After ({len(after)})\n"
                for item in after[:5]:
                    node = item["related_node"]
                    name = node.get("name", "Unknown")
                    days = item["day_difference"]
                    text += f"- **{name}** ({days} days after)\n"
                if len(after) > 5:
                    text += f"  ... and {len(after) - 5} more\n"
        else:
            text += "No temporal patterns found in the specified time window.\n"

        return [TextContent(type="text", text=text)]

    def _format_risk_analysis_results(
        self, result: Dict[str, Any]
    ) -> List[TextContent]:
        """Format compliance risk analysis results."""
        text = "## Compliance Risk Analysis\n\n"
        text += f"**Total Risk Entities Found**: {result.get('total_count', 0)}\n"
        text += f"**Query Time**: {result.get('query_time_ms', 0):.2f}ms\n\n"

        if result.get("results"):
            # Group by risk level
            high_risk = []
            medium_risk = []
            low_risk = []

            for item in result["results"]:
                if item["risk_level"] == "high":
                    high_risk.append(item)
                elif item["risk_level"] == "medium":
                    medium_risk.append(item)
                else:
                    low_risk.append(item)

            if high_risk:
                text += f"### 🔴 High Risk Entities ({len(high_risk)})\n"
                for item in high_risk[:5]:
                    node = item["risky_node"]
                    name = node.get("name", "Unknown")
                    jurisdiction = item.get("jurisdiction", "Unknown")
                    distance = item.get("distance", 0)
                    connections = item.get("connection_count", 0)
                    text += f"- **{name}** ({jurisdiction})\n"
                    text += f"  Distance: {distance} hops, Connections: {connections}\n"
                if len(high_risk) > 5:
                    text += f"  ... and {len(high_risk) - 5} more\n"
                text += "\n"

            if medium_risk:
                text += f"### 🟡 Medium Risk Entities ({len(medium_risk)})\n"
                for item in medium_risk[:3]:
                    node = item["risky_node"]
                    name = node.get("name", "Unknown")
                    jurisdiction = item.get("jurisdiction", "Unknown")
                    distance = item.get("distance", 0)
                    text += f"- **{name}** ({jurisdiction}, Distance: {distance})\n"
                if len(medium_risk) > 3:
                    text += f"  ... and {len(medium_risk) - 3} more\n"
                text += "\n"

            if low_risk:
                text += f"### 🟢 Lower Risk Entities ({len(low_risk)})\n"
                text += f"Found {len(low_risk)} entities with lower risk profiles.\n\n"

            # Summary of jurisdictions
            jurisdictions = {}
            for item in result["results"]:
                jurisdiction = item.get("jurisdiction", "Unknown")
                if jurisdiction not in jurisdictions:
                    jurisdictions[jurisdiction] = 0
                jurisdictions[jurisdiction] += 1

            if jurisdictions:
                text += "### Risk Jurisdictions Summary\n"
                for jurisdiction, count in sorted(
                    jurisdictions.items(), key=lambda x: x[1], reverse=True
                )[:5]:
                    text += f"- {jurisdiction}: {count} entities\n"
        else:
            text += "No risk entities found in the specified network.\n"

        return [TextContent(type="text", text=text)]

    def _format_export_results(self, result: Dict[str, Any]) -> List[TextContent]:
        """Format export operation results."""
        if result.get("success"):
            text = "## ✅ Export Successful\n\n"

            if "export_path" in result:
                text += f"**File Path**: `{result['export_path']}`\n"
            elif "report_path" in result:
                text += f"**Report Path**: `{result['report_path']}`\n"

            text += f"**Format**: {result.get('format', 'N/A')}\n"
            text += f"**Export Time**: {result.get('export_time', 'N/A')}\n"

            if "record_count" in result:
                text += f"**Records Exported**: {result['record_count']}\n"

            if "node_count" in result and "edge_count" in result:
                text += f"**Nodes**: {result['node_count']}\n"
                text += f"**Edges**: {result['edge_count']}\n"

            if "total_queries" in result:
                text += f"**Total Queries**: {result['total_queries']}\n"
                text += f"**Total Results**: {result.get('total_results', 0)}\n"

            text += "\n📁 The exported file is ready for download or further analysis."
        else:
            text = "## ❌ Export Failed\n\n"
            text += f"**Error**: {result.get('error', 'Unknown error')}\n"
            text += f"**Format**: {result.get('format', 'N/A')}\n"
            text += "\nPlease check the export parameters and try again."

        return [TextContent(type="text", text=text)]

    def _format_health_status(self, health: Any) -> List[TextContent]:
        """Format health status results."""
        # Convert health object to dict if it's a Pydantic model
        if hasattr(health, "dict"):
            health_dict = health.dict()
        else:
            health_dict = health

        status = health_dict.get("status", "unknown")
        status_emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}.get(
            status, "❓"
        )

        text = f"## {status_emoji} System Health Status\n\n"
        text += f"**Overall Status**: {status.title()}\n"
        text += f"**Timestamp**: {health_dict.get('timestamp', 'N/A')}\n\n"

        # Database status
        db_connected = health_dict.get("database_connected", False)
        db_status = health_dict.get("database_status", "unknown")
        db_emoji = "✅" if db_connected else "❌"
        text += f"### {db_emoji} Database\n"
        text += f"- **Connected**: {db_connected}\n"
        text += f"- **Status**: {db_status}\n\n"

        # Server status
        server_running = health_dict.get("server_running", False)
        server_emoji = "✅" if server_running else "❌"
        text += f"### {server_emoji} Server\n"
        text += f"- **Running**: {server_running}\n\n"

        # Error counts if available
        error_counts = health_dict.get("error_counts", {})
        if error_counts and any(count > 0 for count in error_counts.values()):
            text += "### 📊 Error Statistics\n"
            for error_type, count in error_counts.items():
                if count > 0:
                    text += f"- **{error_type.replace('_', ' ').title()}**: {count}\n"
            text += "\n"

        # Circuit breaker states if available
        cb_states = health_dict.get("circuit_breaker_states", {})
        if cb_states:
            text += "### 🔄 Circuit Breakers\n"
            for name, state in cb_states.items():
                state_emoji = {"closed": "✅", "open": "❌", "half_open": "⚠️"}.get(
                    state, "❓"
                )
                text += f"- **{name.title()}**: {state_emoji} {state.replace('_', ' ').title()}\n"
            text += "\n"

        # Components summary if available
        components = health_dict.get("components", {})
        if components:
            text += "### 🔧 Components\n"
            for component, details in components.items():
                if isinstance(details, dict) and "status" in details:
                    comp_status = details["status"]
                    comp_emoji = {
                        "healthy": "✅",
                        "unhealthy": "❌",
                        "degraded": "⚠️",
                    }.get(comp_status, "❓")
                    text += f"- **{component.title()}**: {comp_emoji} {comp_status}\n"

        text += f"\n**Server Version**: {health_dict.get('version', '0.1.0')}"

        return [TextContent(type="text", text=text)]

    async def _get_schema_resource(self) -> str:
        """Get database schema information."""
        schema = {
            "node_types": {
                "Entity": {
                    "description": "Offshore entities (companies, trusts, foundations)",
                    "properties": [
                        "name",
                        "jurisdiction",
                        "jurisdiction_description",
                        "address",
                        "incorporation_date",
                        "status",
                        "company_type",
                    ],
                },
                "Officer": {
                    "description": "Individuals who are officers of entities",
                    "properties": ["name", "countries", "country_codes"],
                },
                "Intermediary": {
                    "description": "Intermediary organizations (law firms, banks, corporate service providers)",
                    "properties": ["name", "countries", "country_codes"],
                },
                "Address": {
                    "description": "Physical addresses",
                    "properties": ["name", "address", "countries", "country_codes"],
                },
            },
            "relationship_types": {
                "officer_of": "Officer is an officer of an entity",
                "intermediary_of": "Intermediary provides services to an entity",
                "registered_address": "Address is the registered address of an entity",
                "connected_to": "General connection between nodes",
                "same_name_as": "Nodes with the same name",
                "same_id_as": "Nodes with the same identifier",
            },
        }
        return str(schema)

    async def _get_sources_resource(self) -> str:
        """Get data sources information."""
        sources = {
            "Paradise Papers": {
                "description": "13.4 million documents from offshore service providers and company registries",
                "year": 2017,
                "size": "1.4TB",
            },
            "Panama Papers": {
                "description": "11.5 million documents from Mossack Fonseca law firm",
                "year": 2016,
                "size": "2.6TB",
            },
            "Offshore Leaks": {
                "description": "2.5 million documents from offshore service providers",
                "year": 2013,
                "size": "260GB",
            },
            "Bahamas Leaks": {
                "description": "1.3 million documents from Bahamas corporate registry",
                "year": 2016,
                "size": "1.4GB",
            },
            "Pandora Papers": {
                "description": "11.9 million documents from 14 offshore service providers",
                "year": 2021,
                "size": "2.94TB",
            },
        }
        return str(sources)

    async def _get_jurisdictions_resource(self) -> str:
        """Get jurisdictions information."""
        if self.offshore_server:
            try:
                result = await self.offshore_server.get_statistics("by_jurisdiction")
                return str(result["results"])
            except Exception as e:
                return f"Error fetching jurisdictions: {e}"
        return "Database not available"

    async def _get_help_resource(self) -> str:
        """Get investigation help guide."""
        return """
# Offshore Leaks Investigation Guide

## Getting Started
This database contains information from major offshore financial leaks including the Paradise Papers, Panama Papers, and Pandora Papers.

## Search Strategies

### 1. Entity Investigation
- Start with `search_entities` using a company name or partial name
- Use jurisdiction filters to focus on specific offshore havens
- Check entity status and incorporation dates

### 2. Officer Investigation
- Use `search_officers` to find individuals by name
- Cross-reference officers across multiple entities
- Look for patterns in country associations

### 3. Network Analysis
- Use `get_connections` to explore relationships from a known entity or officer
- Start with depth 1-2 to avoid overwhelming results
- Use `analyze_network` for basic network analysis around a node
- Use `find_shortest_paths` to trace connections between two entities
- Use `analyze_network_patterns` to detect hubs, bridges, and clusters
- Use `find_common_connections` to find mutual connections between entities
- Use `temporal_analysis` to identify entities created around the same time
- Use `compliance_risk_analysis` to identify high-risk jurisdictions in networks

### 4. Data Export and Visualization
- Use `export_results` to save investigation data in JSON, CSV, or Excel format
- Use `export_network_visualization` to create files for D3.js, Gephi, or Cytoscape
- Use `create_investigation_report` to generate comprehensive reports

### 5. Jurisdiction Analysis
- Use statistics to understand data distribution
- Focus investigations on high-activity jurisdictions
- Compare entity counts across different data sources

## Best Practices
- Always verify information independently
- Respect privacy rights and presumption of innocence
- Use for legitimate research and journalistic purposes only
- Cross-reference findings across multiple tools

## Ethical Guidelines
The presence in this database does not imply wrongdoing. Offshore structures have legitimate uses.
Always cite ICIJ as the data source and follow responsible disclosure practices.
"""

    async def start(self) -> None:
        """Start the offshore leaks server."""
        try:
            config = load_config()
            self.offshore_server = OffshoreLeaksServer(config)
            await self.offshore_server.start()
            logger.info("Offshore leaks server started successfully")
        except Exception as e:
            logger.error(f"Failed to start offshore leaks server: {e}")
            raise

    async def stop(self) -> None:
        """Stop the offshore leaks server."""
        if self.offshore_server:
            await self.offshore_server.stop()
            logger.info("Offshore leaks server stopped")


async def main() -> None:
    """Main entry point for the MCP server."""
    if not MCP_AVAILABLE:
        print("Error: MCP is not available. Please install with Python 3.10+ and run:")
        print("pip install -e '.[mcp]'")
        sys.exit(1)

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    server = MCPOffshoreLeaksServer()

    async with stdio_server() as (read_stream, write_stream):
        await server.start()
        try:
            await server.app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="offshore-leaks-mcp-server",
                    server_version="0.1.0",
                    capabilities=server.app.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )
        finally:
            await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
