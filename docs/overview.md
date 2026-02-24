# NL2SQL Project Overview

## Project Intent

The NL2SQL (Natural Language to SQL) project is designed to convert natural language questions into safe, validated SQL queries that can be executed against a MySQL database. The system provides a user-friendly interface that allows non-technical users to query databases using plain English.

## Core Purpose

- **Natural Language Interface**: Convert English questions into SQL queries
- **Safety First**: Validate and restrict queries to prevent malicious operations
- **Schema Awareness**: Automatically introspect database schema to ensure valid queries
- **User-Friendly Access**: Provide a clean interface for non-technical users to access database information

## Architecture

The system follows a three-tier architecture:
1. **Frontend**: Streamlit-based UI for user interaction
2. **Backend**: FastAPI service that handles query processing
3. **Database**: MySQL database with read-only access

## Key Features

- Schema-aware SQL generation
- LLM-powered query conversion
- Validation and safety layer
- Safe execution on MySQL
- Clean Streamlit frontend interface