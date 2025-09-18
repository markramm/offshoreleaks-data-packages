"""Database connection and query management for Neo4j."""

import logging
from typing import Any, Dict, List, Optional

from neo4j import Driver, GraphDatabase
from pydantic import BaseModel

from .config import Neo4jConfig

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

    records: List[Dict[str, Any]]
    summary: Dict[str, Any]
    query_time_ms: Optional[int] = None


class Neo4jDatabase:
    """Neo4j database connection and query manager."""

    def __init__(self, config: Neo4jConfig) -> None:
        """Initialize database connection."""
        self.config = config
        self._driver: Optional[Driver] = None
        self._connected = False

    async def connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self._driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password),
                max_connection_lifetime=self.config.max_connection_lifetime,
                max_connection_pool_size=self.config.max_connection_pool_size,
                connection_timeout=self.config.connection_timeout,
            )

            # Test connection
            await self.health_check()
            self._connected = True
            logger.info("Successfully connected to Neo4j database")

        except Exception as e:
            logger.error(f"Failed to connect to Neo4j database: {e}")
            raise ConnectionError(f"Database connection failed: {e}") from e

    async def disconnect(self) -> None:
        """Close database connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            self._connected = False
            logger.info("Disconnected from Neo4j database")

    async def health_check(self) -> Dict[str, Any]:
        """Check database health and connectivity."""
        if not self._driver:
            raise ConnectionError("Database not connected")

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
            raise ConnectionError(f"Health check failed: {e}") from e

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> QueryResult:
        """Execute a Cypher query and return structured results."""
        if not self._driver:
            raise ConnectionError("Database not connected")

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
                    summary = {
                        "query_type": result.summary().query_type,
                        "counters": dict(result.summary().counters),
                        "result_available_after": result.summary().result_available_after,
                        "result_consumed_after": result.summary().result_consumed_after,
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
                    raise QueryError(f"Query execution failed: {e}") from e

        except Exception as e:
            if isinstance(e, QueryError):
                raise
            logger.error(f"Database session error: {e}")
            raise ConnectionError(f"Database session failed: {e}") from e

    async def get_database_info(self) -> Dict[str, Any]:
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
