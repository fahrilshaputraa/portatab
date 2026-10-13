"""Seed demo data: a tenant with menu/tables plus sample blog & news posts."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import BranchProduct, Category, Product
from apps.platform_admin.services import grant_platform_admin
from apps.subscriptions.services import start_trial
from apps.tables.models import Table
from apps.tenants.models import Tenant
from apps.tenants.services import register_business
from apps.website.models import Post, PostKind
from apps.website.services import unique_post_slug

User = get_user_model()

DEMO_MENU = [
    ("Kopi", [("Kopi Susu", "18000"), ("Americano", "15000")]),
    ("Non-Kopi", [("Matcha Latte", "22000"), ("Teh Manis", "10000")]),
]

DEMO_POSTS = [
    {
        "kind": PostKind.BLOG,
        "title": "Menghitung harga jual kopi susu tanpa menebak-nebak",
        "excerpt": "Tiga angka yang perlu Anda tahu sebelum menetapkan harga menu.",
        "is_featured": True,
        "body": (
            "## Mulai dari biaya per gelas\n\n"
            "Harga jual yang sehat berangkat dari biaya bahan, bukan dari harga kedai sebelah.\n\n"
            "- Catat biaya bahan per gelas\n"
            "- Tambahkan biaya operasional harian\n"
            "- Sisakan margin untuk diri sendiri\n\n"
            "## Tentukan satu harga acuan\n\n"
            "Setelah punya harga acuan, atur variasi per cabang lewat halaman produk."
        ),
    },
    {
        "kind": PostKind.BLOG,
        "title": "Kapan sebaiknya menambah cabang kedua?",
        "excerpt": "Tanda-tanda operasional cabang pertama sudah cukup stabil untuk berkembang.",
        "body": (
            "## Cabang pertama harus stabil dulu\n\n"
            "Menambah cabang sebelum alur order rapi hanya memindahkan masalah ke tempat baru.\n\n"
            "## Tiga tanda yang biasanya muncul\n\n"
            "- Order harian sudah rutin dan tidak ada yang terlewat\n"
            "- Stok tercatat dan tidak sering kehabisan\n"
            "- Kasir dan dapur sudah terbiasa dengan alurnya"
        ),
    },
    {
        "kind": PostKind.NEWS,
        "title": "PortaTap membuka program uji coba untuk kedai kopi",
        "excerpt": "Kami mengundang 20 kedai kopi untuk mencoba PortaTap tanpa biaya.",
        "body": (
            "Program uji coba terbatas dibuka untuk kedai kopi dan warung modern.\n\n"
            "## Yang peserta dapatkan\n\n"
            "- Pendampingan penyiapan menu dan QR meja\n"
            "- Masukan langsung ke tim produk\n"
            "- Harga khusus untuk tahun pertama"
        ),
    },
    {
        "kind": PostKind.NEWS,
        "title": "Pembayaran digital kini diverifikasi otomatis",
        "excerpt": "Status pembayaran digital diperbarui dari penyedia pembayaran, bukan dari bukti transfer.",
        "body": (
            "Konfirmasi pembayaran digital sekarang mengikuti verifikasi dari penyedia pembayaran.\n\n"
            "## Artinya untuk operasional\n\n"
            "- Order digital masuk dapur setelah pembayaran benar-benar lunas\n"
            "- Notifikasi ganda tidak membuat pembayaran tercatat dua kali\n"
            "- Kasir tetap bisa mengonfirmasi pembayaran tunai secara manual"
        ),
    },
]


class Command(BaseCommand):
    help = "Buat tenant demo, menu, meja, dan contoh konten blog/berita."

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
            # Re-running the seed on a tenant created before subscriptions existed
            # must leave the demo usable, not stuck without a plan.
            start_trial(tenant=tenant)

        self._seed_menu(tenant, branch)
        self._seed_tables(branch)
        self._seed_posts(user)
        grant_platform_admin(user)

        table = Table.objects.filter(branch=branch).first()
        self.stdout.write(self.style.SUCCESS("Demo siap."))
        self.stdout.write(f"Login  : {email} / {password}")
        self.stdout.write(f"Menu   : /r/{table.qr_token}/")
        self.stdout.write("Portal : /app/")
        self.stdout.write("Konten : /manage/")

    def _seed_menu(self, tenant, branch):
        for category_name, products in DEMO_MENU:
            category, _ = Category.objects.get_or_create(tenant=tenant, name=category_name)
            for product_name, price in products:
                product, _ = Product.objects.get_or_create(
                    tenant=tenant, name=product_name, defaults={"category": category}
                )
                BranchProduct.objects.get_or_create(
                    branch=branch,
                    product=product,
                    defaults={"price": Decimal(price), "on_hand": 50, "track_stock": True},
                )

    def _seed_tables(self, branch):
        for number in ["A1", "A2", "B1"]:
            Table.objects.get_or_create(
                branch=branch, table_number=number, defaults={"name": f"Meja {number}"}
            )

    def _seed_posts(self, author):
        for data in DEMO_POSTS:
            Post.objects.get_or_create(
                slug=unique_post_slug(data["title"], kind=data["kind"]),
                defaults={**data, "author": author, "status": "DRAFT"},
            )
        for post in Post.objects.all():
            if not post.is_published:
                post.publish()
