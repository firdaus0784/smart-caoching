# Spec: 040-gold-set-dan-uji-pengambilan

| | |
|---|---|
| Kebutuhan | D-08 Bagian 5 dan 6 (U3); BT-35, BT-29; KL-01; C-09, C-16, C-17, C-20 |
| Dokumen terkait | D-08 Bagian 5.1, 5.2, 6 · D-07 Bagian 4.6 · D-10 L1, L2 · spec fitur 004, 025, 039 |
| Status | **Menunggu Gerbang 4** — 13 Oktober 2026 (KB-300). Delapan dari delapan tugas selesai |

## Mengapa fitur ini diusulkan sekarang

Kalibrasi ambang BT-29 (fitur 025) dan pengujian pengambilan U3 (D-08
Bagian 6) sama-sama menunggu *gold set* yang **dibekukan** (D-08 Bagian 5.2).
Isinya pekerjaan tim substansi. Tetapi alat untuk mencatat, memeriksa,
membekukan, dan mengukurnya juga belum ada, sehingga hari *gold set* selesai
disusun tim masih akan diikuti pekerjaan alat yang berminggu-minggu. Sejak
fitur 039, korpus memiliki pemuat dan indeks leksikal yang dapat diukur. Baris
040 disisipkan atas putusan pemegang gerbang (KB-289).

## Yang tidak dikerjakan fitur ini, dinyatakan di muka

- **Menyusun isi *gold set*.** Milik tim substansi (D-08 Bagian 5.2).
  Spec fitur 025 menyatakan alasannya: *agen yang menyusunnya menguji dirinya
  sendiri*. Contoh pada repositori rekaan dan dinyatakan rekaan.
- **Menetapkan ambang.** Ambang U3 milik D-08 Bagian 6; ambang kecukupan
  milik BT-29 (C-16). Fitur ini mengukur dan melaporkan, tidak memutus.
- **Kalibrasi.** Milik fitur 025, yang memakai alat ini sesudah *gold set*
  dibekukan.
- **Uji akurasi menyeluruh U4.** Menuntut model penjawab (ADR-12) dan panel
  ahli.

## Kebutuhan (EARS) yang tidak bergantung pada pertanyaan

| ID | Kebutuhan |
|---|---|
| R-01 | Berkas *gold set* sungguhan **TIDAK BOLEH** masuk repositori (D-08 Bagian 5.2, penyimpanan terpisah); repositori hanya memuat bentuknya dan contoh rekaan |
| R-02 | Validasi **HARUS** menolak berkas yang kuncinya menunjuk dokumen di luar korpus atau bagian tanpa segmen, yang jenisnya di luar A s.d. F, atau yang kuncinya tidak sesuai jenisnya — C dan D tanpa kunci; A, B, E berkunci; F sedikitnya dua kunci |
| R-03 | Pembekuan **HARUS** mencatat sidik isi kanonik berkas beserta komposisinya ke logbook L2; pengukur **HARUS** menolak berkas yang sidiknya tidak tercatat beku (selaras R-02 fitur 025) |
| R-04 | Definisi dan ambang metrik **HARUS** milik D-08 Bagian 6 — dibaca uji dari tabelnya, tidak disalin ke kode (C-16) |
| R-05 | Kebocoran indeks — segmen indeks metadata di antara kandidat penyusunan — **HARUS** diukur setiap putaran, dan putaran dengan kebocoran lebih dari nol **HARUS** dilaporkan gagal kepatuhan (KL-01) |
| R-06 | Setiap putaran **HARUS** tercatat ke logbook L1 (C-09) beserta versi kode, sidik indeks, sidik *gold set*, dan konfigurasi sumber — termasuk putaran yang gagal; laporan **HARUS** menyebut pertanyaan yang gagal (R-05 fitur 025) |
| R-07 | Laporan dan logbook **HARUS** menyebut pengenal pertanyaan dan segmen, **TIDAK BOLEH** memuat teks pertanyaan maupun teks segmen (KM-03) |
| R-08 | Fitur ini **TIDAK BOLEH** menambah rute maupun hak tulis peladen (C-17, C-20); pengukur membaca korpus sebagai peran pemuat yang sudah ada |

## Pertanyaan terbuka

Tiap pertanyaan disertai anjuran; anjuran bukan putusan.

**P-1 · Bentuk dan tempat berkas.**

| Pilihan | Arti |
|---|---|
| A | **JSON Lines di luar repositori**, jalurnya diserahkan pada perkakas; satu baris satu pertanyaan — pengenal, teks, jenis A s.d. F, kategori, kunci jawaban, tanda bernomor regulasi. Repositori memuat bentuknya pada D-08 dan contoh rekaan untuk uji |
| B | Tabel PostgreSQL skema `evaluasi` dengan peran baru |
| C | Di dalam repositori |

**Anjuran: A.** D-08 meminta *gold set* terpisah dari data pengembangan dan
hanya dibuka saat evaluasi; berkas di luar repositori memenuhinya tanpa peran
dan skema baru. Pilihan C bertentangan dengan D-08.

**P-2 · Bentuk kunci jawaban.**

| Pilihan | Arti |
|---|---|
| A | **Dokumen dan pasal.** Segmen dihitung sebagai kunci bila dokumennya sama dan penandanya pasal itu atau bagiannya — ayat dan potongan jendela fitur 038. Tahan pengindeksan ulang dan perubahan ukuran segmen D-07 |
| B | Dokumen dan penanda persis |
| C | Pengenal segmen |

**Anjuran: A.** Kunci disusun tim substansi yang berpikir dalam pasal, bukan
dalam segmen. Pengenal segmen berubah bila D-07 Bagian 3.2 kelak mengubah
ukuran segmen, dan *gold set* yang beku tidak boleh ikut berubah.

**P-3 · Komposisi saat pembekuan.** D-08 Bagian 5.1 menetapkan 200 pertanyaan
— A 100, B 30, C 30, D 15, E 15, F 10 — dan spec fitur 025 mencatat pertanyaan
terbuka tentang ukuran minimum kalibrasi pertama.

| Pilihan | Arti |
|---|---|
| A | **Pembekuan ditolak bila komposisinya menyimpang dari D-08 Bagian 5.1.** *Gold set* lebih kecil bagi prototipe menuntut perubahan D-08 lebih dulu |
| B | Dibekukan dengan penyimpangan tercatat pada L2 dan disebut pada setiap laporan |

**Anjuran: A.** D-08 pemilik tunggal komposisi. Pilihan B memindahkan putusan
itu ke perkakas, dan angka yang lahir dari *gold set* yang menyimpang akan
dibaca seolah memenuhi D-08.

**P-4 · Sumber yang diukur.** Sumber vektor menuntut penyemat sungguhan
(ADR-12), sehingga hari ini hanya sisi leksikal yang dapat berjalan atas korpus.

| Pilihan | Arti |
|---|---|
| A | **Konfigurasi yang tersedia, dinyatakan pada laporan dan L1**: leksikal saja sekarang, hibrida begitu ADR-12. Laporan leksikal tidak pernah menyatakan "U3 lulus" — ambang D-08 berlaku bagi pengambilan hibrida |
| B | Hanya hibrida: pengukur menolak berjalan tanpa penyemat sungguhan |

**Anjuran: A.** Pengukuran leksikal memberi tim gambaran dini apakah pasal
yang semestinya ditemukan memang ditemukan, terutama pada pertanyaan bernomor
regulasi — alasan ADR-03 memilih BM25 — tanpa menyamarkan bahwa U3 belum
dijalankan.

**P-5 · Arti "relevan" pada Precision@5.** D-08 menyebut porsi segmen relevan
pada lima teratas, tetapi *gold set* hanya memuat kunci.

| Pilihan | Arti |
|---|---|
| A | **Relevan = cocok dengan kunci**; dilaporkan sebagai batas bawah, dengan keterangan itu |
| B | Tim menilai relevansi setiap segmen teratas pada berkas penilaian terpisah |

**Anjuran: A.** Tanpa penilaian tambahan, kunci adalah satu-satunya tolok ukur
yang tidak disusun agen. Pilihan B dapat ditambahkan kelak tanpa mengubah
bentuk berkas.

**P-6 · Pertanyaan bernomor regulasi.** D-08 memberi ambang tersendiri.

| Pilihan | Arti |
|---|---|
| A | **Ditandai tim** pada berkas — bidang tersendiri |
| B | Dikenali otomatis dengan pola nomor regulasi |

**Anjuran: A.** Pola yang ditulis agen adalah penafsiran yang menentukan
himpunan bagian pengukuran berambang 95%; tanda dari tim tidak.

## Putusan Gerbang 1 (KB-291)

Pemegang Gerbang 1–4 memilih anjuran pada setiap pertanyaan:

| Pertanyaan | Putusan |
|---|---|
| P-1 | **A** — JSON Lines di luar repositori, jalurnya diserahkan pada perkakas; bentuknya pada D-08, contoh rekaan pada uji |
| P-2 | **A** — kunci berupa dokumen dan pasal; ayat dan potongan jendela pasal itu terhitung kunci |
| P-3 | **A** — pembekuan ditolak bila komposisi menyimpang dari D-08 Bagian 5.1 |
| P-4 | **A** — konfigurasi yang tersedia dinyatakan pada laporan dan L1; laporan leksikal tidak menyatakan U3 lulus |
| P-5 | **A** — relevan berarti cocok dengan kunci; Precision@5 dilaporkan sebagai batas bawah |
| P-6 | **A** — pertanyaan bernomor regulasi ditandai tim pada bidang tersendiri |

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | D-08 Bagian 5.2 |
| R-02 | D-08 Bagian 5.1, 5.2 |
| R-03 | D-08 Bagian 5.2; spec fitur 025 R-01, R-02; D-10 L2 |
| R-04 | D-08 Bagian 6; C-16 |
| R-05 | D-08 Bagian 6; KL-01 |
| R-06 | C-09; D-10 L1; spec fitur 025 R-05, R-06 |
| R-07 | KM-03 |
| R-08 | C-17; C-20 |

## Kriteria penerimaan

- [x] P-1 s.d. P-6 diputus pada Gerbang 1
- [x] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [x] Pengukur dijalankan atas korpus PostgreSQL sebagai peran sungguhan,
      dengan *gold set* rekaan yang dinyatakan rekaan
- [x] `make check` lulus enam gerbang
