# GiftGenius — Інтелектуальний веб-сервіс підбору подарунків

Клієнт-серверний веб-застосунок для персоналізованого підбору 3–5 ідей подарунків на основі віку одержувача, соціального статусу, приводу, інтересів та бюджету в гривнях. Серверна частина інтегрується з **Google Gemini API** (JSON Schema), відфільтровує ідеї, що перевищують бюджет, та формує прямі пошукові посилання на українські маркетплейси (**Rozetka**, **Prom.ua**, **Hotline**).

Проєкт виконується в межах дисципліни **«Життєвий цикл розробки програмного забезпечення»** (ФІОТ КПІ ім. Ігоря Сікорського, група ІК-44).

- **Репозиторій GitHub:** https://github.com/Denys0908/GiftGenius

---

## Стек технологій (згідно з CON-1, CON-2)

- **Frontend (SPA):** Node.js 22 LTS, React 18.3, Vite 5.4, Tailwind CSS 3.4, JavaScript (ES2022)
- **Backend (Модульний моноліт):** Python 3.12, FastAPI 0.115, Uvicorn 0.34, Pydantic 2.9
- **Штучний інтелект:** Google Gemini API (`google-genai` SDK v1.x, модель `gemini-3.1-flash-lite`, клієнтський таймаут `8.0 с` на спробу)
- **База даних та ORM:** SQLAlchemy 2.0, `psycopg2-binary` (підтримка PostgreSQL 16 / Neon.tech + локальний фолбек SQLite)
- **Безпека:** Passlib 1.7.4 + bcrypt 4.0.1, PyJWT 2.8 (HS256, TTL 60 хв), CORS, Rate Limiting (`10/minute` на підбір і автентифікацію), захист від IDOR, ізоляція секретів у `.env`
- **Тестування:** Pytest 8.4, FastAPI `TestClient` (httpx) - 15 модульних та інтеграційних тестів

---

## Структура проєкту

```text
GiftGenius/
├── docs/                           # Архітектурна та QA-документація проєкту
│   ├── architecture.md             # Опис архітектури, SOLID та уточнень відносно ЛР-2
│   └── test-cases.md               # Тест-кейси граничних значень QA (GG-9)
├── src/
│   ├── backend/                    # Серверна частина (FastAPI)
│   │   ├── app/
│   │   │   ├── models/             # ORM-моделі SQLAlchemy (SQLAlchemyBase, User, SavedGift)
│   │   │   ├── schemas/            # DTO-схеми Pydantic v2 (GiftCriteria, GiftCard, Auth, Token)
│   │   │   ├── services/           # Бізнес-логіка та SOLID-інтерфейси (AI, Links, Auth, Wishlist)
│   │   │   ├── routers/            # REST-контролери (gift_router, auth_router, wishlist_router)
│   │   │   ├── config.py           # Зчитування конфігурації із .env
│   │   │   ├── database.py         # Підключення до PostgreSQL / SQLite
│   │   │   └── main.py             # Точка входу FastAPI та створення таблиць БД
│   │   └── requirements.txt        # Зафіксовані версії залежностей Python
│   └── frontend/                   # Клієнтська частина (React SPA)
│       ├── src/
│       │   ├── components/         # GiftForm, GiftCardList, SkeletonLoader, AuthWishlistPanel
│       │   ├── services/           # apiAdapter.js (HTTP), historyManager.js (localStorage)
│       │   ├── App.jsx             # Головний екран і навігація
│       │   ├── index.css           # Директиви Tailwind CSS
│       │   └── main.jsx            # Точка входу React
│       ├── index.html
│       ├── package.json
│       ├── postcss.config.js
│       ├── tailwind.config.js
│       └── vite.config.js
├── tests/                          # Модульні та API-тести бекенду (GG-6, GG-11, GG-12)
│   └── test_giftgenius.py          # 15 тестів: FR-2, FR-4, FR-5, FR-6, NFR-3, NFR-4, IDOR, SOLID
├── .env.example                    # Шаблон змінних оточення (без секретів)
├── .gitignore                      # Виключення .env, venv, node_modules, БД і кешу
├── pytest.ini                      # Налаштування тестів Pytest
└── README.md                       # Документація проєкту
```

---

## Інструкція встановлення та локального запуску

### Передумови

- **Python 3.12** (`py -3.12 --version`)
- **Node.js 20–22 LTS** (`node --version`)
- Безкоштовний API-ключ Google AI Studio (`GEMINI_API_KEY`) для живої генерації рекомендацій (модульні тести `pytest` працюють автономно без ключа).

### 1. Клонування репозиторію та налаштування `.env`

```powershell
git clone https://github.com/Denys0908/GiftGenius.git
cd GiftGenius
Copy-Item .env.example .env
```

Відкрийте створений локальний файл `.env` (ігнорується Git), вкажіть свій ключ у рядку `GEMINI_API_KEY=...` та згенеруйте унікальний `JWT_SECRET` командою `python -c "import secrets; print(secrets.token_hex(32))"`. За замовчуванням для локального запуску увімкнено SQLite (`DATABASE_URL=sqlite:///./giftgenius_local.db`).

### 2. Запуск Backend (Термінал 1)

```powershell
py -3.12 -m venv src\backend\venv
.\src\backend\venv\Scripts\Activate.ps1
pip install -r src\backend\requirements.txt
uvicorn app.main:app --app-dir src\backend --reload
```

- Сервер API: `http://127.0.0.1:8000`
- Інтерактивна документація Swagger: `http://127.0.0.1:8000/docs`

### 3. Запуск Frontend (Термінал 2)

```powershell
cd src\frontend
npm install
npm run dev
```

- Клієнтський інтерфейс: `http://localhost:5173`

### 4. Запуск модульних і API-тестів

```powershell
.\src\backend\venv\Scripts\Activate.ps1
pytest -v
```

---

## Відхилення від специфікації ЛР-1, технічні примітки та статус Jira

1. **Модель Google Gemini (`gemini-3.1-flash-lite` замість `gemini-2.5-flash`):**
   - Для нових API-ключів Google AI Studio модель `models/gemini-2.5-flash` повертає `404 NOT_FOUND`.
   - Згідно з розділом 6 ЛР-1 назва моделі задається через змінну `GEMINI_MODEL_NAME` у `.env`; у проєкті уніфіковано швидку модель **`gemini-3.1-flash-lite`** (середній час живої відповіді `2.5–3.0 с`).
2. **Таймаут `8.0 с` (NFR-1) та фільтрація бюджету (FR-3 / FR-4):**
   - Обмеження `8.0 с` задається на рівні клієнтського `httpx` для кожної окремої HTTP-спроби (`google-genai` SDK за замовчуванням може виконувати автоматичні повторні спроби при тимчасових мережевих збоях).
   - `GeminiAIClient` строго вимагає 3–5 ідей від моделі (FR-3), однак подальший бюджетний фільтр (FR-4) має пріоритет і відкидає позиції дорожчі за `budget_uah`, тому в окремих випадках підсумковий список може містити менше 3 карток.
3. **Візуалізація карток подарунків:**
   - Картки у `GiftCardList.jsx` оформлено тематичними градієнтними обкладинками та іконками за категоріями (працюють миттєво без сторонніх API). Інтеграція реальних фотографій товарів (Unsplash/Pexels API) винесена в окрему задачу беклогу, щоб не перевищувати норматив NFR-1 і не ускладнювати схему БД у межах ЛР-4.
4. **Актуальний статус задач Jira:**
   - **`GG-10` (PostgreSQL 16 на Neon.tech)** - _In Progress_: реалізовано ORM-моделі `User`/`SavedGift`, драйвер `psycopg2-binary` та конфігурацію `DATABASE_URL`, однак локальна перевірка проводилася на SQLite; хмарний інстанс Neon.tech ще не розгорнуто.
   - **`GG-16`** - _To Do_ (наступний етап деплою).

---

## Команда проєкту та розподіл ролей

| Учасник команди                       | Роль у проєкті                                        | Зона відповідальності та внесок (ЛР-4 / Jira)                                                                                                                                                                                                                                                                                                                                                                               |
| :------------------------------------ | :---------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Сардаковський Денис Олександрович** | Backend-розробник / AI Engineer / Database Architect  | Базова структура репозиторію, серверний моноліт FastAPI, конфігурація `.env`, ORM-моделі `User` і `SavedGift`, DTO-схеми Pydantic v2, `GeminiAIClient`, `MarketplaceLinkGenerator`, `GiftRecommendationService`, `AuthService`, `WishlistService`, REST-роутери з Rate Limiting, модульні й API-тести `pytest` та Code Review фронтенду (`GG-2, GG-4, GG-5, GG-6, GG-10, GG-11, GG-12`).                                    |
| **Пономаренко Анжеліка Олегівна**     | Frontend-розробниця / UI/UX-дизайнерка / QA-інженерка | Ініціалізація React 18 + Vite 5 + Tailwind CSS 3.4, адаптивна верстка (`360–2560 px`), анкета `GiftForm` із клієнтською валідацією, `SkeletonLoader`, картки `GiftCardList` із тематичними обкладинками, кабінет `AuthWishlistPanel`, `RestApiHttpAdapter`, `LocalStorageHistoryManager`, тест-кейси граничних значень (`docs/test-cases.md`) та Code Review бекенду (`GG-1, GG-3, GG-7, GG-8, GG-9, GG-13, GG-14, GG-15`). |
