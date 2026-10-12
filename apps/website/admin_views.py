"""Platform-admin content management (blog & news).

Guarded by ``require_platform_admin``: a tenant owner has no access here.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.platform_admin.permissions import require_platform_admin
from apps.tenants.services import record_audit
from apps.website.forms import PostForm
from apps.website.models import Post
from apps.website.services import unique_post_slug


@login_required
@require_platform_admin
def post_list(request):
    kind = request.GET.get("kind", "")
    status = request.GET.get("status", "")

    posts = Post.objects.select_related("author").order_by("-created_at")
    if kind:
        posts = posts.filter(kind=kind)
    if status:
        posts = posts.filter(status=status)

    return render(
        request,
        "manage/post_list.html",
        {"posts": posts, "kind": kind, "status": status},
    )


@login_required
@require_platform_admin
def post_form(request, pk=None):
    post = get_object_or_404(Post, pk=pk) if pk is not None else None

    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            obj = form.save(commit=False)
            if not obj.slug:
                obj.slug = unique_post_slug(obj.title, kind=obj.kind)
            if obj.author_id is None:
                obj.author = request.user
            obj.save()
            record_audit(
                action="post.saved",
                user=request.user,
                entity=obj,
                after={"kind": obj.kind, "status": obj.status},
            )
            messages.success(request, "Tulisan disimpan.")
            return redirect("website_admin:post_list")
    else:
        form = PostForm(instance=post)

    return render(request, "manage/post_form.html", {"form": form, "post": post})


@login_required
@require_platform_admin
@require_POST
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.publish()
    record_audit(action="post.published", user=request.user, entity=post)
    messages.success(request, f"“{post.title}” diterbitkan.")
    return redirect("website_admin:post_list")


@login_required
@require_platform_admin
@require_POST
def post_unpublish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.unpublish()
    record_audit(action="post.unpublished", user=request.user, entity=post)
    messages.success(request, f"“{post.title}” dikembalikan ke draft.")
    return redirect("website_admin:post_list")
