from django.shortcuts import render, redirect

from blog.models import Project, Question, Contact,Certificate


def index(request):
    projects = Project.objects.all()
    questions=Question.objects.all()
    certificates = Certificate.objects.all().order_by('-created_at')

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        Contact.objects.create(
            name=name,
            email=email,
            message=message
        )

        return redirect("home")  # reload page after submit

    context = {
        "projects": projects,
        "questions":questions,
        "certificates":certificates
    }
    return render(request,"blog/index.html",context)

