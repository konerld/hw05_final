from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Название"
    )
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name="Описание")

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )
    author = models.ForeignKey(
        User, related_name="author_posts",
        on_delete=models.CASCADE
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="group_posts",
        blank=True, null=True
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        null=True
    )

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Запись"
        verbose_name_plural = "Записи"

    def __str__(self):
        return self.text


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        related_name="comments",
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User, related_name="comments",
        on_delete=models.CASCADE
    )
    text = models.TextField()
    created = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created"]
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return self.text


"""
class Comment(models.Model):
    post = models.ForeignKey(Post,
        on_delete=models.SET_NULL,
        related_name="comments", blank=True, null=True,
        verbose_name="Комментарий к посту",
        help_text="Добавьте комментарий к посту"
        )
    author = models.ForeignKey(User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name = 'Автор',
        help_text="Автор комментария"
        )
    text = models.CharField(max_length=1000,
        verbose_name='Комментарий к посту'
        )
    created = models.DateTimeField("date published", auto_now_add=True, )
    class Meta:
        ordering = ('created',)
"""