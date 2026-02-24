# Database Connector Component

## Purpose

The database connector component handles all interactions with the MySQL database. It provides a safe and controlled way to execute SQL queries while implementing important security measures.

## Functionality

- **Connection Management**: Establishes and manages MySQL database connections
- **Query Execution**: Safely executes validated SQL queries
- **Result Formatting**: Returns query results in a structured format
- **Safety Enforcement**: Automatically adds LIMIT clauses to prevent large result sets

## Key Features

- Connection pooling with proper resource cleanup
- Automatic LIMIT enforcement for SELECT queries
- Safe result formatting with column names and data rows
- Proper error handling and connection closure

## How It Works

1. Establishes a MySQL connection using configuration parameters
2. Checks if the query is a SELECT statement without a LIMIT clause
3. Automatically appends a LIMIT clause if missing (using default_limit)
4. Executes the query and fetches results
5. Extracts column names from the cursor description
6. Returns both column names and data rows in a structured format
7. Ensures proper cleanup of database resources

## Safety Measures

- Connection timeout to prevent hanging connections
- Read-only operations enforced at the application level
- Automatic LIMIT enforcement to prevent large result sets
- Proper cursor and connection cleanup in finally blocks

## Return Format

The component returns a tuple containing:
- `columns`: List of column names from the query result
- `rows`: List of dictionaries representing each row of data