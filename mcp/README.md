# 🏖️ Offshore Leaks Multi-Interface System

A comprehensive system providing **multiple interfaces** to query the ICIJ Offshore Leaks database for research and investigative journalism purposes.

## 🏗️ Architecture Overview

This system provides **three distinct interfaces** sharing the same backend:

```
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
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **Neo4j database** with offshore leaks data loaded
- **Dependencies**: Will be installed automatically

### Installation

```bash
# Clone and navigate to project
cd /path/to/offshoreleaks-data-packages/mcp

# Install with all interfaces
pip install -e .

# Verify installation
offshore-cli --version
```

### Configuration

Create a `.env` file or set environment variables:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=offshoreleaks
```

## 🎯 Choose Your Interface

### 🖥️ **CLI Tool** (Terminal Users & Automation)

Perfect for terminal users, scripts, and automation:

```bash
# Check system health
offshore-cli health

# Search entities
offshore-cli search entities --name "Apple Inc" --jurisdiction BVI --limit 10

# Search officers
offshore-cli search officers --name "John Smith" --countries "United States"

# Explore connections with graph visualization
offshore-cli connections entity_12345 --max-depth 2 --format graph

# Advanced analysis
offshore-cli analysis paths entity_123 entity_456 --max-depth 6

# Export data
offshore-cli search entities --name Apple --export csv --output results.csv

# Interactive mode for exploration
offshore-cli interactive
```

**Features:**
- 🎨 Rich terminal output with colors and tables
- 📊 ASCII graph visualization
- 📁 Export to CSV, JSON, D3 formats
- 🔄 Interactive REPL mode
- ⚙️ Configurable API endpoints

### 🌐 **REST API** (Web Apps & Integrations)

Perfect for web applications and third-party integrations:

```bash
# Start the API server
offshore-api

# Access endpoints
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/docs  # Interactive API documentation
```

**Endpoints:**
- `POST /api/v1/search/entities` - Entity search
- `POST /api/v1/search/officers` - Officer search
- `POST /api/v1/connections` - Connection exploration
- `POST /api/v1/analysis/paths` - Shortest path analysis
- `POST /api/v1/analysis/patterns` - Network pattern analysis
- `GET /api/v1/entity/{id}` - Individual entity details
- `POST /api/v1/export/search` - Export functionality

**Features:**
- 📜 OpenAPI documentation at `/docs`
- 🔧 CORS support for web apps
- 📄 Standardized JSON responses
- 🔍 Request validation with Pydantic
- 📊 Pagination and metadata

### 🤖 **MCP Server** (AI Agent Integration)

Perfect for Claude AI and other MCP-compatible agents:

```bash
# Start MCP server
offshore-leaks-mcp

# Configure in Claude Desktop config.json
{
  "mcpServers": {
    "offshore-leaks": {
      "command": "offshore-leaks-mcp",
      "env": {
        "NEO4J_URI": "bolt://localhost:7687"
      }
    }
  }
}
```

**Features:**
- 🔗 Direct Claude AI integration
- 🎯 Research-focused tools
- 🛡️ Built-in rate limiting
- 📋 Comprehensive tool schemas

## 📚 Interface Comparison

| Feature | CLI Tool | REST API | MCP Server |
|---------|----------|----------|------------|
| **Best For** | Terminal users, automation | Web apps, integrations | AI agents, Claude |
| **Output Format** | Tables, graphs, JSON | JSON | Structured responses |
| **Export** | ✅ CSV, JSON, D3 | ✅ JSON, CSV | ❌ |
| **Interactive** | ✅ REPL mode | ❌ | ✅ AI conversation |
| **Documentation** | `--help` commands | OpenAPI at `/docs` | Built-in schemas |
| **Authentication** | API key support | Header-based | Built-in |

## 🔧 Development

### Setup Development Environment

```bash
# Install with development dependencies
pip install -e ".[dev,test]"

# Set up pre-commit hooks
pre-commit install

# Install CLI completion (optional)
offshore-cli --install-completion
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m slow          # Performance tests
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src

# All quality checks
pre-commit run --all-files
```

## 📖 Detailed Documentation

- **[CLI Guide](CLI_GUIDE.md)** - Comprehensive CLI command reference
- **[API Reference](API_REFERENCE.md)** - REST API endpoint documentation
- **[Architecture Design](MULTI_INTERFACE_DESIGN.md)** - Detailed system design
- **[Implementation Details](IMPLEMENTATION_COMPLETE.md)** - Technical implementation summary

## 🎯 Use Cases

### **🔬 Research & Analysis**
```bash
# Find entities in tax havens
offshore-cli search entities --jurisdiction "British Virgin Islands" --limit 50

# Trace connections between entities
offshore-cli connections entity_123 --max-depth 3 --format graph

# Export for further analysis
offshore-cli search entities --name "Apple" --export csv --output apple_entities.csv
```

### **🤖 AI-Assisted Investigation**
- Use Claude with MCP server for natural language queries
- AI can explore connections and suggest investigation paths
- Automated pattern recognition and anomaly detection

### **🌐 Web Application Integration**
```javascript
// Frontend integration
const response = await fetch('/api/v1/search/entities', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'Apple Inc', limit: 10 })
});
const results = await response.json();
```

### **⚙️ Automation & Scripts**
```bash
#!/bin/bash
# Automated reporting script
offshore-cli search entities --jurisdiction BVI --export json > bvi_entities.json
offshore-cli stats --format json > db_stats.json
```

## 🛡️ Data & Ethics

### **Data Sources**
This system provides access to public data from:
- Paradise Papers
- Panama Papers
- Offshore Leaks
- Bahamas Leaks
- Pandora Papers

### **Usage Guidelines**
- ✅ Legitimate research and journalism
- ✅ Law enforcement investigations
- ✅ Academic studies
- ❌ Harassment or doxxing
- ❌ Malicious activities
- ❌ Unauthorized commercial use

### **Important Disclaimers**
- Presence in database **does not imply wrongdoing**
- Offshore structures have **legitimate uses**
- Always **verify information independently**
- **Respect privacy rights** and presumption of innocence

## 🚦 Getting Started Examples

### **Basic Health Check**
```bash
# Test all interfaces are working
offshore-cli health
curl http://localhost:8000/api/v1/health
```

### **First Search**
```bash
# CLI: Search for Apple entities
offshore-cli search entities --name Apple --limit 5

# API: Same search via REST
curl -X POST http://localhost:8000/api/v1/search/entities \
  -H "Content-Type: application/json" \
  -d '{"name": "Apple", "limit": 5}'
```

### **Connection Exploration**
```bash
# Find connections to a specific entity
offshore-cli connections 12345 --max-depth 2 --format graph

# Export connection network for visualization
offshore-cli connections 12345 --export d3 --output network.json
```

## 🔧 Troubleshooting

### **Common Issues**

**Command not found:**
```bash
# Ensure proper installation
pip install -e .
# Check PATH includes Python scripts
echo $PATH
```

**Database connection failed:**
```bash
# Check Neo4j is running
offshore-cli health
# Verify connection settings
cat .env
```

**API server won't start:**
```bash
# Check port availability
lsof -i :8000
# Try different port
offshore-api --port 8001
```

## 📦 Dependencies

### **Core Dependencies**
- `neo4j>=5.0.0` - Database driver
- `pydantic>=2.0.0` - Data validation
- `httpx>=0.25.0` - HTTP client

### **CLI Dependencies**
- `typer>=0.9.0` - CLI framework
- `rich>=13.0.0` - Terminal formatting
- `click>=8.0.0` - Command parsing

### **API Dependencies**
- `fastapi>=0.104.0` - Web framework
- `uvicorn>=0.24.0` - ASGI server

### **Development Dependencies**
- `pytest>=7.0.0` - Testing framework
- `black>=23.0.0` - Code formatting
- `ruff>=0.1.0` - Linting
- `mypy>=1.5.0` - Type checking

## 🏆 Benefits

### **🔄 Consistency**
- Same data and queries across all interfaces
- Single source of truth for business logic
- Consistent error handling everywhere

### **🚀 Scalability**
- Each interface can be deployed independently
- API backend scales horizontally
- Easy to add new interfaces

### **👨‍💻 Developer Experience**
- Type-safe APIs with automatic validation
- Rich documentation and examples
- Interactive tools for exploration

### **👥 User Experience**
- Choose the right tool for your workflow
- Consistent functionality across interfaces
- Rich output formats and visualizations

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Attribution

Data provided by the **International Consortium of Investigative Journalists (ICIJ)** Offshore Leaks Database.

---

**🌊 Ready to explore offshore financial networks? Choose your interface and start investigating!**
