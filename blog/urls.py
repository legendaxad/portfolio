from django.urls import path

from blog import views

urlpatterns = [
    path("", views.index, name="home"),
    path("projects/<slug:slug>/", views.project_detail, name="project_detail"),
    path("project/<int:pk>/", views.project_detail_legacy, name="project_detail_legacy"),
    path("notes/", views.post_list, name="post_list"),
    path("notes/<slug:slug>/", views.post_detail, name="post_detail"),
    path("api/github/", views.github_api, name="github_api"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
]
