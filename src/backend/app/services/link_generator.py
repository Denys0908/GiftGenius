from urllib.parse import quote_plus
from app.schemas.gift import MarketplaceLinksSchema
from app.services.interfaces import BaseLinkGenerator


class MarketplaceLinkGenerator(BaseLinkGenerator):
    """
    Генератор прямих пошукових URL на українські маркетплейси (FR-5, CON-4, GG-5).
    Принцип SRP: відповідає виключно за URL-кодування та конструювання посилань.
    """

    rozetka_base: str = "https://rozetka.com.ua/ua/search/?text="
    prom_base: str = "https://prom.ua/ua/search?search_term="
    hotline_base: str = "https://hotline.ua/ua/sr/?q="

    def url_encode_query(self, title: str) -> str:
        """Кодує кириличну назву товару в безпечний URL-формат."""
        return quote_plus(title.strip())

    def build_links(self, title: str) -> MarketplaceLinksSchema:
        """Формує об'єкт MarketplaceLinksSchema для Rozetka, Prom.ua та Hotline."""
        encoded = self.url_encode_query(title)
        return MarketplaceLinksSchema(
            rozetka=f"{self.rozetka_base}{encoded}",
            prom_ua=f"{self.prom_base}{encoded}",
            hotline=f"{self.hotline_base}{encoded}",
        )