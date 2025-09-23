# Multi-Interface Design: CLI, Web App & MCP Server

## Architecture Overview

This design creates a unified system with three interfaces sharing the same core API backend:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Server    │    │   CLI Tool      │    │   Web App       │
│   (Claude)      │    │   (Terminal)    │    │   (Browser)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Shared API     │
                    │  Backend        │
                    │  (FastAPI)      │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Core Business  │
                    │  Logic Layer    │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Neo4j Database │
                    └─────────────────┘
```

## Core Shared Components

### 1. **API Backend** (FastAPI/HTTP REST)
- **Purpose**: Unified HTTP API that all interfaces consume
- **Features**: Entity search, officer search, connection exploration, health checks
- **Benefits**: Single source of truth, consistent behavior, easy testing

### 2. **Business Logic Layer**
- **Reuses**: Existing `OffshoreLeaksServer`, `OffshoreLeaksQueries`, database layer
- **Enhancement**: Extract into service classes for better reusability
- **Interface**: Clean separation between API layer and business logic

### 3. **Data Models**
- **Shared**: Pydantic models for requests/responses across all interfaces
- **Consistent**: Same validation and serialization everywhere
- **Type-safe**: Full type hints for excellent developer experience

## Interface Specifications

### 🖥️ **CLI Tool Design**

#### Features
```bash
# Entity searches
offshore-cli search entities --name "Apple Inc" --jurisdiction BVI --limit 20
offshore-cli search entities --status Active --format table

# Officer searches
offshore-cli search officers --name "John Smith" --countries "United States"

# Connection exploration
offshore-cli connections --start-node "entity_123" --max-depth 3 --format graph

# Interactive mode
offshore-cli interactive  # Starts REPL for exploratory analysis

# Export capabilities
offshore-cli search entities --name "Apple" --export csv --output results.csv
offshore-cli search entities --name "Apple" --export json --output results.json
```

#### Rich Output Formats
- **Table**: Clean tabular data with color coding
- **JSON**: Machine-readable structured output
- **Graph**: ASCII art visualization of connections
- **CSV**: Export for spreadsheet analysis
- **Interactive**: Rich REPL with autocomplete and history

#### CLI Architecture
```python
# CLI entry point
offshore-cli
├── commands/
│   ├── search.py      # Search entities/officers
│   ├── connections.py # Explore relationships
│   ├── export.py      # Data export utilities
│   └── interactive.py # REPL mode
├── formatters/
│   ├── table.py       # Rich table output
│   ├── graph.py       # ASCII graph visualization
│   └── json.py        # Structured output
└── client/
    └── api_client.py  # HTTP client for API backend
```

### 🌐 **React Web App Design**

#### User Interface
```
┌─────────────────────────────────────────────────────────┐
│                    Offshore Leaks Explorer             │
├─────────────────────────────────────────────────────────┤
│  Search: [Entity/Officer] [_______________] [Search]    │
├─────────────────────────────────────────────────────────┤
│  Filters: Jurisdiction [___] Status [___] Date [___]    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │   Results       │  │   Connections   │               │
│  │   Table         │  │   Graph         │               │
│  │                 │  │                 │               │
│  │  Entity 1       │  │      ●──────●   │               │
│  │  Entity 2       │  │      │      │   │               │
│  │  Entity 3       │  │      ●──────●   │               │
│  └─────────────────┘  └─────────────────┘               │
│                                                         │
│  ┌─────────────────────────────────────────────────────┐│
│  │              Entity Details Panel                   ││
│  │  Name: Apple Inc BVI                               ││
│  │  Jurisdiction: British Virgin Islands              ││
│  │  Status: Active                                    ││
│  │  Officers: [Show Connected Officers]               ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

#### Web App Features
- **Advanced Search**: Multiple criteria, filters, sorting
- **Interactive Visualization**: Clickable network graphs with D3.js
- **Entity Details**: Rich detail panels with related information
- **Connection Exploration**: Visual graph traversal
- **Export Functions**: Download results in multiple formats
- **Responsive Design**: Works on desktop, tablet, mobile
- **Real-time Updates**: Live search as you type

#### Web App Architecture
```
web-app/
├── src/
│   ├── components/
│   │   ├── SearchForm.tsx      # Search interface
│   │   ├── ResultsTable.tsx    # Tabular results
│   │   ├── ConnectionGraph.tsx # Network visualization
│   │   ├── EntityDetail.tsx    # Detail panels
│   │   └── ExportTools.tsx     # Download utilities
│   ├── services/
│   │   ├── api.ts              # API client layer
│   │   ├── types.ts            # TypeScript types
│   │   └── utils.ts            # Utility functions
│   ├── hooks/
│   │   ├── useSearch.ts        # Search state management
│   │   └── useConnections.ts   # Graph data management
│   └── pages/
│       ├── Search.tsx          # Main search page
│       ├── Entity.tsx          # Entity detail page
│       └── About.tsx           # Information page
└── package.json
```

## Implementation Plan

### Phase 1: Shared API Backend
1. **Extract Business Logic**: Create service layer from existing `OffshoreLeaksServer`
2. **Create FastAPI App**: HTTP REST API with OpenAPI documentation
3. **Define API Endpoints**: RESTful routes for all operations
4. **Add Response Models**: Consistent JSON responses

### Phase 2: CLI Tool
1. **Create CLI Framework**: Use Click or Typer for command structure
2. **Implement Commands**: Search, connections, export functionality
3. **Add Rich Output**: Tables, colors, progress bars
4. **Interactive Mode**: REPL with autocomplete

### Phase 3: React Web App
1. **Setup React Project**: TypeScript, Vite, modern toolchain
2. **Implement Components**: Search, results, visualization
3. **Add Graph Visualization**: D3.js or React Flow for network graphs
4. **Responsive Design**: Mobile-friendly interface

### Phase 4: Integration & Testing
1. **End-to-End Testing**: All interfaces against same data
2. **Performance Optimization**: Caching, pagination
3. **Documentation**: User guides for each interface
4. **Deployment**: Docker containers, deployment scripts

## Technical Stack

### Backend (Shared)
- **FastAPI**: Modern, fast web framework with automatic OpenAPI docs
- **Pydantic**: Data validation and serialization
- **Neo4j**: Existing graph database
- **Python 3.9+**: Consistent with existing codebase

### CLI Tool
- **Typer**: Modern CLI framework with great type hints
- **Rich**: Beautiful terminal output with tables, colors, progress
- **httpx**: Async HTTP client for API calls
- **Click**: Alternative CLI framework option

### Web App
- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Type safety and excellent developer experience
- **Vite**: Fast build tool and dev server
- **D3.js**: Powerful data visualization for network graphs
- **Tailwind CSS**: Utility-first CSS framework
- **React Query**: Data fetching and caching

### Development Tools
- **Docker**: Containerization for all components
- **Docker Compose**: Local development environment
- **OpenAPI**: API documentation and client generation
- **Storybook**: Component development for React
- **Pytest**: Testing for Python components
- **Jest**: Testing for JavaScript/TypeScript

## API Design

### Core Endpoints
```
GET  /api/v1/health              # Health check
GET  /api/v1/stats               # Database statistics

POST /api/v1/search/entities     # Search entities
POST /api/v1/search/officers     # Search officers
POST /api/v1/connections         # Explore connections

GET  /api/v1/entity/{id}         # Get entity details
GET  /api/v1/officer/{id}        # Get officer details

GET  /api/v1/export/entities     # Export search results
GET  /api/v1/export/officers     # Export search results
```

### Request/Response Examples
```python
# Entity search request
POST /api/v1/search/entities
{
    "name": "Apple Inc",
    "jurisdiction": "BVI",
    "limit": 20,
    "offset": 0
}

# Response
{
    "results": [...],
    "total_count": 150,
    "query_time_ms": 45,
    "pagination": {
        "limit": 20,
        "offset": 0,
        "has_more": true
    }
}
```

## Benefits of This Architecture

### 🔄 **Consistency**
- Same data, same queries, same results across all interfaces
- Single source of truth for business logic
- Consistent error handling and validation

### 🚀 **Scalability**
- API backend can scale independently
- Multiple interface can be deployed separately
- Easy to add new interfaces (mobile app, GraphQL, etc.)

### 🔧 **Maintainability**
- Clear separation of concerns
- Shared code reduces duplication
- Easy testing of individual components

### 👨‍💻 **Developer Experience**
- Type-safe APIs with OpenAPI documentation
- Hot reloading for web development
- Rich CLI with autocomplete and help

### 👥 **User Experience**
- Choose the right tool for the task
- CLI for automation and scripts
- Web app for exploration and visualization
- MCP for AI agent integration

This architecture provides a solid foundation for building multiple interfaces while maintaining code quality, consistency, and developer productivity.
