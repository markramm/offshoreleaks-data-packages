"""HTTP client for communicating with the offshore leaks API."""

from typing import Any, Optional

import httpx
from pydantic import BaseModel

from ..models import (
    ConnectionsParameters,
    EntitySearchParameters,
    OfficerSearchParameters,
)


class APIError(Exception):
    """API communication error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


class APIResponse(BaseModel):
    """API response model."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    timestamp: str
    query_time_ms: Optional[int] = None


class OffshoreLeaksClient:
    """HTTP client for the offshore leaks API."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        """Initialize the client."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(  # nosec B113
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            headers={"Content-Type": "application/json"},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def _request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        """Make HTTP request and return parsed response."""
        if not self._client:
            raise APIError("Client not initialized. Use async context manager.")

        try:
            response = await self._client.request(method, endpoint, **kwargs)
            response_data = response.json()

            if response.status_code >= 400:
                error_msg = response_data.get("error", f"HTTP {response.status_code}")
                raise APIError(error_msg, response.status_code)

            return APIResponse(**response_data)

        except httpx.TimeoutException:
            raise APIError("Request timeout") from None
        except httpx.ConnectError:
            raise APIError(
                f"Failed to connect to API server at {self.base_url}"
            ) from None
        except Exception as e:
            if isinstance(e, APIError):
                raise
            raise APIError(f"Unexpected error: {str(e)}") from e

    async def health_check(self) -> dict[str, Any]:
        """Check API health."""
        response = await self._request("GET", "/api/v1/health")
        return response.data

    async def get_statistics(self, stat_type: str = "overview") -> dict[str, Any]:
        """Get database statistics."""
        response = await self._request(
            "GET", "/api/v1/stats", params={"stat_type": stat_type}
        )
        return response.data

    async def search_entities(
        self,
        name: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        country_codes: Optional[str] = None,
        company_type: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        **kwargs,
    ) -> dict[str, Any]:
        """Search for entities."""
        params = EntitySearchParameters(
            name=name,
            jurisdiction=jurisdiction,
            country_codes=country_codes,
            company_type=company_type,
            status=status,
            source=source,
            limit=limit,
            offset=offset,
            **kwargs,
        )

        response = await self._request(
            "POST", "/api/v1/search/entities", json=params.dict(exclude_none=True)
        )
        return response.data

    async def search_officers(
        self,
        name: Optional[str] = None,
        countries: Optional[str] = None,
        country_codes: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        **kwargs,
    ) -> dict[str, Any]:
        """Search for officers."""
        params = OfficerSearchParameters(
            name=name,
            countries=countries,
            country_codes=country_codes,
            source=source,
            limit=limit,
            offset=offset,
            **kwargs,
        )

        response = await self._request(
            "POST", "/api/v1/search/officers", json=params.dict(exclude_none=True)
        )
        return response.data

    async def get_connections(
        self,
        start_node_id: str,
        relationship_types: Optional[list[str]] = None,
        max_depth: int = 2,
        node_types: Optional[list[str]] = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Explore connections from a starting node."""
        params = ConnectionsParameters(
            start_node_id=start_node_id,
            relationship_types=relationship_types,
            max_depth=max_depth,
            node_types=node_types,
            limit=limit,
        )

        response = await self._request(
            "POST", "/api/v1/connections", json=params.dict(exclude_none=True)
        )
        return response.data

    async def get_entity(self, entity_id: str) -> dict[str, Any]:
        """Get specific entity details."""
        response = await self._request("GET", f"/api/v1/entity/{entity_id}")
        return response.data

    async def get_officer(self, officer_id: str) -> dict[str, Any]:
        """Get specific officer details."""
        response = await self._request("GET", f"/api/v1/officer/{officer_id}")
        return response.data

    async def find_shortest_paths(
        self,
        start_node_id: str,
        end_node_id: str,
        max_depth: int = 6,
        relationship_types: Optional[list[str]] = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Find shortest paths between two nodes."""
        response = await self._request(
            "POST",
            "/api/v1/analysis/paths",
            params={
                "start_node_id": start_node_id,
                "end_node_id": end_node_id,
                "max_depth": max_depth,
                "limit": limit,
            },
            json=(
                {"relationship_types": relationship_types} if relationship_types else {}
            ),
        )
        return response.data

    async def analyze_network_patterns(
        self,
        node_id: str,
        pattern_type: str = "hub",
        max_depth: int = 3,
        min_connections: int = 5,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Analyze network patterns around a node."""
        response = await self._request(
            "POST",
            "/api/v1/analysis/patterns",
            params={
                "node_id": node_id,
                "pattern_type": pattern_type,
                "max_depth": max_depth,
                "min_connections": min_connections,
                "limit": limit,
            },
        )
        return response.data

    async def find_common_connections(
        self,
        node_ids: list[str],
        relationship_types: Optional[list[str]] = None,
        max_depth: int = 2,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Find common connections between multiple nodes."""
        response = await self._request(
            "POST",
            "/api/v1/analysis/common-connections",
            params={"max_depth": max_depth, "limit": limit},
            json={"node_ids": node_ids, "relationship_types": relationship_types},
        )
        return response.data

    async def temporal_analysis(
        self,
        node_id: str,
        date_field: str = "incorporation_date",
        time_window_days: int = 365,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Analyze temporal patterns in entity creation."""
        response = await self._request(
            "POST",
            "/api/v1/analysis/temporal",
            params={
                "node_id": node_id,
                "date_field": date_field,
                "time_window_days": time_window_days,
                "limit": limit,
            },
        )
        return response.data

    async def compliance_risk_analysis(
        self,
        node_id: str,
        risk_jurisdictions: Optional[list[str]] = None,
        max_depth: int = 3,
        limit: int = 30,
    ) -> dict[str, Any]:
        """Analyze compliance risks in entity networks."""
        response = await self._request(
            "POST",
            "/api/v1/analysis/compliance-risk",
            params={"node_id": node_id, "max_depth": max_depth, "limit": limit},
            json=(
                {"risk_jurisdictions": risk_jurisdictions} if risk_jurisdictions else {}
            ),
        )
        return response.data

    async def export_search_results(
        self,
        search_data: dict[str, Any],
        format: str = "json",
        filename: Optional[str] = None,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """Export search results to various formats."""
        response = await self._request(
            "POST",
            "/api/v1/export/search",
            params={
                "format": format,
                "filename": filename,
                "include_metadata": include_metadata,
            },
            json=search_data,
        )
        return response.data

    async def export_network_visualization(
        self,
        connections_data: dict[str, Any],
        format: str = "json",
        filename: Optional[str] = None,
    ) -> dict[str, Any]:
        """Export network data for visualization."""
        response = await self._request(
            "POST",
            "/api/v1/export/network",
            params={"format": format, "filename": filename},
            json=connections_data,
        )
        return response.data


def create_client(
    base_url: str = "http://localhost:8000", timeout: int = 30
) -> OffshoreLeaksClient:
    """Create a new API client instance."""
    return OffshoreLeaksClient(base_url=base_url, timeout=timeout)
