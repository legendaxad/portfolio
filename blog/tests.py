from django.test import TestCase, Client
from django.urls import reverse
from django.contrib import admin
from django.contrib.auth import get_user_model
from blog.models import (
    PersonalInfo, SkillCategory, Skill, Project,
    JourneyMilestone, Certificate, Question, Contact
)
from blog.forms import ContactForm


class PortfolioModelTests(TestCase):
    def setUp(self):
        self.profile = PersonalInfo.get_solo()
        self.cat = SkillCategory.objects.create(name="Backend Engineering", order=1)
        self.skill = Skill.objects.create(
            category=self.cat, name="Python", is_core=True, order=1
        )
        self.project_pub = Project.objects.create(
            title="TestBridge Platform",
            description="Educational assessment engine",
            tech_stack="Python, Django, Chart.js",
            architecture_notes="Auto-save mechanism\nAI speaking scoring",
            status="completed",
            category="backend",
            is_featured=True,
            is_published=True,
            order=1
        )
        self.project_unpub = Project.objects.create(
            title="Draft Project",
            description="Testing unpublished status",
            tech_stack="Test",
            is_published=False,
            order=99
        )
        self.question = Question.objects.create(
            quest="What is your focus?",
            answer="Python Backend Engineering",
            order=1,
            is_published=True
        )
        self.cert = Certificate.objects.create(
            title="PROWEB Certified",
            given_by="PROWEB",
            year="2024",
            description="Web Development",
            order=1,
            is_published=True
        )
        self.milestone = JourneyMilestone.objects.create(
            period="2024 - Present",
            title="Python Backend & Full-Stack Development",
            description="Building scalable backend systems",
            order=1,
            is_published=True
        )

    def test_personal_info_singleton(self):
        p1 = PersonalInfo.get_solo()
        p2 = PersonalInfo.get_solo()
        self.assertEqual(p1.pk, p2.pk)
        self.assertEqual(PersonalInfo.objects.count(), 1)

    def test_project_helpers(self):
        self.assertEqual(
            self.project_pub.get_tech_list(),
            ["Python", "Django", "Chart.js"]
        )
        self.assertEqual(
            self.project_pub.get_highlights_list(),
            ["Auto-save mechanism", "AI speaking scoring"]
        )

    def test_certificate_issuer_property(self):
        self.assertEqual(self.cert.issuer, "PROWEB")

    def test_question_property(self):
        self.assertEqual(self.question.question, "What is your focus?")

    def test_milestone_str(self):
        self.assertIn("2024 - Present", str(self.milestone))


class ContactFormTests(TestCase):
    def test_valid_contact_form(self):
        data = {
            'name': 'Senior Engineer',
            'email': 'recruiter@techcorp.com',
            'subject': 'Backend Role',
            'message': 'We are interested in your Python & Django expertise.'
        }
        form = ContactForm(data=data)
        self.assertTrue(form.is_valid())
        contact = form.save()
        self.assertEqual(contact.name, 'Senior Engineer')
        self.assertEqual(contact.subject, 'Backend Role')
        self.assertFalse(contact.is_read)

    def test_honeypot_spam_rejection(self):
        data = {
            'name': 'Spambot',
            'email': 'bot@spam.com',
            'subject': 'Spam Subject',
            'message': 'Buy cheap backlinks',
            'honeypot': 'http://spamsite.com'
        }
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_missing_required_fields(self):
        data = {
            'name': '',
            'email': 'invalid-email',
            'message': ''
        }
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('message', form.errors)


class PortfolioViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.profile = PersonalInfo.get_solo()
        self.cat = SkillCategory.objects.create(name="Backend Engineering", order=1)
        self.skill = Skill.objects.create(
            category=self.cat, name="Python", is_core=True, order=1
        )
        self.project = Project.objects.create(
            title="MultiShop",
            description="E-commerce backend",
            tech_stack="Python, Django",
            category="backend",
            status="completed",
            is_published=True,
            order=1
        )
        self.unpub_project = Project.objects.create(
            title="Hidden Draft",
            description="Hidden",
            tech_stack="None",
            is_published=False,
            order=2
        )

    def test_index_view_get(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("profile", response.context)
        self.assertIn("skill_categories", response.context)
        self.assertIn("projects", response.context)
        self.assertIn("form", response.context)
        # Verify unpublished project is excluded
        project_titles = [p.title for p in response.context["projects"]]
        self.assertIn("MultiShop", project_titles)
        self.assertNotIn("Hidden Draft", project_titles)
        self.assertContains(response, "MultiShop")

    def test_index_view_post_success(self):
        data = {
            'name': 'Tech Lead',
            'email': 'lead@company.com',
            'subject': 'Django System Consultation',
            'message': 'Let us discuss our backend architecture.'
        }
        response = self.client.post(reverse("home"), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Contact.objects.filter(email='lead@company.com').exists())
        self.assertContains(response, "Thank you! Your message has been received.")

    def test_project_detail_view(self):
        response = self.client.get(reverse("project_detail", kwargs={"pk": self.project.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MultiShop")
        self.assertContains(response, "Primary Stack")

    def test_unpublished_project_detail_404(self):
        response = self.client.get(reverse("project_detail", kwargs={"pk": self.unpub_project.pk}))
        self.assertEqual(response.status_code, 404)


class DjangoAdminConfigurationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(
            username='admin_tester',
            email='admin@test.com',
            password='Password123!'
        )
        self.client = Client()
        self.client.force_login(self.admin_user)

    def test_models_registered_in_admin(self):
        models = [
            PersonalInfo, SkillCategory, Skill, Project,
            JourneyMilestone, Certificate, Question, Contact
        ]
        for model in models:
            self.assertTrue(
                admin.site.is_registered(model),
                f"{model.__name__} is not registered in admin site"
            )

    def test_admin_changelist_views(self):
        # Verify admin change lists load with 200 OK
        admin_urls = [
            'admin:blog_personalinfo_changelist',
            'admin:blog_skillcategory_changelist',
            'admin:blog_skill_changelist',
            'admin:blog_project_changelist',
            'admin:blog_journeymilestone_changelist',
            'admin:blog_certificate_changelist',
            'admin:blog_question_changelist',
            'admin:blog_contact_changelist',
        ]
        for url_name in admin_urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(
                response.status_code, 200,
                f"Admin changelist {url_name} failed with status {response.status_code}"
            )
