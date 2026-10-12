---
name: no-duplicate-logic
description: Larang duplikasi LOGIKA saat menulis atau memperbaiki kode — sebelum membuat function/method/service/component/helper baru, cari dulu kode yang sudah ada dengan logika sama lalu pakai ulang atau parameterkan yang lama, jangan membuat salinan baru dengan nama berbeda; sekaligus hapus kode yang jadi tidak terpakai. Pakai setiap kali membuat, menambah, refactor, memperbaiki, atau me-review kode, dan sebagai self-check WAJIB sebelum menyelesaikan tugas coding apa pun.
metadata:
  author: portatap
  version: "1.0"
---

# No Duplicate Logic — Wajib Reuse, Larang Salinan Logika

Skill ini **selalu aktif** untuk pekerjaan menulis atau memperbaiki kode. Tujuannya satu:
**satu logika = satu tempat**. Duplikasi yang dilarang bukan sekedar nama function yang sama,
tapi **logika yang sama ditulis ulang** di tempat lain — walaupun namanya beda
(`pembelian` vs `userPembelian` vs `adminPembelian`), itu tetap duplikat dan tetap salah.

## Aturan inti (non-negotiable)

1. **Jangan pernah** membuat function/method/service/component/helper baru yang isinya
   (sebagian besar atau seluruh) mengulang logika yang sudah ada di tempat lain.
2. Kalau butuh logika yang sama untuk **kondisi/role/pemakai yang berbeda**, **pakai yang sudah
   ada** dan tambahkan parameter/opsi — bukan bikin salinan baru.
3. Kalau menemukan duplikat saat memperbaiki kode, **satukan** jadi satu sumber kebenaran.
4. **Tidak boleh** meninggalkan kode mati (dead code) setelah perubahan. Kalau jadi tidak
   terpakai, hapus — jangan biarkan sebagai "cadangan".

> Prinsip: lebih baik satu function dengan beberapa parameter daripada lima function yang
> isinya hampir identik.

## The Reuse Ladder — lakukan berurutan, berhenti di langkah pertama yang cukup

Sebelum menulis kode baru, telusuri tangga ini dari atas ke bawah:

1. **Cari yang sudah ada.** Grep dulu sebelum menulis:
   - `grep` nama domain + kata kunci logika (mis. `total`, `discount`, `pembelian`, `calculate`).
   - Cari di `services/`, `utils/`, `selectors/`, `models.py`, `forms.py`, dan helper modul.
   - Cek juga apakah logic serupa sudah ada di view/model lain untuk domain yang berbeda.
2. **Pakai langsung.** Kalau function yang ada sudah pas, import dan pakai. Selesai.
3. **Parameterkan.** Kalau hampir pas tapi beda sedikit (role, sumber data, opsi bentuk output),
   tambahkan parameter/argumen dengan default yang aman sehingga pemanggil lama tetap jalan.
4. **Generalisasi/ekstrak.** Kalau logika tersebar di 2+ tempat, tarik keluar jadi satu
   function bersama di modul yang paling tepat, lalu ganti semua pemanggil ke function itu.
5. **Baru bikin baru.** Hanya kalau benar-benar tidak ada yang bisa dipakai ulang — dan
   pastikan tidak ada nama/logika yang tumpang tindih dengan yang lama.

Kalau kamu melewati langkah 1, kamu melanggar skill ini.

## Contoh nyata (kasus yang dimaksud user)

Kasus: sudah ada function untuk **pembelian oleh user**. Suatu saat butuh pembelian untuk **admin**.

❌ **SALAH** — bikin function baru, logikanya disalin:

```python
def pembelian(user):
    total = sum(item.price * item.qty for item in user.cart)
    total -= hitung_diskon(user)
    return buat_order(user, total)


def user_pembelian(user):          # DUPLIKAT LOGIKA
    total = sum(item.price * item.qty for item in user.cart)
    total -= hitung_diskon(user)
    return buat_order(user, total)


def admin_pembelian(admin):        # DUPLIKAT LAGI
    total = sum(item.price * item.qty for item in admin.cart)
    total -= hitung_diskon(admin)
    return buat_order(admin, total)
```

✅ **BENAR** — satu function, parameterkan perbedaan role/kebijakan:

```python
def buat_pembelian(actor, *, sebagai_admin: bool = False):
    """Satu-satunya jalur pembelian. Role hanya mengubah kebijakan, bukan menyalin logika."""
    total = hitung_total(actor)
    total -= hitung_diskon(actor, sebagai_admin=sebagai_admin)
    return buat_order(actor, total)
```

Satu function bisa dipakai user, admin, staff — perbedaan role jadi **parameter/kebijakan**, bukan
salinan. Kalau perbedaannya makin besar, pecah jadi helper kecil yang **dipakai bersama**
(`hitung_total`, `hitung_diskon`), bukan mengkopi blok besarnya.

## Cara mendeteksi duplikat

Curigai duplikasi kalau menemukan tanda-tanda ini:

- Dua function mirip dengan awalan/sufiks per-role atau per-tipe:
  `get_user_x` / `get_admin_x`, `order_total` vs `invoice_total` dengan isi serupa.
- Blok `if/else` panjang yang mengulang perhitungan yang sama untuk cabang berbeda.
- Copy-paste lalu ganti 1–2 identifier.
- Logika validasi/perhitungan yang sama ditulis di form, view, dan service sekaligus.
- Konstanta/string yang sama diulang di banyak tempat (aturan format, status, dsb).

Kalau menemukannya: **satukan** sebelum menambah fitur di atasnya.

## Aturan dead code

- Setelah refactor, jalankan pencarian pemakaian: kalau tidak ada pemanggil, **hapus**.
- Jangan rename-nama-unused jadi `_var` atau bikin alias/re-export hanya supaya "tidak dianggap
  error". Kalau tidak dipakai, buang total.
- Jangan pertahankan jalur lama sebagai "backwards compatibility" tanpa kebutuhan nyata.
- Jangan bikin helper/abstraksi sekali pakai. Abstraksi baru hanya kalau dipakai ≥2 tempat.

## Self-check WAJIB sebelum bilang tugas selesai

Sebelum menutup tugas yang menyentuh kode, jawab semua ini secara eksplisit:

1. Apakah aku sudah **mencari** function/logika yang sudah ada sebelum menulis yang baru?
2. Apakah setiap function/helper baru benar-benar **tidak mengulang** logika yang sudah ada?
   (Bandingkan isi, bukan cuma nama.)
3. Apakah aku menyatukan duplikat yang kutemukan, alih-alih menambah satu lagi?
4. Apakah ada kode yang jadi **tidak terpakai** dan perlu dihapus?
5. Kalau ada dua implementasi mirip yang sengaja dipertahankan, apa **alasan konkretnya**?
   (Kalau tidak ada alasan kuat → satukan.)

Kalau ada jawaban "belum"/"tidak", perbaiki dulu sebelum lanjut.

## Kapan bikin function baru itu wajar

Reuse **bukan** berarti memaksa satu function monolitik. Bikin baru itu benar kalau:

- Logikanya memang **berbeda secara substansi** (aturan bisnis beda, bukan cuma pemanggil beda).
- Kamu sedang memecah satu function besar jadi bagian kecil yang **dipakai bersama** (refactor
  ke arah lebih DRY), bukan menyalin.
- Perbedaan pemanggil hanya di parameter → jadikan parameter, bukan function baru.

Ambangnya: kalau isi dua function mirip **>70%**, itu kandidat kuat untuk disatukan.

## Hubungan dengan skill lain

- Untuk memindai kode mati secara menyeluruh, kayuh juga skill `dead-code`.
- Setelah rapi, pastikan tetap ada test untuk jalur yang disatukan supaya reuse tidak memecah
  perilaku.
