from .cart import Cart


def cart(request):
    """Добавляет корзину и её размер во все шаблоны."""
    current_cart = Cart(request)
    return {"cart": current_cart, "cart_items_count": len(current_cart)}
