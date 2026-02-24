# Architecture Decision: Schema-Aware Prompting

## Decision

The system automatically introspects the database schema and includes it in the LLM prompt to ensure generated queries only use valid tables and columns.

## Rationale

- **Accuracy**: Ensures LLM generates queries that match the actual database structure
- **Reliability**: Prevents queries against non-existent tables/columns
- **Adaptability**: Works with any database schema without manual configuration
- **Self-Documentation**: The system knows what data is available

## Implementation

- Schema introspector component queries INFORMATION_SCHEMA
- Compact schema representation included in every prompt
- Real-time schema discovery (not cached in MVP)
- Validation layer cross-checks generated SQL against actual schema

## Impact

- Improves query accuracy and success rate
- Eliminates need for manual schema configuration
- Adds slight latency for schema discovery on each query
- Enables the system to work with different database schemas