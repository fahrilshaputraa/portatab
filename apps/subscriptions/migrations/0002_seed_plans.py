"""Seed the subscription plans described in docs/PRD.md §3.1.

The landing page reads plans from the database rather than hardcoding prices, so
this is the single source of truth for the published tiers.
"""

from django.db import migrations

PLANS = [
    {
        "code": "STARTER",
        "name": "Starter",
        "monthly_price": "49000.00",
        "max_branches": 1,
        "max_accounts": 5,
        "features": {"themes": 3, "reports": "basic", "inventory": "simple"},
    },
    {
        "code": "GROWTH",
        "name": "Growth",
        "monthly_price": "149000.00",
        "max_branches": 3,
        "max_accounts": 15,
        "features": {
            "themes": 6,
            "reports": "per_branch",
            "inventory": "history",
            "csv_export": True,
        },
    },
    {
        "code": "BUSINESS",
        "name": "Business",
        "monthly_price": "299000.00",
        "max_branches": 10,
        "max_accounts": 50,
        "features": {
            "themes": "exclusive",
            "reports": "cross_branch",
            "inventory": "history",
            "csv_export": True,
            "priority_support": True,
        },
    },
]


def create_plans(apps, schema_editor):
    Plan = apps.get_model("subscriptions", "Plan")
    for plan in PLANS:
        Plan.objects.update_or_create(code=plan["code"], defaults={**plan})


def remove_plans(apps, schema_editor):
    Plan = apps.get_model("subscriptions", "Plan")
    Plan.objects.filter(code__in=[p["code"] for p in PLANS]).delete()


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0001_initial")]
    operations = [migrations.RunPython(create_plans, remove_plans)]
