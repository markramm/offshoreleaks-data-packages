# Offshore Leaks Database Setup Guide

Complete guide for setting up the Neo4j database with Offshore Leaks data for the MCP server.

## Prerequisites

- **Docker Desktop** installed and running
- **Offshore Leaks database dump** file (e.g., `icij-offshoreleaks-5.13.0.dump`)
- At least **4GB RAM** available for Neo4j
- At least **5GB disk space** for the database

## Quick Start

### 1. Obtain the Database Dump

Download the Offshore Leaks database dump from ICIJ:
- Visit: https://offshoreleaks.icij.org/
- Or use the ICIJ data release repository

Place the `.dump` file in your project directory.

### 2. Start Neo4j with Docker

Create a Docker volume and load the database:

```bash
# Create a persistent volume for Neo4j data
docker volume create offshore-leaks-data

# Load the database dump into the volume
docker run --rm \
  -v offshore-leaks-data:/data \
  -v /path/to/dumps:/dumps \
  neo4j:5.15 \
  bash -c "neo4j-admin database load neo4j --from-stdin < /dumps/icij-offshoreleaks-5.13.0.dump"

# Start Neo4j server
docker run -d \
  --name offshore-leaks-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -v offshore-leaks-data:/data \
  -e NEO4J_AUTH=neo4j/offshoreleaks \
  -e NEO4J_dbms_memory_heap_max__size=4G \
  -e NEO4J_dbms_memory_pagecache_size=2G \
  neo4j:5.15
```

### 3. Verify Database Connection

Access Neo4j Browser at http://localhost:7474
- Username: `neo4j`
- Password: `offshoreleaks`

Test with Cypher query:
```cypher
MATCH (n) RETURN count(n) as total_nodes
```

Expected result: ~2,016,523 nodes

## Database Contents

After successful load, the database contains:

| Node Type | Count | Description |
|-----------|-------|-------------|
| Entity | 814,344 | Offshore companies and organizations |
| Officer | 770,176 | People associated with entities |
| Address | 402,246 | Registered addresses |
| Intermediary | 26,768 | Law firms, intermediaries |
| Other | 2,989 | Other node types |
| **Total Nodes** | **2,016,523** | |
| **Relationships** | **3,339,267** | Connections between nodes |

## Configuration for MCP Server

### Configure Environment Variables

Create `mcp/.env` file (copy from `.env.example`):

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=offshoreleaks
NEO4J_DATABASE=neo4j
```

### Test MCP Server Connection

```bash
cd mcp
source venv/bin/activate

# Test database connection
python3 << EOF
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

## Sample Queries

### Search for Entities
```cypher
MATCH (e:Entity)
WHERE e.name =~ '(?i).*trump.*'
RETURN e.name, e.jurisdiction, e.status
LIMIT 10
```

### Find Officer Connections
```cypher
MATCH (o:Officer)-[r:OFFICER_OF]->(e:Entity)
WHERE o.name CONTAINS 'Smith'
RETURN o.name, type(r), e.name, e.jurisdiction
LIMIT 20
```

### Explore Network
```cypher
MATCH path = (start)-[*1..3]-(connected)
WHERE start.node_id = 10050150
RETURN path
LIMIT 50
```

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs offshore-leaks-neo4j

# Common issues:
# - Port 7474 or 7687 already in use
# - Insufficient memory allocated to Docker
# - Database not properly loaded
```

### Database Empty
```bash
# Verify volume has data
docker run --rm -v offshore-leaks-data:/data neo4j:5.15 \
  du -sh /data/databases/neo4j

# Expected: Several GB of data
```

### Connection Refused
- Ensure Docker is running
- Check container status: `docker ps`
- Verify ports aren't blocked by firewall
- Wait 15-30 seconds for Neo4j to fully start

## Maintenance

### Stop Neo4j
```bash
docker stop offshore-leaks-neo4j
```

### Start Neo4j
```bash
docker start offshore-leaks-neo4j
```

### Remove Everything
```bash
docker stop offshore-leaks-neo4j
docker rm offshore-leaks-neo4j
docker volume rm offshore-leaks-data
```

### Backup Database
```bash
docker exec offshore-leaks-neo4j \
  neo4j-admin database dump neo4j --to-stdout > backup.dump
```

## Performance Tuning

For better performance with large queries:

```bash
docker run -d \
  --name offshore-leaks-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -v offshore-leaks-data:/data \
  -e NEO4J_AUTH=neo4j/offshoreleaks \
  -e NEO4J_dbms_memory_heap_max__size=8G \
  -e NEO4J_dbms_memory_pagecache_size=4G \
  -e NEO4J_dbms_transaction_timeout=60s \
  neo4j:5.15
```

## Security Notes

- **DO NOT** commit `.env` files or database dumps to version control
- Change default password in production
- Restrict network access to Neo4j ports in production
- This setup is for development/research only
