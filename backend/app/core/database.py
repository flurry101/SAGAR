from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Generator
from app.config import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    """FastAPI dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    try:
        from app.models.user import User  # noqa: F401
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Database initialization deferred: {e}")