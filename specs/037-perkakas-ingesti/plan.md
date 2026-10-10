# Plan: 037-perkakas-ingesti

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 9 Oktober 2026 (KB-255); P-1 s.d. P-6 sesuai anjuran |
| Temuan yang diputus sebelum plan | TK-84 A (KB-255): penarikan menghapus segmen dari indeks. TK-85 A (KB-256): unggahan ulang atas dokumen yang berada di korpus ditolak |
| Status | **Gerbang 3 lolos** — 10 Oktober 2026 atas pendelegasian KB-168 (KB-256). Dua dari tujuh tugas selesai |
| Kebutuhan | R-01 s.d. R-11 `spec.md`; FR-B01, FR-B04, FR-B05, FR-B06, FR-B07, FR-B08; C-02, C-03, C-05, C-17, C-20 |

## 1. Letak dan batas

```
perkakas/basis_data/
  01-peran-dan-basis-data.sql   + peran_ingesti, peran_penarikan_dokumen
  15-ingesti.sql                baru — empat catatan karantina; hak ketiga peran
                                dokumen; hak bawaan karantina bagi verifikator dicabut
src/kamus/                      + PutusanGerbang (setujui, tolak, cabut_persetujuan)
src/nlp/anonimisasi/samaran.py  baru — penyamaran enam pengenal berpola dengan token D-03
src/penyimpanan/karantina.py    baru — catatan keadaan gerbang, memori dan PostgreSQL
src/penyimpanan/dasar.py        pindahkan(..., jejak=None)
src/penyimpanan/tiruan.py       jejak ikut pemindahan
src/penyimpanan/postgres.py     jejak dalam pernyataan yang sama; keluar dari korpus
                                membawa segmen keluar dari kedua indeks (TK-84 A)
src/ingest/gerbang.py           keadaan lewat catatan; penyamaran saat terima;
                                unggahan ulang atas dokumen korpus ditolak (TK-85 A)
src/ingest/jejak.py             pemeriksaan baris tanpa menambahkannya
perkakas/ingesti.py             baru — terima, daftar, baca, tinjau, setujui, tolak, cabut
tests/peladen.py, README        kedua peran baru
docs/                           D-14 5.1 dan kamus enum; D-04 7.2 dan KA-04; D-00
```

**`src/api/`, `src/rag/`, `src/llm/`, `src/pengguna/`, `src/telemetri/`, dan
`web/` tidak disentuh.** Tidak ada rute baru (R-10). Tidak ada tepi impor
baru: `ingest → nlp`, `ingest → penyimpanan`, dan `ingest → kamus` sudah
tertulis pada AGENTS.md; `perkakas/` berada di luar `src/`.

## 2. K-1 · Catatan karantina dan peran

Seluruh catatan **tambah-saja**, di skema `karantina` (P-1 A). Tidak satu peran
pun memegang ubah maupun hapus atasnya.

| Tabel | Isi | Penulis |
|---|---|---|
| `karantina.penerimaan` | `nomor`, `id_dokumen`, metadata `Dokumen` (judul, jenis, penerbit, tahun, tingkat kerahasiaan, status persetujuan pemilik), `samaran` (jumlah per jenis, tanpa nilai), `id_penerima`, `diterima_pada`. Satu baris per unggahan; yang terbaru berlaku | `peran_ingesti`, dalam pernyataan yang sama dengan teks dokumen |
| `karantina.temuan_pola` | `nomor_penerimaan`, `pola`, `mulai`, `akhir`, `kutipan` — dari teks **sesudah** disamarkan | `peran_ingesti`, pernyataan yang sama |
| `karantina.tinjauan_temuan` | `nomor_penerimaan`, `id_peninjau`, `catatan`, `ditinjau_pada` | `peran_verifikasi` |
| `karantina.jejak_area` | D-04 Bagian 7.2: `id`, `id_dokumen`, `id_pelaku`, `dari_area`, `ke_area`, `alasan`, `waktu`; ditambah `nomor_penerimaan` dan `putusan` (`PutusanGerbang`) | `peran_verifikasi` (setujui, tolak), `peran_penarikan_dokumen` (cabut) |

`id_penerima`, `id_peninjau`, dan `id_pelaku` dijaga batasan tabel berpola
`^[a-z]{2,8}-[0-9]{3}$` (P-6 A). Alasan, catatan tinjauan, dan kutipan tidak
dapat dijaga peladen dari data pribadi; yang menjaganya pemeriksaan
`JejakArea` dan perkakas, sebelum pernyataan dikirim (R-07).

**Keadaan diturunkan, tidak disimpan** (P-1 A). Bagi penerimaan terbaru `P`:

| Keadaan | Diturunkan dari |
|---|---|
| Area | Tabel `dokumen_sumber` tempat teksnya berada |
| Status anonimisasi | Jejak `setujui` atau `tolak` terbaru yang merujuk `P`; tanpanya `menunggu` |
| Status persetujuan pemilik | Nilai pada `P`, kecuali ada jejak `cabut_persetujuan` yang merujuk `P` |
| Temuan dan tinjauan | Baris yang merujuk `P` saja — unggahan ulang membatalkan tinjauan lama tanpa menghapusnya (R-03) |
| Alasan terakhir | Jejak terbaru dokumen itu, merujuk penerimaan mana pun |

| Peran | Hak | Yang sengaja **tidak** dipegang |
|---|---|---|
| `peran_ingesti` (baru) | `USAGE` karantina dan korpus; `INSERT`, `UPDATE (isi, disimpan_pada)`, dan `SELECT (id)` atas `karantina.dokumen_sumber`; `INSERT` atas `penerimaan` dan `temuan_pola`; `SELECT (id)` atas `korpus.dokumen_sumber` (TK-85 A) | Membaca `isi` di area mana pun; tinjauan, jejak, korpus selain kolom `id`; indeks |
| `peran_verifikasi` | `SELECT` atas keempat catatan; `INSERT` atas `tinjauan_temuan` dan `jejak_area`; **`DELETE` atas `karantina.dokumen_sumber`** | **`INSERT` dan `UPDATE` atas karantina** — dicabut dari hak bawaan skema, juga bagi tabel yang dibuat kelak (P-2 A) |
| `peran_penarikan_dokumen` (baru) | `USAGE` korpus, karantina, kedua indeks; `SELECT`, `DELETE` atas `korpus.dokumen_sumber`; `INSERT` atas `karantina.dokumen_sumber`; `SELECT (nomor, id_dokumen)` atas `penerimaan`; `INSERT` atas `jejak_area`; `SELECT (id_dokumen)` dan `DELETE` atas kedua tabel `segmen_teks` | Teks segmen, kolom vektor; temuan dan tinjauan; menyisipkan ke korpus maupun indeks |

Peran pengambilan, pemanggil model, penyematan, pembaca sumber, dan seluruh
peran aplikasi lain tetap tanpa `USAGE` atas karantina (R-05). Kedua peran
baru tidak memperoleh `CONNECT` ke basis data pseudonim. Uji katalog hak
memeriksa ketiga peran dokumen **persis** di seluruh skema, dan setiap peran
dijalankan **dengan haknya sendiri** pada perintahnya — pelajaran TK-63, TK-64,
dan TK-83: uji yang tersambung sebagai pengelola tidak membuktikan apa pun
tentang peran.

## 3. K-2 · Penyamaran saat menerima (P-5 A)

`src/nlp/anonimisasi/samaran.py`: `samarkan(teks) → HasilSamaran(teks,
jumlah)`. Rentang dari `periksa_data_pribadi()` fitur 015 diganti token D-03 —
`[NIK]`, `[NIP]`, `[NISN]`, `[NUPTK]`, `[TELEPON]`, `[REKENING]` — dari akhir
ke awal, sehingga indeks karakter rentang berikutnya tidak bergeser. Rentang
yang bertindih digabung dan diberi token jenis yang terdeteksi lebih dulu.
`jumlah` memuat keenam jenis, termasuk yang nol, tanpa nilai yang disamarkan.

`Gerbang.terima()` menyamarkan **sebelum** apa pun: pemeriksa pola adversarial
berjalan atas teks tersamar, sehingga kutipan temuan tidak membawa pengenal.
Teks asli tidak diteruskan ke penyimpan. Penyamaran tidak menutup nama dan
alamat (BT-70); `perkakas ingesti baca` menyatakannya setiap kali.

## 4. K-3 · Keadaan gerbang lewat catatan (P-1 A)

`Gerbang` tetap pemegang **aturan**; penyimpannya berubah dari kamus di memori
menjadi `CatatanGerbang` (`src/penyimpanan/karantina.py`), dengan pelaksana
memori dan PostgreSQL yang lulus uji kontrak yang sama. Penyimpanan berada di
bawah ingesti, sehingga catatannya memakai untai dan bilangan, bukan enum
`Dokumen` — alasan yang sama dengan `MetadataDokumen` fitur 032.

- `Gerbang(penyimpan)` tanpa catatan memakai pelaksana memori, sehingga
  **seluruh uji fitur 002 lulus tanpa diubah** (R-02). Aturan tidak bercabang
  menurut pelaksana.
- **Atomik.** `SambunganAktif` tanpa transaksi, sehingga setiap penulisan
  majemuk satu pernyataan:
  - `terima`: teks, penerimaan, dan temuan;
  - `setujui`: hapus dari karantina → sisipkan ke korpus → metadata → jejak
    (`pindahkan(..., metadata=, jejak=)`);
  - `cabut` atas dokumen korpus: hapus dari korpus → sisipkan ke karantina →
    hapus segmen dari kedua indeks → jejak.

  Jejak yang ditolak batasan tabel membatalkan pemindahannya, dan sebaliknya
  (R-06).
- **Keluar dari korpus membawa segmen keluar dari indeks** (TK-84 A). Aturan
  itu tinggal di `PenyimpanPostgres.pindahkan()`, berlaku bagi setiap pemanggil,
  bukan hanya penarikan. Pelaksana memori tidak memiliki indeks.
- **Jejak diperiksa dulu, ditulis bersama pemindahan.** `JejakArea` memperoleh
  pemeriksaan baris tanpa menambahkannya. Alasan berdata pribadi tetap
  membatalkan persetujuan sebelum apa pun tersentuh; pemindahan yang gagal
  tidak lagi meninggalkan baris jejak tanpa perpindahan.
- **TK-85 A.** `terima` atas `id_dokumen` yang sedang di korpus ditolak
  `GalatGerbang`, pada kedua pelaksana. Pada PostgreSQL penolakan itu bagian
  pernyataan sisipnya (`WHERE NOT EXISTS` atas kolom `id` korpus), sehingga
  dua perintah yang bersamaan tidak dapat meloloskannya. Versi baru masuk
  dengan id baru; versi lama ditandai lewat perintah `status` perkakas kurasi
  (TK-81 A).

## 5. K-4 · Perkakas `python -m perkakas.ingesti`

| Perintah | Peran | Isi |
|---|---|---|
| `terima --berkas --id --judul --jenis --penerbit --tahun --kerahasiaan --persetujuan --pelaku` | `peran_ingesti` | Ekstraksi lewat pengekstrak fitur 015 menurut jenis berkas (PDF, DOCX, XLSX, gambar pindai), penyamaran, lalu `Gerbang.terima`. Mencetak jumlah samaran per jenis dan jumlah temuan — tanpa teks |
| `daftar` | `peran_verifikasi` | Dokumen di karantina: id, judul, jenis, tingkat kerahasiaan, status persetujuan, status anonimisasi, jumlah temuan, sudah ditinjau atau belum. Tanpa teks |
| `baca --id` | `peran_verifikasi` | Teks tersamar dan temuan beserta kutipannya, ke keluaran baku saja, diawali pernyataan BT-70 (R-08) |
| `tinjau --id --pelaku --catatan` | `peran_verifikasi` | `Gerbang.tinjau_temuan` |
| `setujui --id --pelaku --alasan` | `peran_verifikasi` | `Gerbang.setujui` |
| `tolak --id --pelaku --alasan` | `peran_verifikasi` | `Gerbang.tolak` |
| `cabut --id --pelaku --alasan` | `peran_penarikan_dokumen` | `Gerbang.cabut_persetujuan` (R-09) |

Sambungan per perintah dengan perannya sendiri, alamat dari `PGHOST` dan
`PGPORT` seperti perkakas kurasi. `--pelaku` diperiksa polanya sebelum
menyambung. Galat dicetak dalam bahasa Indonesia tanpa mengutip alasan,
catatan, maupun teks. Perkakas **tidak** menulis apa pun ke log; keluaran OCR
dicatat ke logbook seperti fitur 015 (C-09).

## 6. K-5 · Kontrak

D-14 Bagian 5.1: keempat catatan karantina, `jejak_area.putusan`, dan letak
bidang `dokumen_sumber.status_anonimisasi`, `status_persetujuan_pemilik`,
`area_simpan` sebagai keadaan yang diturunkan. D-14 kamus enum:
`PutusanGerbang`. D-04 Bagian 7.2 (`jejak_area` bertambah dua bidang; tiga
catatan baru) dan KA-04 (ketiga peran dokumen). Tanpa rute; D-14 Bagian 3 dan
bentuk `/tanya` tidak berubah (R-10).

## 7. Keputusan rancangan Gerbang 2

| Kode | Pertanyaan | Putusan |
|---|---|---|
| K-1 | Catatan dan peran | Bagian 2 — tambah-saja; keadaan diturunkan; tiga peran dokumen |
| K-2 | Penyamaran | Bagian 3 — sebelum pemeriksa pola; dari akhir ke awal |
| K-3 | Keadaan gerbang | Bagian 4 — aturan tetap di `Gerbang`; atomik; segmen ikut keluar; TK-85 A |
| K-4 | Perkakas | Bagian 5 — tujuh perintah, satu peran per perintah |
| K-5 | Kontrak | Bagian 6 |
| K-6 | Batas sentuhan fitur 002 | Aturan tidak berubah kecuali TK-85 A dan urutan jejak (Bagian 4); uji fitur 002 lulus apa adanya |

## 8. Uji

### 8.1 Di dalam `make check`

- Peladen: katalog hak persis ketiga peran dokumen; penolakan berpenyebab
  `permission denied` — ingesti membaca `isi`, verifikator menyisipkan atau
  mengubah karantina, penarikan membaca teks segmen, peran aplikasi lain
  menjangkau karantina; batasan pola pelaku; batasan `putusan` dibandingkan
  dengan enumnya. Setiap peran menjalankan perintahnya dengan haknya sendiri
- Penyamaran: keenam jenis, bertindih, berurutan, nol temuan, indeks karakter
- Catatan gerbang atas memori **dan** PostgreSQL: keadaan bertahan antarobjek
  `Gerbang`; unggahan ulang membatalkan tinjauan; ketiga gerbang tetap
  berdiri sendiri; pemindahan, metadata, dan jejak bersama atau tidak sama
  sekali; penarikan menghapus segmen (TK-84 A); unggahan ulang atas dokumen
  korpus ditolak (TK-85 A)
- Seluruh uji fitur 002 lulus tanpa diubah
- Perkakas: tiap perintah memakai perannya; pelaku tidak berpola ditolak
  sebelum menyambung; tanpa teks dan nilai pada log

### 8.2 Di luar `make check`

Perkakas dijalankan terhadap PostgreSQL dengan berkas contoh yang memuat NIK
dan pola instruksi: `terima` → `daftar` → `baca` → `tinjau` → `setujui`;
pembaca sumber `make jalan` menampilkan metadata dokumen itu tanpa teks —
segmennya milik baris 038; `cabut` → pembaca sumber menjawab tidak ada. Keluaran
dan isi tabel karantina ke `bukti/`. Berkas contoh buatan tim, tanpa data
pribadi sungguhan — NIK contoh dinyatakan sebagai contoh.

### 8.3 Uji mutasi

| Kode | Mutasi | Uji yang wajib merah |
|---|---|---|
| M-1 | `GRANT INSERT ON karantina.dokumen_sumber TO peran_verifikasi` | katalog hak |
| M-2 | `GRANT SELECT (isi) ON karantina.dokumen_sumber TO peran_ingesti` | katalog hak |
| M-3 | `DELETE` atas karantina dicabut dari `peran_verifikasi` | `setujui` berperan |
| M-4 | `GRANT USAGE ON SCHEMA karantina TO peran_pembaca_sumber` | penolakan peladen (R-05) |
| M-5 | Jejak disisipkan dalam pernyataan terpisah dari pemindahan | atomik |
| M-6 | Keluar dari korpus tanpa menghapus segmen | TK-84 |
| M-7 | Tinjauan dibaca tanpa syarat penerimaan terbaru | unggahan ulang (R-03) |
| M-8 | Teks asli disimpan, bukan teks tersamar | penyamaran saat terima |
| M-9 | Pemeriksa pola berjalan atas teks asli | kutipan temuan tanpa pengenal |
| M-10 | Syarat `NOT EXISTS` korpus dihapus | TK-85 |
| M-11 | Batasan pola pelaku dihapus | batasan tabel |
| M-12 | Status anonimisasi dari jejak penerimaan mana pun | keadaan diturunkan |
| M-13 | `baca` menulis teks ke log | perkakas tanpa log |

## 9. Urutan tugas

| Tugas | Isi |
|---|---|
| T-1 | Kontrak: D-14 5.1 dan kamus enum; D-04 7.2 dan KA-04; `PutusanGerbang`; D-00 |
| T-2 | Peladen: `15-ingesti.sql`, dua peran baru, verifikator diperketat; M-1 s.d. M-4, M-11 |
| T-3 | Penyamaran FR-B04; M-8 bagian penyamar |
| T-4 | Catatan gerbang memori dan PostgreSQL; `pindahkan(jejak=)`; segmen ikut keluar; M-5, M-6, M-12 |
| T-5 | `Gerbang` memakai catatan; penyamaran saat terima; TK-85 A; M-7, M-8, M-9, M-10 |
| T-6 | Perkakas ingesti; M-13 |
| T-7 | Bukti ujung ke ujung, penutupan: L8, HKI, L4; status menunggu Gerbang 4 |

## 10. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Rute unggah atau verifikasi tampak perlu | Berhenti; AG-02, R-10 |
| Segmentasi tampak perlu dikerjakan di sini | Berhenti; baris 038 (P-4 A) |
| Uji fitur 002 tampak perlu diubah selain TK-85 | Berhenti; R-02, fitur 002 lolos Gerbang 4 |
| Peran aplikasi tampak perlu menjangkau karantina | Berhenti; C-03 |
| Teks asli tampak perlu disimpan untuk banding | Berhenti; P-5 A |
| Paket ekstraksi atau OCR baru tampak perlu | Berhenti; C-12 |
