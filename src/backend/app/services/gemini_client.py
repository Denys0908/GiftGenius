import json
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import settings
from app.schemas.gift import GiftCriteriaSchema
from app.services.interfaces import BaseAIClient, GeminiAPIError


class _RawGiftIdea(BaseModel):
    """JSON Schema для строгої типізації відповіді Google Gemini API (FR-3)."""
    title: str
    category: str
    estimated_price_uah: float
    reasoning: str


class GeminiAIClient(BaseAIClient):
    """
    Клієнт інтеграції з Google Gemini API через google-genai SDK (FR-3, CON-3, GG-4).
    Принцип SRP: відповідає лише за формування промпту та запит до LLM.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        timeout_sec: float = 8.0,
    ):
        self.api_key: str = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model_name: str = model_name or settings.GEMINI_MODEL_NAME or "gemini-3.1-flash-lite"
        self.timeout_sec: float = timeout_sec

    def build_system_prompt(self, criteria: GiftCriteriaSchema) -> str:
        """Формує структурований українськомовний промпт за критеріями анкети (FR-3, CON-4)."""
        interests_text = ", ".join(criteria.interests)
        return (
            "Ти — асистент підбору подарунків GiftGenius для ринку України.\n"
            "Запропонуй від 3 до 5 конкретних ідей подарунків українською мовою.\n"
            f"- Вік одержувача: {criteria.recipient_age} років\n"
            f"- Кому подарунок: {criteria.recipient_relation}\n"
            f"- Привід: {criteria.occasion}\n"
            f"- Інтереси: {interests_text}\n"
            f"- Максимальний бюджет: {criteria.budget_uah} грн (UAH)\n\n"
            "Правила: ціна кожного подарунка не повинна перевищувати бюджет; "
            "назва (title) має бути зручною для пошуку на Rozetka, Prom.ua та Hotline."
        )

    def generate_raw_ideas(self, prompt: str) -> list[dict]:
        """Викликає Google Gemini API з таймаутом 8.0 с та повертає 3–5 ідей (FR-3, NFR-1)."""
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise GeminiAPIError("Не задано GEMINI_API_KEY у файлі .env.")

        try:
            # Передаємо клієнтський HTTP-таймаут (8.0 с) напряму в httpx через client_args
            client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(client_args={"timeout": self.timeout_sec}),
            )
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[_RawGiftIdea],
                    temperature=0.7,
                ),
            )
            data = json.loads(response.text or "[]")
        except Exception as exc:
            raise GeminiAPIError(f"Помилка зовнішнього сервісу Gemini API: {exc}") from exc

        # Сувора перевірка вимоги FR-3: від 3 до 5 рекомендацій
        if not isinstance(data, list) or not (3 <= len(data) <= 5):
            raise GeminiAPIError("Модель повернула некоректну кількість ідей (очікується від 3 до 5).")

        return data