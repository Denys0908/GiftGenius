from decimal import Decimal
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.routers.auth_router import auth_rate_limiter
from app.database import get_db
from app.main import app
from app.models import SQLAlchemyBase
from app.routers.gift_router import get_recommendation_service, rate_limiter
from app.schemas import GiftCriteriaSchema
from app.services import (
    AuthService,
    BaseAIClient,
    GeminiAPIError,
    GiftRecommendationService,
    MarketplaceLinkGenerator,
    ServiceUnavailableException,
)


# === Тестові заглушки AI-клієнта (демонстрація SOLID: LSP та DIP) ===

class MockAIClient(BaseAIClient):
    """Повертає 3 ідеї в межах бюджету та 1 ідею дорожчу за бюджет (FR-3, FR-4)."""

    def build_system_prompt(self, criteria: GiftCriteriaSchema) -> str:
        return f"Промпт для {criteria.recipient_relation}, бюджет {criteria.budget_uah}"

    def generate_raw_ideas(self, prompt: str) -> list[dict]:
        return [
            {
                "title": "Набір маркерів для скетчингу",
                "category": "Творчість",
                "estimated_price_uah": 1200.0,
                "reasoning": "Підходить для хобі малювання.",
            },
            {
                "title": "Скетчбук А5 із щільним папером",
                "category": "Творчість",
                "estimated_price_uah": 450.0,
                "reasoning": "Зручно брати із собою на пленери.",
            },
            {
                "title": "Настільна гра для компанії",
                "category": "Ігри",
                "estimated_price_uah": 950.0,
                "reasoning": "Додасть веселощів у колі друзів.",
            },
            {
                "title": "Професійний графічний монітор",
                "category": "Електроніка",
                "estimated_price_uah": 9500.0,
                "reasoning": "Перевищує бюджет — має бути відкинутий сервісом.",
            },
        ]


class OverBudgetOnlyAIClient(BaseAIClient):
    """Імітує ситуацію, коли всі згенеровані ідеї перевищують бюджет (FR-4)."""

    def build_system_prompt(self, criteria: GiftCriteriaSchema) -> str:
        return "prompt"

    def generate_raw_ideas(self, prompt: str) -> list[dict]:
        return [
            {
                "title": "Ноутбук ігровий",
                "category": "Електроніка",
                "estimated_price_uah": 45000.0,
                "reasoning": "Занадто дорого для заданого бюджету.",
            }
        ]


class FailingAIClient(BaseAIClient):
    """Імітує збій зовнішнього сервісу Gemini API для перевірки NFR-3 (HTTP 503)."""

    def build_system_prompt(self, criteria: GiftCriteriaSchema) -> str:
        return "prompt"

    def generate_raw_ideas(self, prompt: str) -> list[dict]:
        raise GeminiAPIError("Simulated API outage")


# === Фікстура ізольованого TestClient із чистою тимчасовою БД ===

@pytest.fixture()
def test_client(tmp_path):
    """
    Ізольоване тестове середовище для кожного API-тесту:
    1) tmp_path — вбудована тимчасова папка pytest; створюємо там окрему БД,
       щоб тести не змінювали робочий файл giftgenius_local.db.
    2) app.dependency_overrides[get_db] — підміняє підключення до робочої БД
       на тестову сесію на час виконання тесту.
    3) _requests.clear() — обнуляє лічильники Rate Limiter між тестами.
    """
    db_file = tmp_path / "test_giftgenius.db"
    test_engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    SQLAlchemyBase.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Підключаємо тестову БД замість основної та очищуємо ліміти запитів
    app.dependency_overrides[get_db] = override_get_db
    rate_limiter._requests.clear()
    auth_rate_limiter._requests.clear()

    with TestClient(app) as client:
        yield client

    # Повертаємо стандартні залежності FastAPI та закриваємо з'єднання після тесту
    app.dependency_overrides.clear()
    rate_limiter._requests.clear()
    auth_rate_limiter._requests.clear()
    test_engine.dispose()

# === 1. Тести валідації критеріїв Pydantic (FR-2) ===

def test_gift_criteria_valid():
    criteria = GiftCriteriaSchema(
        recipient_age=21,
        recipient_relation="Подрузі",
        occasion="День народження",
        interests=["кава", "подорожі"],
        budget_uah=Decimal("2500.00"),
    )
    assert criteria.validate_criteria() is True


def test_gift_criteria_rejects_invalid_data():
    with pytest.raises(ValidationError):
        GiftCriteriaSchema(
            recipient_age=150,
            recipient_relation="Другу",
            occasion="Свято",
            interests=["ігри"],
            budget_uah=Decimal("1000.00"),
        )

    with pytest.raises(ValidationError):
        GiftCriteriaSchema(
            recipient_age=25,
            recipient_relation="Другу",
            occasion="Свято",
            interests=["ігри"],
            budget_uah=Decimal("0"),
        )

    with pytest.raises(ValidationError):
        GiftCriteriaSchema(
            recipient_age=25,
            recipient_relation="Другу",
            occasion="Свято",
            interests=["1", "2", "3", "4", "5", "6"],
            budget_uah=Decimal("1000.00"),
        )


# === 2. Тест генератора посилань на українські маркетплейси (FR-5, CON-4) ===

def test_marketplace_link_generator():
    generator = MarketplaceLinkGenerator()
    links = generator.build_links("Настільна гра Catan")

    assert str(links.rozetka).startswith("https://rozetka.com.ua/ua/search/?text=")
    assert str(links.prom_ua).startswith("https://prom.ua/ua/search?search_term=")
    assert str(links.hotline).startswith("https://hotline.ua/ua/sr/?q=")


# === 3. Тести оркестратора: DIP/LSP, фільтр бюджету та збої ШІ (FR-4, NFR-3) ===

def test_recommendation_service_filters_over_budget_ideas():
    service = GiftRecommendationService(
        ai_client=MockAIClient(),
        link_generator=MarketplaceLinkGenerator(),
    )
    criteria = GiftCriteriaSchema(
        recipient_age=20,
        recipient_relation="Подрузі",
        occasion="День народження",
        interests=["малювання"],
        budget_uah=Decimal("1500.00"),
    )

    cards = service.generate_recommendations(criteria)

    assert len(cards) == 3
    assert all(card.estimated_price_uah <= criteria.budget_uah for card in cards)
    assert all("монітор" not in card.title.lower() for card in cards)


def test_recommendation_service_fails_when_all_ideas_over_budget():
    service = GiftRecommendationService(
        ai_client=OverBudgetOnlyAIClient(),
        link_generator=MarketplaceLinkGenerator(),
    )
    criteria = GiftCriteriaSchema(
        recipient_age=20,
        recipient_relation="Другу",
        occasion="Свято",
        interests=["техніка"],
        budget_uah=Decimal("1000.00"),
    )

    with pytest.raises(ServiceUnavailableException):
        service.generate_recommendations(criteria)


def test_recommendation_service_raises_503_on_ai_error():
    service = GiftRecommendationService(
        ai_client=FailingAIClient(),
        link_generator=MarketplaceLinkGenerator(),
    )
    criteria = GiftCriteriaSchema(
        recipient_age=20,
        recipient_relation="Другу",
        occasion="Свято",
        interests=["музика"],
        budget_uah=Decimal("1000.00"),
    )

    with pytest.raises(ServiceUnavailableException):
        service.generate_recommendations(criteria)


# === 4. Тест безпеки AuthService: bcrypt та JWT (FR-6, NFR-4) ===

def test_auth_password_hashing_and_jwt():
    auth = AuthService(jwt_secret="unit_test_secret_key_for_giftgenius_32b")
    hashed = auth.hash_password("strongPass123")

    assert hashed != "strongPass123"
    assert auth.verify_password("strongPass123", hashed) is True
    assert auth.verify_password("wrongPass", hashed) is False

    user_id = uuid4()
    token_dto = auth.create_jwt_token(user_id)
    assert token_dto.token_type == "bearer"
    assert auth.decode_jwt_token(token_dto.access_token) == user_id


# === 5. Інтеграційні тести помилок роботи API (422, 503, 429) ===

def test_api_health_and_validation_422(test_client):
    health = test_client.get("/")
    assert health.status_code == 200
    assert health.json()["service"] == "GiftGenius API"

    bad_response = test_client.post(
        "/api/v1/recommendations",
        json={
            "recipient_age": 0,
            "recipient_relation": "Другу",
            "occasion": "Свято",
            "interests": [],
            "budget_uah": -100,
        },
    )
    assert bad_response.status_code == 422


def test_api_recommendations_returns_503_on_ai_outage(test_client):
    app.dependency_overrides[get_recommendation_service] = lambda: GiftRecommendationService(
        ai_client=FailingAIClient(),
        link_generator=MarketplaceLinkGenerator(),
    )

    response = test_client.post(
        "/api/v1/recommendations",
        json={
            "recipient_age": 22,
            "recipient_relation": "Другу",
            "occasion": "День народження",
            "interests": ["музика"],
            "budget_uah": 1500,
        },
    )
    assert response.status_code == 503
    assert "тимчасово недоступний" in response.json()["detail"].lower()


def test_api_recommendations_rate_limit_429(test_client):
    app.dependency_overrides[get_recommendation_service] = lambda: GiftRecommendationService(
        ai_client=MockAIClient(),
        link_generator=MarketplaceLinkGenerator(),
    )
    payload = {
        "recipient_age": 22,
        "recipient_relation": "Подрузі",
        "occasion": "День народження",
        "interests": ["малювання"],
        "budget_uah": 1500,
    }

    # Перші 10 запитів за хвилину мають пройти (200 OK), 11-й — заблокуватися (429)
    for _ in range(10):
        res = test_client.post("/api/v1/recommendations", json=payload)
        assert res.status_code == 200

    blocked = test_client.post("/api/v1/recommendations", json=payload)
    assert blocked.status_code == 429


# === 6. Інтеграційні тести помилок автентифікації та безпеки (401, 409, IDOR) ===

def test_auth_register_duplicate_email_returns_409(test_client):
    creds = {"email": "denys@kpi.ua", "password": "SecurePassword123"}
    first = test_client.post("/api/v1/auth/register", json=creds)
    assert first.status_code == 201

    duplicate = test_client.post("/api/v1/auth/register", json=creds)
    assert duplicate.status_code == 409


def test_auth_login_wrong_password_returns_401(test_client):
    test_client.post(
        "/api/v1/auth/register",
        json={"email": "student@kpi.ua", "password": "RightPassword123"},
    )

    wrong_pass = test_client.post(
        "/api/v1/auth/login",
        json={"email": "student@kpi.ua", "password": "WrongPassword999"},
    )
    assert wrong_pass.status_code == 401

    unknown_user = test_client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@kpi.ua", "password": "RightPassword123"},
    )
    assert unknown_user.status_code == 401


def test_wishlist_rejects_missing_and_forged_jwt(test_client):
    no_token = test_client.get("/api/v1/wishlist")
    assert no_token.status_code in (401, 403)

    forged_token = test_client.get(
        "/api/v1/wishlist",
        headers={"Authorization": "Bearer fake.forged.jwt_token"},
    )
    assert forged_token.status_code == 401


def test_wishlist_idor_protection_prevents_deleting_other_users_gift(test_client):
    # Реєструємо двох різних користувачів
    user_a = test_client.post(
        "/api/v1/auth/register",
        json={"email": "alice@kpi.ua", "password": "PasswordAlice123"},
    ).json()["access_token"]
    user_b = test_client.post(
        "/api/v1/auth/register",
        json={"email": "bob@kpi.ua", "password": "PasswordBob123"},
    ).json()["access_token"]

    # Користувач A зберігає подарунок
    gift_card = {
        "title": "Настільна гра Catan",
        "category": "Ігри",
        "estimated_price_uah": 1150.0,
        "reasoning": "Класична гра для компанії.",
        "links": {
            "rozetka": "https://rozetka.com.ua/ua/search/?text=Catan",
            "prom_ua": "https://prom.ua/ua/search?search_term=Catan",
            "hotline": "https://hotline.ua/ua/sr/?q=Catan",
        },
    }
    saved = test_client.post(
        "/api/v1/wishlist",
        json=gift_card,
        headers={"Authorization": f"Bearer {user_a}"},
    )
    assert saved.status_code == 201
    gift_id = saved.json()["id"]

    # Користувач B намагається видалити подарунок користувача A (IDOR-атака)
    attack = test_client.delete(
        f"/api/v1/wishlist/{gift_id}",
        headers={"Authorization": f"Bearer {user_b}"},
    )
    assert attack.status_code in (403, 404)

    # Переконуємося, що подарунок користувача A залишився неушкодженим
    owner_list = test_client.get(
        "/api/v1/wishlist",
        headers={"Authorization": f"Bearer {user_a}"},
    )
    assert owner_list.status_code == 200
    assert len(owner_list.json()) == 1





def test_auth_login_rate_limit_429(test_client):
    """Перевіряє блокування перебору паролів (brute-force) після 10 спроб за хвилину."""
    bad_creds = {"email": "victim@kpi.ua", "password": "WrongPassword123"}

    for _ in range(10):
        res = test_client.post("/api/v1/auth/login", json=bad_creds)
        assert res.status_code == 401

    blocked = test_client.post("/api/v1/auth/login", json=bad_creds)
    assert blocked.status_code == 429