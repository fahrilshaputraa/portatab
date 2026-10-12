"""Website content services: Markdown rendering and slug generation."""

import html

import markdown
from django.utils.text import slugify

from apps.website.models import Post

_MARKDOWN_EXTENSIONS = ["extra", "sane_lists"]


def render_body(body: str) -> str:
    """Render stored Markdown to HTML, neutralising any raw HTML first.

    The body is HTML-escaped before Markdown runs, so Markdown formatting works
    but embedded tags cannot execute. The result is safe to mark as trusted HTML.
    """
    if not body:
        return ""
    return markdown.markdown(html.escape(body), extensions=_MARKDOWN_EXTENSIONS)


def unique_post_slug(title: str, *, kind: str | None = None) -> str:
    """A unique slug derived from the title, suffixed when already taken."""
    base = slugify(title)[:150] or "post"
    slug = base
    index = 1
    while Post.objects.filter(slug=slug).exists():
        index += 1
        slug = f"{base}-{index}"
    return slug
