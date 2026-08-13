# Spec: 012-telemetri

| | |
|---|---|
| Kebutuhan | FR-J01, FR-J02, FR-J03, FR-J05, FR-J06 |
| Pasal | **C-04** |
| Dokumen | D-01 Bagian 9, D-04 Bagian 7.4, D-14 Bagian 5.1 |
| Ketergantungan baru | **Nol** |
| Status | **Lolos Gerbang 1–3** (KB-048) |

## 1 · Mengapa fitur ini sekarang

D-01 menyebut taksonomi peristiwa **"luaran teknis kunci 2026"**: ia merekam
perilaku belajar alami tanpa intervensi gamifikasi, sehingga menjadi kelompok
pembanding historis bagi uji 2028. Tanpa telemetri, siklus ini kehilangan
variabel hasil utamanya — rasio penerapan (D-01 Bagian 9.1).

Fitur 022 baru saja menyediakan yang C-04 periksa. Ini pasal terakhir yang
dapat berpindah tanpa `web/` maupun rute.

## 2 · Cakupan

**Di dalam:** taksonomi peristiwa, bentuk `peristiwa` D-04 Bagian 7.4, gerbang
perekaman yang menegakkan C-04, penjagaan `properti` terhadap data pribadi dan
identitas, ekspor CSV, dan pemeriksa C-04.

**Di luar dan dinyatakan:**

| Yang ditunda | Ke mana | Mengapa |
|---|---|---|
| FR-J04 panel analitik | `web/` | Layar, bukan sisi belakang |
| Ekspor Parquet (bagian FR-J03) | menunggu C-12 | Menuntut `pyarrow`, belum disetujui |
| Metrik turunan D-01 Bagian 9.1 | fitur 011 dan panel | Menuntut aliran peristiwa nyata; rasio yang dihitung atas nol peristiwa adalah nol yang terbaca seperti temuan |

Ekspor CSV **dibangun**; Parquet **dinyatakan tertahan**, bukan dilewatkan
diam-diam. FR-J03 karena itu terpenuhi separuh, dan separuhnya disebut.

## 3 · Kebutuhan

| Kode | Pernyataan |
|---|---|
| R-01 | Peristiwa **HARUS** bernilai salah satu kode taksonomi D-01 Bagian 9; kode di luar daftar **TIDAK BOLEH** tersimpan (FR-J01, KM-04) |
| R-02 | Setiap peristiwa **HARUS** membawa enam bidang FR-J02: pseudonim, jenis, waktu, properti, versi aplikasi, versi model |
| R-03 | Peristiwa **TIDAK BOLEH** membawa `id_pengguna`; yang tersimpan **HARUS** pseudonimnya (FR-J02, C-05) |
| R-04 | **JIKA** persetujuan pengguna tidak berkeadaan `diberikan`, **MAKA** peristiwa **TIDAK BOLEH** terekam (**C-04**, FR-J05) |
| R-05 | **JIKA** persetujuan dicabut, **MAKA** perekaman **HARUS** berhenti seketika — tanpa menunggu sesi berakhir atau penyegaran apa pun (**C-04**, FR-J05, FR-A05) |
| R-06 | `properti` **TIDAK BOLEH** memuat data pribadi maupun kunci beridentitas (KM-03, D-14 Bagian 5.1) |
| R-07 | Peristiwa yang sudah terekam **TIDAK BOLEH** dapat diubah maupun dihapus lewat permukaan modul (tambah-saja) |
| R-08 | Telemetri **HARUS** dapat diekspor sebagai CSV (FR-J03 separuh); Parquet dinyatakan tertahan C-12 |
| R-09 | Seluruh waktu disimpan UTC (KM-01) |

## 4 · Bentuk yang menentukan

### 4.1 C-04 adalah bentuk, bukan pemeriksaan

Pasal itu berbunyi *"Telemetri tidak merekam bagi pengguna tanpa persetujuan
aktif. Pencabutan menghentikan perekaman seketika."*

Pemeriksaan yang menegakkannya berbunyi "sebelum merekam, periksa
persetujuan" — dan pemeriksaan semacam itu ada pada **setiap** tempat
perekaman. Satu tempat yang lupa memuatnya tidak menghasilkan galat apa pun;
ia menghasilkan data yang lebih lengkap, dan data yang lebih lengkap tidak
pernah terasa seperti kekeliruan sampai audit etik.

Karena itu `Peristiwa` **hanya dibentuk gerbang perekaman**, dan gerbang itu
menuntut `KeadaanPersetujuan` sebagai argumen — bukan bendera boolean.
Ketiga bentuk pendahulunya sudah membuktikan polanya: `Instruksi` (ADR-13),
`JawabanTervalidasi` (008), `ButirTayang` (010).

### 4.2 Keadaan diserahkan pemanggil, dan itu yang membuat R-05 bekerja

Gerbang menerima keadaan persetujuan **pada saat perekaman**, bukan menyimpan
salinannya. Salinan yang disimpan saat sesi dibuka akan tetap bernilai
`DIBERIKAN` sesudah pengguna mencabut di tengah sesi — dan "seketika" pada
C-04 berubah menjadi "pada sesi berikutnya" tanpa seorang pun mengubah satu
baris pun.

### 4.3 Pseudonim, bukan identitas

FR-J02 menulis "id pengguna **terpseudonim**". `Peristiwa` karena itu tidak
memiliki bidang `id_pengguna` sama sekali — bukan memilikinya lalu
mengosongkannya. Yang tidak ada tidak dapat terisi.

Pemetaannya tinggal di `src/penyimpanan/pseudonim.py` (fitur 022) dan tidak
terjangkau modul ini; itu FR-J06 dan C-05 yang sudah berdiri.

### 4.4 `properti` dijaga dua arah

D-14 Bagian 5.1: *"Isinya mengikuti taksonomi D-01 Bagian 9; tidak pernah
memuat data pribadi."* Dua penjagaan, dan keduanya perlu:

- **Nilainya** disapu pendeteksi FR-B04 — nomor yang tersalin ke properti.
- **Kuncinya** ditolak bila beridentitas — `id_pengguna`, `nama`, `surel`.
  Kunci beridentitas lolos pendeteksi pola sebab nilainya belum tentu berpola.

## 5 · Pertanyaan Gerbang 1

| # | Pertanyaan | Usul |
|---|---|---|
| 1 | C-04 berpindah pada fitur ini? | **Ya.** Yang diperiksanya sudah ada sejak fitur 022, dan gerbang perekaman yang menegakkannya dibangun di sini. Tagihan menyusut **15 → 16** |
| 2 | Metrik turunan D-01 Bagian 9.1 dibangun? | **Tidak.** Rasio yang dihitung atas nol peristiwa adalah nol yang terbaca seperti temuan — bentuk TA-01. Ia menunggu aliran peristiwa nyata |
| 3 | Ekspor Parquet? | **Tidak** — `pyarrow` belum disetujui C-12. CSV dibangun; Parquet dinyatakan tertahan pada `usulan-ketergantungan.md` |

## 6 · Yang tidak dikerjakan di sini

Panel analitik FR-J04, metrik turunan Bagian 9.1, dan ekspor Parquet. Sesudah
fitur ini, **satu-satunya pasal yang tersisa dan tidak menunggu `web/` adalah
C-10** — dan ia sudah dibangun sejak fitur 003.
