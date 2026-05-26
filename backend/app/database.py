from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import DATABASE_URL

# SQLite needs check_same_thread=False for FastAPI's threaded request handling.
_connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
engine = create_engine(DATABASE_URL, connect_args=_connect_args, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM base class
Base = declarative_base()


def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI to inject a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
