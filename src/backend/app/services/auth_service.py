from datetime import datetime, timedelta, timezone
from uuid import UUID
import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.schemas.auth import TokenResponseSchema, UserAuthSchema


class AuthService:
    """
    Сервіс автентифікації користувачів: хешування bcrypt та JWT-токени (FR-6, NFR-4, GG-11).
    Принцип SRP: відповідає лише за безпеку паролів, JWT і реєстрацію/вхід.
    """

    def __init__(
        self,
        jwt_secret: str | None = None,
        jwt_algorithm: str | None = None,
        token_expire_minutes: int | None = None,
    ):
        self.jwt_secret: str = jwt_secret or settings.JWT_SECRET
        self.jwt_algorithm: str = jwt_algorithm or settings.JWT_ALGORITHM
        self.token_expire_minutes: int = token_expire_minutes or settings.JWT_EXPIRE_MINUTES
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, plain: str) -> str:
        """Хешує пароль алгоритмом bcrypt (Passlib, NFR-4)."""
        return self._pwd_context.hash(plain)

    def verify_password(self, plain: str, hashed: str) -> bool:
        """Перевіряє відповідність пароля його bcrypt-хешу."""
        return self._pwd_context.verify(plain, hashed)

    def create_jwt_token(self, user_id: UUID) -> TokenResponseSchema:
        """Генерує підписаний JWT-токен алгоритмом HS256 (FR-6)."""
        now = datetime.now(timezone.utc)
        expires_seconds = self.token_expire_minutes * 60
        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(seconds=expires_seconds),
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return TokenResponseSchema(
            access_token=token,
            token_type="bearer",
            expires_in=expires_seconds,
        )

    def decode_jwt_token(self, token: str) -> UUID:
        """Перевіряє підпис і термін дії JWT та повертає UUID користувача."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise ValueError("У токені відсутній ідентифікатор користувача.")
            return UUID(user_id_str)
        except (jwt.PyJWTError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недійсний або прострочений токен авторизації.",
            ) from exc

    def register_user(self, db: Session, dto: UserAuthSchema) -> TokenResponseSchema:
        """Реєструє нового користувача в таблиці users та повертає JWT (UC-4)."""
        normalized_email = dto.email.lower()
        existing = db.query(User).filter(User.email == normalized_email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Користувач із такою електронною поштою вже існує.",
            )

        new_user = User(
            email=normalized_email,
            password_hash=self.hash_password(dto.password.get_secret_value()),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return self.create_jwt_token(new_user.id)

    def authenticate_user(self, db: Session, dto: UserAuthSchema) -> TokenResponseSchema:
        """Перевіряє email і пароль користувача та видає JWT (UC-4)."""
        normalized_email = dto.email.lower()
        user = db.query(User).filter(User.email == normalized_email).first()
        if not user or not self.verify_password(dto.password.get_secret_value(), user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невірна електронна пошта або пароль.",
            )

        return self.create_jwt_token(user.id)