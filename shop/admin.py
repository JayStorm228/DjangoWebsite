import csv

from django.contrib import admin, messages
from django.db.models import Avg, Count
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html, format_html_join

from .models import Category, Course, Order, OrderItem, Review, SiteSettings

admin.site.site_header = "TRShop — управление магазином"
admin.site.site_title = "TRShop"
admin.site.index_title = "Обзор"
admin.site.empty_value_display = "—"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "courses_link", "created_at")
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("title",)

    @admin.display(description="курсов", ordering="courses_total")
    def courses_link(self, obj):
        if not obj.courses_total:
            return "0"
        url = reverse("admin:shop_course_changelist") + f"?category__id__exact={obj.pk}"
        return format_html('<a href="{}">{}</a>', url, obj.courses_total)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(courses_total=Count("courses"))


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    fields = ("user", "rating", "short_text", "created_at")
    readonly_fields = ("created_at", "short_text")
    autocomplete_fields = ("user",)
    verbose_name = "отзыв"
    verbose_name_plural = "отзывы"

    @admin.display(description="текст")
    def short_text(self, obj):
        return (obj.text[:80] + "…") if len(obj.text) > 80 else obj.text


@admin.action(description="Опубликовать выбранные курсы")
def publish_courses(modeladmin, request, queryset):
    updated = queryset.update(is_published=True)
    modeladmin.message_user(request, f"Опубликовано курсов: {updated}.", messages.SUCCESS)


@admin.action(description="Снять с публикации")
def unpublish_courses(modeladmin, request, queryset):
    updated = queryset.update(is_published=False)
    modeladmin.message_user(request, f"Снято с публикации: {updated}.", messages.SUCCESS)


@admin.action(description="Дублировать курс (копия будет черновиком)")
def duplicate_courses(modeladmin, request, queryset):
    created = 0
    for course in queryset:
        source_pk = course.pk
        course.pk = None
        course._state.adding = True
        course.title = f"{course.title} (копия)"
        course.slug = ""
        course.is_published = False
        course.student_qty = 0
        course.save()
        created += 1
        modeladmin.message_user(
            request,
            f"Создана копия курса №{source_pk} → «{course.title}».",
            messages.SUCCESS,
        )
    if not created:
        modeladmin.message_user(request, "Курсы не выбраны.", messages.WARNING)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "price",
        "level",
        "students",
        "rating_display",
        "is_published",
        "cover",
        "created_at",
    )
    list_filter = ("is_published", "level", "category", "created_at")
    search_fields = ("title", "short_description", "description")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("price", "is_published")
    list_per_page = 25
    list_select_related = ("category",)
    date_hierarchy = "created_at"
    save_on_top = True
    autocomplete_fields = ("category",)
    actions = (publish_courses, unpublish_courses, duplicate_courses)
    readonly_fields = ("created_at", "updated_at", "cover_preview", "public_link")
    inlines = [ReviewInline]
    fieldsets = (
        (
            "Основное",
            {"fields": ("title", "slug", "category", "level", "is_published")},
        ),
        ("Описание", {"fields": ("short_description", "description")}),
        (
            "Цена и метрики",
            {"fields": ("price", "old_price", "duration_hours", "student_qty")},
        ),
        ("Медиа", {"fields": ("image", "cover_preview")}),
        (
            "Служебное",
            {"fields": ("public_link", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(reviews_total=Count("reviews"), rating_avg=Avg("reviews__rating"))
        )

    @admin.display(description="студентов", ordering="student_qty")
    def students(self, obj):
        return obj.student_qty

    @admin.display(description="рейтинг", ordering="rating_avg")
    def rating_display(self, obj):
        if not obj.reviews_total:
            return "—"
        return format_html(
            '<span class="tr-rating">★ {}</span> <span class="tr-muted">({})</span>',
            round(obj.rating_avg, 1),
            obj.reviews_total,
        )

    @admin.display(description="обложка")
    def cover(self, obj):
        if not obj.image:
            return "—"
        return format_html(
            '<img src="{}" class="tr-cover" alt="{}">',
            obj.image.url,
            obj.title,
        )

    @admin.display(description="предпросмотр обложки")
    def cover_preview(self, obj):
        if not obj.image:
            return "Обложка не загружена"
        return format_html(
            '<img src="{}" class="tr-cover-preview" alt="{}">',
            obj.image.url,
            obj.title,
        )

    @admin.display(description="на сайте")
    def public_link(self, obj):
        if not obj.pk or not obj.is_published:
            return "Курс не опубликован"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Открыть страницу курса ↗</a>',
            obj.get_absolute_url(),
        )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("course", "title", "price")
    readonly_fields = ("course", "title", "price")
    can_delete = False


@admin.action(description="Отметить как оплаченные")
def mark_orders_paid(modeladmin, request, queryset):
    updated = queryset.update(status=Order.Status.PAID)
    modeladmin.message_user(request, f"Оплачено заказов: {updated}.", messages.SUCCESS)


@admin.action(description="Отменить выбранные заказы")
def cancel_orders(modeladmin, request, queryset):
    updated = queryset.update(status=Order.Status.CANCELLED)
    modeladmin.message_user(request, f"Отменено заказов: {updated}.", messages.WARNING)


@admin.action(description="Выгрузить в CSV")
def export_orders_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="trshop-orders.csv"'
    response.write("\ufeff")  # BOM, чтобы Excel открыл кириллицу
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["Номер", "Дата", "Покупатель", "Email", "Статус", "Сумма", "Курсы"])
    for order in queryset.prefetch_related("items").select_related("user"):
        writer.writerow(
            [
                order.number,
                order.created_at.strftime("%d.%m.%Y %H:%M"),
                order.user.username,
                order.user.email,
                order.get_status_display(),
                order.total_price,
                ", ".join(item.title for item in order.items.all()),
            ]
        )
    return response


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "items_total", "total_price", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "user__email")
    date_hierarchy = "created_at"
    list_per_page = 25
    list_editable = ("status",)
    readonly_fields = ("number", "user", "total_price", "created_at", "items_list")
    inlines = [OrderItemInline]
    actions = (mark_orders_paid, cancel_orders, export_orders_csv)
    fieldsets = (
        ("Заказ", {"fields": ("number", "user", "status", "total_price", "created_at")}),
        ("Состав", {"fields": ("items_list",)}),
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description="позиций")
    def items_total(self, obj):
        return obj.items.count()

    @admin.display(description="курсы")
    def items_list(self, obj):
        if not obj.pk:
            return "—"
        return format_html_join(
            "<br>",
            "{} — {} ₽",
            ((item.title, item.price) for item in obj.items.all()),
        )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("course", "user", "rating", "short_text", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("course__title", "user__username", "text")
    autocomplete_fields = ("course", "user")
    date_hierarchy = "created_at"
    list_select_related = ("course", "user")

    @admin.display(description="текст")
    def short_text(self, obj):
        return (obj.text[:90] + "…") if len(obj.text) > 90 else obj.text


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Единственная запись: попасть в неё можно из обзора админки."""

    fieldsets = (
        (
            "Бренд",
            {
                "fields": ("site_name", "site_tagline", "footer_text"),
                "description": "Название и подпись видны в шапке сайта, "
                "вкладке браузера и подвале.",
            },
        ),
        (
            "Первый экран",
            {
                "fields": (
                    "hero_badge",
                    "hero_title",
                    "hero_subtitle",
                    "hero_image",
                    "hero_image_preview",
                ),
                "description": "Блок, который посетитель видит первым на главной странице.",
            },
        ),
        (
            "Блок «Почему мы»",
            {"fields": ("about_title", "about_subtitle")},
        ),
        (
            "Контакты и ссылки",
            {
                "fields": (
                    "contact_email",
                    "contact_phone",
                    "contact_address",
                    "telegram_url",
                    "github_url",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Магазин",
            {
                "fields": ("currency_symbol", "courses_per_page"),
                "description": "Символ валюты подставляется во все цены, "
                "а число курсов задаёт размер страницы каталога.",
            },
        ),
    )
    readonly_fields = ("hero_image_preview", "updated_at")
    save_on_top = True

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.load()
        return HttpResponseRedirect(reverse("admin:shop_sitesettings_change", args=[obj.pk]))

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = {
            **(extra_context or {}),
            "site_url": "/",
            "title": "Настройки сайта",
        }
        return super().changeform_view(request, object_id, form_url, extra_context)

    @admin.display(description="текущий фон")
    def hero_image_preview(self, obj):
        if not obj.hero_image:
            return "Используется стандартный фон темы"
        return format_html(
            '<img src="{}" class="tr-hero-preview" alt="Фон первого экрана">',
            obj.hero_image.url,
        )
