# End-to-End Testing Setup

This document describes how to set up and run end-to-end tests for the offshore leaks system.

## Prerequisites

### 1. Neo4j Database with Offshore Leaks Data

You need a Neo4j database containing actual offshore leaks data. This can be:

- **Local Neo4j instance** with imported ICIJ data
- **Remote Neo4j instance** (e.g., AWS, GCP, or hosted service)
- **Docker container** with pre-loaded data

### 2. Database Setup Options

#### Option A: Download ICIJ Data
```bash
# Download and import official ICIJ offshore leaks data
# See: https://offshoreleaks.icij.org/pages/database

# Example for Paradise Papers (replace with your chosen dataset)
curl -O https://cloudfront-files-1.publicintegrity.org/offshoreleaks/paradise-papers/csv/paradise_papers.nodes.entity.csv
curl -O https://cloudfront-files-1.publicintegrity.org/offshoreleaks/paradise-papers/csv/paradise_papers.nodes.officer.csv
curl -O https://cloudfront-files-1.publicintegrity.org/offshoreleaks/paradise-papers/csv/paradise_papers.relationships.csv

# Import into Neo4j using neo4j-admin import or LOAD CSV
```

#### Option B: Sample Data for Testing
```cypher
-- Create minimal test dataset
CREATE (e1:Entity {
  node_id: "test_entity_1",
  name: "Apple Inc",
  jurisdiction: "Nevada",
  status: "Active"
})
CREATE (e2:Entity {
  node_id: "test_entity_2",
  name: "Google LLC",
  jurisdiction: "Delaware",
  status: "Active"
})
CREATE (o1:Officer {
  node_id: "test_officer_1",
  name: "John Smith",
  countries: "United States"
})
CREATE (o2:Officer {
  node_id: "test_officer_2",
  name: "Jane Doe",
  countries: "United Kingdom"
})
CREATE (i1:Intermediary {
  node_id: "test_intermediary_1",
  name: "Legal Firm LLC"
})
CREATE (e1)-[:officer_of]->(o1)
CREATE (e2)-[:officer_of]->(o2)
CREATE (e1)-[:intermediary_of]->(i1)
CREATE (e2)-[:intermediary_of]->(i1)
```

#### Option C: Docker Setup
```bash
# Start Neo4j with sample data
docker run \
  --name offshore-test-db \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/testpassword \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:5.15

# Connect and load test data
docker exec -it offshore-test-db cypher-shell -u neo4j -p testpassword
```

## Environment Configuration

### Required Environment Variables

```bash
# Enable E2E tests
export RUN_E2E_TESTS=1

# Database connection
export E2E_NEO4J_URI="bolt://localhost:7687"
export E2E_NEO4J_USER="neo4j"
export E2E_NEO4J_PASSWORD="your_password"
export E2E_NEO4J_DATABASE="neo4j"

# API endpoint (if testing CLI integration)
export E2E_API_URL="http://localhost:8000"
```

### Optional Configuration

```bash
# For remote databases
export E2E_NEO4J_URI="bolt://your-remote-host:7687"
export E2E_NEO4J_URI="neo4j+s://your-aura-instance.databases.neo4j.io"

# For custom database name
export E2E_NEO4J_DATABASE="offshore_leaks"

# For custom API server
export E2E_API_URL="https://your-api-server.com"
```

## Running E2E Tests

### Quick Start

```bash
# Set environment variables
export RUN_E2E_TESTS=1
export E2E_NEO4J_PASSWORD=your_password

# Run all E2E tests
pytest tests/test_e2e.py -v

# Run specific test categories
pytest tests/test_e2e.py::TestDatabaseConnectivity -v
pytest tests/test_e2e.py::TestServerE2E -v
pytest tests/test_e2e.py::TestCLIE2E -v
pytest tests/test_e2e.py::TestAPIE2E -v
```

### Test Categories

1. **Database Connectivity** (`TestDatabaseConnectivity`)
   - Verifies database connection
   - Checks for required node types (Entity, Officer)
   - Validates data structure

2. **Server E2E** (`TestServerE2E`)
   - Tests MCP server with real data
   - Entity and officer searches
   - Connection exploration
   - Statistics generation

3. **CLI E2E** (`TestCLIE2E`)
   - Tests CLI commands against real API
   - Health checks, searches, statistics
   - Command-line interface validation

4. **API E2E** (`TestAPIE2E`)
   - Tests REST API endpoints
   - HTTP client integration
   - JSON response validation

5. **Data Integrity** (`TestDataIntegrity`)
   - Validates relationship consistency
   - Checks node property completeness
   - Ensures data quality

6. **Performance E2E** (`TestPerformanceE2E`)
   - Tests query performance
   - Validates response times
   - Identifies bottlenecks

### Advanced Usage

```bash
# Run with coverage
pytest tests/test_e2e.py --cov=offshore_leaks_mcp --cov-report=html

# Run slow tests only
pytest tests/test_e2e.py -m "slow" -v

# Run specific database tests
pytest tests/test_e2e.py -k "database" -v

# Run with detailed output
pytest tests/test_e2e.py -v -s

# Parallel execution (if you have pytest-xdist)
pytest tests/test_e2e.py -n auto

# Skip slow tests
pytest tests/test_e2e.py -m "not slow" -v
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest

    services:
      neo4j:
        image: neo4j:5.15
        env:
          NEO4J_AUTH: neo4j/testpassword
        ports:
          - 7687:7687
          - 7474:7474

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -e .[test]

    - name: Wait for Neo4j
      run: |
        until cypher-shell -u neo4j -p testpassword "RETURN 1"; do
          echo "Waiting for Neo4j..."
          sleep 5
        done

    - name: Load test data
      run: |
        cypher-shell -u neo4j -p testpassword < tests/fixtures/sample_data.cypher

    - name: Run E2E tests
      env:
        RUN_E2E_TESTS: 1
        E2E_NEO4J_PASSWORD: testpassword
      run: |
        pytest tests/test_e2e.py -v
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```
   ConnectionRefusedError: [Errno 61] Connection refused
   ```
   - Check Neo4j is running: `systemctl status neo4j`
   - Verify port 7687 is accessible
   - Check firewall settings

2. **Authentication Failed**
   ```
   Neo4j.ClientError.Security.Unauthorized
   ```
   - Verify username/password
   - Check database name
   - Ensure user has required permissions

3. **Empty Database**
   ```
   pytest.skip: E2E database appears to be empty
   ```
   - Load test data using the sample queries above
   - Verify data import completed successfully
   - Check node counts with `MATCH (n) RETURN count(n)`

4. **API Server Not Starting**
   ```
   Could not connect to API server
   ```
   - Check port 8000 is available
   - Verify API server dependencies
   - Check logs for startup errors

### Debugging Tips

```bash
# Check database connectivity
cypher-shell -u neo4j -p your_password "MATCH (n) RETURN count(n)"

# Verify node types
cypher-shell -u neo4j -p your_password "MATCH (n) RETURN distinct labels(n), count(n)"

# Test API manually
curl http://localhost:8000/health

# Check API logs
python -m offshore_leaks_mcp.api --debug

# Verbose test output
pytest tests/test_e2e.py -v -s --tb=short
```

## Performance Tuning

### Database Optimization

```cypher
-- Create indexes for better performance
CREATE INDEX entity_name_idx FOR (e:Entity) ON (e.name);
CREATE INDEX entity_node_id_idx FOR (e:Entity) ON (e.node_id);
CREATE INDEX officer_name_idx FOR (o:Officer) ON (o.name);
CREATE INDEX officer_node_id_idx FOR (o:Officer) ON (o.node_id);
```

### Test Configuration

```bash
# Increase timeouts for large datasets
export E2E_QUERY_TIMEOUT=60
export E2E_CONNECTION_TIMEOUT=30

# Reduce test dataset size for faster runs
export E2E_SEARCH_LIMIT=10
export E2E_CONNECTION_DEPTH=2
```

## Data Quality Checks

The E2E tests include built-in data quality validation:

- **Node completeness**: Ensures entities/officers have required properties
- **Relationship validity**: Verifies relationships connect expected node types
- **Data consistency**: Checks for orphaned nodes and invalid references
- **Performance benchmarks**: Validates query response times

These checks help ensure your offshore leaks database is properly structured and performant for production use.
