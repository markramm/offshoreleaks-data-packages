"""Data models for the offshore leaks MCP server."""

from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, Field


class BaseNode(BaseModel):
    """Base model for all graph nodes."""

    node_id: str = Field(description="Unique identifier for the node")
    name: str = Field(description="Name of the node")
    source_id: str = Field(alias="sourceID", description="Source dataset identifier")
    valid_until: date = Field(description="Date until which this data is valid")


class Entity(BaseNode):
    """Offshore entity (company, trust, foundation)."""

    jurisdiction: str = Field(
        description="Jurisdiction code where entity is registered"
    )
    jurisdiction_description: str = Field(
        description="Human-readable jurisdiction name"
    )
    address: Optional[str] = Field(
        default=None, description="Registered address of the entity"
    )
    incorporation_date: Optional[date] = Field(
        default=None, description="Date of incorporation"
    )
    closed_date: Optional[date] = Field(
        default=None, description="Date entity was closed or struck off"
    )
    company_type: Optional[str] = Field(
        default=None, description="Type of company (Corporation, LLC, Trust, etc.)"
    )
    status: Optional[str] = Field(
        default=None, description="Current status (Active, Defaulted, Struck off, etc.)"
    )
    countries: Optional[str] = Field(
        default=None, description="Countries associated with the entity"
    )
    country_codes: Optional[str] = Field(default=None, description="ISO country codes")
    service_provider: Optional[str] = Field(
        default=None, description="Service provider that created/manages the entity"
    )
    ibc_ruc: Optional[str] = Field(
        default=None, alias="ibcRUC", description="IBC or RUC number"
    )
    note: Optional[str] = Field(
        default=None, description="Additional notes about the entity"
    )
    entity_type: Optional[str] = Field(
        default=None, alias="type", description="Entity type classification"
    )


class Officer(BaseNode):
    """Individual person who is an officer of an entity."""

    countries: Optional[str] = Field(
        default=None, description="Countries associated with the officer"
    )
    country_codes: Optional[str] = Field(default=None, description="ISO country codes")
    note: Optional[str] = Field(
        default=None, description="Additional notes about the officer"
    )


class Intermediary(BaseNode):
    """Intermediary organization (law firm, bank, corporate service provider)."""

    countries: Optional[str] = Field(
        default=None, description="Countries where intermediary operates"
    )
    country_codes: Optional[str] = Field(default=None, description="ISO country codes")


class Other(BaseNode):
    """Other type of entity or intermediary."""

    jurisdiction: Optional[str] = Field(default=None, description="Jurisdiction code")
    jurisdiction_description: Optional[str] = Field(
        default=None, description="Human-readable jurisdiction name"
    )
    countries: Optional[str] = Field(default=None, description="Associated countries")
    country_codes: Optional[str] = Field(default=None, description="ISO country codes")
    status: Optional[str] = Field(default=None, description="Status")
    note: Optional[str] = Field(default=None, description="Additional notes")


class Address(BaseNode):
    """Physical address."""

    address: str = Field(description="Full address text")
    countries: Optional[str] = Field(
        default=None, description="Countries associated with address"
    )
    country_codes: Optional[str] = Field(default=None, description="ISO country codes")


class Relationship(BaseModel):
    """Relationship between nodes in the graph."""

    relationship_type: str = Field(alias="type", description="Type of relationship")
    source_node_id: str = Field(description="Source node identifier")
    target_node_id: str = Field(description="Target node identifier")
    properties: Optional[dict[str, Any]] = Field(
        default=None, description="Additional relationship properties"
    )


class SearchParameters(BaseModel):
    """Base search parameters."""

    limit: int = Field(
        default=20, ge=1, le=100, description="Maximum number of results to return"
    )
    offset: int = Field(
        default=0, ge=0, description="Number of results to skip for pagination"
    )


class EntitySearchParameters(SearchParameters):
    """Search parameters for entities."""

    name: Optional[str] = Field(
        default=None, description="Partial or full name of the entity to search for"
    )
    jurisdiction: Optional[str] = Field(
        default=None,
        description="Jurisdiction code or description where the entity is registered",
    )
    country_codes: Optional[str] = Field(
        default=None, description="ISO country codes associated with the entity"
    )
    company_type: Optional[str] = Field(
        default=None, description="Type of company (e.g., Corporation, LLC, Trust)"
    )
    status: Optional[str] = Field(
        default=None,
        description="Status of the entity (e.g., Active, Defaulted, Struck off)",
    )
    incorporation_date_from: Optional[date] = Field(
        default=None, description="Search entities incorporated after this date"
    )
    incorporation_date_to: Optional[date] = Field(
        default=None, description="Search entities incorporated before this date"
    )
    source: Optional[str] = Field(default=None, description="Filter by data source")


class OfficerSearchParameters(SearchParameters):
    """Search parameters for officers."""

    name: Optional[str] = Field(
        default=None, description="Partial or full name of the officer to search for"
    )
    countries: Optional[str] = Field(
        default=None, description="Countries associated with the officer"
    )
    country_codes: Optional[str] = Field(
        default=None, description="ISO country codes associated with the officer"
    )
    source: Optional[str] = Field(default=None, description="Filter by data source")


class ConnectionsParameters(BaseModel):
    """Parameters for exploring connections."""

    start_node_id: str = Field(
        description="Node ID to start the relationship exploration from"
    )
    relationship_types: Optional[list[str]] = Field(
        default=None,
        description="Types of relationships to follow. If empty, follows all relationship types",
    )
    max_depth: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Maximum number of relationship hops to explore",
    )
    node_types: Optional[list[str]] = Field(
        default=None,
        description="Types of nodes to include in results. If empty, includes all node types",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of connected nodes to return",
    )


class SearchResult(BaseModel):
    """Generic search result container."""

    total_count: int = Field(description="Total number of results available")
    returned_count: int = Field(description="Number of results in this response")
    offset: int = Field(description="Offset used for this query")
    limit: int = Field(description="Limit used for this query")
    results: list[dict[str, Any]] = Field(description="Array of result objects")
    query_time_ms: Optional[int] = Field(
        default=None, description="Query execution time in milliseconds"
    )


class HealthStatus(BaseModel):
    """Health check response with resilience information."""

    status: str = Field(description="Health status (healthy/unhealthy/degraded)")
    database_connected: bool = Field(description="Database connection status")
    database_status: str = Field(
        default="unknown", description="Database health status"
    )
    server_running: bool = Field(description="Server running status")
    timestamp: Any = Field(description="Health check timestamp")
    components: dict[str, Any] = Field(
        default_factory=dict, description="Component health details"
    )
    error_counts: dict[str, int] = Field(
        default_factory=dict, description="Error counts by type"
    )
    circuit_breaker_states: dict[str, str] = Field(
        default_factory=dict, description="Circuit breaker states"
    )
    version: str = Field(default="0.1.0", description="Server version")
    details: Optional[dict[str, Any]] = Field(
        default=None, description="Additional health details"
    )
