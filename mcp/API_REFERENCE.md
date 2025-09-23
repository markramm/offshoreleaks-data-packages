# 🌐 REST API Reference

Complete reference for the offshore leaks FastAPI REST API.

## 📖 Table of Contents

- [Quick Start](#-quick-start)
- [Authentication](#-authentication)
- [Base URL & Versioning](#-base-url--versioning)
- [Request/Response Format](#-requestresponse-format)
- [Health & Status](#-health--status)
- [Search Endpoints](#-search-endpoints)
- [Individual Lookups](#-individual-lookups)
- [Connection Exploration](#-connection-exploration)
- [Advanced Analysis](#-advanced-analysis)
- [Export Functions](#-export-functions)
- [Error Handling](#-error-handling)
- [Rate Limiting](#-rate-limiting)
- [Examples](#-examples)

## 🚀 Quick Start

### Start the API Server
```bash
# Start the server
offshore-api

# Server runs on http://localhost:8000
# Interactive docs at http://localhost:8000/docs
# ReDoc at http://localhost:8000/redoc
```

### Basic Request
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Entity search
curl -X POST http://localhost:8000/api/v1/search/entities \
  -H "Content-Type: application/json" \
  -d '{"name": "Apple Inc", "limit": 5}'
```

### Interactive Documentation
Visit `http://localhost:8000/docs` for interactive API documentation with:
- **Live testing** - Try endpoints directly in browser
- **Schema browser** - Explore request/response models
- **Authentication testing** - Test with API keys
- **Example requests** - Copy-paste ready examples

## 🔐 Authentication

Currently, the API uses **optional authentication**. Future versions will support:

```bash
# API key in header (planned)
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/health

# Bearer token (planned)
curl -H "Authorization: Bearer your-token" http://localhost:8000/api/v1/health
```

## 🌍 Base URL & Versioning

### Base URL Structure
```
http://localhost:8000/api/v1/
```

### API Versioning
- **Current**: `v1` - Stable API with backward compatibility
- **Future**: `v2` - Enhanced features and improvements
- **Legacy**: Deprecated versions supported for 6 months

### CORS Support
The API includes CORS headers for web application integration:
```javascript
// Allowed origins: * (configure for production)
// Allowed methods: GET, POST, PUT, DELETE, OPTIONS
// Allowed headers: *
```

## 📋 Request/Response Format

### Standard Response Format
All endpoints return responses in this format:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "timestamp": "2024-01-15T10:30:45.123456",
  "query_time_ms": 45
}
```

### Search Response Format
Search endpoints include pagination:

```json
{
  "success": true,
  "data": {
    "results": [...],
    "pagination": {
      "limit": 20,
      "offset": 0,
      "total_count": 150,
      "returned_count": 20,
      "has_more": true
    },
    "query_time_ms": 45
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Error Response Format
```json
{
  "success": false,
  "data": null,
  "error": "Validation error: Field 'name' is required",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

## 🏥 Health & Status

### GET /health
Basic health check endpoint.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "database_connected": true,
    "timestamp": "2024-01-15T10:30:45Z"
  }
}
```

### GET /api/v1/health
Detailed health check with version info.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "database_connected": true,
    "server_running": true,
    "version": "1.0.0",
    "timestamp": "2024-01-15T10:30:45Z"
  }
}
```

### GET /api/v1/stats
Database statistics and metadata.

**Query Parameters:**
- `stat_type` (string): Type of statistics (`overview`, `entities`, `officers`)

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/stats?stat_type=overview"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "stat_type": "overview",
    "results": [
      {"metric": "total_entities", "value": 785263},
      {"metric": "total_officers", "value": 345123},
      {"metric": "total_relationships", "value": 1234567}
    ],
    "query_time_ms": 12
  }
}
```

## 🔍 Search Endpoints

### POST /api/v1/search/entities
Search for offshore entities (companies, trusts, foundations).

**Request Body:**
```json
{
  "name": "Apple Inc",
  "jurisdiction": "British Virgin Islands",
  "country_codes": "VG",
  "company_type": "Corporation",
  "status": "Active",
  "incorporation_date_from": "2010-01-01",
  "incorporation_date_to": "2020-12-31",
  "source": "Paradise Papers",
  "limit": 20,
  "offset": 0
}
```

**Request Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Entity name search |
| `jurisdiction` | string | No | Jurisdiction filter |
| `country_codes` | string | No | Country codes (comma-separated) |
| `company_type` | string | No | Company type filter |
| `status` | string | No | Entity status |
| `incorporation_date_from` | date | No | Start date filter |
| `incorporation_date_to` | date | No | End date filter |
| `source` | string | No | Data source filter |
| `limit` | integer | No | Results limit (1-1000, default: 20) |
| `offset` | integer | No | Pagination offset (default: 0) |

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "node_id": "entity_12345",
        "name": "Apple Inc BVI",
        "jurisdiction": "British Virgin Islands",
        "jurisdiction_description": "British Virgin Islands",
        "status": "Active",
        "incorporation_date": "2015-06-01",
        "company_type": "Corporation",
        "sourceID": "Paradise Papers",
        "valid_until": "2023-12-31"
      }
    ],
    "pagination": {
      "limit": 20,
      "offset": 0,
      "total_count": 150,
      "returned_count": 1,
      "has_more": true
    },
    "query_time_ms": 45
  }
}
```

### POST /api/v1/search/officers
Search for officers (individuals associated with entities).

**Request Body:**
```json
{
  "name": "John Smith",
  "countries": "United States",
  "country_codes": "US",
  "source": "Panama Papers",
  "limit": 20,
  "offset": 0
}
```

**Request Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Officer name search |
| `countries` | string | No | Countries filter |
| `country_codes` | string | No | Country codes (comma-separated) |
| `source` | string | No | Data source filter |
| `limit` | integer | No | Results limit (1-1000, default: 20) |
| `offset` | integer | No | Pagination offset (default: 0) |

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "node_id": "officer_67890",
        "name": "John Smith",
        "countries": "United States",
        "country_codes": "US",
        "sourceID": "Panama Papers",
        "valid_until": "2023-12-31"
      }
    ],
    "pagination": {
      "limit": 20,
      "offset": 0,
      "total_count": 45,
      "returned_count": 1,
      "has_more": true
    },
    "query_time_ms": 32
  }
}
```

## 👤 Individual Lookups

### GET /api/v1/entity/{entity_id}
Get details for a specific entity.

**Path Parameters:**
- `entity_id` (string): Entity node ID

**Example Request:**
```bash
curl http://localhost:8000/api/v1/entity/entity_12345
```

**Response:**
```json
{
  "success": true,
  "data": {
    "node_id": "entity_12345",
    "name": "Apple Inc BVI",
    "jurisdiction": "British Virgin Islands",
    "status": "Active",
    "incorporation_date": "2015-06-01",
    "company_type": "Corporation",
    "sourceID": "Paradise Papers"
  }
}
```

### GET /api/v1/officer/{officer_id}
Get details for a specific officer.

**Path Parameters:**
- `officer_id` (string): Officer node ID

**Example Request:**
```bash
curl http://localhost:8000/api/v1/officer/officer_67890
```

**Response:**
```json
{
  "success": true,
  "data": {
    "node_id": "officer_67890",
    "name": "John Smith",
    "countries": "United States",
    "country_codes": "US",
    "sourceID": "Panama Papers"
  }
}
```

## 🕸️ Connection Exploration

### POST /api/v1/connections
Explore connections from a starting node.

**Request Body:**
```json
{
  "start_node_id": "entity_12345",
  "relationship_types": ["OFFICER_OF", "SHAREHOLDER_OF"],
  "max_depth": 2,
  "node_types": ["Entity", "Officer"],
  "limit": 50
}
```

**Request Schema:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start_node_id` | string | Yes | Starting node ID |
| `relationship_types` | array[string] | No | Relationship types filter |
| `max_depth` | integer | No | Maximum exploration depth (1-5, default: 2) |
| `node_types` | array[string] | No | Node types filter |
| `limit` | integer | No | Results limit (1-200, default: 20) |

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "node": {
          "node_id": "officer_67890",
          "name": "John Smith",
          "countries": "United States"
        },
        "distance": 1,
        "first_relationship": {
          "type": "OFFICER_OF",
          "start_date": "2015-01-01",
          "end_date": null
        }
      }
    ],
    "pagination": {
      "limit": 50,
      "offset": 0,
      "total_count": 12,
      "returned_count": 12,
      "has_more": false
    },
    "query_time_ms": 78
  }
}
```

## 🔬 Advanced Analysis

### POST /api/v1/analysis/paths
Find shortest paths between two nodes.

**Query Parameters:**
- `start_node_id` (string): Starting node ID
- `end_node_id` (string): Ending node ID
- `max_depth` (integer): Maximum path depth (1-10, default: 6)
- `limit` (integer): Maximum paths (1-100, default: 10)

**Request Body:**
```json
{
  "relationship_types": ["OFFICER_OF", "OWNS"]
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/paths?start_node_id=entity_123&end_node_id=entity_456&max_depth=6&limit=10" \
  -H "Content-Type: application/json" \
  -d '{"relationship_types": ["OFFICER_OF", "OWNS"]}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "paths": [
      {
        "path_length": 3,
        "relationship_types": ["OFFICER_OF", "OWNS", "SUBSIDIARY_OF"],
        "path_nodes": [
          {"node_id": "entity_123", "name": "Start Entity"},
          {"node_id": "officer_456", "name": "John Smith"},
          {"node_id": "entity_789", "name": "Intermediate Entity"},
          {"node_id": "entity_456", "name": "End Entity"}
        ]
      }
    ],
    "total_count": 1,
    "query_time_ms": 234
  }
}
```

### POST /api/v1/analysis/patterns
Analyze network patterns around a node.

**Query Parameters:**
- `node_id` (string): Node to analyze
- `pattern_type` (string): Pattern type (`hub`, `bridge`, `cluster`)
- `max_depth` (integer): Analysis depth (1-5, default: 3)
- `min_connections` (integer): Minimum connections threshold (default: 5)
- `limit` (integer): Results limit (1-100, default: 20)

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/patterns?node_id=entity_123&pattern_type=hub&max_depth=3&min_connections=5&limit=20"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "patterns": [
      {
        "node": {
          "node_id": "entity_456",
          "name": "Central Entity"
        },
        "connection_count": 25,
        "total_neighbors": 25,
        "relationship_types": ["OFFICER_OF", "OWNS", "SUBSIDIARY_OF"],
        "neighbor_types": ["Entity", "Officer"]
      }
    ],
    "pattern_type": "hub",
    "total_count": 1,
    "query_time_ms": 156
  }
}
```

### POST /api/v1/analysis/common-connections
Find common connections between multiple nodes.

**Query Parameters:**
- `max_depth` (integer): Search depth (1-4, default: 2)
- `limit` (integer): Results limit (1-100, default: 20)

**Request Body:**
```json
{
  "node_ids": ["entity_123", "entity_456", "entity_789"],
  "relationship_types": ["OFFICER_OF", "OWNS"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "common_connections": [
      {
        "common_node": {
          "node_id": "officer_999",
          "name": "Common Officer"
        },
        "connected_sources": ["entity_123", "entity_456"],
        "connection_count": 2,
        "total_neighbors": 15,
        "relationship_types": ["OFFICER_OF"]
      }
    ],
    "source_nodes": ["entity_123", "entity_456", "entity_789"],
    "total_count": 1,
    "query_time_ms": 89
  }
}
```

### POST /api/v1/analysis/temporal
Analyze temporal patterns in entity creation.

**Query Parameters:**
- `node_id` (string): Node to analyze
- `date_field` (string): Date field to analyze (default: `incorporation_date`)
- `time_window_days` (integer): Time window in days (1-3650, default: 365)
- `limit` (integer): Results limit (1-200, default: 50)

**Response:**
```json
{
  "success": true,
  "data": {
    "temporal_patterns": [
      {
        "related_node": {
          "node_id": "entity_456",
          "name": "Related Entity"
        },
        "related_date": "2015-06-15",
        "day_difference": 14,
        "node_types": ["Entity"],
        "temporal_relationship": "same_period"
      }
    ],
    "analysis_node": "entity_123",
    "time_window_days": 365,
    "total_count": 1,
    "query_time_ms": 67
  }
}
```

### POST /api/v1/analysis/compliance-risk
Analyze compliance risks in entity networks.

**Query Parameters:**
- `node_id` (string): Node to analyze
- `max_depth` (integer): Analysis depth (1-5, default: 3)
- `limit` (integer): Results limit (1-100, default: 30)

**Request Body:**
```json
{
  "risk_jurisdictions": ["British Virgin Islands", "Cayman Islands", "Panama"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "risk_analysis": [
      {
        "risky_node": {
          "node_id": "entity_789",
          "name": "High Risk Entity",
          "jurisdiction": "British Virgin Islands"
        },
        "distance": 2,
        "risk_level": "high",
        "jurisdiction": "British Virgin Islands",
        "connection_count": 5,
        "relationship_types": ["OFFICER_OF", "OWNS"],
        "connected_types": ["Entity", "Officer"]
      }
    ],
    "source_node": "entity_123",
    "risk_jurisdictions": ["British Virgin Islands", "Cayman Islands", "Panama"],
    "total_count": 1,
    "query_time_ms": 123
  }
}
```

## 📁 Export Functions

### POST /api/v1/export/search
Export search results to various formats.

**Query Parameters:**
- `format` (string): Export format (`json`, `csv`, `excel`)
- `filename` (string): Output filename (optional)
- `include_metadata` (boolean): Include metadata (default: true)

**Request Body:**
```json
{
  "results": [...],
  "pagination": {...},
  "query_time_ms": 45
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "export_path": "/exports/search_results_20240115_103045.csv",
    "format": "csv",
    "record_count": 150,
    "export_time": "2024-01-15T10:30:45.123456",
    "success": true
  }
}
```

### POST /api/v1/export/network
Export network data for visualization.

**Query Parameters:**
- `format` (string): Export format (`json`, `d3`, `gexf`, `graphml`)
- `filename` (string): Output filename (optional)

**Request Body:**
```json
{
  "results": [...],
  "pagination": {...}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "export_path": "/exports/network_20240115_103045.json",
    "format": "d3",
    "node_count": 25,
    "edge_count": 30,
    "export_time": "2024-01-15T10:30:45.123456",
    "success": true
  }
}
```

## ❌ Error Handling

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (validation error)
- `404` - Not Found
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error
- `503` - Service Unavailable

### Error Response Format
```json
{
  "success": false,
  "data": null,
  "error": "Validation error: Field 'name' is required",
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Common Error Types

**Validation Errors (400, 422):**
```json
{
  "success": false,
  "error": "Validation error: limit must be between 1 and 1000"
}
```

**Not Found Errors (404):**
```json
{
  "success": false,
  "error": "Entity not found"
}
```

**Database Errors (500):**
```json
{
  "success": false,
  "error": "Database error: Connection timeout"
}
```

## 🚦 Rate Limiting

Current implementation:
- **No rate limiting** (development)
- **Planned**: Rate limiting by IP address
- **Planned**: API key-based quotas

Future rate limits:
- **Public endpoints**: 100 requests/minute
- **Authenticated users**: 1000 requests/minute
- **Premium users**: 10,000 requests/minute

Rate limit headers (planned):
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

## 📝 Examples

### JavaScript/TypeScript
```javascript
// Basic entity search
const response = await fetch('/api/v1/search/entities', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    name: 'Apple Inc',
    limit: 10
  })
});

const data = await response.json();
if (data.success) {
  console.log('Found entities:', data.data.results);
} else {
  console.error('Error:', data.error);
}
```

### Python
```python
import httpx

# Async client
async with httpx.AsyncClient() as client:
    response = await client.post(
        'http://localhost:8000/api/v1/search/entities',
        json={'name': 'Apple Inc', 'limit': 10}
    )
    data = response.json()
    if data['success']:
        print(f"Found {len(data['data']['results'])} entities")

# Sync client
import requests

response = requests.post(
    'http://localhost:8000/api/v1/search/entities',
    json={'name': 'Apple Inc', 'limit': 10}
)
data = response.json()
```

### cURL
```bash
# Entity search
curl -X POST http://localhost:8000/api/v1/search/entities \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Apple Inc",
    "jurisdiction": "British Virgin Islands",
    "limit": 10
  }'

# Connection exploration
curl -X POST http://localhost:8000/api/v1/connections \
  -H "Content-Type: application/json" \
  -d '{
    "start_node_id": "entity_12345",
    "max_depth": 2,
    "limit": 20
  }'

# Get entity details
curl http://localhost:8000/api/v1/entity/entity_12345
```

### PHP
```php
<?php
$data = [
    'name' => 'Apple Inc',
    'limit' => 10
];

$response = file_get_contents('http://localhost:8000/api/v1/search/entities', false, stream_context_create([
    'http' => [
        'method' => 'POST',
        'header' => 'Content-Type: application/json',
        'content' => json_encode($data)
    ]
]));

$result = json_decode($response, true);
if ($result['success']) {
    echo "Found " . count($result['data']['results']) . " entities\n";
}
?>
```

---

**📚 For more information, see the [CLI Guide](CLI_GUIDE.md) and [main README](README.md).**
