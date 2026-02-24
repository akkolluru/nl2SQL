# SQL Validator Component

## Purpose

The SQL validator component ensures that generated SQL queries are safe, syntactically correct, and conform to the database schema. It implements multiple layers of validation to prevent malicious or invalid queries from being executed.

## Functionality

- **Syntax Validation**: Checks SQL syntax using sqlglot parser
- **Policy Enforcement**: Ensures only SELECT queries are allowed
- **Schema Validation**: Verifies that tables and columns exist in the database
- **Safety Checks**: Blocks dangerous keywords and functions

## Key Features

- Multi-layer validation approach (syntax, policy, schema, safety)
- Alias-aware schema validation
- Protection against SQL injection and malicious operations
- JOIN safety enforcement (requires ON/USING clauses)

## Validation Layers

### 1. Syntax Validation
- Uses sqlglot to parse the SQL statement
- Catches syntax errors before execution

### 2. Policy Validation
- Only allows SELECT statements in the MVP
- Blocks all data modification operations

### 3. Safety Validation
- Blocks dangerous keywords: DROP, TRUNCATE, ALTER, RENAME, INSERT, UPDATE, DELETE, REPLACE, CREATE, GRANT, REVOKE
- Blocks dangerous functions: LOAD_FILE, SLEEP

### 4. Schema Validation
- Verifies all referenced tables exist in the database
- Checks that all columns exist in their respective tables
- Handles table aliases correctly
- Supports both qualified and unqualified column references

### 5. JOIN Safety
- Requires JOIN clauses to have ON or USING conditions
- Prevents accidental Cartesian products

## How It Works

1. Receives the generated SQL and allowed schema information
2. Performs basic cleaning (removes code fences, ensures semicolons)
3. Checks if the query is a SELECT statement
4. Validates against blocked keywords and functions
5. Parses the SQL using sqlglot to create an AST
6. Builds table-to-alias mappings for proper validation
7. Verifies all referenced tables exist in the allowed set
8. Validates all column references against the schema
9. Ensures JOIN clauses have proper conditions
10. Returns validation result with error messages if validation fails

## Repair Mechanism

The system includes a one-shot repair mechanism that attempts to fix validation errors by sending the error message and schema information back to the LLM for correction.