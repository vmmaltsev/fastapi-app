import pytest
from unittest.mock import MagicMock
from datetime import datetime
from fastapi.testclient import TestClient
from bs4 import BeautifulSoup
from fastapi.responses import RedirectResponse

# Патчим модули базы данных перед импортом приложения
from unittest.mock import patch
with patch("sqlalchemy.create_engine"), patch("sqlalchemy.orm.sessionmaker"):
    from app.main import app
    from app.models import Record
    from app.database import get_db  # импорт зависимости для переопределения

# Создаем тестовый клиент
client = TestClient(app)

# Функция-замена для get_db, возвращающая генератор
def override_get_db(mock_db):
    def _override():
        yield mock_db
    return _override

def test_docs_endpoint():
    """Тест эндпоинта документации."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

def test_openapi_endpoint():
    """Тест эндпоинта OpenAPI."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

def test_read_root():
    """Тест главной страницы с моком базы данных."""
    mock_db = MagicMock()
    # Создаем тестовую запись
    mock_record = Record(id=1, title="Test Record", content="Test Content", created_at=datetime.now(), updated_at=None)
    # Мокаем цепочку вызовов: query -> order_by -> all
    mock_db.query.return_value.order_by.return_value.all.return_value = [mock_record]
    
    # Переопределяем зависимость get_db
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    response = client.get("/")
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")
    assert soup.find("h5", string="New Record")
    assert soup.find("h4", string="All Records")
    # Сбрасываем переопределения
    app.dependency_overrides.clear()

def test_create_record_form():
    """Тест создания записи через форму."""
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    
    # Используем монкипатч для RedirectResponse
    with patch('fastapi.responses.RedirectResponse') as mock_redirect:
        mock_redirect.return_value.status_code = 303
        
        response = client.post("/records/", data={"title": "Test Record", "content": "Test Content"})
        # Проверяем, что запись была добавлена и зафиксирована
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
    
    app.dependency_overrides.clear()

def test_delete_record():
    """Тест удаления записи."""
    mock_db = MagicMock()
    # Мокаем возврат записи для удаления
    mock_record = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_record
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    
    # Используем монкипатч для RedirectResponse
    with patch('fastapi.responses.RedirectResponse') as mock_redirect:
        mock_redirect.return_value.status_code = 303
        
        response = client.post("/records/1/delete")
        # Проверяем, что была вызвана функция удаления записи
        mock_db.delete.assert_called_with(mock_record)
        mock_db.commit.assert_called()
    
    app.dependency_overrides.clear()

def test_health_check():
    """Тест проверки здоровья приложения."""
    mock_db = MagicMock()
    # Для health check можно смоделировать поведение execute
    mock_execute = MagicMock()
    mock_execute.scalar.return_value = 1  # Симулируем, что база доступна
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
    """Тест получения списка записей через API."""
    mock_db = MagicMock()
    mock_record = Record(id=1, title="Test Record", content="Test Content", created_at=datetime.now(), updated_at=None)
    mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [mock_record]
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    
    response = client.get("/api/records/")
    assert response.status_code == 200
    json_response = response.json()
    assert isinstance(json_response, list)
    assert json_response[0]["id"] == 1
    
    app.dependency_overrides.clear()
