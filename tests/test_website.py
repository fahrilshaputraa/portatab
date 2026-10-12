"""Public website (landing, blog, news) and platform content management."""

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.website.models import Post, PostKind, PostStatus
from apps.website.services import render_body


def make_post(**kwargs) -> Post:
    defaults = {
        "kind": PostKind.BLOG,
        "title": "Tulisan uji",
        "slug": "tulisan-uji",
        "body": "Isi tulisan.",
        "status": PostStatus.PUBLISHED,
        "published_at": timezone.now(),
    }
    defaults.update(kwargs)
    return Post.objects.create(**defaults)


# --------------------------------------------------------------- public -----


@pytest.mark.django_db
def test_landing_page_renders_with_plans(client):
    response = client.get(reverse("website:landing"))

    assert response.status_code == 200
    body = response.content.decode()
    for plan_name in ["Starter", "Growth", "Business"]:
        assert plan_name in body


@pytest.mark.django_db
def test_landing_page_lists_latest_content(client):
    make_post(title="Panduan harga menu", slug="panduan-harga-menu")
    make_post(
        kind=PostKind.NEWS, title="Kabar rilis", slug="kabar-rilis", body="Berita singkat."
    )

    body = client.get(reverse("website:landing")).content.decode()

    assert "Panduan harga menu" in body
    assert "Kabar rilis" in body


@pytest.mark.django_db
def test_blog_list_shows_published_but_hides_draft(client):
    make_post(title="Terbit hari ini", slug="terbit-hari-ini")
    make_post(title="Masih draft", slug="masih-draft", status=PostStatus.DRAFT, published_at=None)

    body = client.get(reverse("website:blog_list")).content.decode()

    assert "Terbit hari ini" in body
    assert "Masih draft" not in body


@pytest.mark.django_db
def test_blog_detail_404_for_draft(client):
    make_post(title="Masih draft", slug="masih-draft", status=PostStatus.DRAFT, published_at=None)

    assert client.get(reverse("website:blog_detail", args=["masih-draft"])).status_code == 404


@pytest.mark.django_db
def test_news_and_blog_are_separated(client):
    make_post(kind=PostKind.BLOG, title="Tulisan blog", slug="tulisan-blog")
    make_post(kind=PostKind.NEWS, title="Kabar berita", slug="kabar-berita", body="Berita.")

    news_body = client.get(reverse("website:news_list")).content.decode()
    assert "Kabar berita" in news_body
    assert "Tulisan blog" not in news_body


@pytest.mark.django_db
def test_blog_detail_renders_markdown_headings(client):
    make_post(title="Judul", slug="judul", body="## Sub judul\n\nIsi paragraf.")

    body = client.get(reverse("website:blog_detail", args=["judul"])).content.decode()

    assert "<h2>Sub judul</h2>" in body


def test_markdown_render_neutralises_raw_html():
    rendered = render_body("Halo <script>alert('x')</script>\n\n## Judul")

    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "<h2>Judul</h2>" in rendered


# ------------------------------------------------------- platform admin -----


@pytest.mark.django_db
def test_content_admin_requires_login(client):
    response = client.get(reverse("website_admin:post_list"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]


@pytest.mark.django_db
def test_tenant_owner_cannot_manage_content(client, owner):
    client.force_login(owner)

    assert client.get(reverse("website_admin:post_list")).status_code == 403
    assert client.get(reverse("website_admin:post_create")).status_code == 403


@pytest.mark.django_db
def test_platform_admin_can_create_and_publish(client, platform_admin):
    client.force_login(platform_admin)

    create = client.post(
        reverse("website_admin:post_create"),
        {
            "kind": PostKind.BLOG,
            "title": "Cara menghitung margin",
            "excerpt": "Ringkas saja.",
            "body": "## Margin\n\nIsi.",
            "cover_image_url": "",
            "is_featured": "on",
        },
    )
    assert create.status_code == 302

    post = Post.objects.get(title="Cara menghitung margin")
    assert post.author == platform_admin
    assert post.slug == "cara-menghitung-margin"
    assert post.status == PostStatus.DRAFT

    publish = client.post(reverse("website_admin:post_publish", args=[post.pk]))
    assert publish.status_code == 302
    post.refresh_from_db()
    assert post.is_published
    assert post.published_at is not None

    # Published content is now visible publicly.
    assert client.get(reverse("website:blog_detail", args=[post.slug])).status_code == 200


@pytest.mark.django_db
def test_platform_admin_can_unpublish(client, platform_admin):
    post = make_post(title="Sementara", slug="sementara")
    client.force_login(platform_admin)

    response = client.post(reverse("website_admin:post_unpublish", args=[post.pk]))

    assert response.status_code == 302
    post.refresh_from_db()
    assert post.status == PostStatus.DRAFT
