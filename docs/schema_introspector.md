# Schema Introspector Component

## Purpose

The schema introspector component automatically discovers and provides information about the database structure. It enables the system to understand available tables and columns, which is essential for generating valid SQL queries.

## Functionality

- **Schema Discovery**: Queries INFORMATION_SCHEMA to discover database structure
- **Table Listing**: Provides lists of available tables in the database
- **Column Discovery**: Retrieves column information for specific tables
- **Schema Summary**: Creates a compact representation of the database schema

## Key Features

- Real-time schema introspection from INFORMATION_SCHEMA
- Comprehensive table and column discovery
- Compact schema representation for LLM prompts
- Caching-friendly design (though not implemented in MVP)

## Main Functions

### get_schema_summary()
Returns a compact string representation of the database schema in the format:
"Tables: customers(customer_id, name, city); orders(order_id, customer_id, amount_paid)"

### allowed_sets()
Returns a tuple with:
- Set of all table names in the database
- Dictionary mapping table names to sets of their column names
Used by the validator to check schema validity

### list_tables()
Returns a list of all table names in the database, sorted alphabetically

### list_columns(table_name)
Returns a list of all column names for a given table, ordered by their position in the table

## How It Works

1. Establishes a MySQL connection using configuration parameters
2. Queries INFORMATION_SCHEMA.COLUMNS to get table and column information
3. Organizes the data into appropriate data structures
4. Returns the requested information in the required format
5. Ensures proper cleanup of database resources

## Security Considerations

- Uses read-only access to INFORMATION_SCHEMA
- Parameterized queries to prevent SQL injection
- Proper connection cleanup in finally blocks