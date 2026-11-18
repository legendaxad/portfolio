"""Tests for the portfolio upgrade: slugs, contact API, anti-spam, GitHub proxy,
blog, SEO endpoints, custom 404, admin and the content sync command."""
import json
import time
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import signing
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from blog import github
from blog.forms import TS_SALT, ContactForm
from blog.models import (
    BlogCategory, BlogPost, Contact, JourneyMilestone, PersonalInfo, Project,
    ProjectImage, Skill, SkillCategory,
)
from blog.templatetags.portfolio import rich_text, tech_icon

TEST_CACHE = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


def old_token(seconds_ago=10):
    with mock.patch("blog.forms.time.time", return_value=time.time() - seconds_ago):
        return signing.dumps(int(time.time() - seconds_ago), salt=TS_SALT)


@override_settings(CACHES=TEST_CACHE)
class SlugAndModelTests(TestCase):
    def test_slug_generated_and_unique(self):
        a = Project.objects.create(title="My API", description="x")
        b = Project.objects.create(title="My API", description="y")
        self.assertEqual(a.slug, "my-api")
        self.assertEqual(b.slug, "my-api-2")
        self.assertEqual(a.get_absolute_url(), "/projects/my-api/")

    def test_slug_not_changed_on_title_edit(self):
        p = Project.objects.create(title="Original", description="x")
        p.title = "Renamed"
        p.save()
        self.assertEqual(p.slug, "original")

    def test_linked_technologies_take_priority(self):
        cat = SkillCategory.objects.create(name="Backend")
        dj = Skill.objects.create(category=cat, name="Django")
        p = Project.objects.create(title="P", description="x", tech_stack="Flask, Redis")
        self.assertEqual(p.get_tech_list(), ["Flask", "Redis"])
        p.technologies.add(dj)
        self.assertEqual(p.get_tech_list(), ["Django"])

    def test_mojibake_bullet_is_split(self):
        p = Project(title="P", description="x", tech_stack="Node.js â€¢ TypeScript")
        self.assertEqual(p.get_tech_list(), ["Node.js", "TypeScript"])

    def test_initials(self):
        self.assertEqual(Project(title="MultiShop — Django").initials, "MS")
        self.assertEqual(Project(title="Camper Booking").initials, "CB")
        self.assertEqual(Project(title="BURAK — Restaurant").initials, "BR")

    def test_accent_default_and_validation(self):
        from django.core.exceptions import ValidationError
        p = Project(title="P", description="x")
        self.assertEqual(p.accent, "#4D7CFF")
        p.accent_color = "blue"
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_hero_title_highlight_parts(self):
        info = PersonalInfo(hero_title="Build *great things* daily")
        self.assertEqual(info.hero_title_parts, ("Build ", "great things", " daily"))
        info.hero_title = "No highlight"
        self.assertEqual(info.hero_title_parts, ("No highlight", "", ""))


@override_settings(CACHES=TEST_CACHE)
class PageTests(TestCase):
    def setUp(self):
        cache.clear()
        self.cat = SkillCategory.objects.create(name="Backend Engineering", is_primary=True)
        Skill.objects.create(category=self.cat, name="Django", icon="django", is_core=True)
        self.p1 = Project.objects.create(title="Alpha", description="A", is_featured=True, order=1,
                                         full_description="## Heading\nSee https://example.com", accent_color="#112233")
        self.p2 = Project.objects.create(title="Beta", description="B", order=2, category="automation")
        ProjectImage.objects.create(project=self.p1, image="projects/x.jpg", caption="Screen")
        JourneyMilestone.objects.create(period="2022", title="Uni", description="d", kind="education")

    def test_home_renders_all_sections(self):
        r = self.client.get(reverse("home"))
        self.assertEqual(r.status_code, 200)
        for anchor in ['id="about"', 'id="stack"', 'id="work"', 'id="engineering"', 'id="journey"',
                       'id="github"', 'id="contact"', 'data-shader']:
            self.assertContains(r, anchor)
        self.assertContains(r, "Primary focus")
        self.assertContains(r, "No articles published yet")  # honest empty state
        self.assertEqual([p.title for p in r.context["featured_projects"]], ["Alpha"])
        # Only categories that actually have projects get a filter button
        self.assertEqual([k for k, _ in r.context["project_categories"]], ["backend", "automation"])

    def test_json_ld_is_valid_json(self):
        r = self.client.get(reverse("home"))
        data = json.loads(r.context["ld"])
        self.assertEqual(data["@type"], "Person")

    def test_project_detail_by_slug(self):
        r = self.client.get(self.p1.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "<h2>Heading</h2>", html=True)
        self.assertContains(r, 'href="https://example.com"')
        self.assertContains(r, "Gallery")
        self.assertEqual(r.context["next_project"], self.p2)
        self.assertEqual(json.loads(r.context["ld"])["name"], "Alpha")

    def test_missing_cover_uses_placeholder_not_broken_image(self):
        r = self.client.get(reverse("home"))
        self.assertContains(r, "pvis--gen")

    def test_robots_and_sitemap(self):
        r = self.client.get("/robots.txt")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Sitemap: http://testserver/sitemap.xml", r.content.decode())
        r = self.client.get("/sitemap.xml")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "/projects/alpha/")

    @override_settings(SITE_URL="https://legendaxad.org")
    def test_canonical_uses_site_url(self):
        r = self.client.get(reverse("home"))
        self.assertContains(r, '<link rel="canonical" href="https://legendaxad.org/">')

    @override_settings(DEBUG=False)
    def test_custom_404(self):
        r = self.client.get("/definitely-missing/")
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "This route doesn't resolve", status_code=404)


@override_settings(CACHES=TEST_CACHE)
class ContactApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.valid = {"name": "Jane Recruiter", "email": "jane@example.com",
                      "subject": "Role", "message": "We would like to talk about a backend role."}

    def test_ajax_success_returns_json_and_stores_ip(self):
        r = self.client.post(reverse("home"), {**self.valid, "ts": old_token()}, **AJAX)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["ok"])
        c = Contact.objects.get(email="jane@example.com")
        self.assertEqual(c.ip_address, "127.0.0.1")

    def test_ajax_validation_errors(self):
        r = self.client.post(reverse("home"), {"name": "", "email": "bad", "message": "short"}, **AJAX)
        self.assertEqual(r.status_code, 400)
        errors = r.json()["errors"]
        self.assertIn("email", errors)
        self.assertIn("message", errors)
        self.assertFalse(Contact.objects.exists())

    def test_too_fast_submission_rejected(self):
        token = signing.dumps(int(time.time()), salt=TS_SALT)
        form = ContactForm(data={**self.valid, "ts": token})
        self.assertFalse(form.is_valid())
        self.assertIn("too quickly", str(form.errors))

    def test_tampered_token_rejected(self):
        form = ContactForm(data={**self.valid, "ts": "forged:token"})
        self.assertFalse(form.is_valid())

    def test_too_many_links_rejected(self):
        msg = "http://a http://b http://c http://d buy now"
        form = ContactForm(data={**self.valid, "message": msg})
        self.assertFalse(form.is_valid())

    def test_honeypot_via_view(self):
        r = self.client.post(reverse("home"), {**self.valid, "honeypot": "x"}, **AJAX)
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Contact.objects.exists())

    @override_settings(CONTACT_RATE_LIMIT=2)
    def test_rate_limit(self):
        for _ in range(2):
            self.assertEqual(self.client.post(reverse("home"), self.valid, **AJAX).status_code, 200)
        r = self.client.post(reverse("home"), self.valid, **AJAX)
        self.assertEqual(r.status_code, 429)
        self.assertEqual(Contact.objects.count(), 2)

    def test_non_js_post_redirects_with_message(self):
        r = self.client.post(reverse("home"), self.valid, follow=True)
        self.assertRedirects(r, reverse("home") + "#contact")
        self.assertContains(r, "Thank you! Your message has been received.")

    @override_settings(CONTACT_NOTIFY_EMAIL="me@example.com",
                       EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_notification_email(self):
        from django.core import mail
        self.client.post(reverse("home"), self.valid, **AJAX)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Jane Recruiter", mail.outbox[0].subject)


USER = {"login": "dev", "name": "Dev", "avatar_url": "https://x/a.png?v=4", "html_url": "https://github.com/dev",
        "public_repos": 3, "followers": 1, "following": 0, "created_at": "2020-01-01T00:00:00Z"}
REPOS = [
    {"name": "a", "language": "Python", "fork": False, "html_url": "u", "stargazers_count": 2, "pushed_at": "2026-01-02"},
    {"name": "b", "language": "Python", "fork": False, "html_url": "u", "stargazers_count": 0, "pushed_at": "2026-03-01"},
    {"name": "c", "language": "TypeScript", "fork": False, "html_url": "u", "stargazers_count": 1, "pushed_at": "2025-01-01"},
    {"name": "forked", "language": "Go", "fork": True, "html_url": "u", "stargazers_count": 99, "pushed_at": "2026-05-01"},
]


@override_settings(CACHES=TEST_CACHE)
class GitHubProxyTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_summarize_ignores_forks(self):
        d = github.summarize(USER, REPOS)
        self.assertEqual(d["languages"], [{"name": "Python", "count": 2}, {"name": "TypeScript", "count": 1}])
        self.assertEqual(d["total_stars"], 3)
        self.assertEqual(d["repos"][0]["name"], "b")  # most recently pushed first
        self.assertNotIn("forked", [r["name"] for r in d["repos"]])

    def test_endpoint_success_and_cache(self):
        with mock.patch("blog.github._get", side_effect=[USER, REPOS]) as m:
            r1 = self.client.get(reverse("github_api"))
            r2 = self.client.get(reverse("github_api"))
        self.assertEqual(r1.status_code, 200)
        self.assertTrue(r1.json()["ok"])
        self.assertEqual(r2.json(), r1.json())
        self.assertEqual(m.call_count, 2)  # second request served from cache

    def test_endpoint_failure_returns_503(self):
        import urllib.error
        with mock.patch("blog.github._get", side_effect=urllib.error.URLError("down")):
            r = self.client.get(reverse("github_api"))
        self.assertEqual(r.status_code, 503)
        self.assertFalse(r.json()["ok"])

    def test_stale_copy_served_when_github_down(self):
        import urllib.error
        with mock.patch("blog.github._get", side_effect=[USER, REPOS]):
            github.get_github_summary("legendaxad")
        cache.delete("gh:summary:legendaxad")
        with mock.patch("blog.github._get", side_effect=urllib.error.URLError("down")):
            d = github.get_github_summary("legendaxad")
        self.assertTrue(d["ok"])
        self.assertTrue(d["stale"])

    def test_token_never_exposed(self):
        with override_settings(GITHUB_TOKEN="secret-token"), \
                mock.patch("blog.github._get", side_effect=[USER, REPOS]):
            r = self.client.get(reverse("github_api"))
        self.assertNotIn("secret-token", r.content.decode())


@override_settings(CACHES=TEST_CACHE)
class BlogTests(TestCase):
    def setUp(self):
        self.cat = BlogCategory.objects.create(name="Django")
        self.pub = BlogPost.objects.create(title="Hello Django", category=self.cat, body="word " * 450,
                                           status=BlogPost.STATUS_PUBLISHED)
        self.draft = BlogPost.objects.create(title="Secret draft", body="wip")

    def test_published_at_set_automatically(self):
        self.assertIsNotNone(self.pub.published_at)
        self.assertIsNone(self.draft.published_at)

    def test_reading_time(self):
        self.assertEqual(self.pub.reading_time, 3)

    def test_list_shows_only_published(self):
        r = self.client.get(reverse("post_list"))
        self.assertContains(r, "Hello Django")
        self.assertNotContains(r, "Secret draft")

    def test_category_filter(self):
        other = BlogCategory.objects.create(name="Linux")
        BlogPost.objects.create(title="Linux post", category=other, body="x", status="published")
        r = self.client.get(reverse("post_list") + "?category=linux")
        self.assertContains(r, "Linux post")
        self.assertNotContains(r, "Hello Django")

    def test_draft_404_for_public_but_visible_for_staff(self):
        self.assertEqual(self.client.get(self.draft.get_absolute_url()).status_code, 404)
        staff = get_user_model().objects.create_user("s", password="x", is_staff=True)
        self.client.force_login(staff)
        r = self.client.get(self.draft.get_absolute_url())
        self.assertContains(r, "Draft preview")

    def test_future_post_hidden(self):
        BlogPost.objects.create(title="Future", body="x", status="published",
                                published_at=timezone.now() + timezone.timedelta(days=3))
        self.assertNotContains(self.client.get(reverse("post_list")), "Future")

    def test_related_posts(self):
        rel = BlogPost.objects.create(title="Related one", category=self.cat, body="x", status="published")
        r = self.client.get(self.pub.get_absolute_url())
        self.assertIn(rel, list(r.context["related"]))

    def test_empty_state(self):
        BlogPost.objects.all().delete()
        self.assertContains(self.client.get(reverse("post_list")), "No articles published yet")


class TemplateTagTests(TestCase):
    def test_rich_text_escapes_html(self):
        out = rich_text("<script>alert(1)</script>\n\n## Title\n- item https://x.io\n```\n<b>code</b>\n```")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertIn("<h2>Title</h2>", out)
        self.assertIn('<a href="https://x.io" rel="nofollow">', out)
        self.assertIn("<pre><code>&lt;b&gt;code&lt;/b&gt;</code></pre>", out)

    def test_tech_icon_known_and_fallback(self):
        self.assertIn("icons/tech/django.svg", tech_icon("Django REST Framework"))
        self.assertIn("ti--mono", tech_icon("Chart.js"))


@override_settings(CACHES=TEST_CACHE)
class AdminTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.client.force_login(get_user_model().objects.create_superuser("a", "a@x.io", "pw"))

    def test_new_admin_pages_load(self):
        p = Project.objects.create(title="P", description="x")
        BlogPost.objects.create(title="T", body="b")
        for name in ["admin:blog_blogpost_changelist", "admin:blog_blogcategory_changelist",
                     "admin:blog_blogpost_add", "admin:blog_project_add"]:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertEqual(self.client.get(reverse("admin:blog_project_change", args=[p.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:blog_personalinfo_change", args=[PersonalInfo.get_solo().pk])).status_code, 200)

    def test_publish_action(self):
        post = BlogPost.objects.create(title="T", body="b")
        self.client.post(reverse("admin:blog_blogpost_changelist"),
                         {"action": "make_published", "_selected_action": [post.pk]})
        post.refresh_from_db()
        self.assertEqual(post.status, "published")
        self.assertIsNotNone(post.published_at)

    def test_profile_cannot_be_deleted(self):
        info = PersonalInfo.get_solo()
        r = self.client.get(reverse("admin:blog_personalinfo_delete", args=[info.pk]))
        self.assertEqual(r.status_code, 403)


class SyncCommandTests(TestCase):
    def setUp(self):
        self.info = PersonalInfo.get_solo()
        self.info.github_url = "https://github.com/akhadjon"
        self.info.save()
        for name in ["Backend Engineering", "Frontend Development", "Databases & Storage", "Tools, Systems & Security"]:
            SkillCategory.objects.create(name=name)
        Project.objects.create(title="MultiShop (Python Backend)", slug="multishop-python-backend",
                               description="old", project_link="https://custom.example")

    def test_dry_run_changes_nothing(self):
        call_command("sync_portfolio_content", "--dry-run", stdout=StringIO())
        self.assertFalse(Project.objects.filter(slug="social-media-downloader").exists())
        self.info.refresh_from_db()
        self.assertIn("akhadjon", self.info.github_url)

    def test_apply_is_idempotent_and_preserves_links(self):
        call_command("sync_portfolio_content", stdout=StringIO())
        call_command("sync_portfolio_content", stdout=StringIO())
        self.assertEqual(Project.objects.filter(slug="social-media-downloader").count(), 1)
        ms = Project.objects.get(slug="multishop-python-backend")
        self.assertEqual(ms.project_link, "https://custom.example")  # never overwritten
        self.assertIn("Gunicorn", ms.tech_stack)
        self.assertTrue(SkillCategory.objects.get(name="Backend Engineering").is_primary)
        self.assertTrue(SkillCategory.objects.filter(name="Infrastructure & Tools").exists())
        self.assertEqual(Skill.objects.filter(name="Nginx").count(), 1)
        self.info.refresh_from_db()
        self.assertEqual(self.info.github_url, "https://github.com/legendaxad")
        self.assertEqual(BlogPost.objects.count(), 0)  # never invents articles
