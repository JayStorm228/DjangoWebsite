from rest_framework import serializers

from shop.models import Category, Course, Order, OrderItem, Review


class CategorySerializer(serializers.ModelSerializer):
    courses_count = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="category-detail", lookup_field="slug")

    class Meta:
        model = Category
        fields = ("id", "title", "slug", "description", "courses_count", "url")

    def get_courses_count(self, obj) -> int:
        annotated = getattr(obj, "courses_total", None)
        if annotated is not None:
            return annotated
        return obj.courses.filter(is_published=True).count()


class CourseSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    level_display = serializers.CharField(source="get_level_display", read_only=True)
    rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    url = serializers.HyperlinkedIdentityField(view_name="course-detail", lookup_field="slug")

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "slug",
            "url",
            "category",
            "short_description",
            "description",
            "price",
            "old_price",
            "level",
            "level_display",
            "duration_hours",
            "student_qty",
            "image",
            "rating",
            "reviews_count",
        )

    def get_rating(self, obj) -> float:
        annotated = getattr(obj, "rating_avg", None)
        if annotated is not None:
            return round(annotated, 1) if annotated else 0
        return obj.rating

    def get_reviews_count(self, obj) -> int:
        annotated = getattr(obj, "reviews_total", None)
        if annotated is not None:
            return annotated
        return obj.reviews_count

    def get_image(self, obj) -> str | None:
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = ("id", "user", "rating", "text")


class OrderItemSerializer(serializers.ModelSerializer):
    course_slug = serializers.CharField(source="course.slug", read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "course", "course_slug", "title", "price")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "number",
            "status",
            "status_display",
            "total_price",
            "items",
        )
