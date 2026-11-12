from django.db import OperationalError, ProgrammingError

from .cart import Cart
from .models import SiteSettings


def cart(request):
    """Добавляет корзину и её размер во все шаблоны."""
    current_cart = Cart(request)
    return {"cart": current_cart, "cart_items_count": len(current_cart)}


def site_settings(request):
    """Отдаёт в шаблоны настройки сайта из админки.

    Если таблицы ещё нет (например, до первой миграции), используются значения
    по умолчанию, чтобы сайт не падал с ошибкой 500.
    """
    try:
        settings_obj = SiteSettings.load()
    except (OperationalError, ProgrammingError):
        settings_obj = SiteSettings()
    return {"site_settings": settings_obj}
