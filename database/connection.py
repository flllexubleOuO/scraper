from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config

def get_engine():
    """Create and return database engine."""
    return create_engine(Config.DATABASE_URL)

def get_session():
    """Create and return database session."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def create_tables():
    """Create all tables in the database."""
    from database.models import Base
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
