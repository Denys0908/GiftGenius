from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models import SQLAlchemyBase, SavedGift, User  # noqa: F401
from app.routers import auth_router, gift_router, wishlist_router

# Створення таблиць users та saved_gifts у БД за ORM-моделями
SQLAlchemyBase.metadata.create_all(bind=engine)

app = FastAPI(
    title="GiftGenius API",
    description="REST API веб-сервісу персоналізованого підбору подарунків (ЛР-4).",
    version="1.0.0",
)

# Налаштування CORS для доступу з React SPA (NFR-4)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Підключення функціональних роутерів API
app.include_router(gift_router)
app.include_router(auth_router)
app.include_router(wishlist_router)


@app.get("/", tags=["Health"])
def health_check() -> dict[str, str]:
    """Базова перевірка працездатності сервера."""
    return {"status": "ok", "service": "GiftGenius API"}