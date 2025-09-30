from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    # Database
    db_host: str = os.getenv("DB_HOST", "127.0.0.1")
    db_user: str = os.getenv("DB_USER", "nl2sql_app")
    db_pass: str = os.getenv("DB_PASS", "")
    db_name: str = os.getenv("DB_NAME", "shopdb")

    # Query safety
    default_limit: int = int(os.getenv("DEFAULT_LIMIT", "100"))

    # LLM (Ollama runtime)
    ollama_url: str = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "mistral")

# Create a global settings object
settings = Settings()