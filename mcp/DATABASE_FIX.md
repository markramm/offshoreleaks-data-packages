# Database Module Fix - Neo4j Result Handling

## Issue
The `database.py` module had compatibility issues with the Neo4j Python driver when handling query results and summary information.

## Problems Fixed

### 1. Result Summary Access
**Problem**: Attempting to access `result.summary()` multiple times after consuming records caused an `AttributeError`.

**Root Cause**: The Neo4j driver's `Result` object doesn't have a `summary()` method that can be called multiple times. After consuming records, you need to call `consume()` to get the summary.

**Solution**: Changed from:
```python
result = session.run(query, parameters, timeout=timeout)
records = [record.data() for record in result]
summary = {
    "query_type": result.summary().query_type,
    "counters": dict(result.summary().counters),
    ...
}
```

To:
```python
result = session.run(query, parameters, timeout=timeout)
records = [record.data() for record in result]
result_summary = result.consume()  # Get summary after consuming records
summary = {
    "query_type": result_summary.query_type,
    "counters": counters_dict,
    ...
}
```

### 2. SummaryCounters Serialization
**Problem**: Attempting to convert `SummaryCounters` object to dict using `dict()` failed with `TypeError: 'SummaryCounters' object is not iterable`.

**Root Cause**: The `SummaryCounters` class is not directly iterable and cannot be converted to a dictionary using the `dict()` constructor.

**Solution**: Explicitly extract each counter attribute:
```python
counters = result_summary.counters
counters_dict = {
    "nodes_created": counters.nodes_created,
    "nodes_deleted": counters.nodes_deleted,
    "relationships_created": counters.relationships_created,
    "relationships_deleted": counters.relationships_deleted,
    "properties_set": counters.properties_set,
    "labels_added": counters.labels_added,
    "labels_removed": counters.labels_removed,
    "indexes_added": counters.indexes_added,
    "indexes_removed": counters.indexes_removed,
    "constraints_added": counters.constraints_added,
    "constraints_removed": counters.constraints_removed,
}
```

## Testing
The fix has been verified with:
- ✅ Basic database connectivity tests
- ✅ Entity and officer search queries
- ✅ Complex Cypher queries with aggregations
- ✅ Trump-related offshore entity searches

## Files Modified
- `mcp/src/offshore_leaks_mcp/database.py` - Lines 159-185

## Compatibility
- **Neo4j Driver**: neo4j >= 5.0.0
- **Python**: 3.9+
- **Neo4j Database**: 5.15+

## Impact
This fix enables the MCP server to successfully:
1. Query the Offshore Leaks database
2. Return proper query results and metadata
3. Handle all query types (read, write, aggregations)
4. Work with resilience features (retries, circuit breakers)
