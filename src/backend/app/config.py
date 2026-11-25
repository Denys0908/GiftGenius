import os
from pathlib import Path
from dotenv import load_dotenv

# Шукаємо файл .env у корені репозиторію GiftGenius (на 3 рівні вище від app/config.py)
ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT_DIR / ".env"

# Завантажуємо змінні оточення з .env (NFR-4: ізоляція секретів)
load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    """Клас для централізованого зберігання налаштувань сервера з файлу .env."""

    # Налаштування зовнішнього ШІ Google Gemini API (CON-3)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite")

    # Рядок підключення до БД: основний — PostgreSQL 16, локальний фолбек — SQLite (CON-2)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./giftgenius_local.db")

    # Параметри JWT-автентифікації (FR-6, NFR-4)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev_secret_key_change_me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    # Дозволені домени для політики CORS (NFR-4)
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]


# Єдиний об'єкт налаштувань для імпорту в інших модулях
settings = Settings()