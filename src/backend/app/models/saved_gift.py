import uuid
from decimal import Decimal
from sqlalchemy import ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import SQLAlchemyBase


class SavedGift(SQLAlchemyBase):
    """
    ORM-сутність таблиці saved_gifts (FR-7: список «Збережене» / Wishlist).
    """
    __tablename__ = "saved_gifts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    estimated_price_uah: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=True)

    # Прямі пошукові URL на українські маркетплейси (FR-5, CON-4)
    rozetka_url: Mapped[str] = mapped_column(String(500), nullable=True)
    prom_url: Mapped[str] = mapped_column(String(500), nullable=True)
    hotline_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Зворотний зв'язок із власником картки
    user = relationship("User", back_populates="saved_gifts")