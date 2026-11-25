from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import SQLAlchemyBase


class User(SQLAlchemyBase):
    """
    ORM-сутність таблиці users (FR-6, NFR-4: принцип мінімізації даних —
    зберігаються лише email і bcrypt-хеш пароля).
    """
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Композиція 1 до 0..*: при видаленні користувача його збережені подарунки видаляються каскадно
    saved_gifts = relationship(
        "SavedGift",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def verify_access(self) -> bool:
        """Перевіряє, що обліковий запис коректно ініціалізований і має право доступу."""
        return bool(self.id and self.email and self.password_hash)