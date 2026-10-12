"""Seed a demo tenant with an owner, menu and tables for manual testing."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import BranchProduct, Category, Product
from apps.tables.models import Table
from apps.tenants.models import Tenant
from apps.tenants.services import register_business

User = get_user_model()

DEMO_MENU = [
    ("Kopi", [("Kopi Susu", "18000"), ("Americano", "15000")]),
    ("Non-Kopi", [("Matcha Latte", "22000"), ("Teh Manis", "10000")]),
]


class Command(BaseCommand):
    help = "Buat tenant demo beserta menu dan meja untuk uji manual."

    @transaction.atomic
    def handle(self, *args, **options):
        email = "owner@portatap.test"
        password = "portatap12345"
        user, created = User.objects.get_or_create(
            email=email, defaults={"name": "Demo Owner"}
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])

        tenant = Tenant.objects.filter(memberships__user=user).first()
        if tenant is None:
            tenant, branch = register_business(
                owner=user, business_name="Kopi Demo", branch_name="Pusat"
            )
        else:
            branch = tenant.branches.first()

        for category_name, products in DEMO_MENU:
            category, _ = Category.objects.get_or_create(tenant=tenant, name=category_name)
            for product_name, price in products:
                product, _ = Product.objects.get_or_create(
                    tenant=tenant, name=product_name, defaults={"category": category}
                )
                BranchProduct.objects.get_or_create(
                    branch=branch,
                    product=product,
                    defaults={
                        "price": Decimal(price),
                        "on_hand": 50,
                        "track_stock": True,
                    },
                )

        if not Table.objects.filter(branch=branch).exists():
            for number in ["A1", "A2", "B1"]:
                Table.objects.create(branch=branch, table_number=number, name=f"Meja {number}")

        table = Table.objects.filter(branch=branch).first()
        self.stdout.write(self.style.SUCCESS("Demo siap."))
        self.stdout.write(f"Login  : {email} / {password}")
        self.stdout.write(f"Menu   : /r/{table.qr_token}/")
        self.stdout.write("Portal : /app/")
