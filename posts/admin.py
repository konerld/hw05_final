from django.contrib import admin
from .models import Post, Group


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author')
    search_fields = ('text', 'author',)
    list_filter = ('pub_date', 'text',)
    empty_value_display = ('-пусто-')


class GroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'description')
    search_fields = ('title', 'description',)
    list_filter = ('title', 'description',)
    empty_value_display = ('-пусто-')


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
