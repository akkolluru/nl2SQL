
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.json_adapter import JSONSchemaAdapter
import json
import os

# Mock the dependency to use JSON Adapter
# We can use dependency override or simply configure the factory via env vars if that's how it worked.
# But dependency override is cleaner for tests.

@pytest.fixture
def client(tmp_path):
    # Create a dummy schema file
    schema = {
        "tables": {
            "users": ["id", "name"]
        }
    }
    p = tmp_path / "schema.json"
    p.write_text(json.dumps(schema))
    
    # Override dependency
    from app.main import get_db
    from app.database.base import BaseAdapter
    
    # We need a class that implements BaseAdapter which we already have
    def override_get_db():
        adapter = JSONSchemaAdapter(str(p))
        try:
            yield adapter
        finally:
            adapter.close()
            
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "en" in response.json()["supported_languages"]

def test_query_flow(client):
    # We need to mock generate_sql as well because it calls Ollama or LLM.
    # So we should patch app.main.generate_sql
    from unittest.mock import patch, AsyncMock
    
    with patch("app.main.generate_sql", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "SELECT name FROM users;"
        
        response = client.post("/query", json={"question": "Show all users"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["sql"] == "SELECT name FROM users;"
        # JSON adapter returns empty rows
        assert data["rows"] == []
