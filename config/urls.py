from django.contrib import admin
from django.urls import include, path
from tastypie.api import Api

from api.models import CategoryResource, CourseResource

from .views import index

"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
api = Api(api_name="v1")
course_resource = CourseResource()
category_resource = CategoryResource()
api.register(category_resource)
api.register(course_resource)

urlpatterns = [
    path("admin/", admin.site.urls, name="admin"),
    path("shop/", include("shop.urls")),
    path("", index, name="home"),
    path("api/", include(api.urls)),
]
