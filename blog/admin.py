from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from blog.models import (
    BlogCategory, BlogPost, Certificate, Contact, JourneyMilestone,
    PersonalInfo, Project, ProjectImage, Question, Skill, SkillCategory,
)

# Admin Site Custom Branding
admin.site.site_header = "Ahadjon — Portfolio Administration"
admin.site.site_title = "Ahadjon Portfolio Admin"
admin.site.index_title = "Portfolio Content Management"


def image_preview(field_name, height=56):
    def _preview(self, obj):
        f = getattr(obj, field_name, None)
        if f:
            return format_html(
                '<img src="{}" style="height:{}px;width:auto;border-radius:6px;object-fit:cover" alt="">',
                f.url, height,
            )
        return "—"
    _preview.short_description = "Preview"
    return _preview


@admin.register(PersonalInfo)
class PersonalInfoAdmin(admin.ModelAdmin):
    readonly_fields = ("avatar_preview",)
    fieldsets = (
        ("Developer Identity & Tagline", {
            "fields": ("full_name", "headline", "location", "available_for_hire", "availability_text")
        }),
        ("Hero", {
            "fields": ("hero_title", "hero_subtitle"),
            "description": "Wrap one phrase of the hero title in *asterisks* to accent it.",
        }),
        ("About & Engineering Philosophy", {
            "fields": ("subheadline", "bio_intro", "bio_journey", "bio_philosophy")
        }),
        ("Academic Education", {
            "fields": ("education_institution", "education_degree", "education_period", "education_details")
        }),
        ("Contact & Social Links", {
            "fields": ("email", "github_url", "github_username", "linkedin_url", "telegram_url")
        }),
        ("Media & Resume", {
            "fields": ("avatar", "avatar_preview", "resume_file")
        }),
    )

    avatar_preview = image_preview("avatar", 96)

    def has_add_permission(self, request):
        # Singleton pattern: prevent creating multiple records if one already exists
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1
    fields = ('name', 'icon', 'is_core', 'order')


@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_primary', 'order', 'skill_count')
    list_editable = ('is_primary', 'order')
    search_fields = ('name',)
    inlines = [SkillInline]

    def skill_count(self, obj):
        return obj.skills.count()
    skill_count.short_description = "Total Skills"


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'icon', 'is_core', 'order')
    list_editable = ('icon', 'is_core', 'order')
    list_filter = ('category', 'is_core')
    search_fields = ('name', 'category__name')


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ("image", "preview", "caption", "order")
    readonly_fields = ("preview",)
    preview = image_preview("image")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'cover_preview', 'title', 'category', 'status', 'is_featured',
        'is_published', 'order', 'has_links',
    )
    list_display_links = ('cover_preview', 'title')
    list_editable = ('category', 'status', 'is_featured', 'is_published', 'order')
    list_filter = ('category', 'status', 'is_featured', 'is_published')
    search_fields = ('title', 'tech_stack', 'description', 'full_description', 'architecture_notes')
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("technologies",)
    readonly_fields = ("cover_large",)
    inlines = [ProjectImageInline]
    actions = ("publish", "unpublish", "feature", "unfeature")
    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "slug", "category", "status", "order", "is_featured", "is_published")
        }),
        ("Project Details", {
            "fields": ("description", "full_description", "architecture_notes")
        }),
        ("Technologies", {
            "fields": ("technologies", "tech_stack"),
            "description": "Linked technologies are shown when set; otherwise the comma-separated list is used.",
        }),
        ("Links & Media", {
            "fields": ("project_link", "github_link", "image", "cover_large", "accent_color")
        }),
    )

    cover_preview = image_preview("image", 40)
    cover_large = image_preview("image", 180)

    @admin.display(description="Links")
    def has_links(self, obj):
        parts = []
        if obj.project_link:
            parts.append("Live")
        if obj.github_link:
            parts.append("GitHub")
        return " · ".join(parts) or "—"

    @admin.action(description="Publish selected projects")
    def publish(self, request, qs):
        qs.update(is_published=True)

    @admin.action(description="Hide selected projects")
    def unpublish(self, request, qs):
        qs.update(is_published=False)

    @admin.action(description="Mark as featured")
    def feature(self, request, qs):
        qs.update(is_featured=True)

    @admin.action(description="Remove from featured")
    def unfeature(self, request, qs):
        qs.update(is_featured=False)


@admin.register(JourneyMilestone)
class JourneyMilestoneAdmin(admin.ModelAdmin):
    list_display = ('period', 'title', 'kind', 'organization_or_tag', 'order', 'is_published')
    list_editable = ('kind', 'order', 'is_published')
    list_filter = ('kind', 'is_published')
    search_fields = ('title', 'period', 'description')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'title', 'given_by', 'year', 'is_published', 'order')
    list_display_links = ('thumb', 'title')
    list_editable = ('is_published', 'order')
    list_filter = ('year', 'is_published')
    search_fields = ('title', 'given_by', 'description')
    readonly_fields = ("preview",)
    fieldsets = (
        ("Certificate Details", {
            "fields": ("title", "given_by", "year", "description", "order", "is_published")
        }),
        ("Media & Credentials", {
            "fields": ("image", "preview", "credential_url")
        }),
    )
    thumb = image_preview("image", 40)
    preview = image_preview("image", 220)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quest', 'order', 'is_published')
    list_editable = ('order', 'is_published')
    search_fields = ('quest', 'answer')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_editable = ('is_read',)
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at', 'ip_address')
    date_hierarchy = 'created_at'
    actions = ("mark_read",)

    @admin.action(description="Mark selected as read")
    def mark_read(self, request, qs):
        qs.update(is_read=True)


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "post_count")
    list_editable = ("order",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    @admin.display(description="Posts")
    def post_count(self, obj):
        return obj.posts.count()


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "published_at", "reading_time_display")
    list_filter = ("status", "category")
    search_fields = ("title", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    readonly_fields = ("cover_preview", "updated_at")
    actions = ("make_published", "make_draft")
    fieldsets = (
        (None, {"fields": ("title", "slug", "category", "status", "published_at")}),
        ("Content", {"fields": ("excerpt", "body")}),
        ("Media", {"fields": ("cover", "cover_preview", "updated_at")}),
    )
    cover_preview = image_preview("cover", 160)

    @admin.display(description="Reading time")
    def reading_time_display(self, obj):
        return f"{obj.reading_time} min"

    @admin.action(description="Publish selected posts")
    def make_published(self, request, qs):
        for post in qs:
            post.status = BlogPost.STATUS_PUBLISHED
            post.published_at = post.published_at or timezone.now()
            post.save()

    @admin.action(description="Move selected posts to draft")
    def make_draft(self, request, qs):
        qs.update(status=BlogPost.STATUS_DRAFT)
