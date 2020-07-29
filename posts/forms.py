from django.forms import ModelForm
from django import forms
from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ("group", "text", "image")
        help_texts = {
            "text": "Текст записи",
            "group": "Сообщества",
            "image": "Изображение"
        }
        labels = {
            "text": "Текст записи",
            "group": "Сообщества",
            "image": "Изображение"
        }


class CommentForm(ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Comment
        fields = ("text",)
        help_texts = {
            "text": "Текст комментария"
        }
        labels = {
            "text": "Текст комментария"
        }
