from sqlalchemy import create_engine
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
    echo=True,  # Set to False in production
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Database session generator"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    try:
        # Import models here to ensure they're registered with Base
        from app.models.spatial import (
            SpatialLayer,
            Feature,
            LayerAttribute,
            UploadHistory,
        )

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False


def init_db():
    """Initialize the database"""
    try:
        # Create all tables
        create_tables()
        logger.info("Database initialized successfully with PostGIS extensions")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False
