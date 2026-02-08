
from django import forms
from core.models import Blog
from markdownx.fields import MarkdownxFormField

class BlogForm(forms.Form):
	title=forms.CharField()
	slug = forms.SlugField()
	post = MarkdownxFormField()
	title_image=forms.URLField()
	# class Meta:
	# 	model=Blog
	# 	fields=['title','slug','post','title_image','embed_media']
