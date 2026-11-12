from decimal import Decimal

from django.conf import settings

from .models import Course


class Cart:
    """Корзина на сессии: хранит только идентификаторы курсов."""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if cart is None:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, course: Course) -> None:
        course_id = str(course.pk)
        if course_id not in self.cart:
            self.cart[course_id] = {"price": str(course.price)}
            self.save()

    def remove(self, course_id: int | str) -> None:
        if str(course_id) in self.cart:
            del self.cart[str(course_id)]
            self.save()

    def clear(self) -> None:
        self.session[settings.CART_SESSION_ID] = {}
        self.session.modified = True

    def save(self) -> None:
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def __contains__(self, course) -> bool:
        return str(course.pk) in self.cart

    def __len__(self) -> int:
        return len(self.cart)

    def __iter__(self):
        courses = Course.objects.filter(pk__in=self.cart.keys()).select_related("category")
        yield from courses

    @property
    def total_price(self) -> Decimal:
        return sum((Decimal(item["price"]) for item in self.cart.values()), Decimal("0"))
