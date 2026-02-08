"""
Database Configuration and Session Management

Provides SQLAlchemy Base and session factory for database operations.

Configuration:
- SUPABASE_URL: Postgres connection via Supabase
- Uses connection pooling for performance
- Automatic session cleanup via context manager

Usage:
    from database import get_db, Base

    # In FastAPI dependency injection
    @app.get("/users")
    def get_users(db = Depends(get_db)):
        return db.query(User).all()

    # Create tables (migrations preferred)
    Base.metadata.create_all(bind=engine)
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Database URL from environment (Supabase Postgres)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
DATABASE_URL = SUPABASE_URL.replace("https://", "postgresql://") if SUPABASE_URL else ""

if not DATABASE_URL:
    logger.warning("SUPABASE_URL not configured - database operations will fail")
    DATABASE_URL = "postgresql://localhost/smartlic"  # Fallback for tests

# SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,        # Max 10 concurrent connections
    max_overflow=20,     # Allow 20 additional connections under load
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """
    Database session dependency for FastAPI.

    Yields:
        Session: SQLAlchemy database session

    Usage:
        @app.get("/items")
        def get_items(db = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
