# MCP Integration Guide

This document explains how to integrate the Offshore Leaks MCP server with Claude Desktop and other MCP-compatible clients.

## Overview

The Offshore Leaks MCP Server provides tools for investigating offshore financial networks through Claude's interface. It exposes the Neo4j offshore leaks database via the Model Context Protocol, enabling natural language queries about entities, officers, intermediaries, and their relationships.

## Prerequisites

### Python Version
- **Python 3.10 or higher** is required for MCP integration
- The base server works with Python 3.9+, but MCP protocol requires 3.10+

### Database Requirements
- Neo4j database with offshore leaks data loaded
- Network access to the Neo4j instance
- Valid authentication credentials

### MCP Library
Install the MCP-enabled version:
```bash
pip install -e ".[mcp]"
```

## Claude Desktop Configuration

### 1. Locate Claude Desktop Config

Find your Claude Desktop configuration file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### 2. Add Server Configuration

Add the offshore leaks server to your configuration:

```json
{
  "mcpServers": {
    "offshore-leaks": {
      "command": "offshore-leaks-mcp-server",
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your_password_here",
        "NEO4J_DATABASE": "offshoreleaks",
        "DEBUG": "false"
      }
    }
  }
}
```

### 3. Alternative Python Module Configuration

If the command is not in your PATH, use the Python module directly:

```json
{
  "mcpServers": {
    "offshore-leaks": {
      "command": "python",
      "args": ["-m", "offshore_leaks_mcp.mcp_server"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your_password_here",
        "NEO4J_DATABASE": "offshoreleaks"
      }
    }
  }
}
```

## Available Tools

Once configured, Claude will have access to these investigation tools:

### 1. search_entities
Search for offshore entities (companies, trusts, foundations):
```
Find companies registered in the British Virgin Islands
Search for entities with "Mossack" in the name
Show me active corporations from the Panama Papers
```

### 2. search_officers
Search for individuals who are officers of entities:
```
Find officers named "John Smith"
Search for officers associated with Russian entities
Show me officers from the Paradise Papers dataset
```

### 3. get_connections
Explore relationships between entities:
```
Show connections from entity ID 12345 within 2 degrees
Find relationships between this officer and other entities
Explore the network around this company
```

### 4. get_statistics
Get database statistics and metadata:
```
Show overview statistics of the database
Break down entities by jurisdiction
Display relationship type counts
```

### 5. analyze_network
Analyze network patterns around specific nodes:
```
Analyze the network structure around this entity
Show network patterns for this officer
Provide network analysis for entity ID 67890
```

## Available Resources

The server also provides these resources for context:

- **Database Schema**: Complete schema information
- **Data Sources**: Details about Paradise Papers, Panama Papers, etc.
- **Jurisdictions**: List of jurisdictions with entity counts
- **Investigation Guide**: Best practices for offshore investigations

## Example Usage Scenarios

### 1. Entity Investigation
```
Claude, I want to investigate Appleby, the offshore law firm from the Paradise Papers.
Can you search for entities associated with them and show me their network connections?
```

### 2. Officer Research
```
I'm researching individuals connected to British Virgin Islands companies.
Search for officers from that jurisdiction and show me their entity relationships.
```

### 3. Network Analysis
```
For entity ID 123456, perform a network analysis to understand its connections
and show me the key relationships within 3 degrees of separation.
```

### 4. Jurisdiction Analysis
```
Show me statistics about entities by jurisdiction and help me understand
which offshore havens have the most activity in this database.
```

## Troubleshooting

### Connection Issues
- Verify Neo4j is running and accessible
- Check database credentials in environment variables
- Ensure firewall allows Neo4j connections

### Python Version Issues
```bash
# Check Python version
python --version

# Must be 3.10+
# If not, use pyenv or conda to install Python 3.10+
```

### MCP Library Issues
```bash
# Reinstall with MCP support
pip uninstall offshore-leaks-mcp-server
pip install -e ".[mcp]"
```

### Claude Desktop Connection
- Restart Claude Desktop after configuration changes
- Check logs in Claude Desktop for error messages
- Verify the command path is correct

## Security Considerations

### Environment Variables
Never commit passwords to version control:
- Use environment variables for credentials
- Consider using `.env` files for local development
- Use secrets management in production

### Network Security
- Use TLS for Neo4j connections in production
- Restrict database access to authorized hosts
- Consider VPN for remote database access

### Data Privacy
- This database contains public data from journalism investigations
- Always respect privacy rights and presumption of innocence
- Use only for legitimate research and investigative purposes

## Performance Tuning

### Query Optimization
- Use specific search criteria to limit result sets
- Start with small limits and increase as needed
- Use connection depth limits to avoid expensive queries

### Database Configuration
- Ensure Neo4j has adequate memory allocation
- Configure appropriate connection pool sizes
- Monitor query performance and add indexes as needed

## Development and Testing

### Local Development
```bash
# Start the MCP server directly for testing
python -m offshore_leaks_mcp.mcp_server

# Test with example queries
echo '{"method": "tools/list"}' | python -m offshore_leaks_mcp.mcp_server
```

### Integration Testing
- Test each tool with various parameter combinations
- Verify error handling for invalid inputs
- Check performance with large result sets

## Support and Contribution

For issues, questions, or contributions:
- Check the project repository for documentation
- Submit issues with detailed error messages
- Include environment information in bug reports

## Ethical Usage Guidelines

This tool provides access to data from journalistic investigations into offshore finance. Users must:
- Respect privacy rights and presumption of innocence
- Use for legitimate research, journalism, or law enforcement
- Verify information independently before publication
- Cite ICIJ as the data source
- Follow responsible disclosure practices

The presence of individuals or entities in this database does not imply wrongdoing.
