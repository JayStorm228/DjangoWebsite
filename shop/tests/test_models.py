from decimal import Decimal
from urllib.parse import unquote

import pytest
from django.db import IntegrityError

from shop.models import Category, Course, Review


@pytest.mark.django_db
def test_slug_is_generated_for_russian_title(category):
    course = Course.objects.create(
        title="Курс по вёрстке",
        category=category,
        short_description="Кратко",
        description="Описание",
        price=Decimal("1000.00"),
    )
    assert course.slug
    assert course.get_absolute_url().startswith("/shop/courses/")
    assert unquote(course.get_absolute_url()).endswith(f"/{course.slug}/")


@pytest.mark.django_db
def test_duplicate_slug_is_suffixed(category):
    kwargs = {
        "title": "Одинаковый курс",
        "category": category,
        "short_description": "Кратко",
        "description": "Описание",
        "price": Decimal("1000.00"),
    }
    first = Course.objects.create(**kwargs)
    second = Course.objects.create(**kwargs)
    assert first.slug != second.slug
    assert second.slug.endswith("-2")


@pytest.mark.django_db
def test_rating_and_discount(course, user, other_user):
    Review.objects.create(course=course, user=user, rating=5, text="Класс")
    Review.objects.create(course=course, user=other_user, rating=4, text="Хорошо")
    assert course.rating == 4.5
    assert course.reviews_count == 2
    assert course.discount_percent == 33


@pytest.mark.django_db
def test_one_review_per_user(course, user):
    Review.objects.create(course=course, user=user, rating=5)
    with pytest.raises(IntegrityError):
        Review.objects.create(course=course, user=user, rating=3)


@pytest.mark.django_db
def test_category_slug_generated():
    category = Category.objects.create(title="Аналитика данных")
    assert category.slug == "аналитика-данных"
    assert "category=" in category.get_absolute_url()
