"""Shared pytest fixtures.

Everything is built through the real services so tests exercise the same code
paths production uses.
"""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from apps.accounts.roles import RoleCode
from apps.accounts.services import create_membership, seed_system_roles
from apps.catalog.models import BranchProduct, Category, Product, ProductVariant
from apps.tables.models import Table
from apps.tenants.models import Branch, Tenant

User = get_user_model()


@pytest.fixture
def tenant(db):
    tenant = Tenant.objects.create(name="Kopi Senja", slug="kopi-senja")
    seed_system_roles(tenant)
    return tenant


@pytest.fixture
def branch(tenant):
    return Branch.objects.create(tenant=tenant, name="Pusat", code="MAIN")


@pytest.fixture
def owner(tenant, branch):
    user = User.objects.create_user(
        email="owner@example.com", password="pass12345", name="Owner"
    )
    create_membership(tenant=tenant, user=user, role_code=RoleCode.OWNER, branches=[branch])
    return user


@pytest.fixture
def cashier(tenant, branch):
    user = User.objects.create_user(
        email="kasir@example.com", password="pass12345", name="Kasir"
    )
    create_membership(tenant=tenant, user=user, role_code=RoleCode.CASHIER, branches=[branch])
    return user


@pytest.fixture
def category(tenant):
    return Category.objects.create(tenant=tenant, name="Kopi")


@pytest.fixture
def product(tenant, category):
    return Product.objects.create(tenant=tenant, category=category, name="Kopi Susu")


@pytest.fixture
def variant(product):
    return ProductVariant.objects.create(product=product, name="Large", price_delta=Decimal("3000"))


@pytest.fixture
def branch_product(branch, product):
    return BranchProduct.objects.create(
        branch=branch, product=product, price=Decimal("15000"), on_hand=10, track_stock=True
    )


@pytest.fixture
def table(branch):
    return Table.objects.create(branch=branch, table_number="A1", name="Meja A1")


@pytest.fixture
def other_tenant(db):
    tenant = Tenant.objects.create(name="Bakso Lain", slug="bakso-lain")
    seed_system_roles(tenant)
    return tenant


@pytest.fixture
def other_branch(other_tenant):
    return Branch.objects.create(tenant=other_tenant, name="Cabang Lain", code="MAIN")


@pytest.fixture
def other_owner(other_tenant, other_branch):
    user = User.objects.create_user(
        email="lain@example.com", password="pass12345", name="Orang Lain"
    )
    create_membership(
        tenant=other_tenant, user=user, role_code=RoleCode.OWNER, branches=[other_branch]
    )
    return user


@pytest.fixture
def platform_admin(db):
    """A platform admin granted through the real service (not a raw flag)."""
    from apps.platform_admin.services import grant_platform_admin

    user = User.objects.create_user(
        email="admin@portatap.test", password="pass12345", name="Admin Platform"
    )
    grant_platform_admin(user)
    return user
