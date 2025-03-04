from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database connection parameters from environment variables
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fastapi_app")

# Create database URL для основного подключения
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создаем engine для основного подключения с pool_pre_ping
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Функция-генератор для получения сессии базы данных.
    Автоматически закрывает сессию после использования.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        db.close()

def init_db():
    """
    Инициализирует базу данных, создавая все таблицы.
    Эта функция должна вызываться при запуске приложения.
    """
    max_retries = 10
    retry_delay = 3
    
    # Создаем URL для подключения к базе postgres с pool_pre_ping
    postgres_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
    postgres_engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)
    
    for i in range(max_retries):
        try:
            # Проверяем существование базы данных с параметризованным запросом
            with postgres_engine.connect() as conn:
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname=:dbname"),
                    {"dbname": DB_NAME}
                )
                exists = result.scalar()
                
                # Если база данных не существует, создаем её
                if not exists:
                    logger.info(f"Creating database '{DB_NAME}'...")
                    conn.execute(text("CREATE DATABASE " + DB_NAME))
                    logger.info(f"Database '{DB_NAME}' created")
            
            # Подключаемся к созданной базе данных и создаем таблицы
            with engine.connect() as conn:
                Base.metadata.create_all(bind=engine)
                logger.info(f"Database '{DB_NAME}' tables initialized successfully")
            
            return True
        except Exception as e:
            if i < max_retries - 1:
                logger.warning(f"Database initialization failed: {e}. Retrying in {retry_delay} seconds... ({i+1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to initialize database after {max_retries} attempts: {e}")
                return False
