from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
import os
from dotenv import load_dotenv

from . import models, schemas
from .database import engine, get_db

# Create tables
models.Base.metadata.create_all(bind=engine)

# Load environment variables
load_dotenv()

# Create FastAPI instance
app = FastAPI(
    title="FastAPI PostgreSQL App",
    description="Simple FastAPI application with PostgreSQL connection",
    version="1.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    records = db.query(models.Record).order_by(models.Record.created_at.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"records": records}
    )

@app.post("/records/", response_class=RedirectResponse)
async def create_record(
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    db_record = models.Record(title=title, content=content)
    db.add(db_record)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/records/{record_id}/delete", response_class=RedirectResponse)
async def delete_record(record_id: int, db: Session = Depends(get_db)):
    db_record = db.query(models.Record).filter(models.Record.id == record_id).first()
    if db_record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(db_record)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

# API endpoints for programmatic access
@app.get("/api/records/", response_model=List[schemas.Record])
def read_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    records = db.query(models.Record).offset(skip).limit(limit).all()
    return records

@app.post("/api/records/", response_model=schemas.Record)
def create_record_api(record: schemas.RecordCreate, db: Session = Depends(get_db)):
    db_record = models.Record(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@app.get("/api/records/{record_id}", response_model=schemas.Record)
def read_record(record_id: int, db: Session = Depends(get_db)):
    db_record = db.query(models.Record).filter(models.Record.id == record_id).first()
    if db_record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return db_record

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Check database connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection error: {str(e)}"
        )

@app.put("/records/{record_id}", response_model=schemas.Record)
def update_record(record_id: int, record: schemas.RecordCreate, db: Session = Depends(get_db)):
    db_record = db.query(models.Record).filter(models.Record.id == record_id).first()
    if db_record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    
    for key, value in record.model_dump().items():
        setattr(db_record, key, value)
    
    db.commit()
    db.refresh(db_record)
    return db_record
