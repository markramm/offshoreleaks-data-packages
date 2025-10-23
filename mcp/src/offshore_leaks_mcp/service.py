"""Service layer for offshore leaks business logic."""

import logging
from datetime import datetime
from typing import Any, Optional

from pydantic import ValidationError

from .database import DatabaseError, Neo4jDatabase, QueryError
from .models import (
    ConnectionsParameters,
    EntitySearchParameters,
    OfficerSearchParameters,
    SearchResult,
)
from .queries import OffshoreLeaksQueries

logger = logging.getLogger(__name__)


class OffshoreLeaksService:
    """Service layer for offshore leaks business logic."""

    def __init__(self, database: Neo4jDatabase, query_timeout: int = 30):
        """Initialize the service with database and configuration."""
        self.database = database
        self.query_timeout = query_timeout

    async def search_entities(self, **kwargs: Any) -> SearchResult:
        """Search for offshore entities."""
        try:
            # Validate parameters
            params = EntitySearchParameters(**kwargs)

            # Build and execute query
            query, query_params = OffshoreLeaksQueries.search_entities(
                name=params.name,
                jurisdiction=params.jurisdiction,
                country_codes=params.country_codes,
                company_type=params.company_type,
                status=params.status,
                incorporation_date_from=(
                    params.incorporation_date_from.isoformat()
                    if params.incorporation_date_from
                    else None
                ),
                incorporation_date_to=(
                    params.incorporation_date_to.isoformat()
                    if params.incorporation_date_to
                    else None
                ),
                source=params.source,
                limit=params.limit,
                offset=params.offset,
            )

            result = await self.database.execute_query(
                query,
                query_params,
                timeout=self.query_timeout,
            )

            # Count total results (without pagination)
            # Remove ORDER BY, SKIP, and LIMIT clauses for count query
            count_query = query.replace("RETURN e", "RETURN count(e) as total")
            count_query = (
                count_query.split("ORDER BY")[0].split("SKIP")[0].split("LIMIT")[0]
            )
            count_result = await self.database.execute_query(
                count_query,
                {k: v for k, v in query_params.items() if k not in ["limit", "offset"]},
            )
            total_count = (
                count_result.records[0]["total"] if count_result.records else 0
            )

            # Format results
            entities = [record["e"] for record in result.records]

            return SearchResult(
                total_count=total_count,
                returned_count=len(entities),
                offset=params.offset,
                limit=params.limit,
                results=entities,
                query_time_ms=result.query_time_ms,
            )

        except ValidationError as e:
            logger.error(f"Invalid search parameters: {e}")
            raise ValueError(f"Invalid parameters: {e}") from e
        except (DatabaseError, QueryError) as e:
            logger.error(f"Database error during entity search: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during entity search: {e}")
            raise

    async def search_officers(self, **kwargs: Any) -> SearchResult:
        """Search for officers."""
        try:
            # Validate parameters
            params = OfficerSearchParameters(**kwargs)

            # Build and execute query
            query, query_params = OffshoreLeaksQueries.search_officers(
                name=params.name,
                countries=params.countries,
                country_codes=params.country_codes,
                source=params.source,
                limit=params.limit,
                offset=params.offset,
            )

            result = await self.database.execute_query(
                query,
                query_params,
                timeout=self.query_timeout,
            )

            # Count total results (without pagination)
            # Remove ORDER BY, SKIP, and LIMIT clauses for count query
            count_query = query.replace("RETURN o", "RETURN count(o) as total")
            count_query = (
                count_query.split("ORDER BY")[0].split("SKIP")[0].split("LIMIT")[0]
            )
            count_result = await self.database.execute_query(
                count_query,
                {k: v for k, v in query_params.items() if k not in ["limit", "offset"]},
            )
            total_count = (
                count_result.records[0]["total"] if count_result.records else 0
            )

            # Format results
            officers = [record["o"] for record in result.records]

            return SearchResult(
                total_count=total_count,
                returned_count=len(officers),
                offset=params.offset,
                limit=params.limit,
                results=officers,
                query_time_ms=result.query_time_ms,
            )

        except ValidationError as e:
            logger.error(f"Invalid search parameters: {e}")
            raise ValueError(f"Invalid parameters: {e}") from e
        except (DatabaseError, QueryError) as e:
            logger.error(f"Database error during officer search: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during officer search: {e}")
            raise

    async def get_connections(self, **kwargs: Any) -> SearchResult:
        """Explore connections from a starting node."""
        try:
            # Validate parameters
            params = ConnectionsParameters(**kwargs)

            # Build and execute query
            query, query_params = OffshoreLeaksQueries.get_connections(
                start_node_id=params.start_node_id,
                relationship_types=params.relationship_types,
                max_depth=params.max_depth,
                node_types=params.node_types,
                limit=params.limit,
            )

            result = await self.database.execute_query(
                query,
                query_params,
                timeout=self.query_timeout,
            )

            # Format results
            connections = []
            for record in result.records:
                connection = {
                    "node": record["connected"],
                    "distance": record["distance"],
                    "first_relationship": record["first_relationship"],
                }
                connections.append(connection)

            return SearchResult(
                total_count=len(connections),  # For connections, we return all found
                returned_count=len(connections),
                offset=0,
                limit=params.limit,
                results=connections,
                query_time_ms=result.query_time_ms,
            )

        except ValidationError as e:
            logger.error(f"Invalid connection parameters: {e}")
            raise ValueError(f"Invalid parameters: {e}") from e
        except (DatabaseError, QueryError) as e:
            logger.error(f"Database error during connection search: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during connection search: {e}")
            raise

    async def get_statistics(self, stat_type: str = "overview") -> dict[str, Any]:
        """Get database statistics and metadata."""
        try:
            query, query_params = OffshoreLeaksQueries.get_statistics(stat_type)

            result = await self.database.execute_query(
                query,
                query_params,
                timeout=self.query_timeout,
            )

            return {
                "stat_type": stat_type,
                "results": result.records,
                "query_time_ms": result.query_time_ms,
            }

        except (DatabaseError, QueryError) as e:
            logger.error(f"Database error during statistics query: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during statistics query: {e}")
            raise

    async def find_shortest_paths(
        self,
        start_node_id: str,
        end_node_id: str,
        max_depth: int = 6,
        relationship_types: Optional[list[str]] = None,
        limit: int = 10,
    ) -> SearchResult:
        """Find shortest paths between two nodes."""
        try:
            query, query_params = OffshoreLeaksQueries.find_shortest_paths(
                start_node_id=start_node_id,
                end_node_id=end_node_id,
                max_depth=max_depth,
                relationship_types=relationship_types,
                limit=limit,
            )

            result = await self.database.execute_query(
                query,
                query_params,
                timeout=self.query_timeout,
            )

            # Format path results
            paths = []
            for record in result.records:
                paths.append(
                    {
                        "path_length": record["path_length"],
                        "relationship_types": record["relationship_types"],
                        "path_nodes": record["path_nodes"],
                    }
                )

            return SearchResult(
                total_count=len(paths),
                returned_count=len(paths),
                offset=0,
                limit=limit,
                results=paths,
                query_time_ms=result.query_time_ms,
            )

        except ValidationError as e:
            logger.error(f"Parameter validation error: {e}")
            raise QueryError(f"Invalid parameters: {e}") from e
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during path finding: {e}")
            raise

    async def analyze_network_patterns(
        self,
        node_id: str,
        pattern_type: str = "hub",
        max_depth: int = 3,
        min_connections: int = 5,
        limit: int = 20,
    ) -> SearchResult:
        """Analyze network patterns around a node."""
        try:
            query, query_params = OffshoreLeaksQueries.analyze_network_patterns(
                node_id=node_id,
                pattern_type=pattern_type,
                max_depth=max_depth,
                min_connections=min_connections,
                limit=limit,
            )

            result = await self.database.execute_query(
                query,
                query_params,
                timeout=self.query_timeout,
            )

            # Format pattern analysis results
            patterns = []
            for record in result.records:
                if pattern_type == "cluster":
                    patterns.append(
                        {
                            "cluster_nodes": record["cluster_nodes"],
                            "cluster_strength": record["cluster_strength"],
                            "node_types": record["node_types"],
                        }
                    )
                else:
                    # For hub and bridge patterns
                    node_key = "connected" if pattern_type == "hub" else "bridge"
                    patterns.append(
                        {
                            "node": record.get(node_key),
                            "connection_count": record.get("connection_count", 0),
                            "communities_connected": record.get(
                                "communities_connected", 0
                            ),
                            "total_neighbors": record.get("total_neighbors", 0),
                            "total_connections": record.get("total_connections", 0),
                            "relationship_types": record.get("relationship_types", []),
                            "neighbor_types": record.get("neighbor_types", []),
                        }
                    )

            return SearchResult(
                total_count=len(patterns),
                returned_count=len(patterns),
                offset=0,
                limit=limit,
                results=patterns,
                query_time_ms=result.query_time_ms,
            )

        except ValidationError as e:
            logger.error(f"Parameter validation error: {e}")
            raise QueryError(f"Invalid parameters: {e}") from e
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during network analysis: {e}")
            raise

    async def find_common_connections(
        self,
        node_ids: list[str],
        relationship_types: Optional[list[str]] = None,
        max_depth: int = 2,
        limit: int = 20,
    ) -> SearchResult:
        """Find common connections between multiple nodes."""
        try:
            query, query_params = OffshoreLeaksQueries.find_common_connections(
                node_ids=node_ids,
                relationship_types=relationship_types,
                max_depth=max_depth,
                limit=limit,
            )

            result = await self.database.execute_query(
                query,
                query_params,
                timeout=self.query_timeout,
            )

            # Format common connections results
            connections = []
            for record in result.records:
                connections.append(
                    {
                        "common_node": record["common"],
                        "connected_sources": record["connected_sources"],
                        "connection_count": record["connection_count"],
                        "total_neighbors": record["total_neighbors"],
                        "relationship_types": record["relationship_types"],
                    }
                )

            return SearchResult(
                total_count=len(connections),
                returned_count=len(connections),
                offset=0,
                limit=limit,
                results=connections,
                query_time_ms=result.query_time_ms,
            )

        except ValidationError as e:
            logger.error(f"Parameter validation error: {e}")
            raise QueryError(f"Invalid parameters: {e}") from e
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during common connections analysis: {e}")
            raise

    async def temporal_analysis(
        self,
        node_id: str,
        date_field: str = "incorporation_date",
        time_window_days: int = 365,
        limit: int = 50,
    ) -> SearchResult:
        """Analyze temporal patterns in entity creation."""
        try:
            query, query_params = OffshoreLeaksQueries.temporal_analysis(
                node_id=node_id,
                date_field=date_field,
                time_window_days=time_window_days,
                limit=limit,
            )

            result = await self.database.execute_query(
                query,
                query_params,
                timeout=self.query_timeout,
            )

            # Format temporal analysis results
            temporal_data = []
            for record in result.records:
                temporal_data.append(
                    {
                        "related_node": record["related"],
                        "related_date": record["related_date"],
                        "day_difference": record["day_diff"],
                        "node_types": record["node_types"],
                        "temporal_relationship": record["temporal_relationship"],
                    }
                )

            return SearchResult(
                total_count=len(temporal_data),
                returned_count=len(temporal_data),
                offset=0,
                limit=limit,
                results=temporal_data,
                query_time_ms=result.query_time_ms,
            )

        except ValidationError as e:
            logger.error(f"Parameter validation error: {e}")
            raise QueryError(f"Invalid parameters: {e}") from e
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during temporal analysis: {e}")
            raise

    async def compliance_risk_analysis(
        self,
        node_id: str,
        risk_jurisdictions: Optional[list[str]] = None,
        max_depth: int = 3,
        limit: int = 30,
    ) -> SearchResult:
        """Analyze compliance risks in entity networks."""
        try:
            query, query_params = OffshoreLeaksQueries.compliance_risk_analysis(
                node_id=node_id,
                risk_jurisdictions=risk_jurisdictions,
                max_depth=max_depth,
                limit=limit,
            )

            result = await self.database.execute_query(
                query,
                query_params,
                timeout=self.query_timeout,
            )

            # Format risk analysis results
            risk_data = []
            for record in result.records:
                risk_data.append(
                    {
                        "risky_node": record["risky"],
                        "distance": record["distance"],
                        "risk_level": record["risk_level"],
                        "jurisdiction": record["jurisdiction"],
                        "connection_count": record["connection_count"],
                        "relationship_types": record["relationship_types"],
                        "connected_types": record["connected_types"],
                    }
                )

            return SearchResult(
                total_count=len(risk_data),
                returned_count=len(risk_data),
                offset=0,
                limit=limit,
                results=risk_data,
                query_time_ms=result.query_time_ms,
            )

        except ValidationError as e:
            logger.error(f"Parameter validation error: {e}")
            raise QueryError(f"Invalid parameters: {e}") from e
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during risk analysis: {e}")
            raise

    async def export_results(
        self,
        data: dict[str, Any],
        format: str = "json",
        filename: Optional[str] = None,
        output_dir: str = "exports",
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """Export investigation results to various formats."""
        try:
            from .exporters import DataExporter, ExportConfig

            config = ExportConfig(include_metadata=include_metadata)
            exporter = DataExporter(config)

            if format.lower() == "json":
                file_path = exporter.export_to_json(data, filename, output_dir)
            elif format.lower() == "csv":
                file_path = exporter.export_to_csv(data, filename, output_dir)
            elif format.lower() == "excel":
                file_path = exporter.export_to_excel(data, filename, output_dir)
            else:
                raise ValueError(f"Unsupported export format: {format}")

            return {
                "export_path": file_path,
                "format": format,
                "record_count": len(data.get("results", [])),
                "export_time": datetime.now().isoformat(),
                "success": True,
            }

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {"success": False, "error": str(e), "format": format}

    async def export_network_visualization(
        self,
        connections_data: dict[str, Any],
        format: str = "json",
        filename: Optional[str] = None,
        output_dir: str = "exports",
    ) -> dict[str, Any]:
        """Export network data for visualization tools."""
        try:
            from .exporters import DataExporter, NetworkVisualizer

            visualizer = NetworkVisualizer()
            exporter = DataExporter()

            # Prepare network data
            network_data = visualizer.prepare_network_data(connections_data)

            if format.lower() == "d3":
                d3_data = visualizer.create_d3_visualization_data(network_data)
                file_path = exporter.export_to_json(d3_data, filename, output_dir)
            elif format.lower() in ["gexf", "graphml", "json"]:
                file_path = exporter.export_network_data(
                    network_data["nodes"],
                    network_data["edges"],
                    filename,
                    output_dir,
                    format,
                )
            else:
                raise ValueError(f"Unsupported network format: {format}")

            return {
                "export_path": file_path,
                "format": format,
                "node_count": len(network_data["nodes"]),
                "edge_count": len(network_data["edges"]),
                "export_time": datetime.now().isoformat(),
                "success": True,
            }

        except Exception as e:
            logger.error(f"Network export failed: {e}")
            return {"success": False, "error": str(e), "format": format}

    async def create_investigation_report(
        self,
        investigation_data: dict[str, Any],
        filename: Optional[str] = None,
        output_dir: str = "exports",
    ) -> dict[str, Any]:
        """Create a comprehensive investigation report."""
        try:
            from .exporters import DataExporter

            exporter = DataExporter()
            file_path = exporter.create_investigation_report(
                investigation_data, filename, output_dir
            )

            return {
                "report_path": file_path,
                "export_time": datetime.now().isoformat(),
                "total_queries": investigation_data.get("query_count", 0),
                "total_results": investigation_data.get("total_results", 0),
                "success": True,
            }

        except Exception as e:
            logger.error(f"Report creation failed: {e}")
            return {"success": False, "error": str(e)}
