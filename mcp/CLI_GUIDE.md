# 🖥️ CLI Usage Guide

Comprehensive reference for the `offshore-cli` command-line tool.

## 📖 Table of Contents

- [Installation & Setup](#-installation--setup)
- [Global Options](#-global-options)
- [Core Commands](#-core-commands)
- [Search Commands](#-search-commands)
- [Connection Exploration](#-connection-exploration)
- [Advanced Analysis](#-advanced-analysis)
- [Export Functions](#-export-functions)
- [Interactive Mode](#-interactive-mode)
- [Output Formats](#-output-formats)
- [Examples & Workflows](#-examples--workflows)
- [Troubleshooting](#-troubleshooting)

## 🚀 Installation & Setup

### Install CLI Tool
```bash
# Install the offshore leaks system
pip install -e .

# Verify installation
offshore-cli --version

# Get help
offshore-cli --help
```

### Configuration
Set up your API connection:

```bash
# Option 1: Environment variables
export OFFSHORE_API_URL="http://localhost:8000"
export OFFSHORE_TIMEOUT=30

# Option 2: Use CLI options
offshore-cli --api-url http://localhost:8000 health

# Option 3: Create .env file
echo "OFFSHORE_API_URL=http://localhost:8000" > .env
```

## ⚙️ Global Options

All commands support these global options:

```bash
offshore-cli [GLOBAL OPTIONS] <command> [COMMAND OPTIONS]
```

### Global Options Reference

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--api-url` | | API server URL | `http://localhost:8000` |
| `--timeout` | | Request timeout (seconds) | `30` |
| `--verbose` | `-v` | Enable verbose output | `False` |
| `--version` | | Show version information | |
| `--help` | | Show help message | |

### Examples
```bash
# Use different API server
offshore-cli --api-url https://api.example.com health

# Enable verbose logging
offshore-cli --verbose search entities --name Apple

# Increase timeout for slow queries
offshore-cli --timeout 60 analysis patterns node_123
```

## 🏥 Core Commands

### Health Check
```bash
# Basic health check
offshore-cli health

# With verbose output
offshore-cli --verbose health
```

**Output:**
```
╭─────────────── Health Check ───────────────╮
│ API Status: ✓ Healthy                      │
│ Database: ✓ Connected                      │
│ Timestamp: 2024-01-15T10:30:45Z           │
╰────────────────────────────────────────────╯
```

### Database Statistics
```bash
# Get overview statistics
offshore-cli stats

# Get specific statistics type
offshore-cli stats --type overview

# JSON output
offshore-cli stats --format json
```

**Available stat types:**
- `overview` - General database statistics
- `entities` - Entity-specific statistics
- `officers` - Officer-specific statistics
- `relationships` - Relationship statistics

## 🔍 Search Commands

### Entity Search

**Basic Usage:**
```bash
offshore-cli search entities --name "Apple Inc"
```

**All Options:**
```bash
offshore-cli search entities \
  --name "Apple Inc" \
  --jurisdiction "British Virgin Islands" \
  --status "Active" \
  --country-codes "VG" \
  --company-type "Corporation" \
  --source "Paradise Papers" \
  --limit 20 \
  --offset 0 \
  --format table \
  --export csv \
  --output results.csv
```

**Option Reference:**

| Option | Description | Example |
|--------|-------------|---------|
| `--name` | Entity name search | `--name "Apple"` |
| `--jurisdiction` | Jurisdiction filter | `--jurisdiction "BVI"` |
| `--status` | Entity status | `--status "Active"` |
| `--country-codes` | Country code filter | `--country-codes "VG,KY"` |
| `--company-type` | Company type filter | `--company-type "Corporation"` |
| `--source` | Data source filter | `--source "Paradise Papers"` |
| `--limit` | Max results | `--limit 50` |
| `--offset` | Pagination offset | `--offset 20` |
| `--format` | Output format | `--format json` |
| `--export` | Export format | `--export csv` |
| `--output` | Output file | `--output results.csv` |

### Officer Search

**Basic Usage:**
```bash
offshore-cli search officers --name "John Smith"
```

**All Options:**
```bash
offshore-cli search officers \
  --name "John Smith" \
  --countries "United States" \
  --country-codes "US" \
  --source "Panama Papers" \
  --limit 20 \
  --offset 0 \
  --format table \
  --export json \
  --output officers.json
```

**Option Reference:**

| Option | Description | Example |
|--------|-------------|---------|
| `--name` | Officer name search | `--name "John"` |
| `--countries` | Countries filter | `--countries "United States"` |
| `--country-codes` | Country codes | `--country-codes "US,GB"` |
| `--source` | Data source | `--source "Panama Papers"` |
| `--limit` | Max results | `--limit 30` |
| `--offset` | Pagination offset | `--offset 10` |

### Search Examples

```bash
# Find all Apple entities
offshore-cli search entities --name Apple --limit 10

# Find BVI corporations
offshore-cli search entities --jurisdiction "British Virgin Islands" --company-type Corporation

# Find US officers
offshore-cli search officers --countries "United States" --limit 50

# Export search results
offshore-cli search entities --name Apple --export csv --output apple_entities.csv
```

## 🕸️ Connection Exploration

### Basic Connection Search
```bash
# Explore connections from a node
offshore-cli connections <start_node_id>

# Example
offshore-cli connections entity_12345
```

### Advanced Connection Options
```bash
offshore-cli connections entity_12345 \
  --max-depth 3 \
  --limit 50 \
  --rel-types "OFFICER_OF,SHAREHOLDER_OF" \
  --node-types "Entity,Officer" \
  --format graph \
  --export d3 \
  --output network.json
```

**Option Reference:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--max-depth` | Maximum exploration depth | `2` | `--max-depth 3` |
| `--limit` | Maximum connections | `20` | `--limit 100` |
| `--rel-types` | Relationship types (comma-separated) | All | `--rel-types "OFFICER_OF,OWNS"` |
| `--node-types` | Node types (comma-separated) | All | `--node-types "Entity"` |
| `--format` | Output format | `graph` | `--format table` |
| `--export` | Export format | None | `--export d3` |
| `--output` | Output file | None | `--output network.json` |

### Connection Output Formats

**Graph Format (ASCII Tree):**
```
Found 12 connections

Connection Graph
├── Distance 1
│   ├── John Smith (Officer) via OFFICER_OF
│   └── Apple Holdings (Entity) via SUBSIDIARY_OF
└── Distance 2
    ├── BVI Management Ltd (Entity) via SAME_ADDRESS
    └── Smith Family Trust (Entity) via CONNECTED_TO
```

**Table Format:**
```
┏━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Distance ┃ Name                    ┃ Relationship            ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1        │ John Smith             │ OFFICER_OF              │
│ 1        │ Apple Holdings         │ SUBSIDIARY_OF           │
└──────────┴─────────────────────────┴─────────────────────────┘
```

## 🔬 Advanced Analysis

### Shortest Path Analysis
```bash
# Find paths between two nodes
offshore-cli analysis paths <start_node> <end_node>

# Example with options
offshore-cli analysis paths entity_123 entity_456 \
  --max-depth 6 \
  --limit 10 \
  --rel-types "OFFICER_OF,OWNS"
```

### Network Pattern Analysis
```bash
# Analyze network patterns
offshore-cli analysis patterns <node_id>

# Hub analysis (default)
offshore-cli analysis patterns entity_123 --type hub

# Bridge analysis
offshore-cli analysis patterns entity_123 --type bridge --max-depth 4

# Cluster analysis
offshore-cli analysis patterns entity_123 --type cluster --min-connections 10
```

**Pattern Types:**
- **Hub**: Nodes with many connections (high centrality)
- **Bridge**: Nodes connecting different communities
- **Cluster**: Groups of highly connected nodes

### Analysis Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--type` | Pattern type | `hub` | `--type bridge` |
| `--max-depth` | Analysis depth | `3` | `--max-depth 5` |
| `--min-connections` | Minimum connections threshold | `5` | `--min-connections 10` |
| `--limit` | Maximum results | `20` | `--limit 50` |

## 📁 Export Functions

### Supported Export Formats

**Data Exports:**
- `json` - JSON format
- `csv` - CSV format (for search results)

**Network Exports:**
- `d3` - D3.js visualization format
- `json` - Network JSON format
- `gexf` - Gephi format
- `graphml` - GraphML format

### Export Examples

```bash
# Export entity search to CSV
offshore-cli search entities --name Apple --export csv --output apple.csv

# Export network for D3 visualization
offshore-cli connections entity_123 --export d3 --output network.json

# Export officer search to JSON
offshore-cli search officers --name Smith --export json --output officers.json
```

### Export File Structure

**CSV Export:**
```csv
node_id,name,jurisdiction,status,sourceID
10000001,Apple Inc BVI,British Virgin Islands,Active,Paradise Papers
10000002,Apple Holdings Ltd,Bermuda,Active,Paradise Papers
```

**D3 Network Export:**
```json
{
  "nodes": [
    {"id": "entity_123", "name": "Apple Inc", "type": "Entity"},
    {"id": "officer_456", "name": "John Smith", "type": "Officer"}
  ],
  "links": [
    {"source": "officer_456", "target": "entity_123", "type": "OFFICER_OF"}
  ]
}
```

## 📋 Individual Lookups

### Entity Details
```bash
# Get entity details
offshore-cli entity <entity_id>

# Examples
offshore-cli entity entity_12345
offshore-cli entity entity_12345 --format json
```

### Officer Details
```bash
# Get officer details
offshore-cli officer <officer_id>

# Examples
offshore-cli officer officer_67890
offshore-cli officer officer_67890 --format json
```

**Detail Panel Output:**
```
╭─────────────── Entity Details ───────────────╮
│ Name: Apple Inc BVI                          │
│ Node ID: entity_12345                        │
│ Jurisdiction: British Virgin Islands         │
│ Status: Active                               │
│ Source: Paradise Papers                      │
│ Incorporation Date: 2015-06-01               │
╰───────────────────────────────────────────────╯
```

## 🎮 Interactive Mode

### Starting Interactive Mode
```bash
# Start interactive session
offshore-cli interactive
```

**Interactive Session:**
```
Starting interactive mode. Type 'help' for commands or 'exit' to quit.

offshore-cli> help

Available Commands:

health           - Check API server health
search entities  - Search for entities (interactive)
search officers  - Search for officers (interactive)
help             - Show this help message
exit             - Exit interactive mode

offshore-cli> health
╭─────────────── Health Check ───────────────╮
│ API Status: ✓ Healthy                      │
│ Database: ✓ Connected                      │
╰────────────────────────────────────────────╯

offshore-cli> exit
Goodbye!
```

### Interactive Features
- **Tab completion** - Command and option completion
- **Command history** - Arrow keys to navigate history
- **Context-aware help** - Help for current command
- **Error recovery** - Continue after errors

## 🎨 Output Formats

### Table Format (Default)
- **Colorized columns** with Rich formatting
- **Auto-sized columns** based on content
- **Pagination info** displayed
- **Query timing** shown

### JSON Format
- **Pretty-printed** JSON output
- **Complete data** including metadata
- **Machine-readable** for scripts
- **Consistent structure** across commands

### Graph Format (Connections)
- **ASCII tree visualization** of connections
- **Distance-based grouping** of results
- **Relationship type** display
- **Node type indicators**

## 🎯 Examples & Workflows

### Investigation Workflow
```bash
# 1. Start with entity search
offshore-cli search entities --name "Mossack Fonseca" --limit 10

# 2. Get entity details
offshore-cli entity entity_12345

# 3. Explore connections
offshore-cli connections entity_12345 --max-depth 2 --format graph

# 4. Find related officers
offshore-cli search officers --name "Jurgen Mossack"

# 5. Analyze network patterns
offshore-cli analysis patterns entity_12345 --type hub

# 6. Export for further analysis
offshore-cli connections entity_12345 --export d3 --output investigation.json
```

### Automated Reporting
```bash
#!/bin/bash
# Automated entity analysis script

ENTITY_NAME="Apple"
OUTPUT_DIR="reports"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Search and export entities
offshore-cli search entities --name "$ENTITY_NAME" \
  --export csv --output "$OUTPUT_DIR/entities.csv"

# Get database statistics
offshore-cli stats --format json > "$OUTPUT_DIR/stats.json"

# Search related officers
offshore-cli search officers --name "$ENTITY_NAME" \
  --export json --output "$OUTPUT_DIR/officers.json"

echo "Reports generated in $OUTPUT_DIR/"
```

### Data Export Pipeline
```bash
# Export all BVI entities
offshore-cli search entities --jurisdiction "British Virgin Islands" \
  --limit 1000 --export csv --output bvi_entities.csv

# Export Panama Papers officers
offshore-cli search officers --source "Panama Papers" \
  --limit 1000 --export json --output panama_officers.json

# Export network around specific entity
offshore-cli connections entity_12345 --max-depth 3 \
  --export d3 --output entity_network.json
```

## 🔧 Troubleshooting

### Common Issues

#### Command Not Found
```bash
# Check installation
which offshore-cli
pip show offshore-leaks-mcp-server

# Reinstall if needed
pip install -e .
```

#### API Connection Failed
```bash
# Check API server status
curl http://localhost:8000/health

# Start API server if needed
offshore-api

# Check connection with verbose output
offshore-cli --verbose health
```

#### No Results Found
```bash
# Check search parameters
offshore-cli search entities --name "Apple" --format json

# Try broader search
offshore-cli search entities --name "Apple" --limit 100

# Check database statistics
offshore-cli stats
```

#### Export Failed
```bash
# Check output directory exists
mkdir -p exports

# Use absolute path
offshore-cli search entities --name Apple \
  --export csv --output /full/path/to/results.csv

# Check permissions
ls -la exports/
```

### Debug Options

```bash
# Enable verbose logging
offshore-cli --verbose <command>

# Use different API endpoint
offshore-cli --api-url http://different-server:8000 health

# Increase timeout for slow queries
offshore-cli --timeout 120 analysis patterns node_123
```

### Getting Help

```bash
# Global help
offshore-cli --help

# Command-specific help
offshore-cli search --help
offshore-cli search entities --help

# Show version
offshore-cli --version
```

### Performance Tips

1. **Use appropriate limits** - Don't fetch more data than needed
2. **Filter searches** - Use jurisdiction, status, or source filters
3. **Export large datasets** - Use export functions for big results
4. **Increase timeout** - For complex analysis queries
5. **Use pagination** - For very large result sets

```bash
# Good: Focused search
offshore-cli search entities --name "Apple" --jurisdiction BVI --limit 20

# Better: Export for large datasets
offshore-cli search entities --jurisdiction BVI --export csv --output bvi.csv

# Best: Paginated access
offshore-cli search entities --jurisdiction BVI --limit 100 --offset 0
offshore-cli search entities --jurisdiction BVI --limit 100 --offset 100
```

---

**📚 For more information, see the [main README](README.md) and [API Reference](API_REFERENCE.md).**
