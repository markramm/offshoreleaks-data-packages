# Advanced Network Analysis Tools

This document covers the advanced network analysis capabilities of the Offshore Leaks MCP Server.

## Overview

The server now includes sophisticated network analysis tools for investigating complex offshore financial structures. These tools help investigators understand patterns, relationships, and risk factors in offshore networks.

## Available Analysis Tools

### 1. Shortest Path Analysis (`find_shortest_paths`)

Find the shortest connection paths between two entities in the network.

**Usage:**
```
Find the shortest path between entity A and entity B
Show me how Company X connects to Officer Y
```

**Parameters:**
- `start_node_id`: Starting entity/officer ID
- `end_node_id`: Target entity/officer ID
- `max_depth`: Maximum path length (default: 6)
- `relationship_types`: Optional filter by relationship types
- `limit`: Maximum paths to return (default: 10)

**Use Cases:**
- Tracing ownership chains
- Finding hidden connections between entities
- Understanding relationship complexity

### 2. Network Pattern Analysis (`analyze_network_patterns`)

Detect specific structural patterns in the network around a node.

**Usage:**
```
Analyze hub patterns around this entity
Find bridge nodes in this officer's network
Detect clusters connected to this company
```

**Pattern Types:**
- **Hub**: Nodes with many direct connections (potential control centers)
- **Bridge**: Nodes that connect different communities (intermediaries)
- **Cluster**: Tightly connected groups of entities

**Parameters:**
- `node_id`: Central node for analysis
- `pattern_type`: "hub", "bridge", or "cluster" (default: "hub")
- `max_depth`: Analysis depth (default: 3)
- `min_connections`: Minimum connections threshold (default: 5)
- `limit`: Maximum results (default: 20)

**Use Cases:**
- Identifying control structures
- Finding key intermediaries
- Detecting shell company networks

### 3. Common Connections Analysis (`find_common_connections`)

Find entities that connect multiple target nodes.

**Usage:**
```
Find common connections between these three companies
Show mutual intermediaries for these officers
```

**Parameters:**
- `node_ids`: List of node IDs to analyze (minimum 2)
- `relationship_types`: Optional relationship type filter
- `max_depth`: Connection depth (default: 2)
- `limit`: Maximum results (default: 20)

**Use Cases:**
- Finding shared service providers
- Identifying common beneficial owners
- Detecting coordinated structures

### 4. Temporal Analysis (`temporal_analysis`)

Analyze timing patterns in entity creation around a focal entity.

**Usage:**
```
Show entities created around the same time as this company
Analyze incorporation timing patterns for this network
```

**Parameters:**
- `node_id`: Central entity for temporal analysis
- `date_field`: Date field to analyze (default: "incorporation_date")
- `time_window_days`: Time window in days (default: 365)
- `limit`: Maximum results (default: 50)

**Output Categories:**
- **Before**: Entities created before the focal entity
- **Same Day**: Entities created on the same day
- **After**: Entities created after the focal entity

**Use Cases:**
- Detecting coordinated entity creation
- Finding related incorporation waves
- Identifying suspicious timing patterns

### 5. Compliance Risk Analysis (`compliance_risk_analysis`)

Identify high-risk jurisdictions and entities in a network.

**Usage:**
```
Analyze compliance risks in this entity's network
Show high-risk jurisdiction connections
```

**Parameters:**
- `node_id`: Central entity for risk analysis
- `risk_jurisdictions`: Custom high-risk jurisdictions (optional)
- `max_depth`: Search depth (default: 3)
- `limit`: Maximum results (default: 30)

**Default High-Risk Jurisdictions:**
- British Virgin Islands
- Cayman Islands
- Panama
- Seychelles
- Bahamas
- Bermuda

**Risk Levels:**
- 🔴 **High**: Active entities in high-risk jurisdictions
- 🟡 **Medium**: Inactive entities in high-risk jurisdictions
- 🟢 **Low**: Other entities

**Use Cases:**
- Due diligence investigations
- Regulatory compliance checking
- Risk assessment for business relationships

## Advanced Investigation Workflows

### 1. Comprehensive Entity Investigation

1. Start with basic entity search
2. Use `analyze_network_patterns` to understand the entity's role
3. Apply `compliance_risk_analysis` for risk assessment
4. Use `temporal_analysis` to check timing patterns
5. Employ `find_common_connections` to find related entities

### 2. Tracing Hidden Ownership

1. Identify target beneficial owner and front entity
2. Use `find_shortest_paths` to trace connection routes
3. Apply `analyze_network_patterns` with "bridge" type to find intermediaries
4. Cross-reference with `compliance_risk_analysis` for jurisdiction risks

### 3. Detecting Coordinated Networks

1. Start with suspected entities
2. Use `find_common_connections` to find shared infrastructure
3. Apply `temporal_analysis` to detect coordinated timing
4. Use `analyze_network_patterns` with "cluster" type to map the network

## Performance Considerations

### Query Complexity
- Start with smaller depth values and increase as needed
- Use relationship type filters to focus searches
- Set appropriate limits to avoid overwhelming results

### Optimal Parameters
- **Depth 1-2**: Direct relationships and immediate connections
- **Depth 3-4**: Extended network analysis
- **Depth 5+**: Deep structural analysis (use carefully)

### Result Management
- Use pagination for large result sets
- Filter by specific criteria when possible
- Consider query timeout settings for complex analyses

## Best Practices

### 1. Incremental Analysis
Start with basic tools and progressively use more advanced analysis:
```
Basic Search → Network Analysis → Pattern Detection → Risk Assessment
```

### 2. Cross-Validation
Combine multiple analysis types to validate findings:
- Use temporal analysis to support pattern detection
- Cross-reference risk analysis with ownership patterns
- Validate shortest paths with common connections

### 3. Documentation
Document your investigation path:
- Record which tools were used
- Note significant patterns discovered
- Track risk factors identified

### 4. Ethical Considerations
- Respect privacy rights and presumption of innocence
- Use only for legitimate investigative purposes
- Verify findings through independent sources
- Follow responsible disclosure practices

## Example Investigation Scenarios

### Scenario 1: Due Diligence on Business Partner
```
1. search_entities: "Acme Holdings Ltd"
2. compliance_risk_analysis: node_id="12345"
3. analyze_network_patterns: node_id="12345", pattern_type="hub"
4. temporal_analysis: node_id="12345", time_window_days=180
```

### Scenario 2: Tracing Beneficial Ownership
```
1. search_officers: "John Smith"
2. get_connections: start_node_id="67890", max_depth=3
3. find_shortest_paths: start_node_id="67890", end_node_id="target_entity"
4. analyze_network_patterns: node_id="67890", pattern_type="bridge"
```

### Scenario 3: Investigating Coordinated Structures
```
1. find_common_connections: node_ids=["ent1", "ent2", "ent3"]
2. temporal_analysis: node_id="common_connection", time_window_days=90
3. analyze_network_patterns: node_id="common_connection", pattern_type="cluster"
4. compliance_risk_analysis: node_id="common_connection"
```

## Limitations and Considerations

### Data Coverage
- Analysis is limited to available data in the offshore leaks database
- Not all offshore structures may be captured
- Data represents specific time periods and sources

### Analytical Scope
- Patterns indicate relationships but don't prove wrongdoing
- Risk analysis is based on jurisdictional indicators
- Temporal patterns may have legitimate explanations

### Technical Constraints
- Complex queries may require longer processing time
- Very deep network analysis can be computationally expensive
- Results are limited by configured maximum values

## Support and Updates

This advanced analysis capability is continuously being improved. For questions, issues, or feature requests:

1. Check the main documentation
2. Review investigation guides
3. Submit issues with detailed query examples
4. Include sample data when reporting problems

Remember: These tools are designed to support legitimate investigative work while respecting privacy rights and legal requirements.
