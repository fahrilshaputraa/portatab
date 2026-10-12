from django.contrib import admin

from apps.website.models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "status", "is_featured", "author", "published_at")
    list_filter = ("kind", "status", "is_featured")
    search_fields = ("title", "slug", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
