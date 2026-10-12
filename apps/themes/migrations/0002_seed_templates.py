"""Seed the starter theme templates.

Tenants pick from these in the appearance editor; the catalogue grows as new
templates are built and registered from the platform side.
"""

from django.db import migrations

TEMPLATES = [
    {
        "template_key": "minimal-list",
        "name": "Minimal",
        "version": "1.0.0",
        "minimum_plan": "STARTER",
        "default_configuration": {"layout": "list", "primary_color": "#0068f9"},
    },
    {
        "template_key": "editorial-grid",
        "name": "Editorial",
        "version": "1.0.0",
        "minimum_plan": "GROWTH",
        "default_configuration": {"layout": "grid", "primary_color": "#6736eb"},
    },
    {
        "template_key": "signature",
        "name": "Signature",
        "version": "1.0.0",
        "minimum_plan": "BUSINESS",
        "default_configuration": {"layout": "grid", "primary_color": "#046645"},
    },
]


def create_templates(apps, schema_editor):
    ThemeTemplate = apps.get_model("themes", "ThemeTemplate")
    for template in TEMPLATES:
        ThemeTemplate.objects.update_or_create(
            template_key=template["template_key"], defaults={**template}
        )


def remove_templates(apps, schema_editor):
    ThemeTemplate = apps.get_model("themes", "ThemeTemplate")
    ThemeTemplate.objects.filter(
        template_key__in=[item["template_key"] for item in TEMPLATES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("themes", "0001_initial")]
    operations = [migrations.RunPython(create_templates, remove_templates)]
