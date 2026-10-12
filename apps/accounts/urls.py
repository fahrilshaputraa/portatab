from django.contrib.auth.views import LogoutView
from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.PortatapLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("invite/<uuid:token>/", views.invitation_accept, name="invitation_accept"),
]
