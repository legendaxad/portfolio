from django.urls import path
from blog.views import index, project_detail

urlpatterns = [
    path("", index, name="home"),
    path("project/<int:pk>/", project_detail, name="project_detail"),
]
