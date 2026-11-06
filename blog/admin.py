from django.contrib import admin
from blog.models import (
    PersonalInfo, SkillCategory, Skill, Project,
    JourneyMilestone, Certificate, Question, Contact
)

# Admin Site Custom Branding
admin.site.site_header = "Ahadjon — Portfolio Administration"
admin.site.site_title = "Ahadjon Portfolio Admin"
admin.site.index_title = "Portfolio Content Management"


@admin.register(PersonalInfo)
class PersonalInfoAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Developer Identity & Tagline", {
            "fields": ("full_name", "headline", "subheadline", "location", "available_for_hire")
        }),
        ("About & Engineering Philosophy", {
            "fields": ("bio_intro", "bio_philosophy")
        }),
        ("Academic Education", {
            "fields": ("education_institution", "education_degree", "education_period", "education_details")
        }),
        ("Contact & Social Links", {
            "fields": ("email", "github_url", "linkedin_url", "telegram_url")
        }),
        ("Media & Resume", {
            "fields": ("avatar", "resume_file")
        }),
    )

    def has_add_permission(self, request):
        # Singleton pattern: prevent creating multiple records if one already exists
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1
    fields = ('name', 'is_core', 'order')


@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'skill_count')
    list_editable = ('order',)
    search_fields = ('name',)
    inlines = [SkillInline]

    def skill_count(self, obj):
        return obj.skills.count()
    skill_count.short_description = "Total Skills"


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_core', 'order')
    list_editable = ('is_core', 'order')
    list_filter = ('category', 'is_core')
    search_fields = ('name', 'category__name')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'status', 'is_featured',
        'is_published', 'order', 'project_link'
    )
    list_editable = ('category', 'status', 'is_featured', 'is_published', 'order')
    list_filter = ('category', 'status', 'is_featured', 'is_published')
    search_fields = ('title', 'tech_stack', 'description', 'architecture_notes')
    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "category", "status", "order", "is_featured", "is_published")
        }),
        ("Project Details", {
            "fields": ("description", "tech_stack", "architecture_notes")
        }),
        ("Links & Media", {
            "fields": ("project_link", "github_link", "image")
        }),
    )


@admin.register(JourneyMilestone)
class JourneyMilestoneAdmin(admin.ModelAdmin):
    list_display = ('period', 'title', 'organization_or_tag', 'order', 'is_published')
    list_editable = ('order', 'is_published')
    search_fields = ('title', 'period', 'description')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('title', 'given_by', 'year', 'is_published', 'order')
    list_editable = ('is_published', 'order')
    list_filter = ('year', 'is_published')
    search_fields = ('title', 'given_by', 'description')
    fieldsets = (
        ("Certificate Details", {
            "fields": ("title", "given_by", "year", "description", "order", "is_published")
        }),
        ("Media & Credentials", {
            "fields": ("image", "credential_url")
        }),
    )


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
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')
