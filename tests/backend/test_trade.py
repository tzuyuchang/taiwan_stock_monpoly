import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_trade_endpoint():
    response = client.get("/trade")
    assert response.status_code == 200
    # Expect a JSON list (could be empty)
    assert isinstance(response.json(), list)
