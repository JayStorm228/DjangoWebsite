import pytest
from django.urls import reverse

from shop.models import Course, Order, OrderItem, SiteSettings


@pytest.mark.django_db
def test_admin_requires_staff(client):
    response = client.get(reverse("admin:index"))
    assert response.status_code == 302
    assert "/admin/login/" in response.url


@pytest.mark.django_db
def test_staff_without_permissions_does_not_break_dashboard(client, staff_user):
    client.force_login(staff_user)
    response = client.get(reverse("admin:index"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_shows_stats_and_quick_actions(admin_client, course, user):
    order = Order.objects.create(user=user, total_price=course.price, status=Order.Status.PAID)
    OrderItem.objects.create(order=order, course=course, title=course.title, price=course.price)

    response = admin_client.get(reverse("admin:index"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Обзор магазина" in content
    assert "Последние заказы" in content
    assert "Настроить сайт" in content
    assert "Быстрые действия" in content
    assert order.number in content


@pytest.mark.django_db
def test_settings_changelist_redirects_to_singleton(admin_client):
    response = admin_client.get(reverse("admin:shop_sitesettings_changelist"))
    assert response.status_code == 302
    assert response.url == reverse("admin:shop_sitesettings_change", args=[1])


@pytest.mark.django_db
def test_settings_is_singleton():
    first = SiteSettings.load()
    second = SiteSettings.load()
    second.site_name = "Другое имя"
    second.save()

    assert first.pk == second.pk == 1
    assert SiteSettings.objects.count() == 1
    assert SiteSettings.load().site_name == "Другое имя"


@pytest.mark.django_db
def test_settings_change_updates_public_pages(admin_client):
    SiteSettings.load()
    url = reverse("admin:shop_sitesettings_change", args=[1])

    response = admin_client.post(
        url,
        {
            "site_name": "Академия",
            "site_tagline": "Учим по-новому",
            "hero_badge": "Новый набор",
            "hero_title": "Заголовок из админки",
            "hero_subtitle": "Подзаголовок из админки",
            "about_title": "О нас из админки",
            "about_subtitle": "Текст о нас из админки",
            "contact_email": "hello@example.com",
            "contact_phone": "+7 900 000-00-00",
            "contact_address": "",
            "telegram_url": "",
            "github_url": "",
            "footer_text": "работает на Django",
            "currency_symbol": "₸",
            "courses_per_page": "6",
        },
        follow=True,
    )

    assert response.status_code == 200
    settings_obj = SiteSettings.load()
    assert settings_obj.hero_title == "Заголовок из админки"
    assert settings_obj.currency_symbol == "₸"
    assert settings_obj.courses_per_page == 6

    home = admin_client.get(reverse("home")).content.decode()
    assert "Заголовок из админки" in home

    catalog = admin_client.get(reverse("shop:course_list")).content.decode()
    assert "₸" in catalog


@pytest.mark.django_db
def test_catalog_page_size_comes_from_settings(admin_client, category):
    SiteSettings.objects.update_or_create(pk=1, defaults={"courses_per_page": 3})
    for index in range(5):
        Course.objects.create(
            title=f"Курс {index}",
            category=category,
            short_description="Кратко",
            description="Описание",
            price="1000.00",
        )

    response = admin_client.get(reverse("shop:course_list"))
    assert len(response.context["courses"]) == 3


@pytest.mark.django_db
def test_course_changelist_and_actions(admin_client, course):
    course.is_published = False
    course.save()

    changelist = admin_client.get(reverse("admin:shop_course_changelist"))
    assert changelist.status_code == 200

    response = admin_client.post(
        reverse("admin:shop_course_changelist"),
        {"action": "publish_courses", "_selected_action": [course.pk]},
    )
    assert response.status_code == 302
    course.refresh_from_db()
    assert course.is_published is True

    response = admin_client.post(
        reverse("admin:shop_course_changelist"),
        {"action": "duplicate_courses", "_selected_action": [course.pk]},
    )
    assert response.status_code == 302
    copy = Course.objects.get(title=f"{course.title} (копия)")
    assert copy.is_published is False
    assert copy.slug != course.slug


@pytest.mark.django_db
def test_admin_pages_load(admin_client, course, category, user):
    SiteSettings.load()
    pages = [
        reverse("admin:shop_course_add"),
        reverse("admin:shop_course_change", args=[course.pk]),
        reverse("admin:shop_category_changelist"),
        reverse("admin:shop_category_change", args=[category.pk]),
        reverse("admin:shop_order_changelist"),
        reverse("admin:shop_review_changelist"),
        reverse("admin:shop_sitesettings_change", args=[1]),
    ]
    for url in pages:
        assert admin_client.get(url).status_code == 200, url


@pytest.mark.django_db
def test_orders_csv_export(admin_client, user, course):
    order = Order.objects.create(user=user, total_price=course.price, status=Order.Status.PAID)
    OrderItem.objects.create(order=order, course=course, title=course.title, price=course.price)

    response = admin_client.post(
        reverse("admin:shop_order_changelist"),
        {"action": "export_orders_csv", "_selected_action": [order.pk]},
    )

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    payload = response.content.decode("utf-8-sig")
    assert order.number in payload
    assert user.username in payload
    assert course.title in payload


@pytest.mark.django_db
def test_mark_orders_paid_action(admin_client, user, course):
    order = Order.objects.create(user=user, total_price=course.price, status=Order.Status.NEW)

    response = admin_client.post(
        reverse("admin:shop_order_changelist"),
        {"action": "mark_orders_paid", "_selected_action": [order.pk]},
    )

    assert response.status_code == 302
    order.refresh_from_db()
    assert order.status == Order.Status.PAID
