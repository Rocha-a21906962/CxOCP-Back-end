import pytest
from fastapi.testclient import TestClient
from app import app

# Create a TestClient for your FastAPI app
client = TestClient(app)

# Write your test cases
def test_hello():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from Azure Container App!"}

# pip install pytest httpx