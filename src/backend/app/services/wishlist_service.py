from uuid import UUID
from sqlalchemy.orm import Session

from app.models import SavedGift
from app.schemas import GiftCardSchema


class WishlistService:
    """
    Сервіс керування списком «Збережене» (FR-7, UC-2, GG-12).
    Принцип SRP: відповідає виключно за CRUD-операції з таблицею saved_gifts без прив'язки до HTTP.
    """

    def get_user_wishlist(self, db: Session, user_id: UUID) -> list[SavedGift]:
        """Повертає збережені подарунки конкретного користувача (від новіших до старіших)."""
        return (
            db.query(SavedGift)
            .filter(SavedGift.user_id == user_id)
            .order_by(SavedGift.created_at.desc())
            .all()
        )

    def save_to_wishlist(
        self, db: Session, user_id: UUID, card: GiftCardSchema
    ) -> SavedGift:
        """Зберігає обрану картку подарунка в БД із прив'язкою до user_id."""
        item = SavedGift(
            user_id=user_id,
            title=card.title,
            category=card.category,
            estimated_price_uah=card.estimated_price_uah,
            reasoning=card.reasoning,
            rozetka_url=str(card.links.rozetka),
            prom_url=str(card.links.prom_ua),
            hotline_url=str(card.links.hotline),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def delete_from_wishlist(self, db: Session, user_id: UUID, gift_id: UUID) -> bool:
        """
        Видаляє подарунок лише якщо він належить поточному користувачу (захист від IDOR).
        Повертає True при успішному видаленні або False, якщо запис не знайдено.
        """
        item = (
            db.query(SavedGift)
            .filter(SavedGift.id == gift_id, SavedGift.user_id == user_id)
            .first()
        )
        if not item:
            return False

        db.delete(item)
        db.commit()
        return True