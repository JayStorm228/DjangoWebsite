from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    title = models.CharField("название", max_length=120, unique=True)
    slug = models.SlugField("slug", max_length=140, unique=True, allow_unicode=True)
    description = models.TextField("описание", blank=True)
    created_at = models.DateTimeField("создана", auto_now_add=True)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True) or f"category-{self.pk or 'new'}"
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return f"{reverse('shop:course_list')}?category={self.slug}"


class Course(models.Model):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Для начинающих"
        INTERMEDIATE = "intermediate", "Средний уровень"
        ADVANCED = "advanced", "Продвинутый"

    title = models.CharField("название", max_length=200)
    slug = models.SlugField("slug", max_length=220, unique=True, allow_unicode=True)
    category = models.ForeignKey(
        Category,
        verbose_name="категория",
        related_name="courses",
        on_delete=models.PROTECT,
    )
    short_description = models.CharField("краткое описание", max_length=255)
    description = models.TextField("описание")
    price = models.DecimalField(
        "цена",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    old_price = models.DecimalField(
        "старая цена",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    level = models.CharField(
        "уровень",
        max_length=20,
        choices=Level.choices,
        default=Level.BEGINNER,
    )
    duration_hours = models.PositiveSmallIntegerField("длительность, ч", default=0)
    image = models.ImageField("обложка", upload_to="courses/", blank=True)
    student_qty = models.PositiveIntegerField("студентов", default=0)
    is_published = models.BooleanField("опубликован", default=True)
    created_at = models.DateTimeField("создан", auto_now_add=True)
    updated_at = models.DateTimeField("обновлён", auto_now=True)

    class Meta:
        verbose_name = "курс"
        verbose_name_plural = "курсы"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_published", "-created_at"]),
            models.Index(fields=["title"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or "course"
            slug = base
            counter = 2
            while Course.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("shop:course_detail", args=[self.slug])

    @property
    def rating(self) -> float:
        """Средняя оценка курса (0, если отзывов нет)."""
        reviews = list(self.reviews.all())
        if not reviews:
            return 0
        return round(sum(review.rating for review in reviews) / len(reviews), 1)

    @property
    def reviews_count(self) -> int:
        return self.reviews.count()

    @property
    def discount_percent(self) -> int:
        if not self.old_price or self.old_price <= self.price:
            return 0
        return round((self.old_price - self.price) / self.old_price * 100)


class Review(models.Model):
    course = models.ForeignKey(
        Course,
        verbose_name="курс",
        related_name="reviews",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        "auth.User",
        verbose_name="пользователь",
        related_name="reviews",
        on_delete=models.CASCADE,
    )
    rating = models.PositiveSmallIntegerField(
        "оценка",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    text = models.TextField("текст", blank=True)
    created_at = models.DateTimeField("создан", auto_now_add=True)

    class Meta:
        verbose_name = "отзыв"
        verbose_name_plural = "отзывы"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "user"],
                name="unique_review_per_user",
            )
        ]

    def __str__(self) -> str:
        return f"{self.course}: {self.rating}/5"


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        PAID = "paid", "Оплачен"
        CANCELLED = "cancelled", "Отменён"

    user = models.ForeignKey(
        "auth.User",
        verbose_name="покупатель",
        related_name="orders",
        on_delete=models.CASCADE,
    )
    total_price = models.DecimalField("сумма", max_digits=10, decimal_places=2)
    status = models.CharField(
        "статус",
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    created_at = models.DateTimeField("создан", auto_now_add=True)

    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "заказы"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Заказ №{self.pk} — {self.user}"

    @property
    def number(self) -> str:
        return f"TR-{self.pk:06d}" if self.pk else "TR-000000"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name="заказ",
        related_name="items",
        on_delete=models.CASCADE,
    )
    course = models.ForeignKey(
        Course,
        verbose_name="курс",
        related_name="order_items",
        on_delete=models.PROTECT,
    )
    title = models.CharField("название курса", max_length=200)
    price = models.DecimalField("цена", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "позиция заказа"
        verbose_name_plural = "позиции заказа"

    def __str__(self) -> str:
        return self.title


class SiteSettings(models.Model):
    """Единственная запись с настройками сайта (singleton)."""

    site_name = models.CharField("название сайта", max_length=100, default="TRShop")
    site_tagline = models.CharField(
        "подзаголовок",
        max_length=200,
        default="Учебный магазин курсов на Django",
    )
    hero_badge = models.CharField(
        "бейдж на первом экране",
        max_length=120,
        default="Онлайн-курсы с практикой",
    )
    hero_title = models.CharField(
        "заголовок первого экрана",
        max_length=200,
        default="Учитесь сегодня — применяйте завтра",
    )
    hero_subtitle = models.TextField(
        "текст первого экрана",
        default=(
            "Короткие и понятные курсы по программированию, дизайну и аналитике. "
            "Доступ открывается сразу после покупки, а прогресс всегда под рукой."
        ),
    )
    hero_image = models.ImageField(
        "фон первого экрана",
        upload_to="site/",
        blank=True,
        help_text="Необязательно: если не загрузить, останется стандартный фон темы.",
    )
    about_title = models.CharField(
        "заголовок блока «Почему мы»",
        max_length=200,
        default="Почему TRShop",
    )
    about_subtitle = models.TextField(
        "текст блока «Почему мы»",
        default=(
            "Всё, что нужно для спокойной учёбы: понятная программа, "
            "живые примеры и доступ навсегда."
        ),
    )
    contact_email = models.EmailField("email для связи", blank=True)
    contact_phone = models.CharField("телефон", max_length=40, blank=True)
    contact_address = models.CharField("адрес", max_length=200, blank=True)
    telegram_url = models.URLField("Telegram", blank=True)
    github_url = models.URLField("GitHub", blank=True)
    footer_text = models.CharField(
        "текст в подвале",
        max_length=200,
        default="учебный проект на Django и DRF.",
    )
    currency_symbol = models.CharField("символ валюты", max_length=8, default="₽")
    courses_per_page = models.PositiveSmallIntegerField(
        "курсов на странице каталога",
        default=9,
        validators=[MinValueValidator(3), MaxValueValidator(48)],
    )
    updated_at = models.DateTimeField("обновлено", auto_now=True)

    class Meta:
        verbose_name = "настройки сайта"
        verbose_name_plural = "настройки сайта"

    def __str__(self) -> str:
        return f"Настройки сайта «{self.site_name}»"

    def save(self, *args, **kwargs):
        # Сайт всегда использует одну запись.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SiteSettings":
        settings_obj, _ = cls.objects.get_or_create(pk=1)
        return settings_obj

    def get_absolute_url(self) -> str:
        return "/"
