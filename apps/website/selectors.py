"""Read queries for published website content."""

from django.db.models import QuerySet
from django.utils import timezone

from apps.website.models import Post, PostKind, PostStatus


def published_posts(*, kind: str | None = None) -> QuerySet[Post]:
    """Posts publicly visible now: PUBLISHED and not dated in the future."""
    query = Post.objects.filter(
        status=PostStatus.PUBLISHED, published_at__lte=timezone.now()
    ).select_related("author")
    if kind is not None:
        query = query.filter(kind=kind)
    return query


def published_post_or_none(slug: str, *, kind: str | None = None) -> Post | None:
    return published_posts(kind=kind).filter(slug=slug).first()


def latest_posts(*, limit: int = 3, kind: str | None = None) -> QuerySet[Post]:
    return published_posts(kind=kind)[:limit]


def related_posts(post: Post, *, limit: int = 3) -> QuerySet[Post]:
    """Other published posts of the same kind, newest first."""
    return published_posts(kind=post.kind).exclude(pk=post.pk)[:limit]


def featured_posts(*, limit: int = 3, kind: str | None = None) -> QuerySet[Post]:
    return published_posts(kind=kind).filter(is_featured=True)[:limit]


__all__ = [
    "PostKind",
    "featured_posts",
    "latest_posts",
    "published_post_or_none",
    "published_posts",
    "related_posts",
]
