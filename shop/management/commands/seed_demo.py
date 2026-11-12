"""Наполняет каталог демонстрационными данными.

Запуск: python manage.py seed_demo
Команда идемпотентна: повторный запуск не создаёт дубликаты.
"""

from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from shop.models import Category, Course, Order, OrderItem, Review, SiteSettings

CATEGORIES = [
    ("Программирование", "programmirovanie", "Python, Django, API и всё, что нужно бэкендеру."),
    ("Дизайн", "dizayn", "Интерфейсы, типографика и визуальная коммуникация."),
    ("Аналитика данных", "analitika-dannyh", "SQL, визуализация и принятие решений на данных."),
    ("Маркетинг", "marketing", "Продвижение продукта без бюджета на телевизионную рекламу."),
]

COURSES = [
    {
        "title": "Python с нуля",
        "slug": "python-s-nulya",
        "category": "Программирование",
        "short": "Первый язык программирования: синтаксис, структуры данных и практика.",
        "price": "3990.00",
        "old_price": "5990.00",
        "level": Course.Level.BEGINNER,
        "duration": 24,
        "students": 1240,
        "description": (
            "Курс для тех, кто никогда не программировал. Начинаем с установки Python и первых "
            "скриптов, разбираем переменные, условия, циклы, функции и коллекции.\n\n"
            "Во второй половине курса пишем небольшие практические проекты: калькулятор, "
            "парсер и телеграм-бота. К концу обучения вы уверенно читаете чужой код и "
            "понимаете, как устроены программы изнутри."
        ),
    },
    {
        "title": "Django: backend с нуля",
        "slug": "django-backend",
        "category": "Программирование",
        "short": "Модели, представления, шаблоны, формы и REST API на реальном проекте.",
        "price": "6990.00",
        "old_price": "8990.00",
        "level": Course.Level.INTERMEDIATE,
        "duration": 32,
        "students": 870,
        "description": (
            "Практический курс по Django: от пустого проекта до работающего магазина с "
            "каталогом, корзиной и API.\n\n"
            "Разбираем ORM и миграции, class-based views, формы и валидацию, права доступа, "
            "кэширование и тесты. Отдельный модуль — Django REST Framework и документация "
            "API через OpenAPI."
        ),
    },
    {
        "title": "REST API на Django REST Framework",
        "slug": "rest-api-drf",
        "category": "Программирование",
        "short": "Сериализаторы, права, фильтры, пагинация и OpenAPI-схема.",
        "price": "4990.00",
        "level": Course.Level.INTERMEDIATE,
        "duration": 18,
        "students": 640,
        "description": (
            "Учимся проектировать API, которым удобно пользоваться: единые ответы, "
            "предсказуемые ошибки, пагинация и фильтры.\n\n"
            "Токен-аутентификация, права владельца, троттлинг, версионирование и "
            "автоматическая документация через drf-spectacular. В финале — тесты и "
            "публикация схемы для внешних клиентов."
        ),
    },
    {
        "title": "UI/UX дизайн интерфейсов",
        "slug": "ui-ux-design",
        "category": "Дизайн",
        "short": "Исследование, прототипы, сетки и дизайн-система с нуля.",
        "price": "5990.00",
        "old_price": "7490.00",
        "level": Course.Level.BEGINNER,
        "duration": 22,
        "students": 980,
        "description": (
            "Курс о том, как превращать задачи пользователей в понятные интерфейсы. "
            "Разбираем исследование, сценарии, вайрфреймы и прототипы.\n\n"
            "Отдельный блок — визуальный язык: сетки, отступы, типографика, цвет и "
            "компоненты. В проекте собираем дизайн-систему для вымышленного сервиса."
        ),
    },
    {
        "title": "Figma для начинающих",
        "slug": "figma-dlya-nachinayushchih",
        "category": "Дизайн",
        "short": "Компоненты, автолейауты и прототипы за 10 практических занятий.",
        "price": "2490.00",
        "level": Course.Level.BEGINNER,
        "duration": 10,
        "students": 1520,
        "description": (
            "Компактный интенсив по Figma: осваиваем интерфейс, слои, стили и компоненты.\n\n"
            "Учимся собирать адаптивные макеты на автолейаутах, делать варианты компонентов "
            "и кликабельные прототипы. Подойдёт дизайнерам, разработчикам и продактам."
        ),
    },
    {
        "title": "Аналитика данных на SQL",
        "slug": "analitika-sql",
        "category": "Аналитика данных",
        "short": "SELECT, JOIN, агрегаты и оконные функции на реальных данных.",
        "price": "5490.00",
        "level": Course.Level.INTERMEDIATE,
        "duration": 20,
        "students": 730,
        "description": (
            "Учимся задавать бизнесу правильные вопросы и отвечать на них данными.\n\n"
            "Разбираем SELECT и фильтрацию, JOIN, агрегаты, подзапросы, оконные функции и "
            "оптимизацию запросов. Каждое занятие — практика на учебной базе интернет-магазина."
        ),
    },
    {
        "title": "Визуализация данных",
        "slug": "vizualizaciya-dannyh",
        "category": "Аналитика данных",
        "short": "Дашборды, которые помогают принимать решения, а не просто красивы.",
        "price": "4490.00",
        "level": Course.Level.ADVANCED,
        "duration": 16,
        "students": 410,
        "description": (
            "Курс о том, как из таблиц получаются понятные дашборды. Обсуждаем выбор "
            "графиков, цветовые шкалы и типичные ошибки восприятия.\n\n"
            "Практика в Python (matplotlib, seaborn, plotly) и в BI-инструменте: собираем "
            "дашборд продаж и защищаем решения перед «заказчиком»."
        ),
    },
    {
        "title": "Продуктовый маркетинг",
        "slug": "produktovyy-marketing",
        "category": "Маркетинг",
        "short": "Позиционирование, каналы и метрики без магического мышления.",
        "price": "3990.00",
        "level": Course.Level.INTERMEDIATE,
        "duration": 14,
        "students": 560,
        "description": (
            "Как продукт находит своих пользователей: от исследования аудитории до "
            "воронки и удержания.\n\n"
            "Разбираем позиционирование, ценность, каналы привлечения, unit-экономику и "
            "аналитику кампаний. В конце — маркетинговый план для собственного проекта."
        ),
    },
    {
        "title": "Docker и деплой Django-проекта",
        "slug": "docker-deploy-django",
        "category": "Программирование",
        "short": "Контейнеры, PostgreSQL, gunicorn и публикация проекта в интернете.",
        "price": "5990.00",
        "level": Course.Level.ADVANCED,
        "duration": 12,
        "students": 300,
        "description": (
            "Финальный шаг от «работает у меня» до «работает в интернете».\n\n"
            "Docker и docker compose, переменные окружения, PostgreSQL, gunicorn и "
            "WhiteNoise, статика и медиа, домен, HTTPS и базовый мониторинг. "
            "Разворачиваем Django-магазин на учебном сервере."
        ),
    },
]

REVIEW_TEXTS = [
    (5, "Отличная подача: всё по делу, много практики и понятные примеры."),
    (5, "Курс помог структурировать знания. Особенно понравились домашние задания."),
    (4, "Полезно, но местами хотелось больше подробностей по теории."),
    (4, "Хороший темп и адекватная сложность. Рекомендую как первый шаг."),
]


class Command(BaseCommand):
    help = "Создаёт демонстрационные категории, курсы, отзывы и пользователей."

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {}
        for title, slug, description in CATEGORIES:
            category, _ = Category.objects.get_or_create(
                slug=slug,
                defaults={"title": title, "description": description},
            )
            categories[title] = category

        reviewers = []
        for username, first_name, email in (
            ("anna", "Анна", "anna@example.com"),
            ("ivan", "Иван", "ivan@example.com"),
            ("maria", "Мария", "maria@example.com"),
        ):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first_name, "email": email},
            )
            if created:
                user.set_password("demo12345")
                user.save()
            reviewers.append(user)

        demo_user, created = User.objects.get_or_create(
            username="demo",
            defaults={"email": "demo@example.com", "first_name": "Демо"},
        )
        if created:
            demo_user.set_password("demo12345")
            demo_user.save()

        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@example.com", "is_staff": True, "is_superuser": True},
        )
        if created:
            admin_user.set_password("admin12345")
            admin_user.save()

        images_dir = (
            Path(settings.BASE_DIR) / "static" / "assets" / "img" / "portfolio" / "fullsize"
        )
        image_files = sorted(images_dir.glob("*.jpg")) if images_dir.exists() else []

        for index, data in enumerate(COURSES):
            course, created = Course.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "title": data["title"],
                    "category": categories[data["category"]],
                    "short_description": data["short"],
                    "description": data["description"],
                    "price": Decimal(data["price"]),
                    "old_price": Decimal(data["old_price"]) if data.get("old_price") else None,
                    "level": data["level"],
                    "duration_hours": data["duration"],
                    "student_qty": data["students"],
                },
            )
            if created and image_files:
                source = image_files[index % len(image_files)]
                course.image.save(source.name, ContentFile(source.read_bytes()), save=True)

            if created:
                for offset, reviewer in enumerate(reviewers):
                    rating, text = REVIEW_TEXTS[(index + offset) % len(REVIEW_TEXTS)]
                    Review.objects.get_or_create(
                        course=course,
                        user=reviewer,
                        defaults={"rating": rating, "text": text},
                    )

        if not Order.objects.filter(user=demo_user).exists():
            first_course = Course.objects.filter(is_published=True).first()
            if first_course:
                order = Order.objects.create(
                    user=demo_user,
                    total_price=first_course.price,
                    status=Order.Status.PAID,
                )
                OrderItem.objects.create(
                    order=order,
                    course=first_course,
                    title=first_course.title,
                    price=first_course.price,
                )

        site = SiteSettings.load()
        if not site.contact_email:
            site.contact_email = "hello@trshop.example"
            site.contact_phone = "+7 900 123-45-67"
            site.telegram_url = "https://t.me/trshop"
            site.github_url = "https://github.com/JayStorm228/DjangoWebsite"
            site.save()

        self.stdout.write(self.style.SUCCESS("Демо-данные готовы."))
        self.stdout.write(
            f"  курсов: {Course.objects.count()}, "
            f"категорий: {Category.objects.count()}, "
            f"отзывов: {Review.objects.count()}"
        )
        self.stdout.write("  demo / demo12345 — покупатель")
        self.stdout.write("  admin / admin12345 — администратор")
