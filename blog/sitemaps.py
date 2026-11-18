from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blog.models import BlogPost, Project


class StaticSitemap(Sitemap):
    priority = 1.0
    changefreq = "weekly"

    def items(self):
        return ["home", "post_list"]

    def location(self, item):
        return reverse(item)


class ProjectSitemap(Sitemap):
    priority = 0.8
    changefreq = "monthly"

    def items(self):
        return Project.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


class PostSitemap(Sitemap):
    priority = 0.6
    changefreq = "monthly"

    def items(self):
        return BlogPost.published.all()

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {"static": StaticSitemap, "projects": ProjectSitemap, "posts": PostSitemap}
