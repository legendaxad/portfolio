import json

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Prefetch
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from blog.forms import ContactForm
from blog.github import get_github_summary
from blog.models import (
    BlogCategory, BlogPost, Certificate, JourneyMilestone, PersonalInfo,
    Project, Question, Skill, SkillCategory,
)

SUCCESS_MESSAGE = (
    "Thank you! Your message has been received. I will review it and reply as soon as possible."
)


def _ld(data):
    """Serialize JSON-LD safely for embedding in a <script> tag."""
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")


def _base_url(request):
    return settings.SITE_URL or f"{request.scheme}://{request.get_host()}"


def _person_ld(request, profile):
    base = _base_url(request)
    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": profile.full_name,
        "jobTitle": "Python Backend & Full-Stack Developer",
        "url": base + "/",
        "email": f"mailto:{profile.email}" if profile.email else None,
        "address": {"@type": "PostalAddress", "addressLocality": profile.location},
        "alumniOf": {"@type": "CollegeOrUniversity", "name": profile.education_institution},
        "knowsAbout": [
            "Python", "Django", "Django REST Framework", "FastAPI", "REST APIs", "Node.js",
            "React", "TypeScript", "PostgreSQL", "MongoDB", "Linux", "Nginx", "Information Security",
        ],
        "sameAs": [u for u in (profile.github_url, profile.linkedin_url, profile.telegram_url) if u],
    }
    if profile.avatar:
        data["image"] = base + profile.avatar.url
    return {k: v for k, v in data.items() if v}


def _client_ip(request):
    # Nginx's $proxy_add_x_forwarded_for *appends* the real peer address, so the
    # last entry is the trustworthy one (earlier entries can be client-supplied).
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR")


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _rate_limited(ip):
    key = f"contact:rl:{ip}"
    count = cache.get(key, 0)
    if count >= settings.CONTACT_RATE_LIMIT:
        return True
    cache.set(key, count + 1, 3600)
    return False


def _notify(contact):
    to = settings.CONTACT_NOTIFY_EMAIL
    if not to:
        return
    try:
        send_mail(
            subject=f"[Portfolio] {contact.subject or 'New message'} — {contact.name}",
            message=f"From: {contact.name} <{contact.email}>\n\n{contact.message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to],
            fail_silently=True,
        )
    except Exception:  # never fail the visitor's request because of e-mail
        pass


def _published_projects():
    return (
        Project.objects.filter(is_published=True)
        .prefetch_related(Prefetch("technologies", queryset=Skill.objects.order_by("order")))
    )


def handle_contact(request):
    """Validate + store a contact message. Returns (form, ok, error_text)."""
    form = ContactForm(request.POST)
    if _rate_limited(_client_ip(request)):
        return form, False, "Too many messages from your network. Please try again later or email me directly."
    if form.is_valid():
        contact = form.save(commit=False)
        contact.ip_address = _client_ip(request)
        contact.save()
        _notify(contact)
        return form, True, ""
    return form, False, "There was an error in your submission. Please check the fields and try again."


def index(request):
    form = None
    if request.method == "POST":
        form, ok, error = handle_contact(request)
        if _is_ajax(request):
            if ok:
                return JsonResponse({"ok": True, "message": SUCCESS_MESSAGE})
            return JsonResponse(
                {"ok": False, "message": error, "errors": form.errors.get_json_data()},
                status=429 if "Too many" in error else 400,
            )
        if ok:
            messages.success(request, SUCCESS_MESSAGE)
            return redirect(reverse("home") + "#contact")
        messages.error(request, error)

    projects = _published_projects()
    context = {
        "skill_categories": SkillCategory.objects.prefetch_related("skills"),
        "projects": projects,
        "featured_projects": [p for p in projects if p.is_featured],
        "project_categories": [
            (key, label) for key, label in Project.CATEGORY_CHOICES
            if any(p.category == key for p in projects)
        ],
        "milestones": JourneyMilestone.objects.filter(is_published=True),
        "certificates": Certificate.objects.filter(is_published=True),
        "questions": Question.objects.filter(is_published=True),
        "posts": BlogPost.published.select_related("category")[:3],
        "form": form or ContactForm(),
        "ld": _ld(_person_ld(request, PersonalInfo.get_solo())),
    }
    return render(request, "blog/index.html", context)


def project_detail(request, slug):
    project = get_object_or_404(
        _published_projects().prefetch_related("gallery"), slug=slug
    )
    ordered = list(Project.objects.filter(is_published=True).only("pk", "slug", "title", "accent_color"))
    idx = next((i for i, p in enumerate(ordered) if p.pk == project.pk), 0)
    next_project = ordered[(idx + 1) % len(ordered)] if len(ordered) > 1 else None
    base = _base_url(request)
    ld = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": project.title,
        "description": project.description,
        "url": base + project.get_absolute_url(),
        "keywords": ", ".join(project.get_tech_list()),
        "creator": {"@type": "Person", "name": PersonalInfo.get_solo().full_name},
    }
    if project.github_link:
        ld["codeRepository"] = project.github_link
    if project.image:
        ld["image"] = base + project.image.url
    return render(request, "blog/project_detail.html", {
        "project": project,
        "next_project": next_project,
        "ld": _ld(ld),
    })


def project_detail_legacy(request, pk):
    """Old /project/<pk>/ links keep working via a permanent redirect."""
    project = get_object_or_404(Project, pk=pk, is_published=True)
    return redirect(project.get_absolute_url(), permanent=True)


def post_list(request):
    posts = BlogPost.published.select_related("category")
    active = request.GET.get("category", "")
    if active:
        posts = posts.filter(category__slug=active)
    categories = BlogCategory.objects.filter(
        posts__status=BlogPost.STATUS_PUBLISHED
    ).distinct()
    return render(request, "blog/post_list.html", {
        "posts": posts, "categories": categories, "active_category": active,
    })


def post_detail(request, slug):
    qs = BlogPost.objects.select_related("category")
    if not request.user.is_staff:  # staff can preview drafts
        qs = BlogPost.published.select_related("category")
    post = get_object_or_404(qs, slug=slug)
    related = BlogPost.published.exclude(pk=post.pk)
    if post.category_id:
        related = related.filter(category_id=post.category_id)
    base = _base_url(request)
    ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post.title,
        "description": post.summary,
        "url": base + post.get_absolute_url(),
        "datePublished": post.published_at.isoformat() if post.published_at else None,
        "dateModified": post.updated_at.isoformat(),
        "author": {"@type": "Person", "name": PersonalInfo.get_solo().full_name},
    }
    if post.cover:
        ld["image"] = base + post.cover.url
    return render(request, "blog/post_detail.html", {
        "post": post, "related": related[:3], "ld": _ld({k: v for k, v in ld.items() if v}),
    })


@require_GET
@cache_control(public=True, max_age=600)
def github_api(request):
    profile = PersonalInfo.get_solo()
    data = get_github_summary(profile.github_username)
    return JsonResponse(data, status=200 if data.get("ok") else 503)


@require_GET
def robots_txt(request):
    base = settings.SITE_URL or f"{request.scheme}://{request.get_host()}"
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /api/",
        f"Sitemap: {base}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def page_not_found(request, exception=None):
    return render(request, "404.html", status=404)
