## ADDED Requirements

### Requirement: Content-addressed parse cache
When a cache directory is provided, PDF ingestion SHALL key a parse by the file's content hash (plus
parser) and reuse a cached Evidence Pool on a hit instead of re-parsing, with figure images persisted
in the cache and referenced by stable paths.

#### Scenario: Re-ingesting the same file hits the cache
- **WHEN** the same PDF is ingested twice with the same cache directory
- **THEN** the underlying parse runs only once and the second call returns the cached result
