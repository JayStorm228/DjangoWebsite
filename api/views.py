from django.db.models import Avg, Count, Q
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from shop.models import Category, Course, Order

from .serializers import CategorySerializer, CourseSerializer, OrderSerializer


@extend_schema(tags=["Каталог"])
class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """Публичный каталог курсов: только чтение."""

    serializer_class = CourseSerializer
    lookup_field = "slug"
    filterset_fields = {
        "category__slug": ["exact"],
        "level": ["exact"],
        "price": ["gte", "lte"],
    }
    search_fields = ("title", "short_description", "description")
    ordering_fields = ("price", "created_at", "student_qty", "title")
    ordering = ("-created_at",)

    def get_queryset(self):
        return (
            Course.objects.filter(is_published=True)
            .select_related("category")
            .annotate(rating_avg=Avg("reviews__rating"), reviews_total=Count("reviews"))
        )


@extend_schema(tags=["Каталог"])
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Категории курсов."""

    serializer_class = CategorySerializer
    lookup_field = "slug"
    search_fields = ("title",)

    def get_queryset(self):
        return Category.objects.annotate(
            courses_total=Count("courses", filter=Q(courses__is_published=True))
        ).order_by("title")


@extend_schema(tags=["Заказы"])
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Заказы текущего пользователя (требуется токен или сессия)."""

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.none()

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()
        return Order.objects.filter(user=user).prefetch_related("items").order_by("-created_at")
