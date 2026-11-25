# Архітектура та відповідність принципам SOLID — GiftGenius

Документ описує реалізацію базової структури коду (ЛР-4) у відповідності до специфікації вимог (ЛР-1), UML-діаграм (ЛР-2) та задач беклогу Jira (ЛР-3).

## 1. Трирівнева клієнт-серверна архітектура (Модульний моноліт)

1. **Клієнтський рівень (`src/frontend` - React 18.3, Vite 5.4, Tailwind CSS 3.4):**
   - `components/GiftForm.jsx` - інтерактивна анкета критеріїв та клієнтська валідація (FR-1, FR-2, GG-3).
   - `components/SkeletonLoader.jsx` - неблокуюча анімація завантаження (NFR-2, GG-8).
   - `components/GiftCardList.jsx` - універсальний компонент карток із тематичними градієнтними обкладинками за категоріями, кнопками Rozetka/Prom.ua/Hotline та копіюванням у буфер обміну (FR-4, FR-5, FR-8, GG-8).
   - `components/AuthWishlistPanel.jsx` - вхід, реєстрація, перегляд «Збереженого» та «Історії запитів» (FR-6, FR-7, FR-8, GG-13, GG-15).
   - `services/apiAdapter.js` - клієнт `RestApiHttpAdapter` для REST API з обробкою JWT та кодів 401, 404, 409, 422, 429, 503 (NFR-3, GG-7).
   - `services/historyManager.js` - `LocalStorageHistoryManager` для збереження 5 останніх запитів у браузері (FR-8, GG-14).

2. **Серверний рівень (`src/backend/app` - Python 3.12, FastAPI 0.115, Pydantic 2.9):**
   - `models/` - ORM-моделі `SQLAlchemyBase`, `User` (`users`), `SavedGift` (`saved_gifts`) із каскадним видаленням `cascade="all, delete-orphan"` та `ON DELETE CASCADE` (GG-10).
   - `schemas/` - DTO-схеми `PydanticBaseModel`, `GiftCriteriaSchema`, `MarketplaceLinksSchema`, `GiftCardSchema`, `SavedGiftResponseSchema`, `UserAuthSchema`, `TokenResponseSchema` (GG-2).
   - `services/` - ізольовані сервіси бізнес-логіки: `GeminiAIClient`, `MarketplaceLinkGenerator`, `GiftRecommendationService`, `AuthService`, `WishlistService` (`delete_from_wishlist(...) -> bool`) та абстракції `BaseAIClient`, `BaseLinkGenerator` (GG-4, GG-5, GG-6, GG-11, GG-12).
   - `routers/`- функціональні REST-контролери FastAPI (`gift_router.py`, `auth_router.py`, `wishlist_router.py`) із залежністю `Depends(get_current_user)` та обмеженням частоти `10/minute` на підбір і автентифікацію (NFR-4).

3. **Рівень збереження даних та сторонні сервіси:**
   - **SQLAlchemy 2.0 + PostgreSQL 16 / SQLite** - підтримка хмарної PostgreSQL (Neon.tech, драйвер `psycopg2-binary`) та локального SQLite-фолбеку через змінну `DATABASE_URL` у `.env`.
   - **Google Gemini API** (`google-genai` SDK v1.x, модель `gemini-3.1-flash-lite`, клієнтський таймаут `8.0 с` на спробу, строгий JSON Schema на 3–5 ідей).
   - **Browser LocalStorage** - клієнтське кешування останніх 5 запитів.

---

## 2. Реалізація принципів SOLID у коді

| Принцип SOLID                 | Реалізація в проєкті GiftGenius                                                                                                                                                                                                                                                                                                                           |
| :---------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **S — Single Responsibility** | Кожен модуль виконує одну чітку задачу: `GeminiAIClient` працює лише з LLM, `MarketplaceLinkGenerator` формує URL-посилання, `GiftRecommendationService` оркеструє підбір і фільтрує бюджет, `AuthService` керує bcrypt та JWT, `WishlistService` виконує чистий CRUD без HTTP-залежностей, а роутери відповідають лише за HTTP-рівень і коди відповідей. |
| **O — Open/Closed**           | Додавання нового AI-провайдера або іншого генератора посилань виконується створенням підкласу від `BaseAIClient` / `BaseLinkGenerator` без змін у `GiftRecommendationService`.                                                                                                                                                                            |
| **L — Liskov Substitution**   | Моделі `User` і `SavedGift` взаємозамінно наслідують `SQLAlchemyBase`. Будь-яка реалізація `BaseAIClient` (`GeminiAIClient`, тестові `MockAIClient`, `OverBudgetOnlyAIClient`, `FailingAIClient`) працює всередині `GiftRecommendationService`.                                                                                                           |
| **I — Interface Segregation** | Контракти розділено на вузькі абстрактні класи (`BaseAIClient`, `BaseLinkGenerator` у `services/interfaces.py`) і спеціалізовані DTO-схеми під конкретні запити й відповіді.                                                                                                                                                                              |
| **D — Dependency Inversion**  | `GiftRecommendationService` залежить від абстракцій `BaseAIClient` і `BaseLinkGenerator`, а конкретні реалізації передаються через конструктор `__init__` у фабриці `get_recommendation_service()` (`gift_router.py`).                                                                                                                                    |

---

## 3. Уточнення реалізації відносно діаграм ЛР-2

У процесі реалізації базової структури коду (ЛР-4) введено кілька допоміжних класів і застосовано ідіоматичний стиль FastAPI, що деталізують діаграму класів (ЛР-2, Рисунок 3.3):

| Елемент коду                                                                     | Призначення та обґрунтування відносно ЛР-2                                                                                                                                                                                                                                                                                      |
| :------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `BaseAIClient`, `BaseLinkGenerator` (`services/interfaces.py`)                   | Абстрактні базові класи (ABC) для виконання принципів **DIP** та **ISP** (вимога методички ЛР-4). На діаграмі класів ЛР-2 показана агрегація конкретних реалізацій `GeminiAIClient` і `MarketplaceLinkGenerator`, які тепер реалізують ці контракти.                                                                            |
| `SavedGiftResponseSchema` (`schemas/gift.py`)                                    | Окрема DTO-схема для серіалізації збережених записів із БД (містить поля `id`, `user_id`, `created_at`, `rozetka_url`, `prom_url`, `hotline_url`), щоб не змішувати її з `GiftCardSchema` для свіжої AI-видачі.                                                                                                                 |
| `SimpleRateLimiter` (`routers/gift_router.py`, `routers/auth_router.py`)         | Обмежувач частоти запитів у пам'яті (`10/minute` на IP) для маршрутів `/recommendations`, `/auth/register` і `/auth/login` (NFR-4) без зовнішнього брокера Redis.                                                                                                                                                               |
| `_RawGiftIdea` (`services/gemini_client.py`)                                     | Внутрішня Pydantic-модель для параметра `response_schema` у `google-genai`, яка забезпечує валідний JSON від ШІ (FR-3).                                                                                                                                                                                                         |
| `_DeclarativeRoot` (`models/base.py`)                                            | Технічний базовий клас `DeclarativeBase` із SQLAlchemy 2.0, над яким побудовано абстрактну модель `SQLAlchemyBase` (`__abstract__ = True`) із діаграми ЛР-2.                                                                                                                                                                    |
| Функціональні роутери (`gift_router.py`, `auth_router.py`, `wishlist_router.py`) | Замість класів-контролерів із діаграми ЛР-2 використано стандартні для FastAPI модулі з `APIRouter`, декораторами та залежністю `Depends(get_current_user)` зі збереженням усіх імен маршрутів і функцій (`post_recommendations`, `post_register`, `post_login`, `get_wishlist`, `post_wishlist_item`, `delete_wishlist_item`). |

---

## 4. Безпека та обмеження навчального прототипу (NFR-4)

- **Реалізований захист:** хешування паролів `bcrypt` (`Passlib 1.7.4`), підписані токени `JWT (HS256, TTL 60 хв)`, параметризовані запити SQLAlchemy ORM, ізоляція секретів у `.env`, захист від IDOR (повернення `404` при спробі видалення чужого запису) та захист від brute-force (`10/minute` на `/auth/login` і `/auth/register`).
- **Обмеження локального прототипу:** під час локальної розробки використовується HTTP (без TLS) та збереження JWT у `localStorage` браузера (React базово екранує XSS). Для продакшен-розгортання передбачено перехід на HTTPS та зберігання токенів у `HttpOnly; Secure; SameSite=Lax` cookies.
