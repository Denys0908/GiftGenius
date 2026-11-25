from abc import ABC, abstractmethod
from app.schemas.gift import GiftCriteriaSchema, MarketplaceLinksSchema


class GeminiAPIError(Exception):
    """Помилка взаємодії із зовнішнім сервісом Google Gemini API (NFR-3)."""
    pass


class ServiceUnavailableException(Exception):
    """Уніфіковане виключення для повернення HTTP 503 клієнту (ЛР-2, Рисунок 3.4)."""
    pass


class BaseAIClient(ABC):
    """
    Вузький інтерфейс для AI-клієнта (принципи SOLID: ISP, OCP, DIP).
    Дозволяє підставляти як GeminiAIClient, так і тестовий MockAIClient (LSP).
    """

    @abstractmethod
    def build_system_prompt(self, criteria: GiftCriteriaSchema) -> str:
        """Формує системний промпт на основі критеріїв анкети."""
        pass

    @abstractmethod
    def generate_raw_ideas(self, prompt: str) -> list[dict]:
        """Генерує від 3 до 5 сирих ідей подарунків у форматі списку словників."""
        pass


class BaseLinkGenerator(ABC):
    """
    Вузький інтерфейс для генератора пошукових посилань на маркетплейси (ISP, DIP).
    """

    @abstractmethod
    def url_encode_query(self, title: str) -> str:
        """Кодує назву товару для безпечної передачі в URL."""
        pass

    @abstractmethod
    def build_links(self, title: str) -> MarketplaceLinksSchema:
        """Повертає валідований об'єкт посилань на маркетплейси."""
        pass