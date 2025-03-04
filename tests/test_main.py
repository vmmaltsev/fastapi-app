from fastapi.testclient import TestClient
from app.main import app
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "New Record" in response.text
    assert "All Records" in response.text

def test_create_record_form():
    response = client.post(
        "/records/",
        data={
            "title": "Test Record",
            "content": "Test Content"
        }
    )
    assert response.status_code == 200 or response.status_code == 303

def test_delete_record():
    # First create a record via API
    response = client.post(
        "/api/records/",
        json={
            "title": "Record to Delete",
            "content": "Content to Delete"
        }
    )
    assert response.status_code == 200
    record_id = response.json()["id"]
    
    # Delete the created record
    response = client.post(f"/records/{record_id}/delete")
    assert response.status_code == 200 or response.status_code == 303

def test_api_endpoints():
    # Create test record via API
    response = client.post(
        "/api/records/",
        json={
            "title": "API Test",
            "content": "API Test Content"
        }
    )
    assert response.status_code == 200
    record_id = response.json()["id"]
    
    # Check record retrieval
    response = client.get(f"/api/records/{record_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "API Test"
    
    # Check records list
    response = client.get("/api/records/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

@patch('app.database.SessionLocal')
def test_health_check(mock_session):
    # Создаем мок для сессии базы данных
    mock_db = MagicMock()
    mock_session.return_value = mock_db
    
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert "database" in response.json()
    assert "environment" in response.json()

def test_database_error():
    with patch('app.database.SessionLocal') as mock_session:
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("Database connection error")
        mock_session.return_value = mock_db
        
        response = client.get("/health")
        assert response.status_code == 500
        assert "Database connection error" in response.json()["detail"]

def test_update_record():
    # Create record for update
    response = client.post(
        "/api/records/",
        json={
            "title": "Initial Title",
            "content": "Initial Content"
        }
    )
    assert response.status_code == 200
    record_id = response.json()["id"]
    
    # Update record
    response = client.put(
        f"/records/{record_id}",
        json={
            "title": "Updated Title",
            "content": "Updated Content"
        }
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"
    assert response.json()["content"] == "Updated Content"

def test_record_not_found():
    response = client.get("/api/records/999999")
    assert response.status_code == 404
    assert "Record not found" in response.json()["detail"]

def test_docs_endpoint():
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_openapi_endpoint():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    assert "openapi" in response.json()
    assert "info" in response.json()
    assert response.json()["info"]["title"] == "FastAPI PostgreSQL App"
