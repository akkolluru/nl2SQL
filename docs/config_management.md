# Configuration Management Component

## Purpose

The configuration management component handles all environment-specific settings and application parameters. It provides a centralized way to manage settings without hardcoding values in the application code.

## Functionality

- **Environment Loading**: Loads settings from .env files
- **Parameter Management**: Manages database, LLM, and safety configuration parameters
- **Default Values**: Provides sensible defaults when environment variables are missing
- **Type Conversion**: Ensures configuration values are properly typed

## Key Features

- Secure handling of database credentials
- Flexible LLM configuration (URL, model selection)
- Query safety parameters (default LIMIT enforcement)
- Automatic type conversion for numeric values

## Configuration Parameters

### Database Settings
- `db_host`: Database server hostname (default: "127.0.0.1")
- `db_user`: Database username (default: "nl2sql_app")
- `db_pass`: Database password (default: "")
- `db_name`: Database name (default: "shopdb")

### LLM Settings
- `ollama_url`: Ollama service URL (default: "http://127.0.0.1:11434")
- `ollama_model`: Selected LLM model (default: "mistral")

### Safety Settings
- `default_limit`: Maximum number of rows returned (default: 100)

## How It Works

1. Loads environment variables from the .env file using python-dotenv
2. Creates a Settings object with typed fields
3. Falls back to default values when environment variables are not set
4. Provides a global `settings` instance for other components to use

## Security Considerations

- Database credentials are loaded from environment variables, not hardcoded
- Password defaults to empty string if not provided
- Configuration is validated at startup to catch missing values