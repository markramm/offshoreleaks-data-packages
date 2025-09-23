#!/usr/bin/env python3
"""
Example usage script demonstrating the multi-interface offshore leaks system.

This script shows how to use all three interfaces:
1. Direct service layer (for Python applications)
2. REST API client (for web applications and remote access)
3. CLI tool (for terminal users and automation)
"""

import asyncio
import logging

from src.offshore_leaks_mcp.cli.client import APIError, create_client
from src.offshore_leaks_mcp.config import load_config
from src.offshore_leaks_mcp.database import Neo4jDatabase
from src.offshore_leaks_mcp.service import OffshoreLeaksService


async def demonstrate_service_layer():
    """Demonstrate direct service layer usage."""
    print("\n" + "=" * 60)
    print("1. DIRECT SERVICE LAYER USAGE")
    print("=" * 60)

    try:
        # Load configuration
        config = load_config()
        print("✓ Configuration loaded")

        # Initialize database and service
        database = Neo4jDatabase(config.neo4j)
        service = OffshoreLeaksService(database, config.server.query_timeout)

        # Connect to database
        await database.connect()
        print(f"✓ Database connected: {database.is_connected}")

        # Perform a simple entity search
        print("\n📊 Searching for entities with 'Apple' in name...")
        result = await service.search_entities(name="Apple", limit=3)

        print(f"Found {result.total_count} entities, showing {result.returned_count}")
        for i, entity in enumerate(result.results[:2], 1):
            print(
                f"  {i}. {entity.get('name', 'N/A')} ({entity.get('jurisdiction', 'N/A')})"
            )

        # Get database statistics
        print("\n📈 Getting database statistics...")
        stats = await service.get_statistics("overview")
        print(f"Statistics query completed in {stats['query_time_ms']}ms")
        if stats["results"]:
            print(f"  Sample stat: {stats['results'][0]}")

        # Clean up
        await database.disconnect()
        print("✓ Database disconnected")

    except Exception as e:
        print(f"❌ Service layer error: {e}")
        return False

    return True


async def demonstrate_api_client():
    """Demonstrate API client usage."""
    print("\n" + "=" * 60)
    print("2. REST API CLIENT USAGE")
    print("=" * 60)

    try:
        # Create API client
        async with create_client("http://localhost:8000", timeout=10) as client:
            print("✓ API client created")

            # Check health
            print("\n🏥 Checking API health...")
            health = await client.health_check()
            status = health.get("status", "unknown")
            print(f"API Status: {status}")

            # Search entities via API
            print("\n📊 Searching entities via REST API...")
            entities = await client.search_entities(name="Test", limit=2)

            pagination = entities.get("pagination", {})
            print(f"Found {pagination.get('total_count', 0)} entities")

            # Search officers via API
            print("\n👥 Searching officers via REST API...")
            officers = await client.search_officers(name="John", limit=2)

            pagination = officers.get("pagination", {})
            print(f"Found {pagination.get('total_count', 0)} officers")

            # Get statistics via API
            print("\n📈 Getting statistics via REST API...")
            await client.get_statistics("overview")
            print("Statistics retrieved successfully")

    except APIError as e:
        print(f"❌ API Error: {e}")
        if "Failed to connect" in str(e):
            print("💡 Tip: Make sure to start the API server first:")
            print("   offshore-api")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    return True


def demonstrate_cli_usage():
    """Demonstrate CLI tool usage with example commands."""
    print("\n" + "=" * 60)
    print("3. CLI TOOL USAGE EXAMPLES")
    print("=" * 60)

    cli_examples = [
        ("Check API health", "offshore-cli health"),
        ("Get database statistics", "offshore-cli stats"),
        (
            "Search entities",
            "offshore-cli search entities --name 'Apple Inc' --limit 5",
        ),
        (
            "Search officers",
            "offshore-cli search officers --name 'John Smith' --limit 5",
        ),
        (
            "Explore connections",
            "offshore-cli connections entity_123 --max-depth 2 --format graph",
        ),
        ("Find shortest paths", "offshore-cli analysis paths entity_123 entity_456"),
        (
            "Analyze network patterns",
            "offshore-cli analysis patterns entity_123 --type hub",
        ),
        ("Get entity details", "offshore-cli entity entity_123"),
        ("Interactive mode", "offshore-cli interactive"),
        (
            "Export search results",
            "offshore-cli search entities --name Apple --export csv --output results.csv",
        ),
        (
            "Network export",
            "offshore-cli connections entity_123 --export d3 --output network.json",
        ),
    ]

    print("📋 Available CLI commands:\n")
    for description, command in cli_examples:
        print(f"  {description}:")
        print(f"    {command}\n")

    print("💡 CLI Features:")
    print("  • Rich terminal output with colors and tables")
    print("  • Multiple output formats (table, json, graph)")
    print("  • Export capabilities (CSV, JSON, D3)")
    print("  • Interactive REPL mode")
    print("  • Progress indicators and error handling")
    print("  • Configurable API endpoint and timeouts")


def demonstrate_architecture():
    """Explain the multi-interface architecture."""
    print("\n" + "=" * 60)
    print("MULTI-INTERFACE ARCHITECTURE OVERVIEW")
    print("=" * 60)

    architecture_info = """
📐 ARCHITECTURE LAYERS:

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Server    │    │   CLI Tool      │    │   Web App       │
│   (Claude AI)   │    │   (Terminal)    │    │   (Browser)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  FastAPI REST   │
                    │  API Backend    │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Service Layer  │
                    │  (Business      │
                    │   Logic)        │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Neo4j Database │
                    └─────────────────┘

🔧 COMPONENTS:

1. **Service Layer** (OffshoreLeaksService)
   • Encapsulates all business logic
   • Handles query building and result formatting
   • Used by all interfaces for consistency

2. **FastAPI REST API** (api.py)
   • Provides HTTP endpoints for all operations
   • Standardized JSON request/response format
   • CORS support for web applications
   • Automatic OpenAPI documentation

3. **CLI Tool** (cli/)
   • Rich terminal interface with colors and tables
   • Multiple output formats and export options
   • Interactive REPL mode for exploration
   • Progress indicators and error handling

4. **MCP Server** (server.py)
   • Integration with Claude AI and other MCP clients
   • Same functionality as other interfaces
   • Now delegates to service layer

🚀 BENEFITS:

• **Consistency**: Same data, queries, and results across all interfaces
• **Maintainability**: Single source of truth for business logic
• **Scalability**: Each interface can be deployed independently
• **Flexibility**: Choose the right tool for each use case
• **Developer Experience**: Type-safe, well-documented APIs

🎯 USE CASES:

• **CLI Tool**: Terminal users, automation scripts, CI/CD pipelines
• **REST API**: Web applications, mobile apps, third-party integrations
• **MCP Server**: AI agents, Claude AI integration, research workflows
• **Direct Service**: Python applications, Jupyter notebooks, data analysis
"""

    print(architecture_info)


async def main():
    """Main demonstration function."""
    print("🏖️  OFFSHORE LEAKS MULTI-INTERFACE DEMONSTRATION")
    print("=" * 80)

    # Show architecture overview
    demonstrate_architecture()

    # Demonstrate each interface
    print("\n" + "🔄 INTERFACE DEMONSTRATIONS" + "\n")

    # 1. Service layer (always works)
    service_success = await demonstrate_service_layer()

    # 2. API client (requires API server)
    api_success = await demonstrate_api_client()

    # 3. CLI examples
    demonstrate_cli_usage()

    # Summary
    print("\n" + "=" * 60)
    print("DEMONSTRATION SUMMARY")
    print("=" * 60)

    print(f"✓ Service Layer: {'SUCCESS' if service_success else 'FAILED'}")
    print(
        f"{'✓' if api_success else '❌'} REST API: {'SUCCESS' if api_success else 'FAILED (server not running)'}"
    )
    print("📋 CLI Tool: Examples shown (requires API server)")

    if not api_success:
        print("\n💡 To test API and CLI functionality:")
        print("1. Start the API server in one terminal:")
        print("   offshore-api")
        print("2. Run CLI commands in another terminal:")
        print("   offshore-cli health")
        print("   offshore-cli search entities --name Apple --limit 5")

    print("\n🎉 Multi-interface offshore leaks system is ready!")
    print("Choose the interface that best fits your needs:")
    print("• 🖥️  CLI for terminal usage and automation")
    print("• 🌐 REST API for web apps and integrations")
    print("• 🤖 MCP Server for AI agent integration")
    print("• 🐍 Service layer for Python applications")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run demonstration
    asyncio.run(main())
