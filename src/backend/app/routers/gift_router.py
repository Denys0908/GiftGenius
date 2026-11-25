import time
from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas import GiftCardSchema, GiftCriteriaSchema
from app.services import (
    GeminiAIClient,
    GiftRecommendationService,
    MarketplaceLinkGenerator,
    ServiceUnavailableException,
)

RATE_LIMIT = "10/minute"
router = APIRouter(prefix="/api/v1", tags=["Recommendations"])


class SimpleRateLimiter:
    """Обмежувач частоти запитів у пам'яті: не більше 10 запитів за 60 с з одного IP (NFR-4)."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    def check(self, client_ip: str) -> None:
        now = time.monotonic()
        # Залишаємо лише мітки часу за останні 60 секунд
        recent = [t for t in self._requests.get(client_ip, []) if now - t < self.window_seconds]
        if len(recent) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Перевищено ліміт запитів ({RATE_LIMIT}). Спробуйте за хвилину.",
            )
        recent.append(now)
        self._requests[client_ip] = recent


rate_limiter = SimpleRateLimiter(max_requests=10, window_seconds=60)


def get_recommendation_service() -> GiftRecommendationService:
    """Фабрика залежностей (DIP): передає конкретні реалізації у конструктор оркестратора."""
    return GiftRecommendationService(
        ai_client=GeminiAIClient(),
        link_generator=MarketplaceLinkGenerator(),
    )


@router.post("/recommendations", response_model=list[GiftCardSchema], status_code=200)
def post_recommendations(
    criteria: GiftCriteriaSchema,
    request: Request,
    service: GiftRecommendationService = Depends(get_recommendation_service),
):
    """Публічний маршрут генерації 3–5 рекомендацій подарунків (FR-3, FR-4, FR-5, NFR-3, NFR-4)."""
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter.check(client_ip)

    try:
        return service.generate_recommendations(criteria)
    except ServiceUnavailableException as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc