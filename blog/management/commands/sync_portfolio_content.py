"""Idempotent content refresh for the portfolio.

Every fact here was verified against the owner's repositories (Nov 2026):
package.json / requirements files, source code and the public GitHub API.
Nothing is deleted. Records are matched by slug/name; existing links and
images are never overwritten, only filled in when empty.

    python manage.py sync_portfolio_content            # apply
    python manage.py sync_portfolio_content --dry-run  # preview only
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from blog.models import (
    BlogCategory, JourneyMilestone, PersonalInfo, Project, Skill, SkillCategory,
)

GH = "https://github.com/legendaxad"

PROFILE = {
    "hero_title": "Engineering the systems behind *great digital experiences.*",
    "hero_subtitle": (
        "Python Backend & Full-Stack Developer building scalable applications, "
        "intelligent tools, and reliable digital products."
    ),
    "subheadline": (
        "Python Backend & Full-Stack Developer and Information Security student at Dongshin "
        "University, South Korea. I build Django and Node.js backends, REST APIs and the "
        "React interfaces that use them — and deploy them on Linux."
    ),
    "bio_journey": (
        "I started on the frontend with React and TypeScript, which taught me how much of a product "
        "depends on what happens behind the interface. That curiosity pulled me into Node.js, Express "
        "and MongoDB, and then into Python, where Django and REST APIs became my main tools. Deploying "
        "my own projects on Linux servers with Gunicorn and Nginx showed me the rest of the lifecycle — "
        "and that is the direction I'm growing in: backend engineering with a solid grasp of "
        "infrastructure and security."
    ),
}

CATEGORY_UPDATES = {
    "Backend Engineering": {"is_primary": True, "description": "APIs, business logic, authentication"},
    "Frontend Development": {"description": "Interfaces that consume my APIs"},
    "Databases & Storage": {"description": "Relational and document data"},
    "Tools, Systems & Security": {
        "name": "Infrastructure & Tools", "description": "Shipping, running and securing software",
    },
}

# name -> (category name, icon, is_core)
SKILL_ICONS = {
    "Python": "python", "Django": "django", "FastAPI": "fastapi", "REST APIs": "swagger",
    "Node.js": "nodedotjs", "Express.js": "express", "JWT Authentication": "jsonwebtokens",
    "TypeScript": "typescript", "React": "react", "JavaScript (ES6+)": "javascript",
    "HTML5 & CSS3": "html5", "Material UI": "mui", "PostgreSQL": "postgresql",
    "MongoDB": "mongodb", "SQLite": "sqlite", "Git & GitHub": "github",
    "Linux & Shell Scripting": "linux", "Docker (Project Supported)": "docker",
}
NEW_SKILLS = [
    ("Django REST Framework", "Backend Engineering", "django", True, 3),
    ("Redis", "Databases & Storage", "redis", False, 4),
    ("Nginx", "Infrastructure & Tools", "nginx", True, 4),
    ("Gunicorn", "Infrastructure & Tools", "gunicorn", False, 4),
    ("Stripe", "Infrastructure & Tools", "stripe", False, 6),
]

PROJECTS = [
    {
        "slug": "testbridge-ielts-topik-testing-platform",
        "order": 1, "is_featured": True, "status": "in_progress", "accent_color": "#34D3B4",
        "category": "backend",
        "description": (
            "Django platform for IELTS and TOPIK practice exams — timed sections, answer autosave, "
            "and AI-assisted feedback on speaking and writing."
        ),
        "tech_stack": "Python, Django, OpenAI API, JavaScript, Chart.js, SQLite",
        "architecture_notes": (
            "Separate Django apps for accounts, IELTS and TOPIK exam engines\n"
            "Exam attempts, sections, materials and answers modelled relationally with event logs\n"
            "Synchronized countdown timer with automatic answer saving\n"
            "Speaking answers transcribed and scored through the OpenAI API (fluency, grammar, vocabulary)\n"
            "Subscription plans with daily AI-evaluation and test usage limits"
        ),
        "full_description": (
            "TestBridge is an exam-preparation platform for IELTS and TOPIK (I & II) that I'm building "
            "with Django. The goal is to reproduce the real exam experience — fixed timing, section "
            "order, and instant feedback — rather than a simple quiz app.\n\n"
            "## Backend design\n"
            "The project is split into Django apps for accounts, IELTS and TOPIK. TOPIK exams are "
            "modelled as exams → sections → materials → questions → choices, with attempts, answers and "
            "an event log per attempt so progress can be restored and analysed.\n\n"
            "## AI-assisted evaluation\n"
            "Recorded speaking answers are transcribed and then scored through the OpenAI API on "
            "fluency, grammar, vocabulary, pronunciation and task completion. Writing submissions have "
            "a similar scoring service. Scores are clamped and validated server-side before being "
            "stored.\n\n"
            "## Access control\n"
            "Users get a subscription plan (Free / Standard / Pro) with daily limits on AI evaluations "
            "and tests, reset automatically each day.\n\n"
            "## Status\n"
            "Actively in development — the TOPIK section and speaking features are the current focus."
        ),
    },
    {
        "slug": "multishop-python-backend",
        "title": "MultiShop — Django E-commerce Platform",
        "order": 2, "is_featured": True, "accent_color": "#4D7CFF", "category": "backend",
        "project_link": "https://legendaxad.org", "github_link": f"{GH}/multishop",
        "description": (
            "A deployed Django e-commerce store with a custom user model, cart and checkout, Stripe "
            "test-mode payments, served by Gunicorn behind Nginx over HTTPS."
        ),
        "tech_stack": "Python, Django, SQLite, Stripe, Nginx, Gunicorn, DigitalOcean",
        "architecture_notes": (
            "Modular Django apps for products, orders and authentication\n"
            "Custom user model with registration and login flows\n"
            "Session-backed shopping cart and order workflow\n"
            "Stripe payment integration in test mode\n"
            "Deployed on a DigitalOcean Linux server: Gunicorn + Nginx reverse proxy with HTTPS"
        ),
        "full_description": (
            "MultiShop is the project where I took a Django application all the way from models to a "
            "live server.\n\n"
            "## Application\n"
            "The store is organised into separate Django apps for the catalogue, orders and "
            "authentication, with a custom user model. Products are browsed by category, added to a "
            "session-backed cart and turned into orders. Payments go through Stripe in test mode.\n\n"
            "## Deployment\n"
            "I deployed it myself on a DigitalOcean Linux server: Gunicorn runs the Django app, Nginx "
            "sits in front as a reverse proxy and serves static files, and the site is served over "
            "HTTPS on its own domain. Configuring that stack — services, permissions, static files and "
            "certificates — taught me as much as writing the application."
        ),
    },
    {
        "slug": "burak-restaurant-system",
        "title": "BURAK — Restaurant Management Ecosystem",
        "order": 3, "is_featured": True, "accent_color": "#F2A541", "category": "fullstack",
        "github_link": f"{GH}/burak",
        "description": (
            "A restaurant ecosystem in progress: a Node.js/TypeScript backend with a server-rendered "
            "admin, a React web client, and React Native apps for staff and customers."
        ),
        "tech_stack": "TypeScript, Node.js, Express, MongoDB, React, React Native (Expo), Redux Toolkit",
        "architecture_notes": (
            "Express + TypeScript backend with MongoDB (Mongoose) models\n"
            "Server-rendered admin panel (EJS) with session-based authentication\n"
            "REST API shared by the web and mobile clients, JWT for client auth\n"
            "React web client with Redux Toolkit, React Native (Expo) apps for admin and customer"
        ),
        "full_description": (
            "BURAK is a multi-client restaurant system I'm building to practise designing one backend "
            "for several frontends.\n\n"
            "## Pieces\n"
            "- Backend: Node.js, Express and TypeScript with MongoDB — https://github.com/legendaxad/burak\n"
            "- Web client: React + TypeScript + Redux Toolkit — https://github.com/legendaxad/burak-react\n"
            "- Admin mobile app: React Native (Expo) — https://github.com/legendaxad/burak-app\n"
            "- Customer mobile app: React Native (Expo) — https://github.com/legendaxad/burak-client-app\n\n"
            "## Status\n"
            "In active development. The backend and admin panel are the most complete parts; the "
            "mobile clients are being built out."
        ),
    },
    {
        "slug": "social-media-downloader",
        "create": {"title": "Social Media Downloader Bot"},
        "order": 4, "is_featured": True, "status": "in_progress", "accent_color": "#26A5E4",
        "category": "automation", "github_link": f"{GH}/downloader_bot",
        "description": (
            "A Python Telegram bot that downloads videos from supported social platforms, processes "
            "them with FFmpeg, and sends them back to the user."
        ),
        "tech_stack": "Python, python-telegram-bot, yt-dlp, FFmpeg, Redis",
        "architecture_notes": (
            "Async handlers built on python-telegram-bot\n"
            "Media extraction with yt-dlp and post-processing through FFmpeg\n"
            "Redis-backed job handling with a separate worker process\n"
            "Structured services/handlers/utils layout with logging and error handling"
        ),
        "full_description": (
            "A Telegram bot that takes a link from a supported social platform, downloads the media "
            "with yt-dlp, processes it with FFmpeg where needed, and sends the file back in the chat.\n\n"
            "## Engineering\n"
            "Downloads are slow and can fail, so the bot separates the chat handlers from the work: "
            "jobs go through Redis to a worker process, and the code is split into handlers, services "
            "and utilities. Errors from unsupported links or failed downloads are caught and reported "
            "to the user instead of crashing the bot."
        ),
    },
    {
        "slug": "camper-booking-platform",
        "order": 5, "accent_color": "#7BC67B", "category": "fullstack",
        "description": (
            "Full-stack camper rental and booking app — a React frontend talking to an Express and "
            "MongoDB REST API with authentication and image uploads."
        ),
        "tech_stack": "React, JavaScript, Material UI, Node.js, Express, MongoDB, JWT, AWS S3",
        "architecture_notes": (
            "Express REST API with MongoDB (Mongoose) models\n"
            "JWT authentication with bcrypt-hashed passwords and request validation\n"
            "Image uploads processed with Sharp and stored on AWS S3\n"
            "React + Material UI frontend for browsing and booking"
        ),
    },
    {
        "slug": "clicon-electronics",
        "order": 6, "accent_color": "#FA8232", "category": "frontend",
        "github_link": f"{GH}/cliconweb",
        "description": (
            "Electronics e-commerce frontend with a product catalogue, filtering, cart and "
            "animated, responsive UI."
        ),
        "tech_stack": "React, TypeScript, Material UI, Mantine, Framer Motion",
        "architecture_notes": (
            "Typed React components and routing with React Router\n"
            "Product catalogue with category and specification filters\n"
            "Shopping cart state handling\n"
            "Responsive layout with Material UI / Mantine and Framer Motion animations"
        ),
    },
    {
        "slug": "telegram-automation-bots",
        "title": "Telegram Bots — Translator, Prayer Times & Quotes",
        "order": 7, "accent_color": "#5AC8FA", "category": "automation",
        "github_link": f"{GH}?tab=repositories&q=bot",
        "description": "Small Python Telegram bots: a translator, a prayer-time bot and a quotes bot.",
        "tech_stack": "Python, Telegram Bot API, REST APIs",
        "full_description": (
            "A set of smaller bots I built while learning Python automation and API integration.\n\n"
            "- Translator bot — https://github.com/legendaxad/translator_bot\n"
            "- Prayer time bot — https://github.com/legendaxad/praytimebot\n"
            "- Quotes bot — https://github.com/legendaxad/quotes_bot\n\n"
            "Each bot handles commands and messages through the Telegram Bot API and calls an "
            "external API for its data."
        ),
    },
    {
        "slug": "real-time-messaging-app",
        "title": "Messaging App with Sendbird",
        "order": 8, "accent_color": "#A78BFA", "category": "fullstack",
        "description": (
            "Chat web app built on the Sendbird UI Kit with a React/TypeScript frontend and an Express "
            "backend that manages users."
        ),
        "tech_stack": "React, TypeScript, Sendbird UIKit, Node.js, Express, MongoDB, JWT",
        "architecture_notes": (
            "React + TypeScript frontend using the Sendbird UIKit for channels and messages\n"
            "Express backend with MongoDB for user records\n"
            "JWT-based authentication between client and server"
        ),
    },
    {"slug": "information-security", "order": 9, "accent_color": "#EF6F6C"},
]

MILESTONES = [
    # match title -> updates
    ("Information Security Undergraduate Studies", {"kind": "education", "order": 1}),
    ("Frontend & Full-Stack Engineering", {"kind": "projects", "order": 2}),
    ("Python Backend & Full-Stack Development", {"kind": "projects", "order": 3}),
]
NEW_MILESTONES = [
    {
        "title": "Deployment & Linux Infrastructure", "period": "Ongoing", "kind": "learning",
        "organization_or_tag": "Linux · Nginx · Gunicorn · HTTPS", "order": 4,
        "description": (
            "Deploying my own Django projects on a Linux server — Gunicorn behind Nginx, HTTPS, "
            "services and permissions — and learning server administration, networking and firewall "
            "configuration along the way."
        ),
    },
    {
        "title": "Current Direction: Backend Engineering & DevOps", "period": "Now", "kind": "learning",
        "organization_or_tag": "Backend · Security · DevOps", "order": 5,
        "description": (
            "Deepening backend architecture, PostgreSQL, Docker and production practices, and "
            "connecting them with what I study in information security."
        ),
    },
]

BLOG_CATEGORIES = [
    "Python", "Django", "Backend Architecture", "REST APIs", "TypeScript", "React",
    "Linux", "Deployment", "Cybersecurity", "Lessons Learned",
]


class Command(BaseCommand):
    help = "Refresh portfolio content with verified project data (idempotent, non-destructive)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def log(self, msg):
        self.stdout.write(msg)

    @transaction.atomic
    def handle(self, *args, dry_run=False, **opts):
        self.apply()
        if dry_run:
            transaction.set_rollback(True)
            self.log(self.style.WARNING("Dry run — nothing saved."))
        else:
            self.log(self.style.SUCCESS("Portfolio content synced."))

    def apply(self):
        p = PersonalInfo.get_solo()
        if not p.github_url or "github.com/akhadjon" in p.github_url:
            p.github_url = GH
            self.log("profile: github_url -> legendaxad")
        p.github_username = p.github_username or "legendaxad"
        for k, v in PROFILE.items():
            if k == "subheadline" or not getattr(p, k) or getattr(p, k) == p._meta.get_field(k).default:
                setattr(p, k, v)
        p.save()

        cats = {}
        for name, upd in CATEGORY_UPDATES.items():
            cat = SkillCategory.objects.filter(name=name).first() or \
                SkillCategory.objects.filter(name=upd.get("name", name)).first()
            if not cat:
                cat = SkillCategory.objects.create(name=upd.get("name", name), order=len(cats) + 1)
            for k, v in upd.items():
                setattr(cat, k, v)
            cat.save()
            cats[name] = cats[cat.name] = cat
            self.log(f"category: {cat.name}")

        for name, icon in SKILL_ICONS.items():
            Skill.objects.filter(name=name, icon="").update(icon=icon)
        for name, cat_name, icon, core, order in NEW_SKILLS:
            _, created = Skill.objects.get_or_create(
                name=name, defaults={"category": cats[cat_name], "icon": icon, "is_core": core, "order": order},
            )
            if created:
                self.log(f"skill: + {name}")

        for spec in PROJECTS:
            spec = dict(spec)
            slug, create = spec.pop("slug"), spec.pop("create", None)
            project = Project.objects.filter(slug=slug).first()
            if not project:
                if not create:
                    self.log(self.style.WARNING(f"project '{slug}' not found — skipped"))
                    continue
                project = Project(slug=slug, **create)
                self.log(f"project: + {create['title']}")
            for field in ("project_link", "github_link"):
                if field in spec and getattr(project, field):
                    spec.pop(field)  # never overwrite a link set in admin
            for k, v in spec.items():
                setattr(project, k, v)
            project.save()
            self.log(f"project: ~ {project.title}")

        for title, upd in MILESTONES:
            JourneyMilestone.objects.filter(title=title).update(**upd)
        for m in NEW_MILESTONES:
            _, created = JourneyMilestone.objects.get_or_create(title=m["title"], defaults=m)
            if created:
                self.log(f"milestone: + {m['title']}")

        for i, name in enumerate(BLOG_CATEGORIES):
            BlogCategory.objects.get_or_create(name=name, defaults={"order": i})
