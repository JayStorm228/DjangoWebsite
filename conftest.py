from decimal import Decimal

import pytest
from django.contrib.auth.models import User

from shop.models import Category, Course


@pytest.fixture
def category(db):
    return Category.objects.create(title="Программирование", slug="programmirovanie")


@pytest.fixture
def course(db, category):
    return Course.objects.create(
        title="Python с нуля",
        slug="python-s-nulya",
        category=category,
        short_description="Первый язык программирования",
        description="Подробная программа курса.",
        price=Decimal("3990.00"),
        old_price=Decimal("5990.00"),
        duration_hours=24,
        student_qty=10,
    )


@pytest.fixture
def second_course(db, category):
    return Course.objects.create(
        title="Django: backend",
        slug="django-backend",
        category=category,
        short_description="Модели и представления",
        description="Второй курс.",
        price=Decimal("6990.00"),
        level=Course.Level.ADVANCED,
        duration_hours=32,
    )


@pytest.fixture
def user(db):
    return User.objects.create_user(username="student", password="test-pass-12345")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="another", password="test-pass-12345")


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(username="staff", password="test-pass-12345", is_staff=True)


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="root", email="root@example.com", password="test-pass-12345"
    )


@pytest.fixture
def admin_client(client, admin_user):
    client.force_login(admin_user)
    return client
