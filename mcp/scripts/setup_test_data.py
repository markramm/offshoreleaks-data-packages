#!/usr/bin/env python3
"""Setup script to create minimal test data for E2E testing.

This script creates a small dataset in Neo4j for testing purposes.
Use this when you don't have access to the full ICIJ offshore leaks dataset.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from offshore_leaks_mcp.config import Neo4jConfig
from offshore_leaks_mcp.database import Neo4jDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_test_data(database: Neo4jDatabase) -> None:
    """Create minimal test data for E2E testing."""

    logger.info("Creating test data...")

    # Clear any existing test data
    await database.execute_query(
        """
        MATCH (n)
        WHERE n.node_id STARTS WITH 'test_'
        DETACH DELETE n
    """
    )

    # Create entities
    await database.execute_query(
        """
        CREATE (e1:Entity {
            node_id: 'test_entity_1',
            name: 'Apple Inc.',
            jurisdiction: 'Nevada',
            status: 'Active',
            incorporation_date: '2000-01-01',
            company_type: 'Corporation',
            address: '1 Infinite Loop, Cupertino, CA',
            countries: 'United States',
            sourceID: 'test_source'
        })
        CREATE (e2:Entity {
            node_id: 'test_entity_2',
            name: 'Google Holdings LLC',
            jurisdiction: 'Delaware',
            status: 'Active',
            incorporation_date: '2001-02-15',
            company_type: 'LLC',
            address: '1600 Amphitheatre Parkway, Mountain View, CA',
            countries: 'United States',
            sourceID: 'test_source'
        })
        CREATE (e3:Entity {
            node_id: 'test_entity_3',
            name: 'Offshore Company Ltd',
            jurisdiction: 'British Virgin Islands',
            status: 'Active',
            incorporation_date: '2010-05-20',
            company_type: 'Limited Company',
            address: 'P.O. Box 123, Road Town, Tortola',
            countries: 'British Virgin Islands',
            sourceID: 'test_source'
        })
        CREATE (e4:Entity {
            node_id: 'test_entity_4',
            name: 'Tech Consulting Services',
            jurisdiction: 'Cayman Islands',
            status: 'Active',
            incorporation_date: '2015-03-10',
            company_type: 'Exempted Company',
            address: 'Cricket Square, George Town',
            countries: 'Cayman Islands',
            sourceID: 'test_source'
        })
        CREATE (e5:Entity {
            node_id: 'test_entity_5',
            name: 'Investment Holdings Corp',
            jurisdiction: 'Panama',
            status: 'Active',
            incorporation_date: '2012-08-05',
            company_type: 'Corporation',
            address: 'Via España, Panama City',
            countries: 'Panama',
            sourceID: 'test_source'
        })
    """
    )

    # Create officers
    await database.execute_query(
        """
        CREATE (o1:Officer {
            node_id: 'test_officer_1',
            name: 'John Smith',
            countries: 'United States',
            sourceID: 'test_source'
        })
        CREATE (o2:Officer {
            node_id: 'test_officer_2',
            name: 'Jane Wilson',
            countries: 'United Kingdom',
            sourceID: 'test_source'
        })
        CREATE (o3:Officer {
            node_id: 'test_officer_3',
            name: 'Michael Johnson',
            countries: 'Canada',
            sourceID: 'test_source'
        })
        CREATE (o4:Officer {
            node_id: 'test_officer_4',
            name: 'Sarah Davis',
            countries: 'Australia',
            sourceID: 'test_source'
        })
    """
    )

    # Create intermediaries
    await database.execute_query(
        """
        CREATE (i1:Intermediary {
            node_id: 'test_intermediary_1',
            name: 'Global Legal Services',
            address: '123 Financial District, London',
            countries: 'United Kingdom',
            sourceID: 'test_source'
        })
        CREATE (i2:Intermediary {
            node_id: 'test_intermediary_2',
            name: 'International Consulting Group',
            address: '456 Business Avenue, Singapore',
            countries: 'Singapore',
            sourceID: 'test_source'
        })
    """
    )

    # Create addresses
    await database.execute_query(
        """
        CREATE (a1:Address {
            node_id: 'test_address_1',
            address: '1 Infinite Loop, Cupertino, CA 95014',
            countries: 'United States',
            sourceID: 'test_source'
        })
        CREATE (a2:Address {
            node_id: 'test_address_2',
            address: 'P.O. Box 456, Road Town, Tortola, BVI',
            countries: 'British Virgin Islands',
            sourceID: 'test_source'
        })
    """
    )

    # Create relationships
    await database.execute_query(
        """
        MATCH (e1:Entity {node_id: 'test_entity_1'})
        MATCH (o1:Officer {node_id: 'test_officer_1'})
        MATCH (i1:Intermediary {node_id: 'test_intermediary_1'})
        MATCH (a1:Address {node_id: 'test_address_1'})
        CREATE (o1)-[:officer_of {link: 'test_link_1', sourceID: 'test_source'}]->(e1)
        CREATE (e1)-[:intermediary_of {link: 'test_link_2', sourceID: 'test_source'}]->(i1)
        CREATE (e1)-[:registered_address {link: 'test_link_3', sourceID: 'test_source'}]->(a1)
    """
    )

    await database.execute_query(
        """
        MATCH (e2:Entity {node_id: 'test_entity_2'})
        MATCH (o2:Officer {node_id: 'test_officer_2'})
        MATCH (i1:Intermediary {node_id: 'test_intermediary_1'})
        CREATE (o2)-[:officer_of {link: 'test_link_4', sourceID: 'test_source'}]->(e2)
        CREATE (e2)-[:intermediary_of {link: 'test_link_5', sourceID: 'test_source'}]->(i1)
    """
    )

    await database.execute_query(
        """
        MATCH (e3:Entity {node_id: 'test_entity_3'})
        MATCH (o3:Officer {node_id: 'test_officer_3'})
        MATCH (i2:Intermediary {node_id: 'test_intermediary_2'})
        MATCH (a2:Address {node_id: 'test_address_2'})
        CREATE (o3)-[:officer_of {link: 'test_link_6', sourceID: 'test_source'}]->(e3)
        CREATE (e3)-[:intermediary_of {link: 'test_link_7', sourceID: 'test_source'}]->(i2)
        CREATE (e3)-[:registered_address {link: 'test_link_8', sourceID: 'test_source'}]->(a2)
    """
    )

    await database.execute_query(
        """
        MATCH (e4:Entity {node_id: 'test_entity_4'})
        MATCH (e5:Entity {node_id: 'test_entity_5'})
        MATCH (o4:Officer {node_id: 'test_officer_4'})
        CREATE (o4)-[:officer_of {link: 'test_link_9', sourceID: 'test_source'}]->(e4)
        CREATE (o4)-[:officer_of {link: 'test_link_10', sourceID: 'test_source'}]->(e5)
        CREATE (e4)-[:connected_to {link: 'test_link_11', sourceID: 'test_source'}]->(e5)
    """
    )

    logger.info("Test data created successfully!")


async def verify_test_data(database: Neo4jDatabase) -> None:
    """Verify that test data was created correctly."""

    logger.info("Verifying test data...")

    # Count nodes
    result = await database.execute_query(
        """
        MATCH (n)
        WHERE n.node_id STARTS WITH 'test_'
        RETURN labels(n)[0] as node_type, count(n) as count
        ORDER BY node_type
    """
    )

    logger.info("Node counts:")
    for record in result.records:
        logger.info(f"  {record['node_type']}: {record['count']}")

    # Count relationships
    result = await database.execute_query(
        """
        MATCH (n)-[r]->(m)
        WHERE n.node_id STARTS WITH 'test_' AND m.node_id STARTS WITH 'test_'
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY rel_type
    """
    )

    logger.info("Relationship counts:")
    for record in result.records:
        logger.info(f"  {record['rel_type']}: {record['count']}")

    # Test a sample search
    result = await database.execute_query(
        """
        MATCH (e:Entity)
        WHERE e.node_id STARTS WITH 'test_' AND e.name CONTAINS 'Apple'
        RETURN e.name as name, e.jurisdiction as jurisdiction
    """
    )

    if result.records:
        logger.info("Sample search results:")
        for record in result.records:
            logger.info(f"  {record['name']} ({record['jurisdiction']})")

    logger.info("Test data verification complete!")


async def main():
    """Main setup function."""

    # Get database configuration from environment
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")

    if not neo4j_password:
        neo4j_password = input("Enter Neo4j password: ")

    # Create configuration
    neo4j_config = Neo4jConfig(
        uri=neo4j_uri,
        user=neo4j_user,
        password=neo4j_password,
        database=neo4j_database,
    )

    # Connect to database
    database = Neo4jDatabase(neo4j_config)

    try:
        logger.info(f"Connecting to Neo4j at {neo4j_uri}...")
        await database.connect()

        # Verify connection
        health = await database.health_check()
        logger.info(f"Database health: {health['status']}")

        # Create test data
        await create_test_data(database)

        # Verify test data
        await verify_test_data(database)

        logger.info("✅ Test data setup complete!")
        logger.info("\nTo run E2E tests:")
        logger.info("export RUN_E2E_TESTS=1")
        logger.info(f"export E2E_NEO4J_URI={neo4j_uri}")
        logger.info(f"export E2E_NEO4J_PASSWORD={neo4j_password}")
        logger.info("pytest tests/test_e2e.py -v")

    except Exception as e:
        logger.error(f"Error setting up test data: {e}")
        return 1

    finally:
        await database.disconnect()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
