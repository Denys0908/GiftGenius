from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.routers.gift_router import SimpleRateLimiter
from app.schemas import TokenResponseSchema, UserAuthSchema
from app.services import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
auth_service = AuthService()
bearer_scheme = HTTPBearer()

# Захист від перебору паролів (brute-force) та спаму реєстрацій (NFR-4)
auth_rate_limiter = SimpleRateLimiter(max_requests=10, window_seconds=60)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Перевіряє JWT із заголовка Authorization і повертає поточного користувача з БД."""
    user_id = auth_service.decode_jwt_token(credentials.credentials)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Користувача не знайдено.")
    return user


@router.post("/register", response_model=TokenResponseSchema, status_code=201)
def post_register(
    dto: UserAuthSchema,
    request: Request,
    db: Session = Depends(get_db),
):
    """Реєстрація нового користувача з видачею JWT (FR-6, UC-4)."""
    client_ip = request.client.host if request.client else "unknown"
    auth_rate_limiter.check(client_ip)
    return auth_service.register_user(db, dto)


@router.post("/login", response_model=TokenResponseSchema, status_code=200)
def post_login(
    dto: UserAuthSchema,
    request: Request,
    db: Session = Depends(get_db),
):
    """Автентифікація користувача за email та паролем (FR-6, UC-4)."""
    client_ip = request.client.host if request.client else "unknown"
    auth_rate_limiter.check(client_ip)
    return auth_service.authenticate_user(db, dto)