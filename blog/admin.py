from django.contrib import admin

from blog.models import Project, Question, Contact, Certificate

# Register your models here.
admin.site.register(Project)
admin.site.register(Question)
admin.site.register(Certificate)
admin.site.register(Contact)
