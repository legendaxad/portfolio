from django.db import models

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    tech_stack = models.CharField(max_length=255)
    project_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    quest=models.CharField(max_length=150)
    answer=models.TextField()

    def __str__(self):
        return self.quest

class Contact(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Certificate(models.Model):
    title = models.CharField(max_length=200)
    given_by = models.CharField(max_length=200)
    year = models.CharField(max_length=20)
    description = models.TextField()
    image = models.ImageField(upload_to="certificates/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title