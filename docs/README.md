# NL2SQL Project Documentation

This documentation folder contains detailed explanations of all components and architectural decisions in the NL2SQL project.

## Component Documentation

- [Overview](overview.md) - High-level project overview and intent
- [FastAPI Backend](fastapi_backend.md) - API service that handles query processing
- [Natural Language to SQL](nl2sql_component.md) - Core LLM integration for query generation
- [Configuration Management](config_management.md) - Environment and settings management
- [Database Connector](database_connector.md) - Safe database interaction layer
- [Schema Introspector](schema_introspector.md) - Automatic schema discovery
- [SQL Validator](sql_validator.md) - Multi-layer SQL validation system
- [Prompt Builder](prompt_builder.md) - Schema-aware prompt construction
- [Streamlit Frontend](streamlit_frontend.md) - User interface for natural language queries

## Architectural Decisions

- [SELECT-Only Queries](decision_select_only.md) - Security decision to allow only read operations
- [Schema-Aware Prompting](decision_schema_aware.md) - Including schema in LLM prompts
- [SQL Validation with sqlglot](decision_sql_validation.md) - Multi-layer validation approach
- [Read-Only Database Access](decision_read_only_access.md) - Defense in depth security
- [Default LIMIT Enforcement](decision_limit_enforcement.md) - Preventing large result sets
- [Ollama Integration](decision_ollama_integration.md) - Local LLM service deployment
- [Streamlit Frontend](decision_streamlit_frontend.md) - Rapid development interface
- [FastAPI Backend](decision_fastapi_backend.md) - High-performance API framework

## Project Intent

The NL2SQL project aims to provide a safe, user-friendly interface for converting natural language questions into SQL queries. The system prioritizes security, accuracy, and usability while maintaining a clean, maintainable architecture.