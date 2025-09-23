"""FastAPI application for the offshore leaks REST API."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import Config, load_config
from .database import DatabaseError, Neo4jDatabase, QueryError
from .models import (
    ConnectionsParameters,
    EntitySearchParameters,
    OfficerSearchParameters,
)
from .service import OffshoreLeaksService

logger = logging.getLogger(__name__)

# Global variables for application state
app_state = {}


class APIResponse(BaseModel):
    """Standard API response format."""

    success: bool = True
    data: Any = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    query_time_ms: Optional[int] = None


class PaginationInfo(BaseModel):
    """Pagination information."""

    limit: int
    offset: int
    total_count: int
    returned_count: int
    has_more: bool


class SearchResponse(BaseModel):
    """Search response with pagination."""

    results: list[dict[str, Any]]
    pagination: PaginationInfo
    query_time_ms: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting offshore leaks API server...")

    # Load configuration
    config = load_config()
    app_state["config"] = config

    # Initialize database
    database = Neo4jDatabase(config.neo4j)
    app_state["database"] = database

    # Initialize service
    service = OffshoreLeaksService(database, config.server.query_timeout)
    app_state["service"] = service

    try:
        # Connect to database
        await database.connect()
        logger.info("Database connected successfully")

        yield

    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down offshore leaks API server...")
        if database.is_connected:
            await database.disconnect()
        logger.info("API server shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Offshore Leaks API",
    description="REST API for querying offshore leaks database",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_service() -> OffshoreLeaksService:
    """Dependency to get the service instance."""
    return app_state["service"]


def get_database() -> Neo4jDatabase:
    """Dependency to get the database instance."""
    return app_state["database"]


def get_config() -> Config:
    """Dependency to get the configuration."""
    return app_state["config"]


@app.exception_handler(DatabaseError)
async def database_exception_handler(request, exc: DatabaseError):
    """Handle database errors."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content=APIResponse(success=False, error=f"Database error: {str(exc)}").dict(),
    )


@app.exception_handler(QueryError)
async def query_exception_handler(request, exc: QueryError):
    """Handle query errors."""
    logger.error(f"Query error: {exc}")
    return JSONResponse(
        status_code=400,
        content=APIResponse(success=False, error=f"Query error: {str(exc)}").dict(),
    )


@app.exception_handler(ValueError)
async def value_exception_handler(request, exc: ValueError):
    """Handle validation errors."""
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content=APIResponse(
            success=False, error=f"Validation error: {str(exc)}"
        ).dict(),
    )


# Health endpoints
@app.get("/health", response_model=APIResponse)
async def health_check(database: Neo4jDatabase = Depends(get_database)):
    """Basic health check."""
    try:
        if database.is_connected:
            db_health = await database.health_check()
            status = "healthy" if db_health.get("connected", False) else "unhealthy"
        else:
            status = "unhealthy"

        return APIResponse(
            data={
                "status": status,
                "database_connected": database.is_connected,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return APIResponse(success=False, error=str(e))


@app.get("/api/v1/health", response_model=APIResponse)
async def api_health_check(database: Neo4jDatabase = Depends(get_database)):
    """API v1 health check."""
    return await health_check(database)


@app.get("/api/v1/stats", response_model=APIResponse)
async def get_statistics(
    stat_type: str = Query("overview", description="Type of statistics to retrieve"),
    service: OffshoreLeaksService = Depends(get_service),
):
    """Get database statistics."""
    try:
        result = await service.get_statistics(stat_type)
        return APIResponse(data=result, query_time_ms=result["query_time_ms"])
    except Exception as e:
        logger.error(f"Statistics query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Search endpoints
@app.post("/api/v1/search/entities", response_model=APIResponse)
async def search_entities(
    params: EntitySearchParameters, service: OffshoreLeaksService = Depends(get_service)
):
    """Search for entities."""
    try:
        result = await service.search_entities(**params.dict(exclude_none=True))

        response_data = SearchResponse(
            results=result.results,
            pagination=PaginationInfo(
                limit=result.limit,
                offset=result.offset,
                total_count=result.total_count,
                returned_count=result.returned_count,
                has_more=(result.offset + result.returned_count) < result.total_count,
            ),
            query_time_ms=result.query_time_ms,
        )

        return APIResponse(
            data=response_data.dict(), query_time_ms=result.query_time_ms
        )
    except Exception as e:
        logger.error(f"Entity search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/search/officers", response_model=APIResponse)
async def search_officers(
    params: OfficerSearchParameters,
    service: OffshoreLeaksService = Depends(get_service),
):
    """Search for officers."""
    try:
        result = await service.search_officers(**params.dict(exclude_none=True))

        response_data = SearchResponse(
            results=result.results,
            pagination=PaginationInfo(
                limit=result.limit,
                offset=result.offset,
                total_count=result.total_count,
                returned_count=result.returned_count,
                has_more=(result.offset + result.returned_count) < result.total_count,
            ),
            query_time_ms=result.query_time_ms,
        )

        return APIResponse(
            data=response_data.dict(), query_time_ms=result.query_time_ms
        )
    except Exception as e:
        logger.error(f"Officer search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/connections", response_model=APIResponse)
async def explore_connections(
    params: ConnectionsParameters, service: OffshoreLeaksService = Depends(get_service)
):
    """Explore connections from a starting node."""
    try:
        result = await service.get_connections(**params.dict(exclude_none=True))

        response_data = SearchResponse(
            results=result.results,
            pagination=PaginationInfo(
                limit=result.limit,
                offset=result.offset,
                total_count=result.total_count,
                returned_count=result.returned_count,
                has_more=False,  # Connections don't typically use pagination
            ),
            query_time_ms=result.query_time_ms,
        )

        return APIResponse(
            data=response_data.dict(), query_time_ms=result.query_time_ms
        )
    except Exception as e:
        logger.error(f"Connection exploration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Individual entity/officer endpoints
@app.get("/api/v1/entity/{entity_id}", response_model=APIResponse)
async def get_entity(
    entity_id: str, service: OffshoreLeaksService = Depends(get_service)
):
    """Get specific entity details."""
    try:
        result = await service.search_entities(node_id=entity_id, limit=1)
        if result.results:
            return APIResponse(data=result.results[0])
        else:
            raise HTTPException(status_code=404, detail="Entity not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/officer/{officer_id}", response_model=APIResponse)
async def get_officer(
    officer_id: str, service: OffshoreLeaksService = Depends(get_service)
):
    """Get specific officer details."""
    try:
        result = await service.search_officers(node_id=officer_id, limit=1)
        if result.results:
            return APIResponse(data=result.results[0])
        else:
            raise HTTPException(status_code=404, detail="Officer not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Officer retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Advanced analysis endpoints
@app.post("/api/v1/analysis/paths", response_model=APIResponse)
async def find_shortest_paths(
    start_node_id: str,
    end_node_id: str,
    max_depth: int = Query(6, ge=1, le=10),
    relationship_types: Optional[list[str]] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    service: OffshoreLeaksService = Depends(get_service),
):
    """Find shortest paths between two nodes."""
    try:
        result = await service.find_shortest_paths(
            start_node_id=start_node_id,
            end_node_id=end_node_id,
            max_depth=max_depth,
            relationship_types=relationship_types,
            limit=limit,
        )

        return APIResponse(
            data={
                "paths": result.results,
                "total_count": result.total_count,
                "query_time_ms": result.query_time_ms,
            },
            query_time_ms=result.query_time_ms,
        )
    except Exception as e:
        logger.error(f"Path finding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/analysis/patterns", response_model=APIResponse)
async def analyze_network_patterns(
    node_id: str,
    pattern_type: str = Query("hub", regex="^(hub|bridge|cluster)$"),
    max_depth: int = Query(3, ge=1, le=5),
    min_connections: int = Query(5, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: OffshoreLeaksService = Depends(get_service),
):
    """Analyze network patterns around a node."""
    try:
        result = await service.analyze_network_patterns(
            node_id=node_id,
            pattern_type=pattern_type,
            max_depth=max_depth,
            min_connections=min_connections,
            limit=limit,
        )

        return APIResponse(
            data={
                "patterns": result.results,
                "pattern_type": pattern_type,
                "total_count": result.total_count,
                "query_time_ms": result.query_time_ms,
            },
            query_time_ms=result.query_time_ms,
        )
    except Exception as e:
        logger.error(f"Network pattern analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/analysis/common-connections", response_model=APIResponse)
async def find_common_connections(
    node_ids: list[str],
    relationship_types: Optional[list[str]] = Query(None),
    max_depth: int = Query(2, ge=1, le=4),
    limit: int = Query(20, ge=1, le=100),
    service: OffshoreLeaksService = Depends(get_service),
):
    """Find common connections between multiple nodes."""
    try:
        result = await service.find_common_connections(
            node_ids=node_ids,
            relationship_types=relationship_types,
            max_depth=max_depth,
            limit=limit,
        )

        return APIResponse(
            data={
                "common_connections": result.results,
                "source_nodes": node_ids,
                "total_count": result.total_count,
                "query_time_ms": result.query_time_ms,
            },
            query_time_ms=result.query_time_ms,
        )
    except Exception as e:
        logger.error(f"Common connections analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/analysis/temporal", response_model=APIResponse)
async def temporal_analysis(
    node_id: str,
    date_field: str = Query("incorporation_date"),
    time_window_days: int = Query(365, ge=1, le=3650),
    limit: int = Query(50, ge=1, le=200),
    service: OffshoreLeaksService = Depends(get_service),
):
    """Analyze temporal patterns in entity creation."""
    try:
        result = await service.temporal_analysis(
            node_id=node_id,
            date_field=date_field,
            time_window_days=time_window_days,
            limit=limit,
        )

        return APIResponse(
            data={
                "temporal_patterns": result.results,
                "analysis_node": node_id,
                "time_window_days": time_window_days,
                "total_count": result.total_count,
                "query_time_ms": result.query_time_ms,
            },
            query_time_ms=result.query_time_ms,
        )
    except Exception as e:
        logger.error(f"Temporal analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/analysis/compliance-risk", response_model=APIResponse)
async def compliance_risk_analysis(
    node_id: str,
    risk_jurisdictions: Optional[list[str]] = Query(None),
    max_depth: int = Query(3, ge=1, le=5),
    limit: int = Query(30, ge=1, le=100),
    service: OffshoreLeaksService = Depends(get_service),
):
    """Analyze compliance risks in entity networks."""
    try:
        result = await service.compliance_risk_analysis(
            node_id=node_id,
            risk_jurisdictions=risk_jurisdictions,
            max_depth=max_depth,
            limit=limit,
        )

        return APIResponse(
            data={
                "risk_analysis": result.results,
                "source_node": node_id,
                "risk_jurisdictions": risk_jurisdictions,
                "total_count": result.total_count,
                "query_time_ms": result.query_time_ms,
            },
            query_time_ms=result.query_time_ms,
        )
    except Exception as e:
        logger.error(f"Compliance risk analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Export endpoints
@app.post("/api/v1/export/search", response_model=APIResponse)
async def export_search_results(
    search_data: dict[str, Any],
    format: str = Query("json", regex="^(json|csv|excel)$"),
    filename: Optional[str] = Query(None),
    include_metadata: bool = Query(True),
    service: OffshoreLeaksService = Depends(get_service),
):
    """Export search results to various formats."""
    try:
        result = await service.export_results(
            data=search_data,
            format=format,
            filename=filename,
            include_metadata=include_metadata,
        )

        return APIResponse(data=result)
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/export/network", response_model=APIResponse)
async def export_network_visualization(
    connections_data: dict[str, Any],
    format: str = Query("json", regex="^(json|d3|gexf|graphml)$"),
    filename: Optional[str] = Query(None),
    service: OffshoreLeaksService = Depends(get_service),
):
    """Export network data for visualization."""
    try:
        result = await service.export_network_visualization(
            connections_data=connections_data, format=format, filename=filename
        )

        return APIResponse(data=result)
    except Exception as e:
        logger.error(f"Network export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Root endpoint
@app.get("/", response_model=APIResponse)
async def root():
    """API root endpoint."""
    return APIResponse(
        data={
            "name": "Offshore Leaks API",
            "version": "1.0.0",
            "description": "REST API for querying offshore leaks database",
            "endpoints": {
                "health": "/health",
                "documentation": "/docs",
                "api_v1": "/api/v1",
            },
        }
    )


def main():
    """Main entry point for running the API server."""
    import uvicorn

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the API server
    uvicorn.run(
        "offshore_leaks_mcp.api:app",
        host="0.0.0.0",  # nosec B104
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
