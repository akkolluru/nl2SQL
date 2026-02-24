# Architecture Decision: Default LIMIT Enforcement

## Decision

The system automatically appends a LIMIT clause to SELECT queries that don't already have one, preventing potentially large result sets from overwhelming the system.

## Rationale

- **Performance**: Prevents queries that return excessive amounts of data
- **Resource Management**: Protects against resource exhaustion
- **User Experience**: Ensures quick responses for most queries
- **Configurability**: Allows adjustment based on deployment needs

## Implementation

- Database connector checks for existing LIMIT clause
- Automatically appends LIMIT with default value if missing
- Configurable default limit via environment variables
- Applied at the database execution layer

## Impact

- Prevents accidental resource exhaustion
- Ensures predictable response times
- May truncate results for legitimate large queries
- Provides configurable safety net