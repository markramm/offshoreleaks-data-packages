#!/usr/bin/env python3
"""Example usage of the offshore leaks MCP server."""

import asyncio
import logging
import os

from offshore_leaks_mcp import OffshoreLeaksServer, load_config


async def main() -> None:
    """Demonstrate basic server functionality."""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Load configuration from environment
    # Set these environment variables before running:
    # NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE

    # Check if required environment variables are set
    required_env_vars = ["NEO4J_URI", "NEO4J_PASSWORD"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.info("Please set the following environment variables:")
        logger.info("  NEO4J_URI=bolt://localhost:7687")
        logger.info("  NEO4J_USER=neo4j")
        logger.info("  NEO4J_PASSWORD=your_password")
        logger.info("  NEO4J_DATABASE=neo4j")
        return

    config = load_config()
    server = OffshoreLeaksServer(config)

    try:
        # Start the server
        logger.info("Starting offshore leaks MCP server...")
        await server.start()

        # Perform health check
        health = await server.health_check()
        logger.info(f"Server health status: {health.status}")

        if health.status != "healthy":
            logger.error("Server is not healthy, exiting")
            return

        # Example 1: Search for entities
        logger.info("\n=== Example 1: Search for entities ===")
        entities_result = await server.search_entities(name="Mossack", limit=5)
        logger.info(
            f"Found {entities_result.total_count} entities, showing {entities_result.returned_count}"
        )

        for i, entity in enumerate(entities_result.results[:3], 1):
            logger.info(
                f"  {i}. {entity.get('name', 'Unknown')} ({entity.get('jurisdiction', 'N/A')})"
            )

        # Example 2: Search for officers
        logger.info("\n=== Example 2: Search for officers ===")
        officers_result = await server.search_officers(name="Ross", limit=5)
        logger.info(
            f"Found {officers_result.total_count} officers, showing {officers_result.returned_count}"
        )

        for i, officer in enumerate(officers_result.results[:3], 1):
            logger.info(
                f"  {i}. {officer.get('name', 'Unknown')} ({officer.get('countries', 'N/A')})"
            )

        # Example 3: Get database statistics
        logger.info("\n=== Example 3: Database statistics ===")
        stats = await server.get_statistics("overview")
        if stats["results"]:
            stats_data = stats["results"][0]
            logger.info(f"  Entities: {stats_data.get('entity_count', 0)}")
            logger.info(f"  Officers: {stats_data.get('officer_count', 0)}")
            logger.info(f"  Intermediaries: {stats_data.get('intermediary_count', 0)}")
            logger.info(f"  Relationships: {stats_data.get('relationship_count', 0)}")

        # Example 4: Explore connections (if we have results from earlier searches)
        if entities_result.results:
            entity = entities_result.results[0]
            entity_id = entity.get("node_id")

            if entity_id:
                logger.info(
                    f"\n=== Example 4: Connections from {entity.get('name', 'Entity')} ==="
                )
                connections_result = await server.get_connections(
                    start_node_id=entity_id, max_depth=2, limit=5
                )
                logger.info(f"Found {connections_result.returned_count} connections")

                for i, connection in enumerate(connections_result.results[:3], 1):
                    node = connection["node"]
                    distance = connection["distance"]
                    logger.info(
                        f"  {i}. {node.get('name', 'Unknown')} (distance: {distance})"
                    )

        logger.info("\n=== Example completed successfully ===")

    except Exception as e:
        logger.error(f"Error running example: {e}")
        raise
    finally:
        # Stop the server
        await server.stop()
        logger.info("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
