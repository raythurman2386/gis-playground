from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from utils.logger import setup_logger
from config.logging_config import CURRENT_LOGGING_CONFIG
import os
from dotenv import load_dotenv

load_dotenv()

logger = setup_logger(
    "database",
    log_level=CURRENT_LOGGING_CONFIG["log_level"],
    log_dir=CURRENT_LOGGING_CONFIG["log_dir"],
)

SQLALCHEMY_DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:5432/{os.getenv('POSTGRES_DB')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=os.getenv('FLASK_ENV') != 'production',
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def check_tables_exist():
    """Check if the required tables exist in the database"""
    try:
        inspector = inspect(engine)
        required_tables = ["spatial_layers", "features", "layer_attributes", "upload_history"]
        existing_tables = inspector.get_table_names()
        return all(table in existing_tables for table in required_tables)
    except Exception as e:
        logger.error(f"Failed to check tables: {e}")
        return False


def get_db():
    """Database session generator"""
    if not check_tables_exist():
        logger.error("Database tables do not exist. Please run 'python manage.py init' to initialize the database.")
        raise RuntimeError("Database tables do not exist. Please run 'python manage.py init' to initialize the database.")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
