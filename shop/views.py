from django.shortcuts import get_object_or_404, render

from .models import Category, Course


# Create your views here.
def index(request):
    courses = Course.objects.all()
    title = request.GET.get("title", "")
    category = request.GET.get("category", "")
    if title:
        courses = courses.filter(title=title)
    if category:
        courses = courses.filter(category=category)
    total = courses.count()
    context = {
        "courses": courses,
        "total_courses": total,
        "categories": Category.objects.all(),
        "selected_title": title,
        "selected_category": category,
    }
    return render(request, "shop/courses.html", context)


def single_course(request, course_id):

    course = get_object_or_404(Course, pk=course_id)
    context = {"course": course}
    return render(request, "shop/single_course.html", context)
