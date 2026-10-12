from django.urls import path

from apps.website import views

app_name = "website"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("blog/", views.blog_list, name="blog_list"),
    path("blog/<slug:slug>/", views.blog_detail, name="blog_detail"),
    path("news/", views.news_list, name="news_list"),
    path("news/<slug:slug>/", views.news_detail, name="news_detail"),
]
