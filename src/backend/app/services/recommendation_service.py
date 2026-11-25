from decimal import Decimal
from app.schemas.gift import GiftCardSchema, GiftCriteriaSchema
from app.services.interfaces import (
    BaseAIClient,
    BaseLinkGenerator,
    GeminiAPIError,
    ServiceUnavailableException,
)


class GiftRecommendationService:
    """
    Оркестратор підбору подарунків (FR-3, FR-4, FR-5, GG-6).
    Принципи SOLID:
    - SRP: координує AI-клієнт і генератор посилань.
    - DIP: залежить від абстракцій BaseAIClient і BaseLinkGenerator (передаються в __init__).
    """

    def __init__(self, ai_client: BaseAIClient, link_generator: BaseLinkGenerator):
        self.ai_client = ai_client
        self.link_generator = link_generator

    def generate_recommendations(self, criteria: GiftCriteriaSchema) -> list[GiftCardSchema]:
        """Повний цикл підбору: промпт -> ідеї від ШІ -> фільтр бюджету -> посилання -> картки."""
        prompt = self.ai_client.build_system_prompt(criteria)

        try:
            raw_ideas = self.ai_client.generate_raw_ideas(prompt)
        except (TimeoutError, GeminiAPIError) as exc:
            raise ServiceUnavailableException(
                "Сервіс ШІ тимчасово недоступний. Спробуйте пізніше."
            ) from exc

        cards: list[GiftCardSchema] = []
        for item in raw_ideas:
            price = Decimal(str(item["estimated_price_uah"])).quantize(Decimal("0.01"))

            # FR-4: відкидаємо ідеї, які виходять за межі заданого бюджету
            if price <= 0 or price > criteria.budget_uah:
                continue

            title = str(item["title"]).strip()
            links = self.link_generator.build_links(title)

            cards.append(
                GiftCardSchema(
                    title=title,
                    category=str(item["category"]).strip(),
                    estimated_price_uah=price,
                    reasoning=str(item["reasoning"]).strip(),
                    links=links,
                )
            )

        if not cards:
            raise ServiceUnavailableException(
                "Не вдалося підібрати подарунки в межах вказаного бюджету. Спробуйте ще раз."
            )

        return cards