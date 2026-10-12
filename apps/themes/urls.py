from django.urls import path

from apps.themes import views

app_name = "themes"

urlpatterns = [
    path("", views.editor, name="editor"),
    path("publish/", views.publish, name="publish"),
    path("preview/", views.preview, name="preview"),
]
