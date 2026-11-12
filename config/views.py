from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import render
from django.views.decorators.http import require_GET

from shop.models import Category, Course, Review


@require_GET
def home(request):
    featured = (
        Course.objects.filter(is_published=True)
        .select_related("category")
        .annotate(rating_avg=Avg("reviews__rating"), reviews_total=Count("reviews"))
        .order_by("-student_qty")[:6]
    )
    categories = Category.objects.annotate(
        courses_total=Count("courses", filter=Q(courses__is_published=True))
    ).order_by("-courses_total")
    context = {
        "featured_courses": featured,
        "categories": categories,
        "stats": {
            "courses": Course.objects.filter(is_published=True).count(),
            "students": Course.objects.filter(is_published=True).aggregate(
                total=Sum("student_qty")
            )["total"]
            or 0,
            "reviews": Review.objects.count(),
        },
    }
    return render(request, "home/index.html", context)


def page_not_found(request, exception):
    return render(request, "404.html", status=404)


def server_error(request):
    return render(request, "500.html", status=500)
