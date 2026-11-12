from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Avg, Count, F, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import DetailView, ListView

from .cart import Cart
from .forms import RegisterForm, ReviewForm
from .models import Category, Course, Order, OrderItem, Review

SORT_OPTIONS = {
    "new": ("-created_at", "Сначала новые"),
    "price": ("price", "Сначала дешёвые"),
    "-price": ("-price", "Сначала дорогие"),
    "popular": ("-student_qty", "Популярные"),
    "rating": ("-rating_avg", "По рейтингу"),
}


def _parse_decimal(value: str) -> Decimal | None:
    """Безопасно превращает строку в Decimal (иначе None)."""
    try:
        return Decimal(value.replace(",", "."))
    except (InvalidOperation, AttributeError):
        return None


class CourseListView(ListView):
    model = Course
    template_name = "shop/course_list.html"
    context_object_name = "courses"
    paginate_by = 9

    def get_queryset(self):
        queryset = (
            Course.objects.filter(is_published=True)
            .select_related("category")
            .annotate(rating_avg=Avg("reviews__rating"), reviews_total=Count("reviews"))
        )

        query = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "").strip()
        level = self.request.GET.get("level", "").strip()
        price_min = _parse_decimal(self.request.GET.get("price_min", ""))
        price_max = _parse_decimal(self.request.GET.get("price_max", ""))
        sort = self.request.GET.get("sort", "new")

        if query:
            queryset = queryset.filter(title__icontains=query)
        if category:
            queryset = queryset.filter(category__slug=category)
        if level in Course.Level.values:
            queryset = queryset.filter(level=level)
        if price_min is not None:
            queryset = queryset.filter(price__gte=price_min)
        if price_max is not None:
            queryset = queryset.filter(price__lte=price_max)

        ordering = SORT_OPTIONS.get(sort, SORT_OPTIONS["new"])[0]
        return queryset.order_by(ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        context.update(
            {
                "categories": Category.objects.annotate(
                    courses_total=Count("courses", filter=Q(courses__is_published=True))
                ),
                "levels": Course.Level.choices,
                "sort_options": [(key, label) for key, (_, label) in SORT_OPTIONS.items()],
                "selected": {
                    "q": self.request.GET.get("q", ""),
                    "category": self.request.GET.get("category", ""),
                    "level": self.request.GET.get("level", ""),
                    "price_min": self.request.GET.get("price_min", ""),
                    "price_max": self.request.GET.get("price_max", ""),
                    "sort": self.request.GET.get("sort", "new"),
                },
                "querystring": params.urlencode(),
                "total_found": context["paginator"].count if context.get("paginator") else 0,
            }
        )
        return context


class CourseDetailView(DetailView):
    model = Course
    template_name = "shop/course_detail.html"
    context_object_name = "course"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Course.objects.filter(is_published=True)
            .select_related("category")
            .prefetch_related("reviews__user")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        context.update(
            {
                "related_courses": Course.objects.filter(
                    is_published=True, category=course.category
                )
                .exclude(pk=course.pk)
                .select_related("category")[:3],
                "review_form": ReviewForm(),
                "reviews": course.reviews.select_related("user"),
                "in_cart": course in Cart(self.request),
            }
        )
        return context


@require_POST
def add_review(request: HttpRequest, slug: str) -> HttpResponse:
    course = get_object_or_404(Course, slug=slug, is_published=True)
    if not request.user.is_authenticated:
        messages.info(request, "Чтобы оставить отзыв, войдите в аккаунт.")
        return redirect(f"{course.get_absolute_url()}#reviews")

    form = ReviewForm(request.POST)
    if form.is_valid():
        Review.objects.update_or_create(
            course=course,
            user=request.user,
            defaults={"rating": form.cleaned_data["rating"], "text": form.cleaned_data["text"]},
        )
        messages.success(request, "Спасибо! Ваш отзыв сохранён.")
    else:
        messages.error(request, "Не удалось сохранить отзыв: проверьте оценку и текст.")
    return redirect(f"{course.get_absolute_url()}#reviews")


def cart_detail(request: HttpRequest) -> HttpResponse:
    cart = Cart(request)
    return render(request, "shop/cart.html", {"cart": cart})


@require_POST
def cart_add(request: HttpRequest, course_id: int) -> HttpResponse:
    course = get_object_or_404(Course, pk=course_id, is_published=True)
    cart = Cart(request)
    cart.add(course)
    messages.success(request, f"Курс «{course.title}» добавлен в корзину.")
    return redirect(request.POST.get("next") or "shop:cart")


@require_POST
def cart_remove(request: HttpRequest, course_id: int) -> HttpResponse:
    cart = Cart(request)
    cart.remove(course_id)
    messages.info(request, "Курс удалён из корзины.")
    return redirect("shop:cart")


@login_required
@require_http_methods(["GET", "POST"])
def checkout(request: HttpRequest) -> HttpResponse:
    cart = Cart(request)
    if not cart:
        messages.warning(request, "Корзина пуста — добавьте курс перед оформлением.")
        return redirect("shop:course_list")

    if request.method == "POST":
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                total_price=cart.total_price,
                status=Order.Status.PAID,
            )
            OrderItem.objects.bulk_create(
                [
                    OrderItem(
                        order=order,
                        course=course,
                        title=course.title,
                        price=course.price,
                    )
                    for course in cart
                ]
            )
            Course.objects.filter(pk__in=[course.pk for course in cart]).update(
                student_qty=F("student_qty") + 1
            )
        cart.clear()
        messages.success(
            request, f"Заказ {order.number} оформлен. Курсы доступны в разделе «Мои покупки»."
        )
        return redirect("shop:order_detail", pk=order.pk)

    return render(request, "shop/checkout.html", {"cart": cart})


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "shop/order_list.html"
    context_object_name = "orders"
    paginate_by = 10

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items")
            .order_by("-created_at")
        )


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "shop/order_detail.html"
    context_object_name = "order"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items__course")


def register(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Добро пожаловать, {user.username}!")
        return redirect("shop:course_list")

    return render(request, "registration/register.html", {"form": form})
