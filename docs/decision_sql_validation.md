# Architecture Decision: SQL Validation with sqlglot

## Decision

The system uses the sqlglot library to parse and validate generated SQL, implementing multiple layers of validation including syntax, schema, and safety checks.

## Rationale

- **Security**: Prevents SQL injection and malicious queries
- **Accuracy**: Ensures generated SQL is syntactically correct
- **Schema Compliance**: Verifies queries reference valid tables/columns
- **Flexibility**: sqlglot provides robust parsing and analysis capabilities
- **Alias Handling**: Properly validates queries with table aliases

## Implementation

- Multi-layer validation approach (syntax, policy, schema, safety)
- sqlglot AST analysis for comprehensive query understanding
- Alias-to-table mapping for proper schema validation
- JOIN safety enforcement (requires ON/USING clauses)
- Blocked keywords and functions list

## Impact

- Significantly improves security posture
- Ensures high-quality SQL output
- Adds validation overhead but worth the safety
- Enables complex validation that simple regex cannot handle
- Provides detailed error messages for debugging