from django.db import models
from markdownx.models import MarkdownxField

STATUS = (
    (0, "Draft"),
    (1, "Publish")
)


class Post(models.Model):
    title = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    preview = models.CharField(max_length=200)
    updated_on = models.DateTimeField(auto_now=True)
    content = MarkdownxField()
    created_on = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=STATUS, default=0)

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f'/blog/{self.slug}/'
