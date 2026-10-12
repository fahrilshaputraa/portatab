# PortaTap

Multi-tenant SaaS untuk bisnis F&B: pemesanan lewat QR meja, manajemen menu,
operasional kasir & dapur, pembayaran, stok, dan laporan.

Dokumen produk dan arsitektur ada di [`docs/`](./docs) dan aturan kerja di
[`AGENTS.md`](./AGENTS.md). Panduan gaya visual di [`DESIGN.md`](./DESIGN.md).

## Stack

- **Backend:** Python, Django 6.1, Django Templates, Django ORM
- **Frontend:** Django Templates + HTMX + Tailwind CSS v4, JavaScript seperlunya
- **Database:** PostgreSQL
- **Pembayaran digital:** Midtrans (Snap)

## Requirement

- Python ≥ 3.12 (dikelola dengan [uv](https://docs.astral.sh/uv/))
- Node.js (untuk build Tailwind CSS)
- PostgreSQL

## Setup

```bash
# 1. Dependensi Python
uv sync

# 2. Konfigurasi environment
cp .env.example .env        # lalu sesuaikan nilainya
# DATABASE_URL, DJANGO_SECRET_KEY, kredensial Midtrans

# 3. Database
#    Buat database sesuai DATABASE_URL, lalu:
uv run python manage.py migrate

# 4. Aset frontend (Tailwind)
npm install --include=dev   # bila npm Anda mengeset `omit=dev` secara global
npm run build:css

# 5. Data demo (opsional)
uv run python manage.py seed_demo

# 6. Jalankan
uv run python manage.py runserver
```

Portal owner/staf: `/app/` · Menu pelanggan: `/r/<qr-token>/` ·
Admin Django: `/admin/`.

### Akun demo (`seed_demo`)

`owner@portatap.test` / `portatap12345` — perintah ini juga mencetak URL menu pelanggan.

## Development

```bash
uv run python manage.py runserver     # dev server
npm run watch:css                     # rebuild CSS saat mengedit template
uv run pytest                         # test
uv run ruff check .                   # lint
uv run ruff format .                  # format (opsional)
```

Timer kasir (peringatan 3 menit, tanda terlambat 5 menit) dijalankan manual lewat
management command — tidak ada Celery di MVP:

```bash
uv run python manage.py evaluate_orders           # semua cabang
uv run python manage.py evaluate_orders --branch <id>
```

Jadwalkan tiap menit di cron / scheduler produksi.

## Struktur proyek

```
config/            # proyek Django: settings (base/dev/prod/test), urls, wsgi/asgi
apps/
  core/            # base model, helper form, template filter bersama
  accounts/        # user, membership, role, permission, invitation
  tenants/         # tenant, branch, settings, audit, otorisasi
  customers/       # identitas pelanggan
  catalog/         # kategori, produk, varian, harga & stok per cabang
  tables/          # meja, token QR, sesi meja
  orders/          # order, item snapshot, riwayat status, checkout, menu pelanggan
  payments/        # payment, attempt, refund, webhook, adapter Midtrans
  inventory/       # reservasi & ledger stok
  notifications/   # notifikasi staf + inbox
  promotions/      # promo pelanggan
  subscriptions/   # plan, subscription, invoice, voucher
  themes/          # template & publikasi tema
  reports/         # laporan penjualan + ekspor CSV
  website/         # landing page publik, blog, berita, admin konten
  platform_admin/  # konsol admin platform (tenant, audit, health)
templates/         # layout & komponen bersama; `menu/` untuk pelanggan
docs/              # PRD, ERD, ARCHITECTURE, BUSINESS-RULES, API-CONVENTIONS, DEPLOYMENT
```

Template per-domain tinggal di `apps/<app>/templates/<app>/`; detail konvensi di
[`templates/README.md`](./templates/README.md).

## Yang sudah berjalan

**Alur inti**

- Fondasi multi-tenant: tenant, cabang, membership, role & permission,
  isolasi data, audit log.
- Onboarding owner (registrasi → tenant → cabang pertama) + trial otomatis.
- Manajemen menu: kategori, produk, varian, harga & stok per cabang.
- Meja & QR (termasuk cetak dan regenerasi token).
- Menu QR pelanggan, keranjang, checkout idempoten, lacak status.
- Kasir: daftar order, terima/tolak, timer 3/5 menit.
- Kitchen Display dengan gerbang pembayaran (order digital hanya masuk dapur
  setelah `PAID`).
- Pembayaran tunai (konfirmasi kasir) dan digital (Midtrans + webhook idempoten
  + rekonsiliasi terjadwal).
- Refund penuh dengan status, batas nominal, jejak audit, dan refund digital
  lewat penyedia.
- Reservasi stok atomik + ledger pergerakan stok.
- Laporan penjualan dasar + ekspor CSV.

**Manajemen bisnis**

- Pengaturan bisnis: profil, CRUD cabang, jeda penerimaan order, kebijakan
  operasional (order tunai masuk dapur, ambang stok rendah).
- Tim & Akses: undang staf lewat email, atur role + akses cabang, jaga agar
  owner terakhir tidak bisa dicabut.
- Promosi pelanggan: diskon nominal/persentase, kuota aman dari race, batas per
  pelanggan, pemulihan kuota saat order dibatalkan.
- Inbox notifikasi dengan badge belum dibaca.
- Langganan: trial, ubah paket, invoice dengan snapshot harga, voucher, dan
  penegakan batas paket di backend.
- Tampilan Menu: pilih template, logo/banner/warna/layout, draft terpisah dari
  versi terbit, validasi kontras warna.

**Situs publik & platform**

- Landing page publik, blog, dan berita; artikel ditulis lewat konsol admin.
- Konsol admin platform: daftar & detail tenant, suspend/aktifkan, audit log,
  dan system health.

## Deployment

Panduan deploy, variabel environment, job terjadwal, backup, dan checklist rilis
ada di [`docs/DEPLOYMENT.md`](./docs/DEPLOYMENT.md).

## Belum diimplementasikan

Yang masih terbuka (jujur, bukan tersembunyi):

- **Rate limiting** pada login, checkout publik, dan penukaran promo belum ada —
  untuk sementara pasang di proxy.
- **Uji beban/performa** belum dijalankan.
- **Error tracking** (mis. Sentry) belum dipasang; sinyalnya masih log.
- **Provider pembayaran kedua** butuh adapter sendiri di
  `apps/payments/providers/`.
- Keputusan produk di `docs/PRD.md` §27 (ambang refund, masa berlaku reservasi
  stok, grace period langganan, retensi data) masih perlu ditetapkan.


## Keamanan

Kredensial tidak pernah masuk source control (`.env` di-`.gitignore`). Rahasia
Midtrans hanya dipakai di sisi server; webhook memverifikasi signature dan
diproses idempoten. Semua endpoint portal memvalidasi membership, role, dan akses
cabang di backend.
