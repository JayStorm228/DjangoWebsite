from django.shortcuts import render

from .models import Course


# Create your views here.
def index(request):
    courses = Course.objects.all()
    context = {"courses": courses}
    return render(request, "shop/courses.html", context)
