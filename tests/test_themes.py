"""Menu appearance: configuration validation, draft/publish separation, plans."""

import pytest
from django.urls import reverse

from apps.accounts.roles import RoleCode
from apps.accounts.services import create_membership
from apps.subscriptions.models import Plan
from apps.subscriptions.services import subscribe
from apps.themes import services
from apps.themes.models import (
    PublicationStatus,
    TenantTheme,
    ThemePublication,
    ThemeTemplate,
)

# ------------------------------------------------------------ colour maths ---


def test_contrast_ratio_boundaries():
    assert services.contrast_ratio("#ffffff", "#000000") == pytest.approx(21, abs=0.01)
    assert services.contrast_ratio("#ffffff", "#ffffff") == pytest.approx(1, abs=0.01)


def test_validate_config_rejects_bad_hex():
    problems = services.validate_config({"primary_color": "biru", "layout": "list"})
    assert any("HEX" in problem for problem in problems)


def test_validate_config_rejects_low_contrast():
    # Near-white accent would make white button text unreadable.
    problems = services.validate_config({"primary_color": "#fff3b0", "layout": "list"})
    assert any("kontras" in problem for problem in problems)


def test_validate_config_accepts_a_good_configuration():
    assert services.validate_config({"primary_color": "#0068f9", "layout": "grid"}) == []


def test_validate_config_rejects_unknown_layout():
    problems = services.validate_config({"primary_color": "#0068f9", "layout": "kanban"})
    assert any("Tata letak" in problem for problem in problems)


# -------------------------------------------------------------- drafts ------


@pytest.mark.django_db
def test_ensure_theme_creates_one_row_with_the_entry_template(tenant):
    theme = services.ensure_theme(tenant)

    assert theme.template.template_key == "minimal-list"
    assert services.ensure_theme(tenant).pk == theme.pk


@pytest.mark.django_db
def test_saving_a_draft_does_not_change_what_customers_see(tenant, owner):
    theme = services.ensure_theme(tenant)
    services.publish(tenant_theme=theme, actor=owner)
    before = services.live_config(tenant)

    services.save_draft(
        tenant_theme=theme,
        config={"primary_color": "#046645", "layout": "grid", "logo_url": "", "banner_url": ""},
        actor=owner,
    )

    assert services.live_config(tenant) == before  # live copy untouched
    theme.refresh_from_db()
    assert theme.draft_configuration["primary_color"] == "#046645"


@pytest.mark.django_db
def test_invalid_draft_is_rejected(tenant, owner):
    theme = services.ensure_theme(tenant)

    with pytest.raises(services.ThemeError):
        services.save_draft(
            tenant_theme=theme,
            config={"primary_color": "#fff3b0", "layout": "list"},
            actor=owner,
        )


@pytest.mark.django_db
def test_publish_creates_versioned_publications(tenant, owner):
    theme = services.ensure_theme(tenant)

    first = services.publish(tenant_theme=theme, actor=owner)
    assert first.version_number == 1
    assert first.status == PublicationStatus.PUBLISHED

    services.save_draft(
        tenant_theme=theme,
        config={"primary_color": "#024bb1", "layout": "grid", "logo_url": "", "banner_url": ""},
        actor=owner,
    )
    second = services.publish(tenant_theme=theme, actor=owner)

    assert second.version_number == 2
    first.refresh_from_db()
    assert first.status == PublicationStatus.SUPERSEDED
    assert ThemePublication.objects.filter(tenant_theme=theme).count() == 2
    assert services.live_config(tenant)["layout"] == "grid"


@pytest.mark.django_db
def test_live_config_falls_back_to_defaults_when_unpublished(tenant):
    config = services.live_config(tenant)

    assert config["primary_color"] == services.DEFAULT_CONFIG["primary_color"]
    assert config["layout"] == services.DEFAULT_CONFIG["layout"]


# ---------------------------------------------------------- plan gating -----


@pytest.mark.django_db
def test_starter_tenant_cannot_use_a_business_template(tenant):
    business_template = ThemeTemplate.objects.get(template_key="signature")

    with pytest.raises(services.ThemeError):
        services.assert_template_allowed(tenant=tenant, template=business_template)


@pytest.mark.django_db
def test_upgrading_the_plan_unlocks_more_templates(tenant):
    before = {item.template_key for item in services.available_templates(tenant)}

    subscribe(tenant=tenant, plan=Plan.objects.get(code="BUSINESS"))
    after = {item.template_key for item in services.available_templates(tenant)}

    assert before == {"minimal-list"}
    assert {"minimal-list", "editorial-grid", "signature"} <= after


# ------------------------------------------------------------------- UI -----


@pytest.mark.django_db
def test_owner_can_open_the_editor_and_publish(client, owner, tenant):
    client.force_login(owner)

    page = client.get(reverse("themes:editor"))
    assert page.status_code == 200

    response = client.post(
        reverse("themes:editor"),
        {
            "template": ThemeTemplate.objects.get(template_key="minimal-list").pk,
            "logo_url": "",
            "banner_url": "",
            "primary_color": "#0068f9",
            "layout": "grid",
            "publish": "1",
        },
    )

    assert response.status_code == 302
    assert services.current_publication(tenant).published_configuration["layout"] == "grid"


@pytest.mark.django_db
def test_preview_renders_the_draft(client, owner, tenant):
    services.save_draft(
        tenant_theme=services.ensure_theme(tenant),
        config={"primary_color": "#046645", "layout": "grid", "logo_url": "", "banner_url": ""},
        actor=owner,
    )
    client.force_login(owner)

    response = client.get(reverse("themes:preview"))

    assert response.status_code == 200
    assert "#046645" in response.content.decode()


@pytest.mark.django_db
def test_manager_cannot_edit_the_theme(client, tenant, branch):
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.create_user(
        email="mgr4@example.com", password="pass12345", name="Mgr"
    )
    create_membership(tenant=tenant, user=user, role_code=RoleCode.MANAGER, branches=[branch])

    client.force_login(user)
    assert client.get(reverse("themes:editor")).status_code == 403


# -------------------------------------------------------- public menu -------


@pytest.mark.django_db
def test_public_menu_applies_the_published_theme(client, tenant, owner, branch, table):
    theme = services.ensure_theme(tenant)
    services.save_draft(
        tenant_theme=theme,
        config={"primary_color": "#046645", "layout": "grid", "logo_url": "", "banner_url": ""},
        actor=owner,
    )
    services.publish(tenant_theme=theme, actor=owner)

    body = client.get(reverse("menu:menu", args=[table.qr_token])).content.decode()

    assert "--menu-primary: #046645" in body
    assert TenantTheme.objects.filter(tenant=tenant).count() == 1
