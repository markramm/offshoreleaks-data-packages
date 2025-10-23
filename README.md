# Offshore Leaks Database & MCP Server

[![Neo4j](https://img.shields.io/badge/Neo4j-5.15+-blue.svg)](https://neo4j.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Server-orange.svg)](https://modelcontextprotocol.io/)

**Comprehensive MCP server for querying the ICIJ Offshore Leaks database** - Panama Papers, Paradise Papers, and more.

This repository provides an MCP (Model Context Protocol) server that enables AI assistants like Claude to search and analyze the Offshore Leaks database containing information about offshore entities, officers, intermediaries, and their connections.

## 🌟 Features

- **🔍 Entity Search**: Search 814,000+ offshore companies and organizations
- **👥 Officer Search**: Query 770,000+ individuals associated with offshore entities
- **🔗 Connection Exploration**: Discover relationships between entities, officers, and intermediaries
- **📊 Network Analysis**: Analyze patterns and connections in offshore networks
- **🤖 MCP Protocol**: Direct integration with Claude and other MCP-compatible AI assistants
- **🐳 Docker-Ready**: Simple Docker-based Neo4j setup
- **✅ Verified & Tested**: Working with 2M+ node database

## 📊 Database Contents

The Offshore Leaks database includes:

| Node Type | Count | Description |
|-----------|-------|-------------|
| **Entity** | 814,344 | Offshore companies, trusts, and organizations |
| **Officer** | 770,176 | People associated with entities |
| **Address** | 402,246 | Registered addresses |
| **Intermediary** | 26,768 | Law firms, banks, intermediaries |
| **Other** | 2,989 | Other related entities |
| **Total Nodes** | **2,016,523** | |
| **Relationships** | **3,339,267** | Connections between all entities |

**Data Sources**: Panama Papers, Paradise Papers, Offshore Leaks, Bahamas Leaks, and more from ICIJ.

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (for Neo4j database)
- **Python 3.9+**
- **Offshore Leaks database dump** (download from [ICIJ](https://offshoreleaks.icij.org/))

### 1. Set Up the Database

Follow the comprehensive setup guide: **[DATABASE_SETUP.md](DATABASE_SETUP.md)**

Quick Docker setup:

```bash
# Create volume and load database
docker volume create offshore-leaks-data

docker run --rm \
  -v offshore-leaks-data:/data \
  -v /path/to/dumps:/dumps \
  neo4j:5.15 \
  bash -c "neo4j-admin database load neo4j --from-stdin < /dumps/icij-offshoreleaks-5.13.0.dump"

# Start Neo4j
docker run -d \
  --name offshore-leaks-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -v offshore-leaks-data:/data \
  -e NEO4J_AUTH=neo4j/offshoreleaks \
  -e NEO4J_dbms_memory_heap_max__size=4G \
  -e NEO4J_dbms_memory_pagecache_size=2G \
  neo4j:5.15
```

### 2. Configure MCP Server

```bash
cd mcp

# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
# NEO4J_URI=bolt://localhost:7687
# NEO4J_PASSWORD=offshoreleaks
```

### 3. Install MCP Server

```bash
cd mcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with MCP support (requires Python 3.10+)
pip install -e ".[mcp]"

# Or install base version (Python 3.9+)
pip install -e .
```

### 4. Launch MCP Server

#### Option A: Run Standalone Server

```bash
# Activate environment
source venv/bin/activate

# Start MCP server
python -m offshore_leaks_mcp.mcp_server
```

#### Option B: Integrate with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "offshore-leaks": {
      "command": "python",
      "args": [
        "-m",
        "offshore_leaks_mcp.mcp_server"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "offshoreleaks",
        "NEO4J_DATABASE": "neo4j"
      },
      "cwd": "/path/to/offshoreleaks-data-packages/mcp"
    }
  }
}
```

Then restart Claude Desktop. The server will appear in the MCP servers list.

### 5. Test the Server

```bash
# Test database connection
python << EOF
import asyncio
from offshore_leaks_mcp.config import load_config
from offshore_leaks_mcp.database import Neo4jDatabase

async def test():
    cfg = load_config()
    db = Neo4jDatabase(cfg.neo4j)
    await db.connect()
    result = await db.execute_query('MATCH (n) RETURN count(n) as count')
    print(f"✓ Connected! Nodes: {result.records[0]['count']:,}")
    await db.disconnect()

asyncio.run(test())
EOF
```

## 💡 Usage Examples

### Using with Claude Desktop

Once configured, you can ask Claude questions like:

```
"Search the Offshore Leaks database for entities related to 'Trump'"

"Find officers associated with companies in the British Virgin Islands"

"Show me connections between entity ID 10050150 and other entities"

"What are the most common jurisdictions in the database?"
```

### Using the Python API

```python
import asyncio
from offshore_leaks_mcp.config import load_config
from offshore_leaks_mcp.database import Neo4jDatabase
from offshore_leaks_mcp.queries import OffshoreLeaksQueries

async def search_entities():
    cfg = load_config()
    db = Neo4jDatabase(cfg.neo4j)
    await db.connect()

    # Search for entities
    query, params = OffshoreLeaksQueries.search_entities(
        name="trump",
        limit=10
    )
    result = await db.execute_query(query, params)

    for record in result.records:
        entity = record['e']
        print(f"{entity['name']} ({entity['jurisdiction']})")

    await db.disconnect()

asyncio.run(search_entities())
```

### Direct Neo4j Queries

Access Neo4j Browser at http://localhost:7474

```cypher
// Search for entities
MATCH (e:Entity)
WHERE e.name =~ '(?i).*trump.*'
RETURN e.name, e.jurisdiction, e.status
LIMIT 10

// Find officer connections
MATCH (o:Officer)-[r:OFFICER_OF]->(e:Entity)
WHERE o.name CONTAINS 'Smith'
RETURN o.name, e.name, e.jurisdiction
LIMIT 20

// Explore network
MATCH path = (start)-[*1..3]-(connected)
WHERE start.node_id = 10050150
RETURN path
LIMIT 50
```

## 📚 Documentation

- **[DATABASE_SETUP.md](DATABASE_SETUP.md)** - Complete database setup guide
- **[mcp/DATABASE_FIX.md](mcp/DATABASE_FIX.md)** - Technical details of recent fixes
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **[mcp/README.md](mcp/README.md)** - Detailed MCP server documentation

## 🏗️ Architecture

```
┌─────────────────┐
│   Claude AI     │
│   (via MCP)     │
└────────┬────────┘
         │
┌────────▼────────┐
│  MCP Server     │
│  (Python)       │
└────────┬────────┘
         │
┌────────▼────────┐
│  Neo4j Database │
│  (Docker)       │
└─────────────────┘
```

## 🔧 Troubleshooting

### Database Connection Issues

```bash
# Check Neo4j is running
docker ps | grep offshore-leaks-neo4j

# View logs
docker logs offshore-leaks-neo4j

# Test connection
docker exec offshore-leaks-neo4j cypher-shell -u neo4j -p offshoreleaks "RETURN 'connected' as status"
```

### MCP Server Not Appearing in Claude

1. Check config file path is correct
2. Verify environment variables are set
3. Restart Claude Desktop completely
4. Check Claude Desktop logs: `~/Library/Logs/Claude/`

### Import Errors

```bash
# Reinstall dependencies
cd mcp
source venv/bin/activate
pip install -e ".[mcp]"
```

See **[DATABASE_SETUP.md](DATABASE_SETUP.md)** for more troubleshooting.

## 🔐 Security & Privacy

- **Local Only**: Database and MCP server run locally on your machine
- **No External Connections**: Data never leaves your computer
- **Git Protected**: `.gitignore` configured to prevent committing:
  - Database dumps and CSV files
  - Environment files with credentials
  - Personal test scripts

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project builds upon the ICIJ Offshore Leaks Database.

**Important**: The Offshore Leaks data is provided by ICIJ for journalistic and research purposes. Please respect their terms of use and data licensing.

## 🙏 Acknowledgments

- **ICIJ** (International Consortium of Investigative Journalists) for the Offshore Leaks Database
- Original data from Panama Papers, Paradise Papers, and other leak investigations
- Neo4j for the graph database platform
- Anthropic for the Model Context Protocol specification

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/markramm/offshoreleaks-data-packages/issues)
- **Discussions**: [GitHub Discussions](https://github.com/markramm/offshoreleaks-data-packages/discussions)
- **ICIJ Data**: [offshoreleaks.icij.org](https://offshoreleaks.icij.org/)

## 🔗 Related Resources

- [ICIJ Offshore Leaks Database](https://offshoreleaks.icij.org/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Claude Desktop](https://claude.ai/)

---

**⚠️ Research & Journalism Use**: This database is intended for research, journalism, and investigative purposes. Always verify information from multiple sources before drawing conclusions.
