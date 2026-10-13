"""Public website views: landing page, blog and news.

All content here is public and read-only. Draft posts are never exposed.
"""

from django.http import Http404
from django.shortcuts import render

from apps.subscriptions.models import Plan, PlanStatus
from apps.website import selectors
from apps.website.models import PostKind
from apps.website.services import render_body

PROBLEMS = [
    "Order masih dicatat manual oleh kasir, dan sering terlewat saat jam sibuk.",
    "Pesanan salah diteruskan ke dapur, atau menunggu terlalu lama tanpa ada yang sadar.",
    "Harga dan ketersediaan berbeda di tiap cabang, tapi tidak terkontrol dari satu tempat.",
    "Stok tidak tercatat, jadi menu baru ditandai habis setelah pelanggan mengeluh.",
]

FEATURES = [
    {
        "title": "Pelanggan memesan dari meja, tanpa antre dan tanpa aplikasi",
        "body": "Tempel satu QR di meja. Pelanggan memindai, memilih menu, dan checkout "
        "sendiri — lengkap dengan nomor order untuk melacak statusnya.",
    },
    {
        "title": "Kasir dan dapur selalu sinkron",
        "body": "Order masuk ke dashboard kasir dengan peringatan 3 menit dan penanda "
        "terlambat 5 menit. Dapur hanya menerima order yang sudah boleh diproses.",
    },
    {
        "title": "Harga dan stok per cabang",
        "body": "Atur harga, ketersediaan, dan stok tiap cabang. Stok direservasi saat "
        "checkout supaya tidak pernah terjual dua kali.",
    },
    {
        "title": "Pembayaran dan refund yang tercatat",
        "body": "Tunai dikonfirmasi kasir, digital diverifikasi langsung dari penyedia "
        "pembayaran. Refund punya alasan, pelaksana, dan batas nominal.",
    },
    {
        "title": "Laporan penjualan siap ekspor",
        "body": "Penjualan kotor, diskon, penjualan bersih, pembayaran tertagih, dan "
        "refund dalam satu tampilan — tinggal unduh CSV-nya.",
    },
]

STEPS = [
    ("Siapkan menu", "Buat kategori dan produk, lalu atur harga per cabang."),
    ("Buat meja dan cetak QR", "Setiap meja punya QR sendiri untuk dibuka pelanggan."),
    ("Terima order", "Kasir menerima, dapur memproses, dan order selesai tercatat."),
]


def landing(request):
    return render(
        request,
        "website/landing.html",
        {
            "problems": PROBLEMS,
            "features": FEATURES,
            "steps": STEPS,
            "plans": Plan.objects.filter(status=PlanStatus.ACTIVE).order_by("monthly_price"),
        },
    )


def _post_list(request, *, kind: str, heading: str, description: str):
    return render(
        request,
        "website/post_list.html",
        {
            "kind": kind,
            "heading": heading,
            "description": description,
            "posts": selectors.published_posts(kind=kind),
        },
    )


def blog_list(request):
    return _post_list(
        request,
        kind=PostKind.BLOG,
        heading="Blog",
        description="Catatan tentang operasional, menu, dan pertumbuhan bisnis F&B.",
    )


def news_list(request):
    return _post_list(
        request,
        kind=PostKind.NEWS,
        heading="Berita",
        description="Kabar terbaru seputar PortaTap.",
    )


def _post_detail(request, slug: str, *, kind: str):
    post = selectors.published_post_or_none(slug, kind=kind)
    if post is None:
        raise Http404("Tulisan tidak ditemukan.")
    return render(
        request,
        "website/post_detail.html",
        {
            "post": post,
            "kind": kind,
            "body_html": render_body(post.body),
            "related": selectors.related_posts(post, limit=3),
        },
    )


def blog_detail(request, slug):
    return _post_detail(request, slug, kind=PostKind.BLOG)


def news_detail(request, slug):
    return _post_detail(request, slug, kind=PostKind.NEWS)
