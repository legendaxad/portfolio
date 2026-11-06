from django.db import models


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
    subheadline = models.TextField(
        default=(
            "Information Security student at Dongshin University in South Korea. "
            "Passionate about backend systems, REST APIs, database architecture, "
            "and building complete, production-ready full-stack applications."
        )
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
    github_url = models.URLField(blank=True, default="https://github.com/akhadjon")
    linkedin_url = models.URLField(blank=True, null=True)
    telegram_url = models.URLField(blank=True, default="https://t.me/akhadjon")
    available_for_hire = models.BooleanField(default=True)
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


class SkillCategory(models.Model):
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Skill Category"
        verbose_name_plural = "Skill Categories"

    def __str__(self):
        return self.name


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

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Skill"
        verbose_name_plural = "Skills"

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class Project(models.Model):
    CATEGORY_CHOICES = [
        ('all', 'All'),
        ('backend', 'Python & Backend'),
        ('fullstack', 'Full-Stack'),
        ('automation', 'Automation & Bots'),
        ('systems', 'Systems & Security'),
    ]

    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('in_progress', 'Ongoing / In Development'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    tech_stack = models.CharField(max_length=255)
    project_link = models.URLField(blank=True, null=True)
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
    image = models.ImageField(upload_to="projects/", blank=True, null=True)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return self.title

    def get_tech_list(self):
        """Splits tech stack into clean badges."""
        if not self.tech_stack:
            return []
        cleaned = self.tech_stack.replace('•', ',').replace('|', ',')
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


class JourneyMilestone(models.Model):
    period = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    organization_or_tag = models.CharField(max_length=200, blank=True)
    description = models.TextField()
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

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"


class Certificate(models.Model):
    title = models.CharField(max_length=200)
    given_by = models.CharField(max_length=200)
    year = models.CharField(max_length=20)
    description = models.TextField()
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
