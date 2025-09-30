# Project Progress

## Implemented Features
- **Schema-aware SQL generation**  
  Database schema is introspected automatically and provided to the LLM to ensure only valid tables and columns are used.

- **LLM-powered SQL generation**  
  English questions are translated into SQL using Ollama with models like Mistral.

- **Validation & safety layer**  
  SQL is checked for syntax, schema validity, and blocked keywords. Only `SELECT` queries are allowed.

- **Safe execution on MySQL**  
  Queries run under a read-only user with enforced `LIMIT` for large outputs.

- **FastAPI backend**  
  Provides `/query`, `/health`, and optional schema endpoints for frontend integration.

- **Streamlit frontend**  
  Clean UI with:
  - input box for questions  
  - results table  
  - optional generated SQL view  
  - history of queries  
  - CSV export  
  - sidebar for settings