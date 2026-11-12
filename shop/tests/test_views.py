from decimal import Decimal

import pytest
from django.urls import reverse

from shop.models import Order, OrderItem, Review


@pytest.mark.django_db
def test_home_page_shows_courses(client, course):
    response = client.get(reverse("home"))
    assert response.status_code == 200
    assert course.title.encode() in response.content


@pytest.mark.django_db
def test_catalog_filters(client, course, second_course):
    url = reverse("shop:course_list")

    assert client.get(url).status_code == 200

    by_title = client.get(url, {"q": "python"})
    assert list(by_title.context["courses"]) == [course]

    by_category = client.get(url, {"category": "programmirovanie"})
    assert by_category.context["paginator"].count == 2

    by_level = client.get(url, {"level": "advanced"})
    assert list(by_level.context["courses"]) == [second_course]

    by_price = client.get(url, {"price_min": "5000", "price_max": "8000"})
    assert list(by_price.context["courses"]) == [second_course]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "params",
    [
        {"category": "не существует"},
        {"category": "../../etc/passwd"},
        {"price_min": "abc", "price_max": "-"},
        {"level": "unknown"},
        {"sort": "'; DROP TABLE shop_course; --"},
    ],
)
def test_catalog_survives_bad_query_params(client, course, params):
    response = client.get(reverse("shop:course_list"), params)
    assert response.status_code == 200


@pytest.mark.django_db
def test_unpublished_course_is_hidden(client, course):
    course.is_published = False
    course.save()

    assert client.get(reverse("shop:course_list")).context["paginator"].count == 0
    assert client.get(course.get_absolute_url()).status_code == 404


@pytest.mark.django_db
def test_course_detail_renders(client, course):
    response = client.get(course.get_absolute_url())
    assert response.status_code == 200
    assert response.context["course"] == course
    assert "Подробная программа курса" in response.content.decode()


@pytest.mark.django_db
def test_unknown_course_returns_custom_404(client):
    response = client.get("/shop/courses/not-a-course/")
    assert response.status_code == 404
    assert "Такой страницы нет" in response.content.decode()


@pytest.mark.django_db
def test_cart_add_and_remove(client, course):
    response = client.post(reverse("shop:cart_add", args=[course.pk]))
    assert response.status_code == 302
    assert client.session["cart"] == {str(course.pk): {"price": str(course.price)}}

    cart_page = client.get(reverse("shop:cart"))
    assert cart_page.status_code == 200
    assert course.title.encode() in cart_page.content

    client.post(reverse("shop:cart_remove", args=[course.pk]))
    assert client.session["cart"] == {}


@pytest.mark.django_db
def test_cart_total(client, course, second_course):
    client.post(reverse("shop:cart_add", args=[course.pk]))
    client.post(reverse("shop:cart_add", args=[second_course.pk]))

    total = client.get(reverse("shop:cart")).context["cart"].total_price
    assert total == Decimal("10980.00")


@pytest.mark.django_db
def test_checkout_requires_login(client, course):
    client.post(reverse("shop:cart_add", args=[course.pk]))
    response = client.get(reverse("shop:checkout"))
    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_checkout_creates_paid_order(auth_client, user, course):
    auth_client.post(reverse("shop:cart_add", args=[course.pk]))
    response = auth_client.post(reverse("shop:checkout"))

    order = Order.objects.get(user=user)
    assert response.status_code == 302
    assert order.status == Order.Status.PAID
    assert order.total_price == course.price
    assert OrderItem.objects.filter(order=order, course=course).exists()
    assert auth_client.session["cart"] == {}

    course.refresh_from_db()
    assert course.student_qty == 11


@pytest.mark.django_db
def test_checkout_with_empty_cart_redirects(auth_client):
    response = auth_client.get(reverse("shop:checkout"))
    assert response.status_code == 302
    assert response.url == reverse("shop:course_list")


@pytest.mark.django_db
def test_order_detail_is_private(auth_client, user, other_user, course):
    other_order = Order.objects.create(
        user=other_user, total_price=course.price, status=Order.Status.PAID
    )
    assert auth_client.get(reverse("shop:order_detail", args=[other_order.pk])).status_code == 404

    own_order = Order.objects.create(user=user, total_price=course.price, status=Order.Status.PAID)
    assert auth_client.get(reverse("shop:order_detail", args=[own_order.pk])).status_code == 200


@pytest.mark.django_db
def test_order_list_only_shows_own_orders(auth_client, user, other_user, course):
    own = Order.objects.create(user=user, total_price=course.price, status=Order.Status.PAID)
    other = Order.objects.create(
        user=other_user, total_price=course.price, status=Order.Status.PAID
    )

    response = auth_client.get(reverse("shop:order_list"))
    orders = list(response.context["orders"])
    assert own in orders
    assert other not in orders


@pytest.mark.django_db
def test_registration_logs_user_in(client):
    response = client.post(
        reverse("shop:register"),
        {
            "username": "newbie",
            "email": "newbie@example.com",
            "first_name": "Новик",
            "password1": "very-secret-pass-123",
            "password2": "very-secret-pass-123",
        },
    )
    assert response.status_code == 302
    assert client.session["_auth_user_id"]


@pytest.mark.django_db
def test_review_requires_login(client, course):
    response = client.post(reverse("shop:add_review", args=[course.slug]), {"rating": 5})
    assert response.status_code == 302
    assert Review.objects.count() == 0


@pytest.mark.django_db
def test_review_created_and_updated(auth_client, user, course):
    url = reverse("shop:add_review", args=[course.slug])
    auth_client.post(url, {"rating": 4, "text": "Хорошо"})
    assert Review.objects.filter(course=course, user=user, rating=4).exists()

    auth_client.post(url, {"rating": 5, "text": "Отлично"})
    reviews = Review.objects.filter(course=course, user=user)
    assert reviews.count() == 1
    assert reviews.first().rating == 5
