from django.urls import path

from . import views

app_name = "shop"

urlpatterns = [
    path("", views.CourseListView.as_view(), name="course_list"),
    path("courses/<str:slug>/", views.CourseDetailView.as_view(), name="course_detail"),
    path("courses/<str:slug>/reviews/", views.add_review, name="add_review"),
    path("cart/", views.cart_detail, name="cart"),
    path("cart/add/<int:course_id>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:course_id>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.OrderListView.as_view(), name="order_list"),
    path("orders/<int:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    path("register/", views.register, name="register"),
]
