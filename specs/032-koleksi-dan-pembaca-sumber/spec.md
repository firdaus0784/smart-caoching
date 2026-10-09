# Spec: 032-koleksi-dan-pembaca-sumber

| | |
|---|---|
| Kebutuhan | FR-F11, FR-G06, FR-G10; NFR-09; C-02, C-03, C-04, C-05, C-07, C-13, C-14, C-17, C-20 |
| Dokumen terkait | D-01 Bagian 9 (`citation_opened`, `discovery_saved`) dan 9.1 · D-02 J1-4, J2, J3-5, titik kritis T2 · D-05 Bagian 3.1, S-06 blok 8, S-10, S-11, K-7 · D-06 Bagian 4 dan 7.5 · D-14 Bagian 3.2, 3.3, 4.1, 4.6 · spec fitur 013, 033, 034, 035 |
| Status | **Gerbang 3 lolos** — 9 Oktober 2026 atas pendelegasian KB-168 (KB-243). Enam dari delapan tugas selesai |

## Mengapa fitur ini diusulkan sekarang

Baris 031 tertahan TK-71; baris 032 tidak menunggu putusan tim lain. Dua hal
yang pengguna sudah lihat belum dapat dipakai: tombol **Simpan** pada blok 8
S-06 tidak tampil karena "Simpan milik baris 032" (D-05, fitur 013), dan
**dasar rujukan** pada S-09 menyebut pasal tanpa dapat dibuka — titik kritis T2
D-02, sitasi pertama, berhenti pada nama dokumen. Sejak fitur 035 analitik juga
menyatakan rasio penelusuran sumber belum terukur dengan sebab "pembaca sumber
belum dibangun".

## Temuan yang diajukan bersama usulan ini

**TK-80 · D-14 tidak memuat rute untuk menampilkan maupun mengosongkan
koleksi.** Bagian 3 memuat `POST /butir/{id}/simpan` dan `GET /sumber/{id}`
saja. S-11 "Koleksi tersimpan" menampilkan butir yang disimpan beserta
catatannya (FR-G06) dan ditelusuri per kategori dan jenis sumber (FR-G10, yang
D-05 petakan ke S-11), tetapi tidak ada rute yang mendaftarnya; tidak ada pula
jalan mengeluarkan butir dari koleksi. Bentuknya sama dengan TK-77: pekerjaan
yang dipetakan ke layar tanpa rute. AG-02 melarang menambahkannya tanpa putusan
(P-1).

## Di luar cakupan

- Komitmen dan jurnal belajar pada "Milik saya" — baris 031, tertahan TK-71
- Arsip seluruh butir tayang di luar koleksi pengguna — FR-G10 dipenuhi atas
  koleksi, mengikuti pemetaan D-05 S-11; penelusuran yang lebih luas melampaui
  pagu harian FR-G05 dan bukan putusan baris ini
- Membuka sumber butir pada beranda — `SumberButir` membawa tautan luar, bukan
  dokumen korpus
- Pembaca bagi `bacaan_lanjutan` — sumber indeks metadata tidak pernah menjadi
  dasar klaim (FR-D06); tautannya tetap tautan luar
- Pengunduhan dokumen utuh, anotasi pada dokumen, dan penanda halaman

## Kebutuhan (EARS) yang tidak bergantung pada pertanyaan

| ID | Kebutuhan |
|---|---|
| R-01 | `POST /butir/{id}/simpan` **HARUS** hanya terbuka bagi peran `pengguna`, dan hanya bagi butir yang pernah tayang bagi pemanggil; selainnya **HARUS** berbentuk sama persis dengan butir yang tidak dikenal (pola detail butir D-14 Bagian 4.6) |
| R-02 | Catatan pribadi boleh kosong; **JIKA** ia memuat data pribadi berpola (FR-B04), **MAKA** simpan ditolak sebelum tersimpan dan catatan **TIDAK BOLEH** sampai ke log (KM-03) |
| R-03 | Menyimpan **TIDAK BOLEH** mengubah pemilihan beranda maupun jawaban (C-14): koleksi bukan sinyal personalisasi |
| R-04 | `GET /sumber/{id}` **HARUS** hanya terbuka bagi peran `pengguna` dan hanya menjangkau dokumen **korpus** yang anonimisasinya terverifikasi; dokumen karantina, yang tidak dikenal, dan yang tidak memenuhi syarat **HARUS** berbentuk sama (C-03) |
| R-05 | Pembaca sumber **TIDAK BOLEH** memanggil model maupun jalur penjawab, dan **TIDAK BOLEH** menulis apa pun selain peristiwa telemetri (C-08, C-17) |
| R-06 | Teks segmen berlisensi di luar daftar lisensi terbuka D-06 Bagian 4 **TIDAK BOLEH** dikirim pembaca sumber (D-06 Bagian 4; C-02 lapis tampilan; sejalan dengan FR-G08 bagi butir) |
| R-07 | Status keberlakuan dokumen dan rujukan penggantinya **HARUS** tampil sebelum isinya; dokumen berstatus `dicabut` **HARUS** dinyatakan tidak berlaku (C-07) |
| R-08 | Penarikan data (fitur 033) **HARUS** menghapus koleksi dan catatannya; daftar data yang ditarik pada S-14 menyebutnya |
| R-09 | Bentuk setiap rute **HARUS** ditulis ke D-14 sebelum kodenya; tanggapan `/tanya` **TIDAK BOLEH** berubah (C-20) |
| R-10 | Navigasi "Milik saya" (D-05 Bagian 3.1) **HARUS** tampil ketika koleksi terbangun, berisi Koleksi saja; komitmen dan jurnal **TIDAK BOLEH** tampil sebagai tujuan kosong (K-7 fitur 013) |

## Pertanyaan terbuka

Tiap pertanyaan disertai anjuran; anjuran bukan putusan.

**P-1 · TK-80 — rute koleksi.**

| Pilihan | Arti |
|---|---|
| A | **Dua rute baru:** `GET /api/v1/koleksi` — butir tersimpan beserta catatan, disaring kategori dan jenis sumber (FR-G06, FR-G10) — dan `DELETE /api/v1/butir/{id}/simpan` untuk mengeluarkan butir dari koleksi |
| B | Satu rute baru `GET /api/v1/koleksi`; koleksi tambah-saja, butir tidak dapat dikeluarkan |
| C | Tanpa rute baru: Simpan terpasang pada S-06, tetapi S-11 tidak dibangun; koleksi tersimpan tanpa dapat dilihat |

**Anjuran: A.** Koleksi yang tidak dapat dilihat bukan koleksi, dan koleksi
yang tidak dapat dikosongkan membuat pengguna ragu menyimpan. Rute baru hanya
sah atas putusan Anda (AG-02).

**P-2 · Isi pembaca sumber (S-10).** Korpus memuat dokumen publik **dan**
dokumen sekolah berpersetujuan pemilik (`internal_sekolah`, `terbatas`).
Jawaban meringkas keduanya; membuka teksnya kata demi kata bagi kepala sekolah
lain adalah pemakaian yang berbeda.

| Pilihan | Arti |
|---|---|
| A | **Bagian yang dirujuk saja**, bila dokumen `publik`, berlisensi terbuka, dan anonimisasinya terverifikasi. Selainnya metadata — judul, penerbit, tahun, bagian, status — beserta tautan luar bila ada, tanpa teks |
| B | Seperti A, tetapi dokumen utuh dengan gulir ke bagian yang dirujuk |
| C | Teks bagian bagi semua tingkat kerahasiaan, selama berlisensi terbuka |
| D | Tanpa pembaca di dalam aplikasi: tautan luar saja |

**Anjuran: A.** FR-F11 meminta bagian spesifik, bukan dokumen utuh. Apakah
persetujuan pemilik dokumen sekolah (ET-04) mencakup penayangan teks kepada
peserta lain adalah putusan tim etik; sampai diputus, teksnya tidak tampil.

**P-3 · Telemetri dan analitik.** D-01 Bagian 9 menetapkan `citation_opened`
(id sumber, jenis sumber) dan `discovery_saved` (ada/tidak catatan pribadi).
TK-73 mencatat `citation_opened` hanya teramati di peramban; dengan rute
pembaca, ia teramati di peladen.

| Pilihan | Arti |
|---|---|
| A | **Rekam keduanya** lewat gerbang C-04, dengan properti D-01 apa adanya. Analitik fitur 035 menghitung rasio penelusuran sumber D-01 Bagian 9.1 (`citation_opened` / `answer_served`); `rasio_penelusuran_sumber` keluar dari daftar belum terukur |
| B | Rekam keduanya; analitik tidak berubah |
| C | Tidak merekam pada baris ini |

**Anjuran: A.** Definisi rasionya sudah ditetapkan D-01 Bagian 9.1, bukan
dikarang pelaksana. Mengubah analitik berarti mengubah bentuk D-14 Bagian 4.8
dan daftar `MetrikTertunda` — keduanya hanya atas putusan ini.

**P-4 · Butir tersimpan yang kemudian ditarik.** D-06 Bagian 7.5: pengguna
"tetap dapat melihatnya dalam koleksi, disertai penanda bahwa dasar rujukannya
telah berubah".

| Pilihan | Arti |
|---|---|
| A | **Sesuai D-06:** judul, catatan, dan isi tetap terbaca; penanda "dasar rujukannya telah berubah" tampil **sebelum** isi, sejalan dengan penanda dasar rujukan S-09 |
| B | Judul, catatan, dan penanda saja; isinya tidak lagi tampil |

**Anjuran: A.** Itu bunyi D-06, dan penandanya mendahului isi sehingga tidak
terbaca sebagai dasar yang masih berlaku. Pilihan B lebih ketat terhadap
regulasi yang dicabut; ia menuntut D-06 Bagian 7.5 ditulis ulang.

## Putusan Gerbang 1 (KB-241)

Pemegang Gerbang 1–4 memilih anjuran pada setiap pertanyaan:

| Pertanyaan | Putusan |
|---|---|
| P-1 | **A** — **dua rute baru disetujui** untuk D-14 Bagian 3.3: `GET /api/v1/koleksi` (bersaring kategori dan jenis sumber) dan `DELETE /api/v1/butir/{id}/simpan`. TK-80 diputus |
| P-2 | **A** — pembaca menampilkan teks bagian yang dirujuk hanya bagi dokumen `publik`, berlisensi terbuka, dan beranonimisasi terverifikasi; selainnya metadata dan tautan luar. Cakupan persetujuan dokumen sekolah (ET-04) diputus tim etik |
| P-3 | **A** — `citation_opened` dan `discovery_saved` direkam lewat gerbang C-04 dengan properti D-01; analitik menghitung rasio penelusuran sumber D-01 Bagian 9.1 dan `rasio_penelusuran_sumber` keluar dari daftar belum terukur |
| P-4 | **A** — sesuai D-06 Bagian 7.5: butir tersimpan yang ditarik tetap terbaca dengan penanda "dasar rujukannya telah berubah" sebelum isinya |

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | FR-G06; D-14 Bagian 3.3 dan 4.6 |
| R-02 | FR-B04; KM-03 |
| R-03 | C-14 |
| R-04 | FR-F11; C-03; D-14 Bagian 3.2 |
| R-05 | C-08; C-17 |
| R-06 | D-06 Bagian 4; C-02; FR-G08 sebagai padanan bagi butir |
| R-07 | C-07; FR-F14 |
| R-08 | NFR-09; fitur 033 |
| R-09 | C-20 |
| R-10 | D-05 Bagian 3.1; K-7 fitur 013 |

## Kriteria penerimaan

- [x] P-1 s.d. P-4 diputus pada Gerbang 1
- [ ] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [ ] Hak peran pembaca sumber diuji terhadap peladen: korpus terbaca, karantina
      dan kolom vektor tidak
- [ ] Penarikan data menghapus koleksi, diuji terhadap PostgreSQL
- [ ] `make check` lulus enam gerbang
