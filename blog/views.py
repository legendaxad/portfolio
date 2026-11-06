from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from blog.models import (
    PersonalInfo, SkillCategory, Project,
    JourneyMilestone, Certificate, Question, Contact
)
from blog.forms import ContactForm


def index(request):
    profile = PersonalInfo.get_solo()
    skill_categories = SkillCategory.objects.prefetch_related('skills').all()
    projects = Project.objects.filter(is_published=True)
    featured_projects = projects.filter(is_featured=True)
    milestones = JourneyMilestone.objects.filter(is_published=True)
    certificates = Certificate.objects.filter(is_published=True)
    questions = Question.objects.filter(is_published=True)

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Thank you! Your message has been received. I will review it and reply as soon as possible."
            )
            return redirect("home")
        else:
            messages.error(
                request,
                "There was an error in your submission. Please check the fields and try again."
            )
    else:
        form = ContactForm()

    context = {
        "profile": profile,
        "skill_categories": skill_categories,
        "projects": projects,
        "featured_projects": featured_projects,
        "milestones": milestones,
        "certificates": certificates,
        "questions": questions,
        "form": form,
    }
    return render(request, "blog/index.html", context)


def project_detail(request, pk):
    """Fallback detail view for direct project links or deep-linking."""
    project = get_object_or_404(Project, pk=pk, is_published=True)
    profile = PersonalInfo.get_solo()
    return render(request, "blog/project_detail.html", {
        "project": project,
        "profile": profile,
    })
