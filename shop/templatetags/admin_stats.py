from django import template
from django.contrib.auth.models import User
from django.db.models import Avg, Sum

from shop.models import Course, Order, Review

register = template.Library()


@register.simple_tag
def admin_stats() -> dict:
    """Цифры для обзорной панели админки."""
    paid_orders = Order.objects.filter(status=Order.Status.PAID)
    return {
        "courses_total": Course.objects.count(),
        "courses_published": Course.objects.filter(is_published=True).count(),
        "courses_draft": Course.objects.filter(is_published=False).count(),
        "students": Course.objects.aggregate(total=Sum("student_qty"))["total"] or 0,
        "orders_total": Order.objects.count(),
        "orders_paid": paid_orders.count(),
        "revenue": paid_orders.aggregate(total=Sum("total_price"))["total"] or 0,
        "reviews": Review.objects.count(),
        "avg_rating": Review.objects.aggregate(avg=Avg("rating"))["avg"],
        "users": User.objects.count(),
    }


@register.inclusion_tag("admin/includes/recent_orders.html")
def recent_orders(limit: int = 5) -> dict:
    return {
        "orders": Order.objects.select_related("user")
        .prefetch_related("items")
        .order_by("-created_at")[:limit]
    }
