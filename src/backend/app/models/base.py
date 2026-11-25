import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class _DeclarativeRoot(DeclarativeBase):
    """Внутрішній корінь декларативних моделей SQLAlchemy 2.0."""
    pass


class SQLAlchemyBase(_DeclarativeRoot):
    """
    Абстрактний базовий клас для всіх сутностей БД (ЛР-2, Рисунок 3.2).
    Забезпечує спільні поля id (UUID PK) та created_at для моделей User і SavedGift
    (принцип LSP: усі моделі наслідують єдиний базовий контракт).
    """
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )