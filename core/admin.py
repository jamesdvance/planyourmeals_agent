from django.contrib import admin

# Register your models here.
from markdownx.admin import MarkdownxModelAdmin
from .models import Blog

admin.site.register(Blog, MarkdownxModelAdmin)