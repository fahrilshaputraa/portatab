"""Public marketing site content: blog articles and news.

Blog and news share one model because they are the same shape (title, slug,
body, cover, publish state) and differ only by ``kind``. That keeps one list,
one detail view and one editor instead of two near-identical stacks.

Content is authored only by platform admins (docs/PRD.md §20); tenant-authored
content is never rendered through this path.
"""

from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class PostKind(models.TextChoices):
    BLOG = "BLOG", "Blog"
    NEWS = "NEWS", "Berita"


class PostStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PUBLISHED = "PUBLISHED", "Terbit"


class Post(BaseModel):
    kind = models.CharField(max_length=8, choices=PostKind.choices, db_index=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=160, unique=True)
    excerpt = models.CharField(
        max_length=320, blank=True, help_text="Ringkasan singkat untuk daftar dan hasil pencarian."
    )
    body = models.TextField(help_text="Ditulis dalam Markdown.")
    cover_image_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=16, choices=PostStatus.choices, default=PostStatus.DRAFT, db_index=True
    )
    is_featured = models.BooleanField(
        default=False, help_text="Tampilkan menonjol di halaman utama publik."
    )
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
    )
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["kind", "status", "published_at"]),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def is_published(self) -> bool:
        return self.status == PostStatus.PUBLISHED

    def publish(self) -> None:
        self.status = PostStatus.PUBLISHED
        self.published_at = self.published_at or timezone.now()
        self.save(update_fields=["status", "published_at", "updated_at"])

    def unpublish(self) -> None:
        self.status = PostStatus.DRAFT
        self.save(update_fields=["status", "updated_at"])
