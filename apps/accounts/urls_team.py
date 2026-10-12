from django.urls import path

from apps.accounts import team_views

app_name = "team"

urlpatterns = [
    path("", team_views.team_list, name="list"),
    path("invite/", team_views.invite_staff, name="invite"),
    path("<uuid:pk>/edit/", team_views.member_edit, name="member_edit"),
    path(
        "invitations/<uuid:pk>/cancel/",
        team_views.invitation_cancel,
        name="invitation_cancel",
    ),
]
