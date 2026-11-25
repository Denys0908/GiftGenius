from app.routers.auth_router import get_current_user, router as auth_router
from app.routers.gift_router import router as gift_router
from app.routers.wishlist_router import router as wishlist_router

__all__ = ["auth_router", "gift_router", "wishlist_router", "get_current_user"]