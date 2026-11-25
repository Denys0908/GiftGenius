from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.routers.auth_router import get_current_user
from app.schemas import GiftCardSchema, SavedGiftResponseSchema
from app.services import WishlistService

router = APIRouter(prefix="/api/v1/wishlist", tags=["Wishlist"])
wishlist_service = WishlistService()


@router.get("", response_model=list[SavedGiftResponseSchema], status_code=200)
def get_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Повертає список збережених подарунків поточного користувача (FR-7, UC-2)."""
    return wishlist_service.get_user_wishlist(db, current_user.id)


@router.post("", response_model=SavedGiftResponseSchema, status_code=201)
def post_wishlist_item(
    card: GiftCardSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Зберігає картку подарунка у список «Збережене» поточного користувача (FR-7, UC-2)."""
    return wishlist_service.save_to_wishlist(db, current_user.id, card)


@router.delete("/{gift_id}", status_code=204)
def delete_wishlist_item(
    gift_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Видаляє подарунок зі списку «Збережене», повертаючи 404 для чужих або відсутніх ID."""
    deleted = wishlist_service.delete_from_wishlist(db, current_user.id, gift_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Подарунок не знайдено у вашому списку «Збережене».",
        )
    return Response(status_code=204)