from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Course, Order, OrderItem, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "courses_total", "created_at")
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}

    @admin.display(description="курсов")
    def courses_total(self, obj):
        return obj.courses.count()


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    fields = ("user", "rating", "text", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "price",
        "level",
        "student_qty",
        "is_published",
        "cover",
        "created_at",
    )
    list_filter = ("is_published", "level", "category")
    search_fields = ("title", "short_description", "description")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_published",)
    readonly_fields = ("created_at", "updated_at", "cover_preview")
    inlines = [ReviewInline]
    fieldsets = (
        ("Основное", {"fields": ("title", "slug", "category", "level", "is_published")}),
        ("Описание", {"fields": ("short_description", "description")}),
        ("Цена и метрики", {"fields": ("price", "old_price", "duration_hours", "student_qty")}),
        ("Медиа", {"fields": ("image", "cover_preview")}),
        ("Даты", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="обложка")
    def cover(self, obj):
        if not obj.image:
            return "—"
        return format_html('<img src="{}" style="height:36px;border-radius:4px">', obj.image.url)

    @admin.display(description="предпросмотр")
    def cover_preview(self, obj):
        if not obj.image:
            return "Обложка не загружена"
        return format_html(
            '<img src="{}" style="max-height:240px;border-radius:8px">', obj.image.url
        )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("course", "title", "price")
    readonly_fields = ("course", "title", "price")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "total_price", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user", "total_price", "created_at")
    inlines = [OrderItemInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("course", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("course__title", "user__username", "text")
