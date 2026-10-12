
# PRODUCT REQUIREMENTS DOCUMENT (PRD)

# PortaTap — QR Ordering & F&B Management SaaS

**Versi:** 1.0
**Status:** Draft untuk eksekusi MVP
**Tanggal:** 12 Oktober 2026
**Product Owner:** PortaTap Founder
**Target pasar:** UMKM F&B, warung modern, kedai kopi, kafe kecil, dan bisnis F&B multi-cabang
**Model bisnis:** Subscription SaaS
**Platform:** Web application, responsive desktop dan mobile

---

# 1. PRODUCT OVERVIEW

## 1.1 Deskripsi Produk

PortaTap adalah platform SaaS untuk membantu bisnis Food & Beverage (F&B) mengelola pemesanan makanan dan minuman melalui QR Code pada meja.

Pelanggan dapat memindai QR meja, melihat menu, memilih produk, checkout, melakukan pembayaran, dan melacak status pesanan tanpa harus membuat akun.

Pemilik bisnis dan staf menggunakan dashboard terpusat untuk mengelola menu, meja, order, pembayaran, stok, promosi, laporan, dan operasional cabang.

PortaTap juga menyediakan fitur kustomisasi tampilan QR menu agar setiap bisnis dapat menampilkan identitas visual yang sesuai dengan brand mereka.

## 1.2 Problem Statement

Bisnis F&B kecil sering menghadapi masalah berikut:

1. Pemesanan masih bergantung pada pencatatan manual oleh kasir.
2. Order dapat terlewat atau salah diteruskan ke dapur.
3. Menu dan harga sulit dikelola secara konsisten.
4. Stok produk tidak tercatat dengan baik.
5. Owner sulit memantau penjualan dan performa cabang.
6. QR menu yang tersedia sering memiliki tampilan generik dan kurang mencerminkan identitas brand.
7. Sistem POS dan digital ordering yang lebih lengkap bisa terasa mahal atau terlalu kompleks untuk bisnis kecil.

## 1.3 Product Vision

Menjadi platform QR ordering yang terjangkau, mudah digunakan, dan dapat dikembangkan bersama bisnis F&B dari satu kedai hingga beberapa cabang.

## 1.4 Product Goals

- Mempermudah pelanggan melakukan pemesanan mandiri melalui QR.
- Mempercepat alur order dari pelanggan ke kasir dan dapur.
- Menyediakan pencatatan transaksi yang konsisten dan dapat ditelusuri.
- Memberikan visibilitas stok, pembayaran, refund, dan penjualan.
- Memungkinkan owner mengelola satu atau banyak cabang.
- Menyediakan kustomisasi menu sesuai identitas brand.
- Menghasilkan pendapatan berulang melalui subscription.

## 1.5 Non-Goals MVP

Fitur berikut tidak menjadi prioritas MVP:

- Manajemen bahan baku, resep, dan food costing.
- Modul akuntansi lengkap.
- Payroll dan manajemen karyawan kompleks.
- Delivery fleet atau kurir internal.
- Loyalty points dan membership pelanggan.
- Integrasi dengan banyak payment gateway sekaligus.
- Website builder bebas atau custom HTML/JavaScript dari tenant.
- Marketplace template publik.
- Split bill dan penggabungan pembayaran kompleks.
- Native Android/iOS application.

---

# 2. TARGET USERS & PERSONAS

## 2.1 Business Owner

Pemilik bisnis yang ingin mengelola operasional dan performa usaha.

Kebutuhan:

- Melihat penjualan dan order.
- Mengelola produk dan harga.
- Mengelola staf dan cabang.
- Mengontrol stok, refund, dan promosi.
- Mengatur tampilan QR menu.
- Mengelola subscription.

## 2.2 Branch Manager

Pengelola operasional cabang.

Kebutuhan:

- Memantau order cabang.
- Mengelola ketersediaan produk dan stok sesuai izin.
- Mengawasi kasir dan dapur.
- Menyetujui refund sesuai batas kewenangan.
- Melihat laporan cabang.

## 2.3 Cashier

Staf yang menangani penerimaan order dan transaksi.

Kebutuhan:

- Mendapat notifikasi order baru.
- Mengonfirmasi atau menolak order.
- Mengonfirmasi pembayaran tunai.
- Menangani permintaan refund.
- Melihat status pembayaran dan order.

## 2.4 Kitchen Staff

Staf yang mempersiapkan pesanan.

Kebutuhan:

- Melihat antrean order yang sudah boleh diproses.
- Memulai persiapan.
- Menandai order siap disajikan.
- Mendapat notifikasi suara saat order baru masuk.

## 2.5 Customer

Pelanggan yang memesan makanan atau minuman.

Kebutuhan:

- Memindai QR meja.
- Melihat menu dan harga.
- Memilih produk dan varian.
- Checkout tanpa login.
- Memilih metode pembayaran.
- Melacak status order.
- Mengajukan refund melalui kasir jika ada masalah.

---

# 3. SUBSCRIPTION & MONETIZATION

## 3.1 Rencana Paket

Harga berikut merupakan hipotesis awal yang akan divalidasi melalui pilot.

### Starter — Rp49.000/bulan

Target: kedai kecil dan UMKM F&B.

Fitur:

- 1 cabang.
- Maksimal 5 akun owner/staf.
- QR menu dan pemesanan dine-in.
- Dashboard order dan Kitchen Display.
- Pembayaran tunai dan satu integrasi pembayaran digital.
- Stok produk sederhana.
- Laporan penjualan dasar.
- 3 template dasar.
- Logo, warna utama, banner, dan layout grid/list.

### Growth — Rp149.000/bulan

Target: bisnis yang berkembang dan membutuhkan lebih banyak fleksibilitas.

Fitur:

- Maksimal 3 cabang.
- Maksimal 15 akun owner/staf.
- Seluruh fitur Starter.
- Laporan per cabang dan gabungan.
- Riwayat perubahan stok.
- Ekspor laporan dasar.
- Katalog template lebih luas.
- Kustomisasi visual tambahan.

### Business — Rp299.000/bulan

Target: bisnis multi-cabang yang membutuhkan kontrol dan identitas visual lebih khusus.

Fitur:

- Maksimal 10 cabang.
- Maksimal 50 akun owner/staf.
- Seluruh fitur Growth.
- Analitik lintas cabang.
- Hak akses lebih terperinci.
- Template eksklusif.
- Opsi layanan custom UI oleh tim PortaTap dengan cakupan yang disepakati.
- Dukungan prioritas.

**Catatan:** layanan pembuatan UI khusus tidak otomatis berarti unlimited custom design dalam biaya subscription. Biaya implementasi dan maintenance perlu ditentukan berdasarkan scope.

## 3.2 Subscription Rules

- Subscription dimiliki oleh tenant, bukan oleh akun owner atau staf.
- Satu tenant mempunyai satu subscription aktif pada satu waktu.
- Paket menentukan batas cabang, akun, dan fitur.
- Status subscription dipisahkan dari status operasional tenant.
- Perubahan harga paket tidak mengubah invoice yang sudah diterbitkan.
- Batas penggunaan paket divalidasi oleh backend.
- Pembayaran subscription PortaTap terpisah dari pembayaran makanan pelanggan.

Status subscription:

- `trialing`
- `active`
- `past_due`
- `cancelled`
- `expired`

## 3.3 Free Trial

Usulan awal: trial selama 14 hari untuk tenant baru.

Ketentuan:

- Masa trial ditentukan oleh backend.
- Owner dapat melihat tanggal berakhirnya trial.
- Saat trial berakhir, tenant menerima notifikasi untuk berlangganan.
- Perilaku aplikasi setelah subscription berakhir harus mengikuti kebijakan grace period dan pembatasan akses yang ditetapkan.

## 3.4 Subscription Voucher

Admin PortaTap dapat membuat voucher untuk diskon subscription.

Contoh:

- Kode: `EARLYBIRD`
- Paket: Starter.
- Harga normal: Rp49.000/bulan.
- Harga promo: Rp39.000/bulan.
- Durasi: 3 bulan.
- Kuota: sesuai konfigurasi admin.
- Target: tenant baru.
- Setelah promo: kembali ke harga normal.

Business rules:

- Voucher diverifikasi di backend.
- Voucher hanya dapat digunakan jika memenuhi ketentuan.
- Penggunaan voucher dicatat per tenant dan subscription.
- Sistem menyimpan harga, diskon, periode promo, dan nilai invoice.
- Voucher early adopter hanya dapat digunakan sekali per tenant, kecuali aturan promo menyatakan berbeda.
- Voucher subscription tidak dapat digunakan untuk diskon order makanan.

Entitas terkait:

- `plans`
- `plan_features`
- `subscriptions`
- `subscription_invoices`
- `promotions`
- `promotion_codes`
- `promotion_redemptions`

---

# 4. SYSTEM ARCHITECTURE

## 4.1 Portal Architecture

PortaTap menggunakan satu backend dan satu PostgreSQL database untuk MVP.

Frontend dapat dipisahkan menjadi beberapa area:

- Owner Portal: `app.portatap.com`
- Staff Portal: `staff.portatap.com`
- Customer QR Menu: domain publik PortaTap.
- Admin Portal: area khusus untuk administrasi platform.

Subdomain di atas adalah rancangan, bukan persyaratan domain final.

## 4.2 Authentication & Authorization

- Owner dan staf menggunakan sistem autentikasi yang sama.
- Satu user account dapat mempunyai membership pada beberapa tenant.
- Setiap membership mempunyai role dan akses cabang.
- Platform Admin memiliki otorisasi terpisah dari tenant owner.
- Backend memvalidasi role, tenant membership, dan branch access pada setiap request.
- Frontend tidak boleh menjadi satu-satunya lapisan keamanan.
- Password disimpan menggunakan mekanisme hashing yang aman.
- Session dan token harus memiliki mekanisme expiry dan revocation yang sesuai.

## 4.3 Multi-Tenant Isolation

MVP menggunakan satu database PostgreSQL dengan shared schema dan tenant-scoped data.

Business rules:

- Setiap data operasional harus terhubung ke tenant yang benar.
- Data cabang harus memiliki relasi ke tenant.
- Query tidak boleh mempercayai `tenant_id` dari browser tanpa validasi membership.
- Semua endpoint memvalidasi tenant dan branch access.
- PostgreSQL Row-Level Security dapat digunakan sebagai lapisan pertahanan tambahan.
- Log, file upload, dan aset gambar juga harus mengikuti isolasi tenant.

## 4.4 Realtime

Realtime digunakan untuk:

- Order baru masuk.
- Update status order.
- Update antrean dapur.
- Peringatan order terlambat.
- Update status pembayaran yang relevan.

Implementasi dapat menggunakan WebSocket atau Server-Sent Events.

Realtime hanya menjadi mekanisme distribusi event. Database tetap menjadi sumber kebenaran status transaksi.

---

# 5. USER ROLES & PERMISSIONS

| Modul           | Owner                   | Branch Manager          | Cashier                         | Kitchen Staff           |
| --------------- | ----------------------- | ----------------------- | ------------------------------- | ----------------------- |
| Dashboard       | Semua cabang            | Cabang yang diizinkan   | Ringkasan operasional           | Antrean dapur           |
| Menu & Products | Kelola                  | Sesuai izin             | Read-only atau terbatas         | Tidak                   |
| Tables & QR     | Kelola                  | Cabang yang diizinkan   | Lihat                           | Tidak                   |
| Orders          | Semua cabang            | Cabang yang diizinkan   | Kelola order                    | Update status persiapan |
| Payments        | Lihat semua             | Sesuai izin             | Proses pembayaran               | Tidak                   |
| Refunds         | Lihat dan mengatur izin | Menyetujui sesuai batas | Memproses sesuai izin           | Tidak                   |
| Inventory       | Semua cabang            | Kelola sesuai izin      | Sesuai izin                     | Tidak                   |
| Promotions      | Kelola                  | Sesuai izin             | Terapkan voucher pada transaksi | Tidak                   |
| Sales Reports   | Semua cabang            | Laporan cabang          | Ringkasan terbatas              | Tidak                   |
| Team & Access   | Kelola                  | Terbatas                | Tidak                           | Tidak                   |
| Theme Editor    | Kelola                  | Opsional sesuai izin    | Tidak                           | Tidak                   |
| Subscription    | Kelola                  | Tidak                   | Tidak                           | Tidak                   |

Akses refund dan perubahan sensitif dapat dibatasi berdasarkan nominal serta kebijakan owner.

---

# 6. TENANT PORTAL INFORMATION ARCHITECTURE

Sidebar Tenant Portal terdiri dari:

## Overview

- Dashboard

## Operational

- Orders
- Kitchen Display
- Payments & Refunds

## Business Management

- Menu & Products
- Tables & QR Codes
- Inventory
- Promotions

## Reports & Administration

- Sales Reports
- Team & Access
- Menu Appearance
- Business Settings
- Subscription & Billing

Menu ditampilkan sesuai role dan akses cabang pengguna.

---

# 7. BUSINESS ONBOARDING

## 7.1 Tenant Registration

Alur:

1. Owner mendaftar.
2. Sistem membuat user account.
3. Owner membuat tenant/business profile.
4. Sistem membuat tenant membership dengan role Owner.
5. Owner membuat cabang pertama.
6. Owner mengatur identitas bisnis dan jam operasional.
7. Owner menambahkan produk dan kategori.
8. Owner membuat meja dan QR.
9. Owner memilih theme.
10. Tenant siap menerima order setelah seluruh konfigurasi wajib terpenuhi.

## 7.2 Staff Invitation

- Owner mengundang staf melalui email.
- Owner memilih role dan cabang.
- Jika user sudah ada, sistem menambahkan membership; tidak membuat akun duplikat.
- Jika user belum ada, sistem mengirim invitation untuk membuat akun.
- Invitation memiliki masa berlaku dan hanya dapat digunakan sesuai ketentuannya.
- Setelah login, pengguna dengan beberapa membership dapat memilih workspace.

---

# 8. MENU & PRODUCT MANAGEMENT

## 8.1 Categories

Owner dapat:

- Membuat dan mengubah kategori.
- Mengatur urutan kategori.
- Mengaktifkan atau menonaktifkan kategori.
- Menentukan kategori yang tampil pada QR menu.

## 8.2 Products

Data produk:

- Nama.
- Deskripsi.
- Foto.
- Kategori.
- Status aktif.
- Informasi varian.
- Ketersediaan per cabang.

## 8.3 Product Variants

Contoh:

- Regular.
- Large.
- Hot.
- Iced.

Setiap varian dapat mempunyai harga dan status ketersediaan tersendiri.

## 8.4 Branch Product Configuration

Produk dapat dijual pada cabang tertentu.

Konfigurasi:

- Harga per cabang.
- Status tersedia.
- Stok produk.
- Batas stok atau ambang stok rendah.

## 8.5 Order Snapshot

Saat checkout, sistem menyimpan snapshot:

- Nama produk.
- Varian.
- Harga satuan.
- Kuantitas.
- Diskon.
- Subtotal.

Perubahan menu tidak boleh mengubah order lama.

---

# 9. TABLE & QR CODE MANAGEMENT

## 9.1 Table Management

Owner dapat:

- Membuat meja.
- Mengubah nama atau nomor meja.
- Mengaktifkan atau menonaktifkan meja.
- Melihat order aktif yang terhubung ke meja.
- Mengunduh QR satuan atau dalam batch.
- Mencetak QR untuk dipasang di meja.
- Meregenerasi token QR jika diperlukan.

## 9.2 QR Rules

- QR mengidentifikasi meja dan cabang yang terdaftar.
- Backend memvalidasi meja dan cabang ketika menu dibuka dan checkout dilakukan.
- QR bukan bukti pembayaran dan bukan otorisasi untuk akses dashboard.
- Meja yang dinonaktifkan tidak dapat menerima order baru.
- QR yang diregenerasi mengikuti kebijakan invalidasi token sebelumnya.

## 9.3 Table Sessions

Sistem dapat menggunakan `table_sessions` untuk mengelompokkan beberapa order selama satu kunjungan meja.

Namun:

- Setiap checkout tetap menghasilkan order baru.
- Order memiliki nomor dan status tersendiri.
- Pembayaran setiap order terpisah untuk MVP.
- Split bill dan penggabungan pembayaran tidak termasuk MVP.

---

# 10. CUSTOMER ORDERING FLOW

## 10.1 Customer Flow

1. Pelanggan scan QR meja.
2. Sistem memvalidasi QR dan membuka menu cabang.
3. Pelanggan melihat menu, harga, dan ketersediaan.
4. Pelanggan memilih produk dan varian.
5. Pelanggan menambahkan produk ke cart.
6. Pelanggan memilih metode pembayaran.
7. Pelanggan checkout.
8. Backend memvalidasi harga, ketersediaan, stok, dan total.
9. Sistem membuat order baru.
10. Sistem menampilkan nomor order dan status.
11. Pelanggan dapat melacak status order.

Pelanggan tidak wajib membuat akun.

## 10.2 Repeat Order

- Pelanggan dapat menggunakan QR meja yang sama untuk membuat order berikutnya.
- Setiap checkout menghasilkan order baru.
- Order baru tidak otomatis mengubah order lama.
- Pelanggan dapat melihat order aktif yang terkait dengan sesi meja melalui token akses yang valid.
- Pelanggan tidak boleh mengakses order pelanggan atau tenant lain.

---

# 11. ORDER MANAGEMENT

## 11.1 Order Status

Status utama:

- `PENDING`
- `CONFIRMED`
- `PREPARING`
- `READY`
- `COMPLETED`
- `REJECTED`
- `CANCELLED`

Makna:

- `PENDING`: order dibuat dan menunggu keputusan kasir.
- `CONFIRMED`: order diterima oleh kedai.
- `PREPARING`: dapur mulai memproses.
- `READY`: pesanan siap disajikan.
- `COMPLETED`: pesanan selesai diserahkan.
- `REJECTED`: order ditolak kedai.
- `CANCELLED`: order dibatalkan melalui aturan yang sah.

Status order tidak boleh digunakan untuk mewakili status pembayaran atau refund.

## 11.2 Order Confirmation

- Kasir dapat menerima atau menolak order `PENDING`.
- Kasir dapat memeriksa order saat pembayaran digital sedang berlangsung.
- Order digital tidak boleh masuk antrean dapur sebelum pembayaran terverifikasi `PAID`.
- Order tunai yang diterima dapat diteruskan ke dapur meskipun belum dibayar jika kebijakan kedai mengizinkan.
- Status order dan pembayaran dikelola terpisah.
- Setiap perubahan status dicatat dalam `order_status_history`.

## 11.3 Timeout Rules

- Pada menit ke-3 tanpa respons kasir, sistem mengirim peringatan.
- Pada menit ke-5, order ditandai terlambat.
- Order tidak otomatis dibatalkan.
- Order tetap `PENDING` sampai keputusan kasir atau tindakan lain yang sah.
- Timer menggunakan waktu server.
- Event peringatan harus idempotent agar tidak dikirim berulang tanpa alasan.
- Timeout konfirmasi kasir tidak boleh menimpa status pembayaran.

## 11.4 Order Rejection

Jika order ditolak:

- Sistem mencatat alasan penolakan.
- Reservasi stok dilepas jika aman.
- Jika order belum dibayar, penolakan dapat diselesaikan tanpa refund.
- Jika pembayaran sudah berhasil, sistem membuat kasus refund.
- Jika pembayaran masih belum pasti, sistem melakukan rekonsiliasi status sebelum menyelesaikan kasus.

## 11.5 Order History

Setiap order menyimpan:

- Nomor order.
- Tenant dan cabang.
- Meja atau sesi meja.
- Item dan snapshot harga.
- Subtotal, diskon, dan total.
- Status order.
- Waktu pembuatan dan perubahan.
- Metode pembayaran.
- Referensi pembayaran.
- Catatan penolakan atau pembatalan jika ada.

---

# 12. PAYMENT MANAGEMENT

## 12.1 Payment Methods

MVP mendukung:

- Tunai.
- Satu integrasi payment gateway digital yang dipilih saat implementasi.

Dukungan QRIS bergantung pada kemampuan dan ketentuan payment gateway yang digunakan.

## 12.2 Payment Status

- `UNPAID`
- `PENDING`
- `PAID`
- `FAILED`
- `EXPIRED`

Status pembayaran terpisah dari status order.

## 12.3 Cash Payment

- Kasir mengonfirmasi penerimaan uang.
- Sistem mencatat jumlah yang diterima, waktu, kasir, dan order terkait.
- Pembayaran yang sama tidak boleh tercatat dua kali.
- Koreksi transaksi harus melalui mekanisme yang dapat diaudit.

## 12.4 Digital Payment

- Backend membuat payment attempt melalui gateway.
- Backend memverifikasi status transaksi melalui webhook atau API resmi.
- Redirect browser tidak menjadi satu-satunya sumber kebenaran.
- Screenshot bukti pembayaran tidak dianggap sebagai konfirmasi otomatis.
- Webhook harus diverifikasi dan diproses secara idempotent.
- Transaksi yang belum memiliki hasil final harus dapat direkonsiliasi.
- Kegagalan satu payment attempt tidak boleh menghalangi percobaan lain yang valid.

## 12.5 Payment and Kitchen Rules

Untuk order digital:

- Kasir boleh memeriksa order saat pembayaran berlangsung.
- Kasir dapat menerima order lebih awal sesuai kebijakan.
- Dapur hanya boleh memulai persiapan setelah pembayaran terverifikasi `PAID`.
- Order yang sudah `CONFIRMED` tetapi belum dibayar harus tetap tertahan dari Kitchen Display.
- Setelah pembayaran berhasil, sistem dapat meneruskan order ke antrean dapur jika order masih valid dan belum dibatalkan atau ditolak.

---

# 13. REFUND MANAGEMENT

## 13.1 Refund Policy

Pelanggan mengajukan refund secara langsung kepada kasir.

Refund dikelola dari dashboard kasir, bukan melalui tombol refund mandiri pada QR menu pelanggan.

## 13.2 Refund Flow

1. Pelanggan menyampaikan nomor order dan alasan.
2. Kasir membuka detail order.
3. Kasir memeriksa status order dan pembayaran.
4. Kasir menentukan apakah refund memenuhi syarat.
5. Kasir menyetujui atau menolak sesuai hak akses.
6. Jika disetujui, sistem mencatat refund dan memproses pengembalian dana.
7. Sistem memperbarui status refund berdasarkan hasil sebenarnya.
8. Riwayat refund tersimpan dan dapat ditelusuri.

## 13.3 Refund Status

- `REQUESTED`
- `APPROVED`
- `PROCESSING`
- `SUCCEEDED`
- `FAILED`
- `REJECTED`
- `CANCELLED`

Status refund merupakan entitas terpisah dari status order dan payment.

## 13.4 Refund Rules

- Order belum dibayar menggunakan pembatalan order, bukan refund.
- Refund tunai dicatat setelah kasir benar-benar mengembalikan uang.
- Refund digital diproses melalui mekanisme payment gateway yang tersedia.
- Refund digital belum dianggap berhasil sebelum ada konfirmasi yang sesuai.
- Refund gagal memerlukan tindak lanjut.
- Refund harus mencegah pengembalian dana ganda.
- Refund penuh menjadi cakupan awal MVP.
- Refund parsial dapat dikembangkan kemudian.
- Semua tindakan refund mencatat nominal, alasan, pengguna, waktu, dan referensi transaksi.

## 13.5 Refund Permissions

- Cashier dapat memproses refund sesuai batas kewenangan.
- Branch Manager dapat menyetujui kasus khusus atau nominal yang lebih tinggi.
- Owner dapat mengatur kebijakan dan melihat seluruh refund bisnisnya.
- Admin PortaTap membantu investigasi platform, tetapi tidak otomatis memiliki hak untuk mengembalikan uang merchant.

---

# 14. INVENTORY MANAGEMENT

## 14.1 Inventory Scope

MVP hanya mengelola stok produk jadi per cabang.

Tidak termasuk:

- Bahan baku.
- Resep.
- Konversi satuan bahan.
- Purchase order pemasok.

## 14.2 Stock Model

Konsep stok:

- `on_hand`: stok fisik yang tercatat.
- `reserved`: stok yang dialokasikan untuk order aktif.
- `available`: stok yang masih bisa dijual.

Rumus:

`available = on_hand - reserved`

## 14.3 Stock Rules

- Stok divalidasi ulang di server ketika checkout.
- Reservasi dilakukan secara atomik di database.
- Dua checkout bersamaan tidak boleh menjual stok yang sama.
- Reservasi dipertahankan ketika order menunggu keputusan.
- Reservasi dilepas ketika order ditolak atau dibatalkan secara sah dan status pembayaran sudah aman.
- Stok dikonsumsi ketika order mulai diproses.
- Konsumsi dan pelepasan reservasi harus dilakukan secara konsisten dan atomik.
- Order yang sudah mulai diproses tidak boleh mengembalikan stok secara otomatis tanpa aturan yang sesuai.
- Koreksi stok harus mencatat alasan dan pengguna.

## 14.4 Stock Movement

Setiap perubahan stok mencatat:

- Produk.
- Cabang.
- Jenis pergerakan.
- Jumlah.
- Referensi order jika ada.
- Alasan.
- Waktu.
- Pengguna yang melakukan perubahan.

---

# 15. TENANT PROMOTIONS & CUSTOMER VOUCHERS

## 15.1 Purpose

Modul Promotions digunakan oleh owner untuk membuat promo yang berlaku pada pembelian makanan dan minuman pelanggan.

Modul ini terpisah dari voucher subscription PortaTap.

## 15.2 Promotion Types

MVP mendukung:

- Diskon nominal.
- Diskon persentase.
- Minimum nilai order.
- Periode berlaku.
- Kuota penggunaan.
- Maksimum penggunaan per pelanggan atau order.
- Pembatasan produk, kategori, atau cabang.

## 15.3 Promotion Rules

- Promo harus aktif dan berada dalam periode berlaku.
- Backend memvalidasi kode, kuota, cabang, produk, dan syarat transaksi.
- Diskon dihitung ulang di server.
- Penggunaan voucher dicatat dan dihubungkan ke order.
- Penumpukan beberapa promo tidak termasuk MVP kecuali aturan eksplisit disiapkan.
- Pembatalan order mengikuti aturan pemulihan kuota yang konsisten.
- Laporan membedakan penjualan sebelum diskon, diskon, dan penjualan setelah diskon.

## 15.4 Data Entities

- `promotions`
- `promotion_codes`
- `promotion_redemptions`

---

# 16. MENU APPEARANCE & THEME EDITOR

## 16.1 Objective

Memberikan kebebasan kepada tenant untuk menyesuaikan tampilan QR menu sesuai identitas bisnis.

## 16.2 Theme Editor MVP

- Pilihan template.
- Logo.
- Warna utama.
- Banner.
- Grid atau list layout.
- Live preview mobile.
- Penyimpanan draft.
- Validasi kontras.
- Publikasi theme.

## 16.3 Theme Packages by Subscription

Starter:

- Tiga template dasar.
- Branding dasar.
- Warna, logo, banner, dan layout.

Growth:

- Katalog template lebih luas.
- Pilihan font preset.
- Variasi kartu produk dan kategori.
- Pengaturan visual tambahan.

Business:

- Template eksklusif.
- Kustomisasi visual lanjutan.
- Opsi layanan custom UI oleh PortaTap sesuai scope.

## 16.4 Theme Editor Behavior

- Perubahan terlihat langsung di preview.
- Draft tidak langsung mengubah tampilan pelanggan.
- Draft dapat disimpan otomatis.
- Status penyimpanan terlihat.
- Owner menekan Publish untuk menerbitkan perubahan.
- Kegagalan publikasi tidak boleh merusak versi aktif sebelumnya.
- Template harus responsif dan tetap berfungsi pada berbagai ukuran layar.

## 16.5 Theme Management by Admin

Admin PortaTap sekaligus dapat menjalankan peran developer.

Workflow:

1. Developer membuat template.
2. Template di-build dan divalidasi.
3. Admin mendaftarkan paket template.
4. Admin melakukan preview staging.
5. Admin mengatur metadata, versi, dan paket yang diizinkan.
6. Admin memublikasikan template.
7. Template tersedia di katalog tenant sesuai hak paket.

Upload template tidak boleh berarti menjalankan JavaScript bebas langsung dari database. Paket kode harus melalui validasi, pengujian, dan deployment yang terkontrol.

## 16.6 Theme Versioning

- Setiap template memiliki ID dan versi.
- Versi yang dipublikasikan dicatat.
- Menonaktifkan template tidak boleh langsung merusak tenant yang masih menggunakannya.
- Perubahan template harus kompatibel dengan konfigurasi tenant atau memiliki prosedur migrasi.
- Theme tidak boleh mengubah logika pembayaran, stok, atau keamanan.

## 16.7 Theme Data

Entitas yang disarankan:

- `tenant_themes`
- `theme_drafts`
- `theme_publications`
- `media_assets`
- `theme_audit_logs`

Default MVP: theme berada di tingkat tenant dan diwariskan ke cabang. Override theme per cabang menjadi fitur lanjutan.

---

# 17. NOTIFICATION SYSTEM

## 17.1 Notification Events

MVP mencakup:

- Order baru.
- Order belum direspons.
- Order terlambat.
- Order baru masuk antrean dapur.
- Order siap disajikan.
- Pembayaran digital berhasil atau gagal.
- Refund memerlukan tindak lanjut.

## 17.2 Sound Notifications

- Order baru menghasilkan suara pada dashboard kasir.
- Order terlambat memberikan peringatan pada menit ke-3 dan penanda terlambat pada menit ke-5.
- Order yang sudah memenuhi syarat masuk dapur menghasilkan suara khusus di Kitchen Display.
- Order digital yang belum dibayar tidak menghasilkan notifikasi bahwa order siap diproses.
- Suara dapat diaktifkan atau dimatikan per perangkat.
- Suara kasir dan dapur dapat dibedakan.
- Event yang diterima berulang tidak boleh menghasilkan bunyi berulang tanpa alasan.

## 17.3 Browser Behavior

- Sediakan tombol aktivasi suara karena browser dapat memblokir autoplay.
- Jika suara gagal diputar, notifikasi visual tetap berjalan.
- Gunakan mekanisme realtime agar dashboard tidak perlu refresh manual.
- Sistem tetap harus melakukan sinkronisasi ulang setelah koneksi terputus.

---

# 18. SALES REPORTING

## 18.1 Reports MVP

- Penjualan berdasarkan periode.
- Penjualan per cabang.
- Jumlah order selesai.
- Produk terlaris.
- Metode pembayaran.
- Diskon dan penggunaan voucher.
- Pembatalan dan penolakan order.
- Refund.
- Ringkasan stok.

## 18.2 Metric Definitions

Laporan harus membedakan:

- Nilai order sebelum diskon.
- Diskon.
- Penjualan setelah diskon.
- Pembayaran yang berhasil.
- Pembayaran yang belum lunas.
- Refund yang berhasil.
- Penjualan bersih sesuai definisi laporan.

Definisi penjualan bersih yang digunakan harus konsisten, misalnya nilai order selesai setelah diskon dikurangi refund yang berhasil, dengan penanganan refund parsial jika fitur tersebut tersedia.

Pembayaran yang belum lunas tidak boleh otomatis dianggap sebagai arus kas yang sudah diterima.

## 18.3 Export

MVP menyediakan ekspor CSV untuk laporan dasar jika implementasi memungkinkan dalam scope sprint pelaporan.

---

# 19. BUSINESS SETTINGS

Pengaturan bisnis meliputi:

- Nama bisnis.
- Logo.
- Informasi kontak.
- Cabang.
- Jam operasional.
- Status penerimaan order.
- Preferensi notifikasi.
- Kebijakan operasional sederhana.
- Pengaturan hak akses yang tersedia untuk owner.

Cabang yang sedang tidak menerima order tidak boleh menerima checkout baru, tetapi order yang sudah ada tetap harus dapat diselesaikan sesuai aturan.

---

# 20. ADMIN PORTAL

Admin Portal digunakan oleh founder/developer PortaTap untuk mengelola platform.

Modul:

- Tenant Management.
- Subscription Plans.
- Subscription Vouchers.
- Theme Management.
- Template Registry.
- Template Preview dan Publication.
- System Health.
- Audit Logs.

## 20.1 Tenant Management

Admin dapat:

- Melihat daftar tenant.
- Melihat status subscription.
- Melihat informasi operasional yang diperlukan untuk support.
- Menonaktifkan tenant berdasarkan kebijakan.
- Menelusuri audit dan kasus support.

Akses admin ke data tenant harus dibatasi sesuai kebutuhan dan dicatat. Admin tidak otomatis berperan sebagai owner tenant.

## 20.2 Subscription Administration

Admin dapat:

- Mengatur paket dan harga.
- Mengatur batas fitur.
- Membuat dan menonaktifkan voucher subscription.
- Mengatur kuota dan periode promo.
- Melihat redemption.
- Menelusuri invoice dan status subscription.

## 20.3 Template Registry

Admin dapat:

- Mendaftarkan template.
- Mengunggah paket template yang sudah dibangun.
- Mengatur metadata.
- Mengatur versi.
- Memilih paket yang dapat menggunakan template.
- Preview di staging.
- Memublikasikan atau menonaktifkan versi.
- Melihat tenant yang menggunakan template tersebut.

---

# 21. DATA MODEL / DATABASE BLUEPRINT

Daftar berikut merupakan rancangan entitas inti. Kolom, indeks, constraint, dan relasi final ditentukan pada tahap database design.

## 21.1 Identity & Tenancy

- `users`
- `tenants`
- `branches`
- `tenant_memberships`
- `branch_memberships`
- `roles`
- `invitations`

## 21.2 Business Data

- `categories`
- `products`
- `product_variants`
- `branch_products`
- `tables`
- `table_sessions`

## 21.3 Ordering

- `orders`
- `order_items`
- `order_status_history`

## 21.4 Payment & Refund

- `payments`
- `payment_attempts`
- `refunds`
- `payment_webhook_events`

## 21.5 Inventory

- `stock_reservations`
- `stock_movements`

## 21.6 Promotions

- `promotions`
- `promotion_codes`
- `promotion_redemptions`

## 21.7 Subscription

- `plans`
- `plan_features`
- `subscriptions`
- `subscription_invoices`
- `subscription_events`
- `subscription_voucher_redemptions`

## 21.8 Themes

- `tenant_themes`
- `theme_drafts`
- `theme_publications`
- `media_assets`
- `theme_audit_logs`

## 21.9 Auditing

- `audit_logs`

Audit logs digunakan untuk perubahan sensitif seperti harga, stok, role, pembayaran, refund, subscription, dan theme publication.

---

# 22. NON-FUNCTIONAL REQUIREMENTS

## 22.1 Security

- Semua endpoint memvalidasi autentikasi dan otorisasi.
- Isolasi tenant diterapkan pada backend.
- Validasi input dilakukan di server.
- File upload dibatasi berdasarkan tipe, ukuran, dan izin.
- Payment webhook diverifikasi.
- Operasi sensitif harus idempotent jika sesuai.
- Rahasia dan kredensial tidak boleh disimpan di frontend.
- Aksi sensitif dicatat di audit log.

## 22.2 Reliability

- Perubahan stok dan pembuatan order menggunakan transaksi database yang sesuai.
- Pembayaran dan refund memiliki status yang dapat direkonsiliasi.
- Sistem menangani event realtime yang berulang.
- Kegagalan integrasi tidak boleh menyebabkan status transaksi palsu.
- Backup dan prosedur pemulihan database harus disiapkan sebelum produksi.

## 22.3 Performance

Target performa harus ditentukan dan diuji sebelum produksi. MVP harus memiliki:

- Pagination untuk daftar order dan transaksi.
- Indeks database untuk query berdasarkan tenant, cabang, status, dan waktu.
- Batas ukuran upload.
- Pemrosesan asynchronous untuk tugas yang tidak perlu memblokir checkout.
- Pengujian beban yang sesuai target pilot dan proyeksi bisnis.

## 22.4 Accessibility & Responsive UI

- QR menu harus nyaman digunakan pada smartphone.
- Teks dan komponen UI harus memiliki kontras yang memadai.
- Status tidak boleh dibedakan hanya dengan warna.
- Dashboard kasir dan dapur harus terbaca dari layar operasional.
- Theme harus tetap usable ketika nama produk atau deskripsi panjang.

---

# 23. MVP SCOPE & PRIORITY

## P0 — Core MVP

- Tenant dan branch management.
- Authentication, roles, dan permissions.
- Onboarding bisnis.
- Product dan category management.
- Table dan QR management.
- Customer QR menu.
- Cart dan checkout.
- Order management.
- Kitchen Display.
- Pembayaran tunai.
- Satu integrasi pembayaran digital.
- Refund penuh dengan pencatatan status.
- Stok produk sederhana.
- Sound notifications.
- Basic sales report.
- Tenant isolation.
- Audit log untuk transaksi dan tindakan sensitif.
- Subscription foundation.
- Backup dan monitoring dasar.

## P1 — Growth Features

- Tenant promotions dan customer vouchers.
- Advanced sales reporting.
- CSV export.
- Theme Editor yang lebih lengkap.
- Theme Registry dan publikasi template terkontrol.
- Multi-branch reporting.
- Template katalog yang lebih luas.
- Fitur pengaturan operasional lanjutan.

## P2 — Advanced Features

- Loyalty.
- Ingredient inventory dan resep.
- Akuntansi.
- Integrasi delivery.
- Split bill.
- Multi-payment provider.
- Theme builder yang lebih fleksibel.
- Advanced analytics.

---

# 24. ACCEPTANCE CRITERIA

## 24.1 Authentication & Tenant Isolation

- User hanya dapat mengakses tenant dan cabang sesuai membership.
- User yang sama dapat memiliki membership di beberapa tenant.
- Tenant tidak dapat membaca atau mengubah data tenant lain.
- Role divalidasi di backend.

## 24.2 Ordering

- Checkout berhasil membuat satu order baru.
- Harga dan item disimpan sebagai snapshot.
- Order muncul di dashboard kasir.
- Order yang ditolak memiliki alasan.
- Setiap perubahan status tercatat.
- Order baru dari QR yang sama menjadi order terpisah.

## 24.3 Payments

- Pembayaran tunai harus dikonfirmasi kasir.
- Pembayaran digital harus diverifikasi backend.
- Webhook berulang tidak membuat pembayaran ganda.
- Order digital belum dibayar tidak dapat masuk ke dapur.
- Order yang ditolak setelah pembayaran berhasil menghasilkan kasus refund.

## 24.4 Inventory

- Checkout tidak boleh menjual stok melebihi ketersediaan.
- Reservasi stok dilakukan secara atomik.
- Reservasi dilepas sesuai aturan penolakan atau pembatalan.
- Pergerakan stok dapat ditelusuri.

## 24.5 Refund

- Refund hanya dapat diproses oleh role yang berwenang.
- Refund menyimpan nominal, alasan, waktu, dan pelaksana.
- Refund digital mengikuti konfirmasi penyedia pembayaran.
- Refund yang berhasil tidak dapat dieksekusi ulang secara tidak sengaja.
- Refund gagal tetap terlihat untuk ditindaklanjuti.

## 24.6 Theme Editor

- Perubahan terlihat di preview.
- Draft tidak mengubah versi published.
- Kontras warna divalidasi.
- Publikasi gagal tidak merusak versi aktif.
- Theme tidak dapat mengakses data tenant lain.

## 24.7 Notifications

- Order baru memicu notifikasi visual dan suara jika diaktifkan.
- Peringatan dikirim setelah 3 menit.
- Order ditandai terlambat setelah 5 menit tanpa auto-cancel.
- Order digital yang belum dibayar tidak memicu antrean dapur.

---

# 25. IMPLEMENTATION ROADMAP

## Phase 1 — Foundation

- Setup repository dan environment.
- Database dan migration.
- Authentication.
- Tenant, branch, dan membership.
- Authorization dan tenant isolation.
- Audit logging dasar.

**Output:** fondasi multi-tenant dapat digunakan dan diuji.

## Phase 2 — Business Setup

- Categories dan products.
- Product variants.
- Branch products.
- Tables dan QR.
- Business settings.
- Onboarding tenant.

**Output:** owner dapat menyiapkan bisnis dan menu.

## Phase 3 — Ordering Engine

- Customer QR menu.
- Cart dan checkout.
- Order creation.
- Order status transitions.
- Stock reservation.
- Cashier dashboard.
- Realtime order events.
- Kitchen Display dan sound notification.

**Output:** alur order end-to-end berjalan.

## Phase 4 — Payment & Refund

- Cash payment.
- Integrasi satu payment gateway.
- Webhook processing.
- Payment reconciliation.
- Refund management.
- Stock release dan consumption rules.

**Output:** transaksi dapat dibayar, ditelusuri, dan direkonsiliasi.

## Phase 5 — Business Management

- Inventory management.
- Sales reports.
- Tenant promotions.
- CSV export jika masuk scope rilis.
- Team & Access.

**Output:** tenant dapat mengelola operasional dan melihat hasil bisnis.

## Phase 6 — Subscription & Theme

- Subscription foundation.
- Plan dan entitlement.
- Subscription invoices.
- Voucher subscription.
- Theme Editor.
- Theme Registry.
- Template publication workflow.

**Output:** tenant dapat menggunakan paket berbayar dan menyesuaikan tampilan menu.

## Phase 7 — Pilot & Production Readiness

- Uji coba pada beberapa kedai.
- Uji skenario order bersamaan.
- Uji pembayaran gagal dan webhook duplikat.
- Uji penolakan order setelah pembayaran.
- Uji refund gagal.
- Uji isolasi tenant.
- Uji backup dan recovery.
- Monitoring error dan performa.
- Perbaikan UX berdasarkan feedback pilot.

**Output:** MVP siap untuk peluncuran terbatas.

---

# 26. RISKS & MITIGATIONS

| Risiko                                 | Mitigasi                                                        |
| -------------------------------------- | --------------------------------------------------------------- |
| Kebocoran data antar-tenant            | Authorization backend, tenant-scoped queries, pengujian isolasi |
| Overselling stok                       | Reservasi atomik dan transaksi database                         |
| Pembayaran terduplikasi                | Idempotency dan unique transaction reference                    |
| Order digital diproses sebelum dibayar | Guard pada transisi ke antrean dapur                            |
| Refund terlupakan                      | Kasus refund otomatis untuk order berbayar yang ditolak         |
| Notifikasi tidak terdengar             | Tombol aktivasi suara, visual fallback, dan reconnect handling  |
| Theme merusak halaman pelanggan        | Template terkontrol, versi, staging, dan publikasi atomik       |
| Subscription tidak konsisten           | Snapshot harga invoice dan pemisahan subscription/payment       |
| Scope MVP terlalu besar                | P0 diprioritaskan dan fitur P1/P2 tidak menghambat rilis awal   |

---

# 27. OPEN DECISIONS BEFORE PRODUCTION

Keputusan berikut perlu diselesaikan sebelum implementasi terkait dianggap final:

1. Memilih payment gateway dan mekanisme refund yang didukung.
2. Menentukan durasi pembayaran digital berdasarkan ketentuan gateway.
3. Menetapkan kebijakan grace period setelah subscription berakhir.
4. Menentukan batas nominal refund yang dapat diproses kasir tanpa persetujuan manager.
5. Menentukan kapan reservasi stok kedaluwarsa untuk order yang masih menunggu keputusan.
6. Menentukan aturan penumpukan voucher pelanggan.
7. Menentukan apakah harga produk dapat berbeda per cabang pada rilis pertama.
8. Menentukan kebijakan retensi data dan privasi.
9. Menetapkan target performa dan beban berdasarkan proyeksi pilot.
10. Menetapkan apakah tenant promotions dan Theme Editor dirilis bersamaan atau bertahap.

Keputusan yang belum final tidak boleh diimplementasikan berdasarkan asumsi tersembunyi. Setiap keputusan perlu dicatat dan diuji terhadap alur bisnis yang sudah ditetapkan.

---

# 28. DEFINITION OF DONE

Satu fitur dianggap selesai ketika:

- Business rules telah diimplementasikan.
- Backend validation dan authorization tersedia.
- Database migration dan constraints sesuai.
- UI menampilkan loading, empty, error, dan success states.
- Audit log tersedia untuk aksi sensitif.
- Unit test atau integration test untuk alur penting lulus.
- Edge cases relevan telah diuji.
- Dokumentasi API dan aturan bisnis diperbarui.
- Tidak ada regresi pada order, pembayaran, stok, dan isolasi tenant.
- Fitur telah diuji pada environment staging.

---

# 29. FINAL PRODUCT DIRECTION

PortaTap dibangun sebagai SaaS multi-tenant untuk bisnis F&B, dengan QR ordering sebagai inti produk.

Prinsip pengembangan:

1. Sederhana untuk kedai kecil.
2. Konsisten dalam pencatatan transaksi.
3. Aman dalam isolasi tenant dan otorisasi.
4. Realtime untuk operasional order.
5. Memisahkan order, payment, refund, inventory, dan subscription.
6. Memberikan fleksibilitas branding melalui theme system terkontrol.
7. Menambah fitur berdasarkan kebutuhan bisnis yang tervalidasi.
8. Menghindari kompleksitas yang tidak dibutuhkan untuk MVP.

**Prioritas utama adalah membuat satu alur end-to-end yang dapat diandalkan:**

Tenant setup → Menu → Meja dan QR → Customer checkout → Kasir → Pembayaran → Kitchen → Penyelesaian order → Stok dan laporan.

Setelah alur inti stabil, PortaTap dapat berkembang melalui voucher pelanggan, custom theme, paket subscription, dan dukungan multi-cabang yang lebih luas.

**End of PRD — PortaTap v1.0**
