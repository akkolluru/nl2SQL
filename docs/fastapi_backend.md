# FastAPI Backend Component

## Purpose

The FastAPI backend serves as the core API service that handles the conversion of natural language questions into SQL queries. It acts as the intermediary between the frontend interface and the database operations.

## Functionality

- **API Endpoints**: Provides `/health`, `/schema`, and `/query` endpoints
- **Request Processing**: Takes natural language questions and processes them through the NL2SQL pipeline
- **Meta Query Handling**: Directly handles schema-related questions without using the LLM
- **Response Formatting**: Returns structured responses with SQL, columns, and data rows

## Key Features

- Health check endpoint for monitoring service status
- Schema introspection endpoint to view database structure
- Query endpoint that processes natural language to SQL
- Built-in meta query handling for schema exploration

## How It Works

1. Receives a natural language question via the `/query` endpoint
2. Checks if it's a meta question (about schema/tables) and handles directly
3. If it's a regular query, builds a schema-aware prompt
4. Sends the prompt to the LLM service for SQL generation
5. Validates the generated SQL against safety rules
6. Executes the validated SQL against the database
7. Returns the results in a structured format

## Endpoints

- `GET /`: Service information and available endpoints
- `GET /health`: Health check returning service status
- `GET /schema`: Returns database schema summary
- `POST /query`: Converts natural language to SQL and executes it