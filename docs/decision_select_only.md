# Architecture Decision: SELECT-Only Queries

## Decision

The system enforces that only SELECT queries are allowed in the MVP, blocking all data modification operations (INSERT, UPDATE, DELETE, etc.).

## Rationale

- **Security**: Prevents malicious users from modifying or deleting data
- **Safety**: Ensures the system can only read data, not change it
- **Simplicity**: Reduces complexity in the validation layer for the MVP
- **Trust**: Allows deployment in environments where data integrity is critical

## Implementation

- Validation layer explicitly checks that queries start with SELECT
- Blocked keywords list includes all data modification commands
- Clear error messages when non-SELECT queries are detected
- Optional repair mechanism attempts to fix invalid queries

## Impact

- Limits functionality to read-only operations
- Significantly reduces security risks
- Simplifies validation logic
- May require future expansion for write operations with proper controls