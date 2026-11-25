from pydantic import EmailStr, Field, SecretStr
from app.schemas.base import PydanticBaseModel


class UserAuthSchema(PydanticBaseModel):
    """Вхідна DTO-схема для реєстрації та входу користувача (FR-6, NFR-4)."""

    email: EmailStr
    password: SecretStr = Field(..., min_length=8, description="Пароль мінімум 8 символів")


class TokenResponseSchema(PydanticBaseModel):
    """Вихідна DTO-схема з JWT-токеном авторизації (FR-6)."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600