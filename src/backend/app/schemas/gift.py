from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import ConfigDict, Field, HttpUrl, field_validator
from app.schemas.base import PydanticBaseModel


class GiftCriteriaSchema(PydanticBaseModel):
    """Вхідна DTO-схема анкети критеріїв підбору подарунка (FR-1, FR-2)."""

    recipient_age: int = Field(..., ge=1, le=120, description="Вік одержувача від 1 до 120 років")
    recipient_relation: str = Field(..., min_length=1, max_length=100, description="Кому подарунок")
    occasion: str = Field(..., min_length=1, max_length=100, description="Святковий привід")
    interests: list[str] = Field(..., description="Список від 1 до 5 тегів інтересів (до 200 символів)")
    budget_uah: Decimal = Field(
        ..., gt=0, max_digits=10, decimal_places=2, description="Максимальний бюджет у грн (> 0)"
    )

    @field_validator("interests")
    @classmethod
    def check_interests_rules(cls, tags: list[str]) -> list[str]:
        """Перевіряє правила FR-2: 1..5 непорожніх тегів загальною довжиною до 200 символів."""
        cleaned = [tag.strip() for tag in tags if tag.strip()]
        if not (1 <= len(cleaned) <= 5):
            raise ValueError("Потрібно вказати від 1 до 5 тегів інтересів.")
        total_length = sum(len(tag) for tag in cleaned)
        if total_length > 200:
            raise ValueError("Загальна довжина тегів інтересів не повинна перевищувати 200 символів.")
        return cleaned

    def validate_criteria(self) -> bool:
        """Явна перевірка коректності критеріїв анкети (ЛР-2, Рисунок 3.2)."""
        total_length = sum(len(tag) for tag in self.interests)
        return (
            1 <= self.recipient_age <= 120
            and self.budget_uah > 0
            and 1 <= len(self.interests) <= 5
            and total_length <= 200
        )


class MarketplaceLinksSchema(PydanticBaseModel):
    """ValueObject із прямими пошуковими посиланнями на українські маркетплейси (FR-5)."""

    rozetka: HttpUrl
    prom_ua: HttpUrl
    hotline: HttpUrl


class GiftCardSchema(PydanticBaseModel):
    """Вихідна DTO-схема картки подарунка (FR-4), композиційно містить MarketplaceLinksSchema."""

    title: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    estimated_price_uah: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)
    reasoning: str = Field(..., min_length=1)
    links: MarketplaceLinksSchema


class SavedGiftResponseSchema(PydanticBaseModel):
    """Схема для серіалізації ORM-об'єкта SavedGift у JSON-відповідь WishlistRouter (FR-7)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    category: str
    estimated_price_uah: Decimal
    reasoning: str | None = None
    rozetka_url: str | None = None
    prom_url: str | None = None
    hotline_url: str | None = None
    created_at: datetime