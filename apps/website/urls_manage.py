from django.urls import path

from apps.website import admin_views

app_name = "website_admin"

urlpatterns = [
    path("", admin_views.post_list, name="post_list"),
    path("new/", admin_views.post_form, name="post_create"),
    path("<uuid:pk>/edit/", admin_views.post_form, name="post_edit"),
    path("<uuid:pk>/publish/", admin_views.post_publish, name="post_publish"),
    path("<uuid:pk>/unpublish/", admin_views.post_unpublish, name="post_unpublish"),
]
