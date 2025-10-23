# Changelog

All notable changes to the Offshore Leaks MCP Server project.

## [Unreleased]

### Fixed
- **Database Module**: Fixed Neo4j Result object handling in `database.py`
  - Fixed `result.summary()` access after consuming records by using `result.consume()`
  - Fixed SummaryCounters serialization by explicitly extracting counter attributes
  - Resolves issues with query execution and metadata retrieval

### Added
- **Documentation**: Created comprehensive database setup guide (`DATABASE_SETUP.md`)
  - Docker-based Neo4j setup instructions
  - Database loading procedures
  - Configuration examples
  - Sample queries and troubleshooting
- **Documentation**: Added database fix details (`mcp/DATABASE_FIX.md`)
  - Technical explanation of the fixes
  - Code examples showing before/after
  - Testing verification

### Changed
- **Git Ignore**: Updated `.gitignore` to exclude sensitive data and test files
  - Added exclusions for database dumps (*.dump, *.csv, *.zip)
  - Added exclusions for test scripts and temporary files
  - Prevents accidental commit of large data files

### Verified
- ✅ MCP server database connectivity
- ✅ Entity and officer search functionality
- ✅ Complex Cypher query execution
- ✅ Successful queries against 2M+ node database

## Previous Releases

See git commit history for earlier changes.
