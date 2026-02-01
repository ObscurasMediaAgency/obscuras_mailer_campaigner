"""
Obscuras Campaign Manager - Database Configuration
SQLAlchemy database setup and session management.
"""

from pathlib import Path
from contextlib import contextmanager
from typing import Any
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from utils.logging_config import get_logger

# ═══════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════

logger = get_logger("models.database")

# ═══════════════════════════════════════════════════════════════════
# DATABASE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent.parent
DATABASE_DIR = BASE_DIR / "data"
DATABASE_FILE = DATABASE_DIR / "campaigns.db"

# Ensure data directory exists
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
logger.debug(f"Datenbank-Verzeichnis: {DATABASE_DIR}")

# SQLAlchemy Setup
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ═══════════════════════════════════════════════════════════════════
# SQL QUERY LOGGING (für Development)
# ═══════════════════════════════════════════════════════════════════

@event.listens_for(engine, "before_cursor_execute")
def log_queries(
    conn: Any,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any,
    executemany: bool
) -> None:
    """Log SQL queries in debug mode."""
    sql_logger = get_logger("models.sql")
    sql_logger.debug(f"SQL: {statement[:100]}..." if len(statement) > 100 else f"SQL: {statement}")


def init_database() -> None:
    """Initialize database and create all tables."""
    logger.info("Initialisiere Datenbank...")
    
    # Import models to register them with Base.metadata
    # Using __import__ to avoid unused import warnings
    __import__("models.campaign")
    __import__("models.contact")
    __import__("models.smtp_profile")
    __import__("models.send_log")
    __import__("models.template")
    __import__("models.blacklist")
    
    Base.metadata.create_all(bind=engine)
    logger.info(f"✓ Datenbank initialisiert: {DATABASE_FILE}")
    
    # Log table count
    table_count = len(Base.metadata.tables)
    logger.debug(f"Tabellen erstellt/verifiziert: {table_count}")


@contextmanager
def get_session():
    """
    Get a database session as context manager.
    
    Usage:
        with get_session() as session:
            session.query(Model).all()
    """
    session = SessionLocal()
    logger.debug("Neue Datenbank-Session geöffnet")
    try:
        yield session
        session.commit()
        logger.debug("Session erfolgreich committed")
    except Exception as e:
        session.rollback()
        logger.error(f"Session rollback nach Fehler: {e}")
        raise
    finally:
        session.close()
        logger.debug("Session geschlossen")


def get_session_simple():
    """Get a database session (without context manager)."""
    return SessionLocal()


def get_engine():
    """Get the database engine."""
    return engine

