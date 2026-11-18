import math
import re

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import slugify

hex_color_validator = RegexValidator(
    regex=r"^#(?:[0-9a-fA-F]{3}){1,2}$",
    message="Use a hex colour such as #4D7CFF.",
)


def unique_slug(instance, value, field="slug", max_length=220):
    """Generate a slug from `value` that is unique for the instance's model."""
    base = (slugify(value) or "item")[: max_length - 6].strip("-")
    slug, n = base, 2
    qs = type(instance)._default_manager.all()
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)
    while qs.filter(**{field: slug}).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


class PersonalInfo(models.Model):
    """
    Singleton model to manage developer identity, hero text,
    education, bio, and social links dynamically via Django Admin.
    """
    full_name = models.CharField(max_length=150, default="Ahadjon (Akhadbek)")
    headline = models.CharField(
        max_length=200,
        default="Full-Stack Developer | Python Backend Engineer"
    )
    hero_title = models.CharField(
        max_length=200,
        default="Engineering the systems behind great digital experiences.",
        help_text="Main hero headline. Wrap one phrase in *asterisks* to highlight it.",
    )
    hero_subtitle = models.CharField(
        max_length=300,
        default=(
            "Python Backend & Full-Stack Developer building scalable applications, "
            "intelligent tools, and reliable digital products."
        ),
    )
    subheadline = models.TextField(
        default=(
            "Information Security student at Dongshin University in South Korea. "
            "Passionate about backend systems, REST APIs, database architecture, "
            "and building complete, production-ready full-stack applications."
        ),
        help_text="Used as the SEO meta description.",
    )
    bio_intro = models.TextField(
        default=(
            "I am an Information Security student at Dongshin University in South Korea "
            "with a focused interest in software development and backend engineering. "
            "I enjoy understanding how applications work internally, designing clean database schemas, "
            "implementing secure authentication flows, and building scalable REST APIs that power modern client applications."
        )
    )
    bio_philosophy = models.TextField(
        default=(
            "Rather than treating engineering as just connecting templates, I prioritize solid system design, "
            "maintainable code, data integrity, and defensive security practices. I am committed to continuous learning "
            "and proving my capabilities through real-world software projects."
        )
    )
    bio_journey = models.TextField(
        blank=True,
        help_text="Optional extra paragraph about how you got into software development.",
    )
    education_institution = models.CharField(max_length=200, default="Dongshin University")
    education_degree = models.CharField(max_length=200, default="B.S. in Information Security")
    education_period = models.CharField(max_length=100, default="2022 – Present (3rd Year)")
    education_details = models.TextField(
        default=(
            "Core coursework in Information Security, Network Security, Operating Systems, "
            "Cryptographic Principles, System Architecture, and Software Engineering."
        )
    )
    email = models.EmailField(default="abdulaxadjon9@gmail.com")
    location = models.CharField(max_length=150, default="South Korea")
    github_url = models.URLField(blank=True, default="https://github.com/legendaxad")
    github_username = models.CharField(
        max_length=80, blank=True, default="legendaxad",
        help_text="Used by the GitHub section to load public repositories.",
    )
    linkedin_url = models.URLField(blank=True, null=True)
    telegram_url = models.URLField(blank=True, default="https://t.me/akhadjon")
    available_for_hire = models.BooleanField(default=True)
    availability_text = models.CharField(
        max_length=120, blank=True, default="Open to backend & full-stack opportunities",
        help_text="Shown in the hero only while 'available for hire' is checked.",
    )
    avatar = models.ImageField(upload_to="profile/", blank=True, null=True)
    resume_file = models.FileField(upload_to="documents/", blank=True, null=True)

    class Meta:
        verbose_name = "Personal Profile & Site Settings"
        verbose_name_plural = "Personal Profile & Site Settings"

    def __str__(self):
        return self.full_name

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    @property
    def short_name(self):
        """First word of the name, e.g. 'Ahadjon'."""
        return (self.full_name or "Ahadjon").split()[0]

    @property
    def hero_title_parts(self):
        """Split '*highlight*' markup into (before, highlight, after)."""
        m = re.match(r"^(.*?)\*(.+?)\*(.*)$", self.hero_title or "")
        if not m:
            return (self.hero_title, "", "")
        return m.groups()


class SkillCategory(models.Model):
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(
        default=False,
        help_text="Visually emphasise this category (e.g. Backend).",
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Skill Category"
        verbose_name_plural = "Skill Categories"

    def __str__(self):
        return self.name

    @property
    def key(self):
        return slugify(self.name) or f"cat-{self.pk}"


class Skill(models.Model):
    category = models.ForeignKey(
        SkillCategory,
        on_delete=models.CASCADE,
        related_name="skills"
    )
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    is_core = models.BooleanField(
        default=False,
        help_text="Highlight as a primary technical focus"
    )
    icon = models.CharField(
        max_length=60, blank=True,
        help_text="Icon file name in static/icons/tech (without .svg), e.g. 'django'.",
    )

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Skill"
        verbose_name_plural = "Skills"

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Project(models.Model):
    CATEGORY_CHOICES = [
        ('backend', 'Python & Backend'),
        ('fullstack', 'Full-Stack'),
        ('frontend', 'Frontend'),
        ('automation', 'Automation & Bots'),
        ('systems', 'Systems & Security'),
    ]

    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('in_progress', 'Ongoing / In Development'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(help_text="Short description shown on cards (1–2 sentences).")
    full_description = models.TextField(
        blank=True,
        help_text="Long-form case study. Blank lines separate paragraphs; URLs become links.",
    )
    tech_stack = models.CharField(
        max_length=255, blank=True,
        help_text="Comma-separated fallback list. Linked technologies below take priority.",
    )
    technologies = models.ManyToManyField(
        "Skill", blank=True, related_name="projects",
        help_text="Technologies from the skills list used by this project.",
    )
    project_link = models.URLField("Live demo URL", blank=True, null=True)
    github_link = models.URLField(
        blank=True,
        null=True,
        help_text="Link to GitHub repository"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='backend'
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='completed'
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Show in featured case study highlights"
    )
    is_published = models.BooleanField(
        default=True,
        help_text="Uncheck to hide from public site without deleting"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first"
    )
    architecture_notes = models.TextField(
        blank=True,
        help_text="Key technical challenges or architecture highlights (one per line)"
    )
    image = models.ImageField("Cover image", upload_to="projects/", blank=True, null=True)
    accent_color = models.CharField(
        max_length=7, blank=True, default="", validators=[hex_color_validator],
        help_text="Project accent colour, e.g. #4D7CFF. Leave blank for the default.",
    )
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("project_detail", kwargs={"slug": self.slug})

    def get_tech_list(self):
        """Technology names: linked skills first, falling back to tech_stack text."""
        if self.pk:
            linked = [s.name for s in self.technologies.all()]
            if linked:
                return linked
        if not self.tech_stack:
            return []
        cleaned = (
            self.tech_stack.replace('â€¢', ',').replace('•', ',').replace('|', ',')
        )
        return [t.strip() for t in cleaned.split(',') if t.strip()]

    def get_highlights_list(self):
        """Returns architecture highlights as a list of strings."""
        if not self.architecture_notes:
            return []
        return [
            line.strip().lstrip('•-* ').strip()
            for line in self.architecture_notes.splitlines()
            if line.strip()
        ]

    @property
    def accent(self):
        return self.accent_color or "#4D7CFF"

    @property
    def initials(self):
        """'MultiShop' -> 'MS', 'Camper Booking' -> 'CB', 'BURAK — …' -> 'BR'."""
        words = re.findall(r"[A-Za-z0-9]+", self.title)
        if not words:
            return "P"
        caps = re.findall(r"[A-Z]", words[0])
        if len(caps) >= 2 and not words[0].isupper():
            return "".join(caps[:2])
        return "".join(w[0] for w in words[:2]).upper()


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(upload_to="projects/gallery/")
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Gallery image"

    def __str__(self):
        return self.caption or f"{self.project.title} image #{self.pk}"


class JourneyMilestone(models.Model):
    KIND_CHOICES = [
        ('education', 'Education'),
        ('projects', 'Independent projects'),
        ('learning', 'Current learning'),
    ]
    period = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    organization_or_tag = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='projects')
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Journey Milestone"
        verbose_name_plural = "Journey Milestones"

    def __str__(self):
        return f"{self.period} - {self.title}"


class Question(models.Model):
    quest = models.CharField(max_length=150)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.quest

    @property
    def question(self):
        return self.quest


class Contact(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True, default='')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"


class Certificate(models.Model):
    title = models.CharField(max_length=200)
    given_by = models.CharField("Issuer", max_length=200)
    year = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="certificates/")
    credential_url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    @property
    def issuer(self):
        return self.given_by


# ----------------------------------------------------------------------------
# Engineering notes (blog)
# ----------------------------------------------------------------------------

class BlogCategory(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Blog category"
        verbose_name_plural = "Blog categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, max_length=90)
        super().save(*args, **kwargs)


class PublishedPostManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            status=BlogPost.STATUS_PUBLISHED, published_at__lte=timezone.now()
        )


class BlogPost(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CHOICES = [(STATUS_DRAFT, "Draft"), (STATUS_PUBLISHED, "Published")]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.ForeignKey(
        BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts"
    )
    excerpt = models.CharField(max_length=300, blank=True, help_text="Shown on cards and in meta description.")
    body = models.TextField(
        help_text="Plain text. Blank lines separate paragraphs; lines starting with '## ' become headings; "
                  "lines wrapped in ``` become code blocks; URLs become links."
    )
    cover = models.ImageField(upload_to="blog/", blank=True, null=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    published_at = models.DateTimeField(
        blank=True, null=True, help_text="Set automatically when first published."
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()
    published = PublishedPostManager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "Blog post"

    def __str__(self):
        return self.title

    def clean(self):
        if self.status == self.STATUS_PUBLISHED and not (self.body or "").strip():
            raise ValidationError({"body": "A published post needs content."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        if self.status == self.STATUS_PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("post_detail", kwargs={"slug": self.slug})

    @property
    def reading_time(self):
        words = len(strip_tags(self.body or "").split())
        return max(1, math.ceil(words / 220))

    @property
    def summary(self):
        if self.excerpt:
            return self.excerpt
        text = " ".join(strip_tags(self.body or "").split())
        return (text[:200] + "…") if len(text) > 200 else text
