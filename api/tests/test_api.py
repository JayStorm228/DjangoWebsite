import pytest
from rest_framework.authtoken.models import Token

from shop.models import Course, Order, OrderItem, Review


@pytest.mark.django_db
def test_course_list_is_public(client, course, second_course):
    response = client.get("/api/v1/courses/")
    assert response.status_code == 200

    payload = response.json()
    assert payload["count"] == 2
    slugs = {item["slug"] for item in payload["results"]}
    assert slugs == {course.slug, second_course.slug}

    item = next(item for item in payload["results"] if item["slug"] == course.slug)
    assert item["category"]["slug"] == "programmirovanie"
    assert item["level"] == Course.Level.BEGINNER
    assert item["reviews_count"] == 0
    assert item["rating"] == 0
    assert item["image"] is None


@pytest.mark.django_db
def test_unpublished_course_hidden_in_api(client, course):
    course.is_published = False
    course.save()
    payload = client.get("/api/v1/courses/").json()
    assert payload["count"] == 0


@pytest.mark.django_db
def test_course_detail_by_slug(client, course):
    response = client.get(f"/api/v1/courses/{course.slug}/")
    assert response.status_code == 200
    assert response.json()["title"] == course.title

    assert client.get("/api/v1/courses/unknown/").status_code == 404


@pytest.mark.django_db
def test_search_filters_and_ordering(client, course, second_course):
    by_search = client.get("/api/v1/courses/", {"search": "python"}).json()
    assert [item["slug"] for item in by_search["results"]] == [course.slug]

    by_level = client.get("/api/v1/courses/", {"level": "advanced"}).json()
    assert [item["slug"] for item in by_level["results"]] == [second_course.slug]

    by_category = client.get("/api/v1/courses/", {"category__slug": "programmirovanie"}).json()
    assert by_category["count"] == 2

    by_price = client.get("/api/v1/courses/", {"price__gte": "5000"}).json()
    assert [item["slug"] for item in by_price["results"]] == [second_course.slug]

    cheaper_first = client.get("/api/v1/courses/", {"ordering": "price"}).json()
    prices = [float(item["price"]) for item in cheaper_first["results"]]
    assert prices == sorted(prices)


@pytest.mark.django_db
def test_rating_in_api(client, course, user, other_user):
    Review.objects.create(course=course, user=user, rating=5)
    Review.objects.create(course=course, user=other_user, rating=4)

    item = client.get(f"/api/v1/courses/{course.slug}/").json()
    assert item["rating"] == 4.5
    assert item["reviews_count"] == 2


@pytest.mark.django_db
def test_categories_api(client, category, course):
    response = client.get("/api/v1/categories/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["results"][0]["courses_count"] == 1


@pytest.mark.django_db
def test_api_is_read_only(client):
    response = client.post("/api/v1/courses/", {"title": "Хак"}, content_type="application/json")
    assert response.status_code in (401, 403, 405)


@pytest.mark.django_db
def test_orders_require_authentication(client):
    assert client.get("/api/v1/orders/").status_code == 401


@pytest.mark.django_db
def test_orders_are_filtered_by_owner(auth_client, user, other_user, course):
    own = Order.objects.create(user=user, total_price=course.price)
    OrderItem.objects.create(order=own, course=course, title=course.title, price=course.price)
    other = Order.objects.create(user=other_user, total_price=course.price)

    payload = auth_client.get("/api/v1/orders/").json()
    ids = [item["id"] for item in payload["results"]]
    assert own.pk in ids
    assert other.pk not in ids
    assert payload["results"][0]["items"][0]["title"] == course.title


@pytest.mark.django_db
def test_token_authentication(client, user):
    token = Token.objects.create(user=user)
    response = client.get("/api/v1/orders/", HTTP_AUTHORIZATION=f"Token {token.key}")
    assert response.status_code == 200

    bad = client.get("/api/v1/orders/", HTTP_AUTHORIZATION="Token wrong")
    assert bad.status_code == 401


@pytest.mark.django_db
def test_token_endpoint(client, user):
    response = client.post(
        "/api/v1/auth/token/",
        {"username": user.username, "password": "test-pass-12345"},
    )
    assert response.status_code == 200
    assert "token" in response.json()


@pytest.mark.django_db
def test_schema_and_docs(client):
    assert client.get("/api/schema/").status_code == 200
    assert client.get("/api/docs/").status_code == 200
