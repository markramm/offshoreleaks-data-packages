"""Configuration management for the offshore leaks MCP server."""

import os

from pydantic import BaseModel, Field


class Neo4jConfig(BaseModel):
    """Neo4j database configuration."""

    uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    user: str = Field(default="neo4j", description="Neo4j username")
    password: str = Field(description="Neo4j password")
    database: str = Field(default="neo4j", description="Neo4j database name")
    max_connection_lifetime: int = Field(
        default=1000, description="Max connection lifetime in seconds"
    )
    max_connection_pool_size: int = Field(
        default=100, description="Max connection pool size"
    )
    connection_timeout: float = Field(
        default=30.0, description="Connection timeout in seconds"
    )


class ServerConfig(BaseModel):
    """MCP server configuration."""

    name: str = Field(default="offshore-leaks-mcp-server", description="Server name")
    version: str = Field(default="0.1.0", description="Server version")
    debug: bool = Field(default=False, description="Enable debug mode")
    max_query_complexity: int = Field(
        default=1000, description="Maximum query complexity score"
    )
    default_limit: int = Field(default=20, description="Default result limit")
    max_limit: int = Field(default=100, description="Maximum result limit")
    query_timeout: float = Field(default=30.0, description="Query timeout in seconds")


class Config(BaseModel):
    """Complete application configuration."""

    neo4j: Neo4jConfig
    server: ServerConfig


def load_config() -> Config:
    """Load configuration from environment variables."""
    neo4j_config = Neo4jConfig(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", ""),
        database=os.getenv("NEO4J_DATABASE", "neo4j"),
        max_connection_lifetime=int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "1000")),
        max_connection_pool_size=int(
            os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "100")
        ),
        connection_timeout=float(os.getenv("NEO4J_CONNECTION_TIMEOUT", "30.0")),
    )

    server_config = ServerConfig(
        name=os.getenv("SERVER_NAME", "offshore-leaks-mcp-server"),
        version=os.getenv("SERVER_VERSION", "0.1.0"),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        max_query_complexity=int(os.getenv("MAX_QUERY_COMPLEXITY", "1000")),
        default_limit=int(os.getenv("DEFAULT_LIMIT", "20")),
        max_limit=int(os.getenv("MAX_LIMIT", "100")),
        query_timeout=float(os.getenv("QUERY_TIMEOUT", "30.0")),
    )

    return Config(neo4j=neo4j_config, server=server_config)
