from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
import time
import logging
import re  # Optional: for validating DB_NAME

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Retrieve database connection parameters from environment variables
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fastapi_app")

# Optional: Validate DB_NAME to allow only alphanumeric characters and underscores
if not re.match(r'^\w+$', DB_NAME):
    raise ValueError("Invalid DB_NAME provided.")

# Create database URL for the main connection
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine for the main connection with pool_pre_ping enabled
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Generator function to obtain a database session.
    Automatically closes the session after use.
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
    Initializes the database by creating all tables.
    This function should be called at application startup.
    """
    max_retries = 10
    retry_delay = 3

    # Create URL for connecting to the 'postgres' database with pool_pre_ping enabled
    postgres_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
    postgres_engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)

    for i in range(max_retries):
        try:
            # Check if the target database exists using a parameterized query
            with postgres_engine.connect() as conn:
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname=:dbname"),
                    {"dbname": DB_NAME}
                )
                exists = result.scalar()

                # If the database does not exist, create it
                if not exists:
                    logger.info(f"Creating database '{DB_NAME}'...")
                    # Note: Parameterization is not available for DDL statements; ensure DB_NAME is safe.
                    conn.execute(text("CREATE DATABASE " + DB_NAME))
                    logger.info(f"Database '{DB_NAME}' created")

            # Connect to the target database and create tables
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
