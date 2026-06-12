from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import the shared Base so main.py can call Base.metadata.create_all(bind=engine)
from app.models.base import Base  # noqa: E402, F401


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()