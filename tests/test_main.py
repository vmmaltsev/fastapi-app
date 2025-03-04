import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup
from fastapi.responses import RedirectResponse

# Patch database modules before importing the application
with patch("sqlalchemy.create_engine"), patch("sqlalchemy.orm.sessionmaker"):
    from app.main import app
    from app.models import Record
    from app.database import get_db  # import dependency for override

# Create a test client
client = TestClient(app)

from typing import Generator

def override_get_db(mock_db: MagicMock) -> Generator[MagicMock, None, None]:
    """Override function for get_db dependency."""
    def _override():
        yield mock_db
    return _override

def test_docs_endpoint():
    """Test the documentation endpoint."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

def test_openapi_endpoint():
    """Test the OpenAPI endpoint."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

def test_read_root():
    """Test the main page with a mocked database."""
    mock_db = MagicMock()
    # Create a test record
    mock_record = Record(
        id=1, 
        title="Test Record", 
        content="Test Content", 
        created_at=datetime.now(), 
        updated_at=None
    )
    # Mock the chain: query -> order_by -> all
    mock_db.query.return_value.order_by.return_value.all.return_value = [mock_record]
    
    # Override get_db dependency
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    response = client.get("/")
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    # Verify that the template contains expected headings
    assert soup.find("h5", string="New Record")
    assert soup.find("h4", string="All Records")
    # Clear dependency overrides
    app.dependency_overrides.clear()

def test_create_record_form():
    """Test creating a record through a form."""
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    
    # Patch RedirectResponse in the module where it's used (e.g., app.main.RedirectResponse)
    with patch('app.main.RedirectResponse') as mock_redirect:
        mock_redirect.return_value.status_code = 303
        
        response = client.post("/records/", data={"title": "Test Record", "content": "Test Content"})
        # Check that the record was added and committed
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
    
    app.dependency_overrides.clear()

def test_delete_record():
    """Test deleting a record."""
    mock_db = MagicMock()
    # Mock return of a record for deletion
    mock_record = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_record
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    
    # Patch RedirectResponse in the module where it's used
    with patch('app.main.RedirectResponse') as mock_redirect:
        mock_redirect.return_value.status_code = 303
        
        response = client.post("/records/1/delete")
        # Check that delete and commit methods were called
        mock_db.delete.assert_called_with(mock_record)
        mock_db.commit.assert_called()
    
    app.dependency_overrides.clear()

def test_health_check():
    """Test the health check endpoint."""
    mock_db = MagicMock()
    # Simulate execute behavior for health check
    mock_execute = MagicMock()
    mock_execute.scalar.return_value = 1  # Simulate database available
    mock_db.execute.return_value = mock_execute
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert data["database"]["status"] in ["connected", "error"]
    
    app.dependency_overrides.clear()

def test_api_get_records():
    """Test retrieving a list of records via the API."""
    mock_db = MagicMock()
    mock_record = Record(
        id=1, 
        title="Test Record", 
        content="Test Content", 
        created_at=datetime.now(), 
        updated_at=None
    )
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [mock_record]
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    
    response = client.get("/api/records/")
    assert response.status_code == 200
    json_response = response.json()
    assert isinstance(json_response, list)
    assert json_response[0]["id"] == 1
    
    app.dependency_overrides.clear()

def test_api_create_record():
    """Тест создания записи через API."""
    mock_db = MagicMock()
    # Создаем имитацию возвращаемого объекта
    created_record = Record(
        id=1,
        title="API Test Record",
        content="API Test Content",
        created_at=datetime.now(),
        updated_at=None
    )
    # Настраиваем mock для возврата созданной записи после refresh
    mock_db.refresh = MagicMock(side_effect=lambda obj: setattr(obj, 'id', 1) or setattr(obj, 'created_at', created_record.created_at))
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    
    # Создаем тестовые данные
    test_data = {
        "title": "API Test Record",
        "content": "API Test Content"
    }
    
    response = client.post("/api/records/", json=test_data)
    assert response.status_code == 200
    
    # Проверяем, что запись была добавлена и сохранена
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    
    # Проверяем данные в ответе
    json_response = response.json()
    assert json_response["title"] == test_data["title"]
    assert json_response["content"] == test_data["content"]
    assert "id" in json_response
    assert "created_at" in json_response
    
    app.dependency_overrides.clear()

def test_api_get_record():
    """Тест получения конкретной записи через API."""
    mock_db = MagicMock()
    mock_record = Record(
        id=1, 
        title="Test Record", 
        content="Test Content", 
        created_at=datetime.now(), 
        updated_at=None
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_record
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    
    response = client.get("/api/records/1")
    assert response.status_code == 200
    
    # Проверяем данные в ответе
    json_response = response.json()
    assert json_response["id"] == 1
    assert json_response["title"] == "Test Record"
    assert json_response["content"] == "Test Content"
    
    app.dependency_overrides.clear()

def test_update_record():
    """Тест обновления записи."""
    mock_db = MagicMock()
    mock_record = Record(
        id=1, 
        title="Original Title", 
        content="Original Content", 
        created_at=datetime.now(), 
        updated_at=None
    )
    mock_db.query.return_value.filter.return_value.first.return_value = mock_record
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    
    # Данные для обновления
    update_data = {
        "title": "Updated Title",
        "content": "Updated Content"
    }
    
    response = client.put("/records/1", json=update_data)
    assert response.status_code == 200
    
    # Проверяем, что атрибуты были обновлены
    assert mock_record.title == "Updated Title"
    assert mock_record.content == "Updated Content"
    
    # Проверяем, что изменения были сохранены
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    
    # Проверяем данные в ответе
    json_response = response.json()
    assert json_response["id"] == 1
    assert json_response["title"] == "Updated Title"
    assert json_response["content"] == "Updated Content"
    
    app.dependency_overrides.clear()

def test_record_not_found():
    """Тест обработки ситуации, когда запись не найдена."""
    mock_db = MagicMock()
    # Возвращаем None, чтобы симулировать отсутствие записи
    mock_db.query.return_value.filter.return_value.first.return_value = None
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    
    # Проверяем GET запрос к несуществующей записи
    response = client.get("/api/records/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Record not found"
    
    # Проверяем PUT запрос к несуществующей записи
    update_data = {"title": "Updated Title", "content": "Updated Content"}
    response = client.put("/records/999", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Record not found"
    
    # Проверяем DELETE запрос к несуществующей записи
    response = client.post("/records/999/delete")
    assert response.status_code == 404
    
    app.dependency_overrides.clear()
