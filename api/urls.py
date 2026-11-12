from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, CourseViewSet, OrderViewSet

router = DefaultRouter()
router.register("courses", CourseViewSet, basename="course")
router.register("categories", CategoryViewSet, basename="category")
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/token/", obtain_auth_token, name="api-token"),
]
