# Offshore Leaks MCP Server

A Model Context Protocol (MCP) server providing access to the ICIJ Offshore Leaks database for research and investigative journalism purposes.

## Overview

This MCP server enables Claude and other AI assistants to query the International Consortium of Investigative Journalists (ICIJ) Offshore Leaks database, which contains data from:

- Paradise Papers
- Panama Papers
- Offshore Leaks
- Bahamas Leaks
- Pandora Papers

## Features

- **Read-only access** to public offshore financial data
- **Graph-based queries** leveraging Neo4j relationships
- **Network analysis** tools for investigating connections
- **Research-focused** with ethical usage guidelines
- **Rate limiting** and query complexity controls

## Quick Start

### Prerequisites

- Python 3.10+
- Neo4j database with offshore leaks data loaded
- MCP-compatible client (like Claude Desktop)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

### Configuration

Create a `.env` file:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=offshoreleaks
```

### Running the Server

```bash
# Development mode
python -m offshore_leaks_mcp.server

# Production mode
offshore-leaks-mcp
```

## API Reference

See [API Specification](docs/api-spec.json) for complete tool definitions and schemas.

### Core Tools

- `search_entities` - Find offshore companies, trusts, foundations
- `search_officers` - Find individuals by name/role
- `get_connections` - Explore relationships between nodes
- `analyze_network` - Network analysis and centrality measures

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev,test]"

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Code formatting
black src tests
ruff check src tests

# Type checking
mypy src
```

### Testing

```bash
# Unit tests only
pytest -m "not integration"

# Integration tests (requires running Neo4j)
pytest -m integration

# All tests
pytest
```

## Usage Guidelines

This server provides access to public data released by ICIJ for legitimate research and journalistic purposes. Users must:

- Verify information independently before making public claims
- Respect privacy rights and presumption of innocence
- Use for legitimate research, journalism, or law enforcement only
- Cite ICIJ as the data source in any publications
- Not use for harassment, doxxing, or other malicious activities

## Disclaimer

The presence of individuals or entities in this database does not imply wrongdoing. Offshore structures have legitimate uses.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Attribution

Data provided by the International Consortium of Investigative Journalists (ICIJ) Offshore Leaks Database.
