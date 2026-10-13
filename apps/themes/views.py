"""Menu appearance editor (draft, preview, publish)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.roles import Perm
from apps.tenants.permissions import require_permission, require_tenant
from apps.tenants.services import record_audit
from apps.themes import services
from apps.themes.forms import ThemeConfigForm


def _config_from_form(form) -> dict:
    data = form.cleaned_data
    return {
        "logo_url": data["logo_url"] or "",
        "banner_url": data["banner_url"] or "",
        "primary_color": data["primary_color"].strip().lower(),
        "layout": data["layout"],
    }


@login_required
@require_tenant
@require_permission(Perm.THEMES_MANAGE)
def editor(request):
    tenant = request.tenant

    try:
        theme = services.ensure_theme(tenant)
    except services.ThemeError as exc:
        # No catalogue yet (or every template deactivated): show the reason
        # instead of failing the request.
        return render(
            request,
            "themes/editor.html",
            {"unavailable": str(exc), "theme": None, "form": None, "templates": [],
             "publication": None, "draft_config": dict(services.DEFAULT_CONFIG)},
        )

    allowed = services.available_templates(tenant)

    if request.method == "POST":
        form = ThemeConfigForm(request.POST, allowed_templates=allowed)
        if form.is_valid():
            template = form.cleaned_data["template"]
            try:
                services.assert_template_allowed(tenant=tenant, template=template)
                if theme.template_id != template.pk:
                    theme.template = template
                    theme.save(update_fields=["template", "updated_at"])
                services.save_draft(
                    tenant_theme=theme, config=_config_from_form(form), actor=request.user
                )
            except services.ThemeError as exc:
                messages.error(request, str(exc))
            else:
                record_audit(
                    action="theme.draft_saved",
                    tenant=tenant,
                    user=request.user,
                    entity=theme,
                    request=request,
                )
                if "publish" in request.POST:
                    try:
                        publication = services.publish(
                            tenant_theme=theme, actor=request.user
                        )
                    except services.ThemeError as exc:
                        messages.error(request, str(exc))
                    else:
                        record_audit(
                            action="theme.published",
                            tenant=tenant,
                            user=request.user,
                            entity=theme,
                            after={"version": publication.version_number},
                            request=request,
                        )
                        messages.success(
                            request,
                            f"Tema versi {publication.version_number} diterbitkan untuk pelanggan.",
                        )
                else:
                    messages.success(request, "Draft disimpan. Pelanggan belum terpengaruh.")
                return redirect("themes:editor")
    else:
        form = ThemeConfigForm(
            initial={**theme.draft_configuration, "template": theme.template_id},
            allowed_templates=allowed,
        )

    return render(
        request,
        "themes/editor.html",
        {
            "theme": theme,
            "form": form,
            "templates": allowed,
            "publication": services.current_publication(tenant),
            "draft_config": {**services.DEFAULT_CONFIG, **(theme.draft_configuration or {})},
        },
    )


@login_required
@require_tenant
@require_permission(Perm.THEMES_MANAGE)
@require_POST
def publish(request):
    try:
        theme = services.ensure_theme(request.tenant)
    except services.ThemeError as exc:
        messages.error(request, str(exc))
        return redirect("themes:editor")
    try:
        publication = services.publish(tenant_theme=theme, actor=request.user)
    except services.ThemeError as exc:
        messages.error(request, str(exc))
    else:
        record_audit(
            action="theme.published",
            tenant=request.tenant,
            user=request.user,
            entity=theme,
            after={"version": publication.version_number},
            request=request,
        )
        messages.success(request, f"Tema versi {publication.version_number} diterbitkan.")
    return redirect("themes:editor")


@login_required
@require_tenant
@require_permission(Perm.THEMES_MANAGE)
def preview(request):
    """Render the customer menu with the draft configuration."""
    config = {**services.DEFAULT_CONFIG, **(services.ensure_theme(request.tenant).draft_configuration or {})}
    table = request.branch.tables.first() if request.branch else None
    return render(
        request,
        "themes/preview.html",
        {"config": config, "table": table, "tenant": request.tenant},
    )
