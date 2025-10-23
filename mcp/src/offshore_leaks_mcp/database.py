"""Database connection and query management for Neo4j."""

import logging
from typing import Any, Optional

from neo4j import Driver, GraphDatabase, basic_auth
from pydantic import BaseModel

from .config import Neo4jConfig
from .resilience import ErrorType, RetryableError, database_resilient

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database operations."""

    pass


class ConnectionError(DatabaseError):
    """Exception raised when database connection fails."""

    pass


class QueryError(DatabaseError):
    """Exception raised when query execution fails."""

    pass


class QueryResult(BaseModel):
    """Structured query result."""

    records: list[dict[str, Any]]
    summary: dict[str, Any]
    query_time_ms: Optional[int] = None


class Neo4jDatabase:
    """Neo4j database connection and query manager."""

    def __init__(self, config: Neo4jConfig) -> None:
        """Initialize database connection."""
        self.config = config
        self._driver: Optional[Driver] = None
        self._connected = False

    @database_resilient
    async def connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self._driver = GraphDatabase.driver(
                self.config.uri,
                auth=basic_auth(self.config.user, self.config.password),
                max_connection_lifetime=self.config.max_connection_lifetime,
                max_connection_pool_size=self.config.max_connection_pool_size,
                connection_timeout=self.config.connection_timeout,
            )

            # Test connection with health check
            await self._basic_health_check()
            self._connected = True
            logger.info("Successfully connected to Neo4j database")

        except Exception as e:
            logger.error(f"Failed to connect to Neo4j database: {e}")
            # Convert to retryable error for resilience mechanism
            raise RetryableError(
                f"Database connection failed: {e}", ErrorType.DATABASE_CONNECTION
            ) from e

    async def disconnect(self) -> None:
        """Close database connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            self._connected = False
            logger.info("Disconnected from Neo4j database")

    async def _basic_health_check(self) -> None:
        """Basic connectivity test for connection establishment."""
        if not self._driver:
            raise ConnectionError("Database driver not initialized")

        try:
            with self._driver.session(database=self.config.database) as session:
                result = session.run("RETURN 1 as health_check")
                record = result.single()

                if not record or record["health_check"] != 1:
                    raise QueryError("Health check query returned unexpected result")

        except Exception as e:
            logger.error(f"Basic health check failed: {e}")
            raise ConnectionError(f"Health check failed: {e}") from e

    @database_resilient
    async def health_check(self) -> dict[str, Any]:
        """Check database health and connectivity with resilience."""
        if not self._driver:
            raise RetryableError(
                "Database not connected", ErrorType.DATABASE_CONNECTION
            )

        try:
            with self._driver.session(database=self.config.database) as session:
                result = session.run("RETURN 1 as health_check")
                record = result.single()

                if record and record["health_check"] == 1:
                    return {
                        "status": "healthy",
                        "database": self.config.database,
                        "uri": self.config.uri,
                        "connected": True,
                    }
                else:
                    raise QueryError("Health check query returned unexpected result")

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            # Determine if this is a connection issue or query issue
            if any(
                keyword in str(e).lower()
                for keyword in ["connection", "network", "timeout"]
            ):
                raise RetryableError(
                    f"Health check failed: {e}", ErrorType.DATABASE_CONNECTION
                ) from e
            else:
                raise QueryError(f"Health check failed: {e}") from e

    @database_resilient
    async def execute_query(
        self,
        query: str,
        parameters: Optional[dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> QueryResult:
        """Execute a Cypher query and return structured results with resilience."""
        if not self._driver:
            raise RetryableError(
                "Database not connected", ErrorType.DATABASE_CONNECTION
            )

        if parameters is None:
            parameters = {}

        try:
            with self._driver.session(database=self.config.database) as session:
                start_time = None
                try:
                    import time

                    start_time = time.time()

                    result = session.run(query, parameters, timeout=timeout)
                    records = [record.data() for record in result]
                    # Get summary after consuming all records
                    result_summary = result.consume()

                    # Convert SummaryCounters to dict
                    counters = result_summary.counters
                    counters_dict = {
                        "nodes_created": counters.nodes_created,
                        "nodes_deleted": counters.nodes_deleted,
                        "relationships_created": counters.relationships_created,
                        "relationships_deleted": counters.relationships_deleted,
                        "properties_set": counters.properties_set,
                        "labels_added": counters.labels_added,
                        "labels_removed": counters.labels_removed,
                        "indexes_added": counters.indexes_added,
                        "indexes_removed": counters.indexes_removed,
                        "constraints_added": counters.constraints_added,
                        "constraints_removed": counters.constraints_removed,
                    }

                    summary = {
                        "query_type": result_summary.query_type,
                        "counters": counters_dict,
                        "result_available_after": result_summary.result_available_after,
                        "result_consumed_after": result_summary.result_consumed_after,
                    }

                    end_time = time.time()
                    query_time_ms = (
                        int((end_time - start_time) * 1000) if start_time else None
                    )

                    logger.debug(
                        f"Query executed in {query_time_ms}ms, returned {len(records)} records"
                    )

                    return QueryResult(
                        records=records,
                        summary=summary,
                        query_time_ms=query_time_ms,
                    )

                except Exception as e:
                    logger.error(f"Query execution failed: {e}")
                    logger.debug(f"Query: {query}")
                    logger.debug(f"Parameters: {parameters}")

                    # Classify error for resilience handling
                    error_msg = str(e).lower()
                    if any(
                        keyword in error_msg for keyword in ["timeout", "timed out"]
                    ):
                        raise RetryableError(
                            f"Query timeout: {e}", ErrorType.QUERY_TIMEOUT
                        ) from e
                    elif any(
                        keyword in error_msg for keyword in ["connection", "network"]
                    ):
                        raise RetryableError(
                            f"Connection error during query: {e}",
                            ErrorType.DATABASE_CONNECTION,
                        ) from e
                    else:
                        raise QueryError(f"Query execution failed: {e}") from e

        except Exception as e:
            if isinstance(e, (QueryError, RetryableError)):
                raise
            logger.error(f"Database session error: {e}")

            # Session errors are typically connection-related
            raise RetryableError(
                f"Database session failed: {e}", ErrorType.DATABASE_CONNECTION
            ) from e

    async def get_database_info(self) -> dict[str, Any]:
        """Get database metadata and statistics."""
        queries = {
            "node_counts": """
                MATCH (n)
                RETURN labels(n) as labels, count(*) as count
                ORDER BY count DESC
            """,
            "relationship_counts": """
                MATCH ()-[r]->()
                RETURN type(r) as relationship_type, count(*) as count
                ORDER BY count DESC
            """,
            "database_size": """
                CALL dbms.queryJmx("org.neo4j:instance=kernel#0,name=Store file sizes")
                YIELD attributes
                RETURN attributes.TotalStoreSize.value as total_size_bytes
            """,
        }

        results = {}
        for query_name, query in queries.items():
            try:
                result = await self.execute_query(query)
                results[query_name] = result.records
            except Exception as e:
                logger.warning(f"Failed to get {query_name}: {e}")
                results[query_name] = []

        return results

    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._connected and self._driver is not None

    def __del__(self) -> None:
        """Cleanup database connection on object destruction."""
        if self._driver:
            self._driver.close()
