"""System role and permission registry.

Permissions are global definitions; each tenant gets its own copy of the system
roles (seeded on tenant creation) so owners can adjust them per business.
"""


class Perm:
    """Canonical permission codes. Adding one here makes it seedable everywhere."""

    ORDERS_VIEW = "orders.view"
    ORDERS_ACCEPT = "orders.accept"
    ORDERS_REJECT = "orders.reject"
    ORDERS_PREPARE = "orders.prepare"
    ORDERS_READY = "orders.ready"
    ORDERS_COMPLETE = "orders.complete"

    PAYMENTS_VIEW = "payments.view"
    PAYMENTS_CONFIRM_CASH = "payments.confirm_cash"

    REFUNDS_VIEW = "refunds.view"
    REFUNDS_REQUEST = "refunds.request"
    REFUNDS_APPROVE = "refunds.approve"

    CATALOG_VIEW = "catalog.view"
    CATALOG_MANAGE = "catalog.manage"

    TABLES_VIEW = "tables.view"
    TABLES_MANAGE = "tables.manage"

    INVENTORY_VIEW = "inventory.view"
    INVENTORY_MANAGE = "inventory.manage"

    PROMOTIONS_VIEW = "promotions.view"
    PROMOTIONS_MANAGE = "promotions.manage"

    REPORTS_VIEW = "reports.view"

    TEAM_MANAGE = "team.manage"
    THEMES_MANAGE = "themes.manage"
    SETTINGS_MANAGE = "settings.manage"
    SUBSCRIPTION_MANAGE = "subscription.manage"


ALL_PERMISSIONS: dict[str, str] = {
    Perm.ORDERS_VIEW: "Melihat order",
    Perm.ORDERS_ACCEPT: "Menerima order",
    Perm.ORDERS_REJECT: "Menolak order",
    Perm.ORDERS_PREPARE: "Memulai persiapan order",
    Perm.ORDERS_READY: "Menandai order siap",
    Perm.ORDERS_COMPLETE: "Menyelesaikan order",
    Perm.PAYMENTS_VIEW: "Melihat pembayaran",
    Perm.PAYMENTS_CONFIRM_CASH: "Mengonfirmasi pembayaran tunai",
    Perm.REFUNDS_VIEW: "Melihat refund",
    Perm.REFUNDS_REQUEST: "Mengajukan refund",
    Perm.REFUNDS_APPROVE: "Menyetujui refund",
    Perm.CATALOG_VIEW: "Melihat menu & produk",
    Perm.CATALOG_MANAGE: "Mengelola menu & produk",
    Perm.TABLES_VIEW: "Melihat meja",
    Perm.TABLES_MANAGE: "Mengelola meja & QR",
    Perm.INVENTORY_VIEW: "Melihat stok",
    Perm.INVENTORY_MANAGE: "Mengelola stok",
    Perm.PROMOTIONS_VIEW: "Melihat promosi",
    Perm.PROMOTIONS_MANAGE: "Mengelola promosi",
    Perm.REPORTS_VIEW: "Melihat laporan penjualan",
    Perm.TEAM_MANAGE: "Mengelola tim & akses",
    Perm.THEMES_MANAGE: "Mengelola tampilan menu",
    Perm.SETTINGS_MANAGE: "Mengelola pengaturan bisnis",
    Perm.SUBSCRIPTION_MANAGE: "Mengelola subscription",
}


class RoleCode:
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    CASHIER = "CASHIER"
    KITCHEN = "KITCHEN"


# System roles seeded for every tenant: role code -> (display name, permissions).
SYSTEM_ROLES: dict[str, tuple[str, list[str]]] = {
    RoleCode.OWNER: ("Owner", list(ALL_PERMISSIONS.keys())),
    RoleCode.MANAGER: (
        "Branch Manager",
        [
            Perm.ORDERS_VIEW,
            Perm.ORDERS_ACCEPT,
            Perm.ORDERS_REJECT,
            Perm.ORDERS_PREPARE,
            Perm.ORDERS_READY,
            Perm.ORDERS_COMPLETE,
            Perm.PAYMENTS_VIEW,
            Perm.PAYMENTS_CONFIRM_CASH,
            Perm.REFUNDS_VIEW,
            Perm.REFUNDS_REQUEST,
            Perm.REFUNDS_APPROVE,
            Perm.CATALOG_VIEW,
            Perm.CATALOG_MANAGE,
            Perm.TABLES_VIEW,
            Perm.TABLES_MANAGE,
            Perm.INVENTORY_VIEW,
            Perm.INVENTORY_MANAGE,
            Perm.PROMOTIONS_VIEW,
            Perm.PROMOTIONS_MANAGE,
            Perm.REPORTS_VIEW,
        ],
    ),
    RoleCode.CASHIER: (
        "Cashier",
        [
            Perm.ORDERS_VIEW,
            Perm.ORDERS_ACCEPT,
            Perm.ORDERS_REJECT,
            Perm.ORDERS_COMPLETE,
            Perm.PAYMENTS_VIEW,
            Perm.PAYMENTS_CONFIRM_CASH,
            Perm.REFUNDS_VIEW,
            Perm.REFUNDS_REQUEST,
            Perm.CATALOG_VIEW,
            Perm.TABLES_VIEW,
        ],
    ),
    RoleCode.KITCHEN: (
        "Kitchen Staff",
        [
            Perm.ORDERS_VIEW,
            Perm.ORDERS_PREPARE,
            Perm.ORDERS_READY,
        ],
    ),
}

# Roles that may see every branch of the tenant regardless of branch memberships.
TENANT_WIDE_ROLES = {RoleCode.OWNER, RoleCode.MANAGER}
