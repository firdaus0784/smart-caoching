# Plan: 028-penyambungan-riwayat-percakapan

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 28 September 2026 (KB-138), P-1 s.d. P-6 pilihan A |
| Status | **Gerbang 4 lolos** — 1 Oktober 2026 (KB-149). Gerbang 2 lolos KB-139 |
| Kebutuhan | R-01 s.d. R-17 `spec.md`; C-05, C-13, C-14, C-17, C-20 |

## 1. Letak dan batas

```
perkakas/basis_data/
  01-peran-dan-basis-data.sql   (ubah)  peran_riwayat
  06-riwayat.sql                (baru)  skema riwayat, dua tabel, hak tambah-saja
src/penyimpanan/
  riwayat.py                    (baru)  PenyimpanRiwayat: memori dan PostgreSQL
src/api/
  identitas.py                  (baru)  Identitas(peran, pemilik) — P-1
  galat.py                      (baru)  bentuk galat D-14 4.2, KodeGalat, id_jejak — P-4
  aplikasi.py                   (ubah)  /tanya mencatat giliran; pemilik; data pribadi
  percakapan.py                 (ubah)  Giliran tetap di sini; Percakapan memori dilepas
perkakas/jalankan_lokal.py      (ubah)  pemilik pengembangan tetap; riwayat memori/PostgreSQL
perkakas/pemeriksa/
  bahasa_antarmuka.py           (ubah)  jalan keluar galat baru bagi C-13 Aturan 2
  kontrak_web.py                (ubah)  antarmuka Giliran dan RiwayatPercakapan
web/src/
  kontrak.ts, klien.ts          (ubah)  id_percakapan; klien riwayat
  percakapan.ts                 (baru)  pengenal percakapan aktif
  tanya/Riwayat*.tsx            (baru)  blok 9 dan 10 S-09
  mikrokopi.ts                  (ubah)
docs/D14.md                     (ubah)  Bagian 5: dua tabel — SEBELUM kode (T-1)
src/rag/, src/llm/              TIDAK DISENTUH SATU BARIS PUN (R-11)
```

**Aturan arah menentukan letak validasi.** `src/penyimpanan/` tidak boleh
mengimpor `src/api/` maupun `src/nlp/`. `Giliran` — yang memanggil pendeteksi
data pribadi — karena itu **tetap** di `src/api/percakapan.py`, dan penyimpan
riwayat hanya menerima nilai yang sudah sah. Penyimpan yang memvalidasi ulang
akan memuat salinan kedua pendeteksi, dan salinan itu yang akan tertinggal.

## 2. Blast radius, diukur di muka

| Kelompok | Berkas |
|---|---|
| Baru | `06-riwayat.sql`, `src/penyimpanan/riwayat.py`, `src/api/identitas.py`, `src/api/galat.py`, `web/src/percakapan.ts`, dua komponen web, uji masing-masing |
| Diubah — backend | `aplikasi.py`, `percakapan.py`, `01-peran-dan-basis-data.sql`, `jalankan_lokal.py` |
| Diubah — pemeriksa | `bahasa_antarmuka.py` (C-13), `kontrak_web.py` (V-03) |
| Diubah — web | `kontrak.ts`, `klien.ts`, `mikrokopi.ts`, `LayarTanya.tsx`, `halaman.test.ts` |
| Diubah — uji yang ada | `tests/api/test_aplikasi.py` (bentuk galat, identitas), `tests/penyimpanan/test_persiapan_basis_data.py` (peran baru) |
| Dokumen | D-14 Bagian 5 (dan 4.3 bila K-1 diterima), D-00 |
| `src/rag/`, `src/llm/` | **0** |

`tests/api/test_aplikasi.py` berubah karena bentuk galatnya berubah (P-4),
bukan karena perilakunya dilonggarkan. Tiap pernyataan lama tentang status
dan pesan dipertahankan; yang berubah hanya letak pesannya pada badan.

## 3. Penyimpanan — P-3, R-08, R-12, R-13

Skema baru `riwayat` pada basis data **perilaku** `smart_coaching`, tempat
telemetri juga menyimpan pseudonim. Peta pseudonim tetap pada basis datanya
sendiri (C-05); tabel di sini hanya memuat pseudonimnya.

| Tabel | Kolom | Catatan |
|---|---|---|
| `riwayat.percakapan` | `id_percakapan uuid` PK · `pemilik text` · `dibuat_pada timestamptz` | Pemilik ditetapkan sekali; tidak ada hak ubah |
| `riwayat.giliran` | `nomor bigint` identitas · `id_percakapan uuid` FK · `pertanyaan text` · `id_pesan text` · `waktu timestamptz` | Tambah-saja |

Nama tabel dan kolom ditulis ke D-14 Bagian 5 pada **T-1, sebelum SQL mana
pun**, sesuai aturan gaya `AGENTS.md`.

| Peran | `riwayat` | Alasan |
|---|---|---|
| `peran_riwayat` (baru) | `SELECT`, `INSERT` pada kedua tabel; `USAGE` urutan `nomor` | Tanpa `UPDATE`, `DELETE`, `TRUNCATE` — R-08 ditegakkan peladen, bukan hanya oleh ketiadaan metode |
| `peran_penjawaban` | **Tanpa `USAGE`** | C-17 — jalur penjawaban tidak menulis, dan juga tidak perlu membaca riwayat (R-07) |
| Peran lain | Tanpa `USAGE` | — |

Penolakan diuji terhadap peladen dengan sebabnya: `permission denied` pada
stderr, bukan sekadar kode keluar (pelajaran KB-098 dan TK-64). Uji juga
menjalankan `peran_riwayat` **berjalan** — menambah dan membaca — bukan hanya
ditolak, bentuk yang TK-64 tuntut.

**Kepemilikan pada penulisan.** `catat` menjalankan `INSERT … ON CONFLICT DO
NOTHING` atas `riwayat.percakapan`, lalu membaca pemiliknya. Bila pemiliknya
bukan pemanggil, giliran **tidak ditulis** dan galat `BukanPemilik` naik —
diterjemahkan lapisan HTTP menjadi 404 yang sama dengan pengenal tak dikenal
(R-02). Seluruhnya dalam satu transaksi.

**Dua pelaksana, satu uji kontrak.** `RiwayatMemori` (uji dan `make jalan`
tanpa basis data) dan `RiwayatPostgres`. Satu himpunan uji perilaku dijalankan
atas keduanya; uji yang hanya ada bagi pelaksana memori menguji tiruan, bukan
sistemnya. R-13 diuji pada `RiwayatPostgres`: dua penyimpan dengan sambungan
berbeda — yang kedua membaca yang ditulis pertama.

## 4. Identitas — P-1, R-06, R-17

`PenentuIdentitas.peran()` menjadi `PenentuIdentitas.identitas()` yang
mengembalikan `Identitas(peran, pemilik)`. `pemilik` berupa pseudonim —
bentuk yang sama dengan `Peristiwa.pseudonim` fitur 012 — dan **bukan**
identitas langsung. Autentikasi kelak mengisi penentu ini; riwayat tidak
berubah pada hari itu.

`perkakas/jalankan_lokal.py` memakai satu pemilik tetap bernama
`pengembangan-pemilik-tunggal`: menyatakan dirinya, sama dengan penanda versi
`pengembangan`. Ia tetap hanya mengikat `127.0.0.1`.

Kepemilikan diuji dengan **dua** identitas tiruan: pemilik B tidak dapat
membaca daftar A, membaca percakapan A, menulis giliran ke percakapan A,
maupun membedakan percakapan A dari yang tidak ada.

## 5. Bentuk galat dan pertanyaan berdata pribadi — P-4, P-6

`src/api/galat.py` memuat `KodeGalat` — tujuh kode D-14 Bagian 4.2 sebagai
enum — dan satu fungsi yang menyusun badan `{"galat": {"kode",
"pesan_pengguna", "id_jejak"}}`. `id_jejak` dibangkitkan per galat
(`trc_` diikuti heksadesimal acak, mengikuti contoh D-14) dan ditulis ke
logger operasional `smart_coaching.operasional` bersama kode, rute, dan
**nama kelas** sebab teknisnya. Isi pertanyaan tidak pernah ditulis; diuji
dengan menangkap log dan mencari pertanyaan berdata pribadi di dalamnya.

| Keadaan | Status | Kode |
|---|---|---|
| Peran tidak mencukupi | 403 | `TIDAK_BERWENANG` |
| Badan tidak sah, pertanyaan kosong, `id_percakapan` bukan UUID v4 | 400 | `VALIDASI_GAGAL` |
| Pertanyaan berdata pribadi (R-15) | 400 | `VALIDASI_GAGAL` |
| Percakapan tidak dikenal atau milik orang lain | 404 | `SUMBER_TIDAK_ADA` |
| Penyedia model gagal (`GalatLayananModel`) | 503 | `LAYANAN_MODEL_GAGAL` |
| Selebihnya — penangan pengecualian umum | 500 | `GALAT_INTERNAL` |

Pemeriksaan data pribadi berjalan **sebelum** `jalur.jawab` dipanggil, dan
itu diuji dengan menghitung panggilan jalur tiruan: nol. Pesannya menyebut
jenis masalahnya tanpa mengutip nomornya (KB-049).

Pemeriksa C-13 Aturan 2 saat ini mengenal `_galat()` dan `content["pesan"]`
sebagai jalan keluar. Keduanya diganti bentuk baru, dan pemeriksanya ikut
dimutakhirkan — tanpanya pesan baru lolos C-13 tanpa dibaca (bentuk KB-133).

## 6. Keputusan rancangan Gerbang 2

**Diputus 28 September 2026 (KB-139): ketiganya sesuai anjuran.** Pernyataan
pemegang gerbang berbunyi *"sesuai anjuran K-2, K-2 dan K-3 sekaligus"*;
dibaca sebagai K-1, K-2, dan K-3, sebab K-2 tertulis dua kali dan "sekaligus"
menunjuk ketiganya. Tafsiran itu dicatat pada KB-139 agar dapat dikoreksi.

Uraian semula disimpan di bawah.

**K-1 · Urutan daftar percakapan.** D-14 Bagian 4.3 menulis daftar
"terurut", dan kode mengurutkannya menurut pengenal. Pengenal kini UUID acak,
sehingga urutan itu tidak bermakna bagi siapa pun.
**Anjuran:** terbaru lebih dulu menurut `dibuat_pada`, dan kalimat D-14
Bagian 4.3 diperjelas demikian pada T-1. Bentuk tanggapan tidak berubah.

**K-2 · Daftar percakapan hanya berisi pengenal.** Layar yang menampilkan
UUID tidak berguna bagi kepala sekolah; yang bermakna adalah pertanyaan
pertamanya. Menambahkannya ke tanggapan daftar mengubah bentuk D-14 Bagian
4.3.
**Anjuran:** bentuk tidak diubah. Layar membaca paling banyak **sepuluh**
percakapan terbaru, satu permintaan per percakapan, dan menampilkan
pertanyaan pertamanya. Biayanya sepuluh permintaan kecil saat blok 10 dibuka
— bukan saat layar dimuat. Bila Gerbang 2 lebih memilih mengubah bentuk
daftar, itu perubahan D-14 yang saya tulis lebih dulu.

**K-3 · Pesan penolakan data pribadi di layar.** Layar fitur 027 sengaja tidak
membaca badan galat (R-10 fitur 027, mutasi M-7), sehingga 400 karena data
pribadi dan 400 karena kalimat tidak utuh tampil dengan kalimat yang sama:
*"Tulis ulang dengan kalimat utuh"* — keliru bagi penanya yang menulis NIK.
**Anjuran:** kalimat `pertanyaan_ditolak` pada `mikrokopi.ts` diperluas agar
benar bagi keduanya — *"Pertanyaan belum dapat diproses. Pastikan kalimatnya
utuh dan tanpa nomor pribadi."* Layar tetap tidak membaca badan galat;
jaminan fitur 027 utuh.

## 7. Layar — P-5, R-09

| Blok | Isi | Sumber |
|---|---|---|
| 9 · Pertanyaan sebelumnya | Pertanyaan-pertanyaan percakapan aktif, **tanpa jawaban** | `GET /api/v1/percakapan/{id}`, dimuat ulang sesudah tiap jawaban |
| 10 · Percakapan terdahulu | Pertanyaan pertama dari percakapan terdahulu (K-2); tombol "Percakapan baru" | `GET /api/v1/percakapan` |

Mengetuk pertanyaan lama **mengisi isian**, tidak mengirim. Tidak ada
tanggapan yang disimpan di peramban maupun peladen (C-07).

Pengenal percakapan aktif dibangkitkan `crypto.randomUUID()` dan disimpan pada
simpanan lokal agar percakapan berlanjut sesudah muat ulang. Ia **bukan**
token: mengetahuinya tidak memberi akses, sebab kepemilikan ditentukan
identitas di peladen (R-02). Uji `halaman.test.ts` yang membatasi penulisan
simpanan lokal diperluas ke kunci kedua ini secara tegas, bukan dilonggarkan.

`kontrak.ts` memperoleh `Giliran` dan bentuk kedua rute riwayat; pemeriksa
kontrak V-03 membandingkannya dengan model Python, sebagaimana `Tanggapan`.

## 8. Uji

### 8.1 Di dalam `make check`

Seluruh uji basis data berjalan terhadap PostgreSQL sungguhan, sebab sifat yang
dijaga — hak tambah-saja, penolakan tulis bagi jalur penjawaban — tidak dapat
ditiru. Uji lapisan HTTP memakai `TestClient` dengan dua identitas tiruan dan
`RiwayatMemori`; uji kontrak penyimpan menjalankan perilaku yang sama atas
`RiwayatPostgres`.

### 8.2 Di luar `make check`

Playwright global, sama dengan fitur 027: dua pertanyaan pada satu percakapan,
muat ulang, percakapan berlanjut dan blok 9 memuat keduanya; percakapan baru;
blok 10 memuat yang lama. Terhadap `make jalan` dengan riwayat PostgreSQL.

### 8.3 Uji mutasi

| | Mutasi | Yang wajib menangkapnya |
|---|---|---|
| M-1 | Saringan pemilik pada daftar dihapus | R-03 |
| M-2 | Pemeriksaan pemilik saat mencatat dihapus | R-02 |
| M-3 | Percakapan milik orang lain dijawab 403, bukan 404 | R-02, R-03 |
| M-4 | Pemeriksaan data pribadi dipindah sesudah `jalur.jawab` | R-15 |
| M-5 | Pencatatan giliran dihapus dari `/tanya` | R-01 |
| M-6 | `peran_riwayat` diberi `UPDATE` | R-08, R-12 |
| M-7 | `peran_penjawaban` diberi `USAGE` atas `riwayat` | R-05, C-17 |
| M-8 | Galat kembali ke bentuk `{"pesan"}` | R-14 |
| M-9 | `id_jejak` tidak ditulis ke log | R-14 |
| M-10 | Pertanyaan ditulis ke log operasional | R-14, R-15 |
| M-11 | `jalur.jawab` menerima giliran sebelumnya | R-07, C-14 |
| M-12 | Mengetuk pertanyaan lama langsung mengirimnya | R-09 |
| M-13 | Satu bidang `Giliran` pada `kontrak.ts` diganti nama | V-03 |
| M-14 | `id_percakapan` bukan UUID v4 diterima | R-16 |

## 9. Urutan tugas

| | Tugas | Mengapa di sini |
|---|---|---|
| T-1 | D-14 Bagian 5 (dua tabel) dan 4.3 (K-1) | Nama tabel sebelum SQL; kontrak sebelum kode |
| T-2 | `06-riwayat.sql`, `peran_riwayat`, uji hak terhadap peladen | Peladen menegakkan tambah-saja sebelum ada penulisnya |
| T-3 | `src/penyimpanan/riwayat.py`, dua pelaksana, satu uji kontrak | Penyimpan sebelum pemakainya |
| T-4 | `Identitas` dan penentu identitas | Pemilik sebelum riwayat ditulis |
| T-5 | Bentuk galat D-14 4.2, log operasional, pemeriksa C-13 | Galat 404 yang R-02 tuntut perlu bentuknya lebih dulu |
| T-6 | `/tanya` mencatat giliran; kepemilikan; data pribadi; rute riwayat tersaring | Inti fitur — TK-65, TK-67, TK-68 |
| T-7 | Web: `id_percakapan`, blok 9 dan 10, kontrak | Pembaca bagi penulis T-6 |
| T-8 | Mutasi M-1 s.d. M-14, bukti Playwright, `src/rag/` dan `src/llm/` tanpa perubahan | |
| T-9 | Penutupan: TK-65 s.d. TK-68 pada D-00, L8, dokumen HKI, L4 | |

## 10. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Kepemilikan ternyata menuntut perubahan `src/rag/` atau `src/llm/` | **Berhenti.** R-11 |
| Bentuk tanggapan `/tanya` ternyata perlu berubah | **Berhenti.** C-20; P-2 memilih jalan tanpa perubahan itu |
| Pemisahan pseudonim ternyata menuntut basis data pseudonim terjangkau layanan aplikasi | **Berhenti.** C-05 |
| Paket baru tampak perlu (misalnya pembangkit UUID) | **Berhenti.** C-12 — `crypto.randomUUID()` dan `uuid` pustaka baku Python sudah cukup |
