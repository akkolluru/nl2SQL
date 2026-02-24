# Natural Language to SQL Component

## Purpose

The NL2SQL component is responsible for converting natural language questions into executable SQL queries using a Large Language Model (LLM). It serves as the core intelligence of the system, translating human-readable questions into database queries.

## Functionality

- **LLM Communication**: Sends prompts to the Ollama service and receives SQL responses
- **Prompt Processing**: Formats and sends schema-aware prompts to the LLM
- **Response Cleaning**: Cleans and normalizes the LLM's SQL output
- **Code Fence Handling**: Removes markdown code fences and "sql" tags from LLM output

## Key Features

- Asynchronous communication with Ollama service
- Automatic cleaning of LLM artifacts (code fences, "sql" tags)
- SQL statement normalization (ensuring proper semicolons)
- Integration with the configuration system for LLM settings

## How It Works

1. Receives a formatted prompt containing the user question and database schema
2. Sends the prompt to the Ollama API endpoint
3. Waits for the LLM to generate a SQL response
4. Cleans the response by removing markdown formatting
5. Ensures the SQL statement ends with a semicolon
6. Returns the cleaned SQL query to the calling component

## Configuration

- Uses settings from the config module for Ollama URL and model selection
- Supports configurable timeout for API requests (60 seconds by default)
- Compatible with various Ollama models (default: mistral)