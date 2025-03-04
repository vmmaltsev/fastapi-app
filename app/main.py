from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
import os
import logging
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from sqlalchemy import text

from . import models, schemas
from .database import get_db, init_db

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()  # Убедитесь, что init_db корректно инициализирует базу
    logger.info("Database initialized successfully")
    yield
    logger.info("Shutting down...")

# Создание экземпляра FastAPI
app = FastAPI(
    title="FastAPI PostgreSQL App",
    description="Simple FastAPI application with PostgreSQL connection",
    version="0.1.0",
    lifespan=lifespan
)

# Настройка статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    """Главная страница приложения."""
    records = db.query(models.Record).order_by(models.Record.created_at.desc()).all()
    return templates.TemplateResponse(request, "index.html", {"records": records})

@app.post("/records/", response_class=RedirectResponse)
async def create_record(
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    """Создание новой записи через форму."""
    record = models.Record(title=title, content=content)
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при создании записи: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка базы данных")
    return RedirectResponse(url="/", status_code=303)

@app.post("/records/{record_id}/delete", response_class=RedirectResponse)
async def delete_record(record_id: int, db: Session = Depends(get_db)):
    """Удаление записи."""
    record = db.query(models.Record).filter(models.Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    try:
        db.delete(record)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при удалении записи: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка базы данных")
    return RedirectResponse(url="/", status_code=303)

@app.get("/api/records/", response_model=List[schemas.Record])
def read_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Получение списка записей через API."""
    return db.query(models.Record).offset(skip).limit(limit).all()

@app.post("/api/records/", response_model=schemas.Record)
def create_record_api(record: schemas.RecordCreate, db: Session = Depends(get_db)):
    """Создание новой записи через API."""
    db_record = models.Record(title=record.title, content=record.content)
    try:
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при создании записи через API: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка базы данных")
    return db_record

@app.get("/api/records/{record_id}", response_model=schemas.Record)
def read_record(record_id: int, db: Session = Depends(get_db)):
    """Получение одной записи по ID."""
    record = db.query(models.Record).filter(models.Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Проверка состояния приложения."""
    health_data = {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }
    try:
        db.execute(text("SELECT 1"))
        health_data["database"] = {"status": "connected"}
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        health_data["database"] = {"status": "error", "message": str(e)}
    return health_data

@app.put("/records/{record_id}", response_model=schemas.Record)
def update_record(record_id: int, record: schemas.RecordCreate, db: Session = Depends(get_db)):
    """Обновление записи."""
    db_record = db.query(models.Record).filter(models.Record.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    update_data = record.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_record, key, value)
    
    try:
        db.commit()
        db.refresh(db_record)
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при обновлении записи: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка базы данных")
    return db_record
