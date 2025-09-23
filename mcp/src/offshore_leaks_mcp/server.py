"""Main MCP server implementation for offshore leaks database."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

from .config import Config, load_config
from .database import Neo4jDatabase
from .models import (
    HealthStatus,
    SearchResult,
)
from .resilience import GracefulShutdown, HealthChecker, resilience_manager
from .service import OffshoreLeaksService

logger = logging.getLogger(__name__)


class OffshoreLeaksServer:
    """MCP server for offshore leaks database queries."""

    def __init__(self, config: Optional[Config] = None) -> None:
        """Initialize the server with configuration."""
        self.config = config or load_config()
        self.database = Neo4jDatabase(self.config.neo4j)
        self.service = OffshoreLeaksService(
            self.database, self.config.server.query_timeout
        )
        self._running = False
        self.health_checker = HealthChecker()
        self.shutdown_handler = GracefulShutdown()

        # Add shutdown hooks
        self.shutdown_handler.add_shutdown_hook(self._shutdown_database)
        self.shutdown_handler.add_shutdown_hook(self._cleanup_resources)

    async def start(self) -> None:
        """Start the server and establish database connection."""
        try:
            await self.database.connect()
            self._running = True
            logger.info(
                f"Offshore Leaks MCP Server {self.config.server.version} started"
            )
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise

    async def stop(self) -> None:
        """Stop the server and close database connection."""
        try:
            await self.shutdown_handler.shutdown()
            self._running = False
            logger.info("Offshore Leaks MCP Server stopped")
        except Exception as e:
            logger.error(f"Error stopping server: {e}")

    async def _shutdown_database(self) -> None:
        """Shutdown hook for database cleanup."""
        try:
            await self.database.disconnect()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

    async def _cleanup_resources(self) -> None:
        """Shutdown hook for general resource cleanup."""
        try:
            # Log final error statistics
            error_stats = resilience_manager.get_error_stats()
            logger.info(f"Final error statistics: {error_stats}")
        except Exception as e:
            logger.error(f"Error during resource cleanup: {e}")

    async def get_enhanced_health_status(self) -> HealthStatus:
        """Get comprehensive health status with resilience information."""
        try:
            # Check database health
            db_health = await self.health_checker.check_database_health(self.database)

            # Check server health
            server_health = await self.health_checker.check_server_health(self)

            # Get overall health
            overall_health = self.health_checker.get_overall_health()

            # Get resilience statistics
            error_stats = resilience_manager.get_error_stats()

            return HealthStatus(
                status=overall_health["status"],
                timestamp=datetime.now(),
                database_connected=db_health.get("connected", False),
                database_status=db_health.get("status", "unknown"),
                server_running=server_health.get("running", False),
                components={
                    "database": db_health,
                    "server": server_health,
                    "resilience": error_stats,
                },
                error_counts=error_stats.get("error_counts", {}),
                circuit_breaker_states=error_stats.get("circuit_breaker_states", {}),
            )

        except Exception as e:
            logger.error(f"Enhanced health check failed: {e}")
            return HealthStatus(
                status="unhealthy",
                timestamp=datetime.now(),
                database_connected=False,
                database_status="unknown",
                server_running=self._running,
                components={"error": str(e)},
                error_counts={},
                circuit_breaker_states={},
            )

    async def health_check(self) -> HealthStatus:
        """Perform health check on server and database."""
        try:
            # Check database connectivity
            if self.database.is_connected:
                db_health = await self.database.health_check()
                database_connected = True
                details = db_health
            else:
                database_connected = False
                details = {"error": "Database not connected"}

            status = "healthy" if database_connected else "unhealthy"

            return HealthStatus(
                status=status,
                database_connected=database_connected,
                server_running=self._running,
                version=self.config.server.version,
                timestamp=datetime.utcnow().isoformat(),
                details=details,
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthStatus(
                status="unhealthy",
                database_connected=False,
                server_running=self._running,
                version=self.config.server.version,
                timestamp=datetime.utcnow().isoformat(),
                details={"error": str(e)},
            )

    async def search_entities(self, **kwargs: Any) -> SearchResult:
        """Search for offshore entities."""
        return await self.service.search_entities(**kwargs)

    async def search_officers(self, **kwargs: Any) -> SearchResult:
        """Search for officers."""
        return await self.service.search_officers(**kwargs)

    async def get_connections(self, **kwargs: Any) -> SearchResult:
        """Explore connections from a starting node."""
        return await self.service.get_connections(**kwargs)

    async def get_statistics(self, stat_type: str = "overview") -> dict[str, Any]:
        """Get database statistics and metadata."""
        return await self.service.get_statistics(stat_type)

    async def find_shortest_paths(
        self,
        start_node_id: str,
        end_node_id: str,
        max_depth: int = 6,
        relationship_types: Optional[list] = None,
        limit: int = 10,
    ) -> SearchResult:
        """Find shortest paths between two nodes."""
        return await self.service.find_shortest_paths(
            start_node_id=start_node_id,
            end_node_id=end_node_id,
            max_depth=max_depth,
            relationship_types=relationship_types,
            limit=limit,
        )

    async def analyze_network_patterns(
        self,
        node_id: str,
        pattern_type: str = "hub",
        max_depth: int = 3,
        min_connections: int = 5,
        limit: int = 20,
    ) -> SearchResult:
        """Analyze network patterns around a node."""
        return await self.service.analyze_network_patterns(
            node_id=node_id,
            pattern_type=pattern_type,
            max_depth=max_depth,
            min_connections=min_connections,
            limit=limit,
        )

    async def find_common_connections(
        self,
        node_ids: list,
        relationship_types: Optional[list] = None,
        max_depth: int = 2,
        limit: int = 20,
    ) -> SearchResult:
        """Find common connections between multiple nodes."""
        return await self.service.find_common_connections(
            node_ids=node_ids,
            relationship_types=relationship_types,
            max_depth=max_depth,
            limit=limit,
        )

    async def temporal_analysis(
        self,
        node_id: str,
        date_field: str = "incorporation_date",
        time_window_days: int = 365,
        limit: int = 50,
    ) -> SearchResult:
        """Analyze temporal patterns in entity creation."""
        return await self.service.temporal_analysis(
            node_id=node_id,
            date_field=date_field,
            time_window_days=time_window_days,
            limit=limit,
        )

    async def compliance_risk_analysis(
        self,
        node_id: str,
        risk_jurisdictions: Optional[list] = None,
        max_depth: int = 3,
        limit: int = 30,
    ) -> SearchResult:
        """Analyze compliance risks in entity networks."""
        return await self.service.compliance_risk_analysis(
            node_id=node_id,
            risk_jurisdictions=risk_jurisdictions,
            max_depth=max_depth,
            limit=limit,
        )

    async def export_results(
        self,
        data: dict[str, Any],
        format: str = "json",
        filename: Optional[str] = None,
        output_dir: str = "exports",
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """Export investigation results to various formats."""
        return await self.service.export_results(
            data=data,
            format=format,
            filename=filename,
            output_dir=output_dir,
            include_metadata=include_metadata,
        )

    async def export_network_visualization(
        self,
        connections_data: dict[str, Any],
        format: str = "json",
        filename: Optional[str] = None,
        output_dir: str = "exports",
    ) -> dict[str, Any]:
        """Export network data for visualization tools."""
        return await self.service.export_network_visualization(
            connections_data=connections_data,
            format=format,
            filename=filename,
            output_dir=output_dir,
        )

    async def create_investigation_report(
        self,
        investigation_data: dict[str, Any],
        filename: Optional[str] = None,
        output_dir: str = "exports",
    ) -> dict[str, Any]:
        """Create a comprehensive investigation report."""
        return await self.service.create_investigation_report(
            investigation_data=investigation_data,
            filename=filename,
            output_dir=output_dir,
        )

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running and self.database.is_connected


async def main() -> None:
    """Main entry point for running the server."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load configuration
    config = load_config()

    if config.server.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    # Create and start server
    server = OffshoreLeaksServer(config)

    try:
        await server.start()

        # Perform health check
        health = await server.health_check()
        logger.info(f"Server health: {health.status}")

        if health.status == "healthy":
            logger.info("Server ready to handle requests")

            # Keep the server running
            while server.is_running:
                await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
