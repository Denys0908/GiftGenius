from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.config import settings

# Локальний фолбек на SQLite потребує check_same_thread=False для роботи з FastAPI
is_sqlite = settings.DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

# Підключення до БД: підтримує PostgreSQL 16 (CON-2) та локальний SQLite
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

# Фабрика сесій для обробки HTTP-запитів
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Надає сесію БД для кожного запиту FastAPI та гарантовано закриває її після завершення."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()