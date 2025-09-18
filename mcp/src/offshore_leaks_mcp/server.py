"""Main MCP server implementation for offshore leaks database."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import ValidationError

from .config import Config, load_config
from .database import DatabaseError, Neo4jDatabase, QueryError
from .models import (
    ConnectionsParameters,
    EntitySearchParameters,
    HealthStatus,
    OfficerSearchParameters,
    SearchResult,
)
from .queries import OffshoreLeaksQueries

logger = logging.getLogger(__name__)


class OffshoreLeaksServer:
    """MCP server for offshore leaks database queries."""

    def __init__(self, config: Optional[Config] = None) -> None:
        """Initialize the server with configuration."""
        self.config = config or load_config()
        self.database = Neo4jDatabase(self.config.neo4j)
        self._running = False

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
            await self.database.disconnect()
            self._running = False
            logger.info("Offshore Leaks MCP Server stopped")
        except Exception as e:
            logger.error(f"Error stopping server: {e}")

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
                version=self.config.server.version,
                timestamp=datetime.utcnow().isoformat(),
                details=details,
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthStatus(
                status="unhealthy",
                database_connected=False,
                version=self.config.server.version,
                timestamp=datetime.utcnow().isoformat(),
                details={"error": str(e)},
            )

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
                timeout=self.config.server.query_timeout,
            )

            # Count total results (without pagination)
            count_query = query.replace("RETURN e", "RETURN count(e) as total").split(
                "SKIP"
            )[0]
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
            raise ValueError(f"Invalid parameters: {e}")
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
                timeout=self.config.server.query_timeout,
            )

            # Count total results (without pagination)
            count_query = query.replace("RETURN o", "RETURN count(o) as total").split(
                "SKIP"
            )[0]
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
            raise ValueError(f"Invalid parameters: {e}")
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
                timeout=self.config.server.query_timeout,
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
            raise ValueError(f"Invalid parameters: {e}")
        except (DatabaseError, QueryError) as e:
            logger.error(f"Database error during connection search: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during connection search: {e}")
            raise

    async def get_statistics(self, stat_type: str = "overview") -> Dict[str, Any]:
        """Get database statistics and metadata."""
        try:
            query, query_params = OffshoreLeaksQueries.get_statistics(stat_type)

            result = await self.database.execute_query(
                query,
                query_params,
                timeout=self.config.server.query_timeout,
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
