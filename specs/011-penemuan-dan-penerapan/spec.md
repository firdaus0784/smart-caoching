# Spec: 011-penemuan-dan-penerapan

| | |
|---|---|
| Kebutuhan | FR-G01 s.d. FR-G09, FR-H01 s.d. FR-H07 |
| Dokumen terkait | D-01 Bagian 6 Modul G dan H, D-02 Bagian 5, D-05, D-11 Bagian 3.5 |
| Pasal konstitusi yang menyentuh fitur ini | C-04, C-13, C-14, C-15 |
| Status | Menunggu Gerbang 1 |

## Tujuan

Sesudah fitur ini, rantai **membaca → memeriksa pemahaman → berkomitmen →
ditanyai penerapannya** berdiri utuh di sisi belakang. D-01 menyebut rantai ini
*"kontribusi paling kuat untuk artikel jurnal, karena mengukur Kirkpatrick
Level 3 (perubahan perilaku), bukan sekadar Level 1 (reaksi)"*.

Seluruh prasyaratnya sudah ada: prioritas manajerial (022), butir yang lolos
kurasi (010), gerbang telemetri berpersetujuan (012), dan pagu tayang harian
yang sudah bernama `PAGU_TAYANG_PER_PENGGUNA` sejak fitur 010.

## Keputusan Gerbang 1 · TK-51 — FR-H03 menuntut niat pelaksanaan

**Ini keputusan yang menahan fitur ini, dan ia diputus di sini.**

FR-H03 sebagaimana tertulis meminta *"satu komitmen tindakan konkret beserta
tenggat mandiri"*. Bukti yang dikutip proposal — Gollwitzer & Sheeran (2006),
94 studi, lebih dari 8.000 partisipan, *d* = 0,65 — berlaku bagi **niat
pelaksanaan**: rencana berbentuk **jika–maka** yang mengaitkan isyarat keadaan
tertentu dengan tindakan tertentu (Gollwitzer 1999).

Komitmen konkret bertenggat **bukan** niat pelaksanaan. Bila FR-H03 dibangun
apa adanya, fitur ini mewujudkan mekanisme yang **tidak menanggung bukti yang
dikutip untuk membenarkannya** — dan kekeliruannya baru terlihat pada analisis
hasil, ketika rasio penerapan tidak mendekati harapan dan tidak ada yang tahu
sebabnya rancangan, bukan populasi.

**Putusan: komitmen berbentuk dua bidang terpisah — isyarat dan tindakan —
dan keduanya wajib.** Bukan satu bidang teks bebas. Bidang bebas akan diisi
"saya akan lebih rajin memantau", yang tidak membawa satu pun sifat yang
membuat *d* = 0,65 berlaku.

| | |
|---|---|
| `isyarat` | Kapan atau pada keadaan apa — *"jika rapat komite berikutnya dibuka"* |
| `tindakan` | Apa yang dilakukan — *"maka saya sampaikan tiga butir ini"* |
| `tenggat` | **Bukan bagian rencananya.** Ia kapan sistem menanyakan status (FR-H04) |

Pemisahan `tenggat` dari rencananya disengaja: niat pelaksanaan bersandar pada
isyarat keadaan, bukan pada tanggal. Menyatukan keduanya membuat penggunanya
menuliskan tanggal sebagai isyarat — dan tanggal bukan isyarat keadaan.

Perubahan naskah FR-H03 pada D-01 sudah diusulkan pada D-11 Bagian 5 dan
**tetap menunggu berita acara rapat**. Kode dibangun mengikuti bentuk yang
diputus di sini; bila rapat menolaknya, yang berubah dua bidang pada satu
modul.

## Di luar cakupan

- **Seluruh layar** (D-05). `web/` belum ada; yang dibangun sisi belakangnya,
  sama seperti fitur 009, 010, 021.
- **Isi *knowledge check*** — pertanyaan dan kunci jawabannya pekerjaan
  kurator, bukan kode. Mekanismenya dibangun; isinya menyusul.
- **FR-H05 lampiran bukti** — menuntut penyimpanan berkas dan anonimisasi atas
  unggahan; menunggu penggerak PostgreSQL (C-12).
- **FR-H07 ekspor PDF** — menuntut ketergantungan yang belum disetujui (C-12).
  Dinyatakan tertahan, bukan dilewatkan, mengikuti `parquet_tertahan()` (012).
- **FR-G09 kalender manajerial** — D-02 Bagian 5 belum memuat kalender yang
  dapat dibaca mesin; D-11 Bagian 5 sudah mengusulkan penambahannya.
- **Penyimpanan tetap.** Semua di memori, mengikuti `JejakKurasi` (010) dan
  `Percakapan` (021).

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | Feed **HARUS** disaring terhadap prioritas manajerial pengguna (FR-A03) dan **TIDAK BOLEH** menayangkan butir di luar prioritas itu (FR-G01) |
| R-02 | Butir tayang **HARUS** membawa keenam bidang FR-G02 sebagai tipe, bukan untai bebas |
| R-03 | **JIKA** perkiraan waktu baca melampaui 7 menit, **MAKA** butir **TIDAK BOLEH** tayang (FR-G03) |
| R-04 | Setiap butir **HARUS** membawa label jenis sumber dari empat nilai FR-G04, sebagai tipe |
| R-05 | Feed **TIDAK BOLEH** menayangkan lebih dari `PAGU_TAYANG_PER_PENGGUNA` butir baru per pengguna per hari (FR-G05) |
| R-06 | Pagu tayang **HARUS** memakai tetapan fitur 010, bukan angka kedua |
| R-07 | **KETIKA** pengguna menyatakan "belum relevan", sistem **HARUS** mencatat alasannya sebagai umpan balik penyaringan (FR-G07) |
| R-08 | **JIKA** butir berasal dari terbitan berlisensi tertutup, **MAKA** feed **HANYA BOLEH** menayangkan metadata, abstrak, dan parafrase — **tidak pernah** teks penuh (FR-G08, C-02) |
| R-09 | *Knowledge check* **HARUS** memuat 1 sampai 3 pertanyaan (FR-H01) |
| R-10 | Umpan balik jawaban **HARUS** menyertakan rujukan bagian sumber (FR-H02) |
| R-11 | Komitmen **HARUS** berbentuk niat pelaksanaan: `isyarat` dan `tindakan` sebagai dua bidang wajib terpisah (FR-H03, TK-51) |
| R-12 | Komitmen **TIDAK BOLEH** dapat dibentuk dari satu bidang teks bebas |
| R-13 | Status penerapan **HARUS** memakai empat nilai FR-H04 sebagai tipe: sudah diterapkan, sedang berjalan, belum, tidak jadi |
| R-14 | **JIKA** status "tidak jadi" dipilih, **MAKA** alasan **HARUS** terisi (FR-H04) |
| R-15 | Jurnal belajar **HARUS** memuat ketiga bagian FR-H06 — dipelajari, dipahami, diterapkan |
| R-16 | Bidang teks bebas mana pun **TIDAK BOLEH** menerima data pribadi (KM-03, FR-B04) |
| R-17 | Perekaman peristiwa **HARUS** lewat gerbang telemetri fitur 012; sistem **TIDAK BOLEH** merekam tanpa persetujuan aktif (C-04) |
| R-18 | Sistem **TIDAK BOLEH** membuat tabel poin, lencana, papan peringkat, atau pertemanan (C-15) |

**R-11 dan R-12 berpasangan, dan keduanya inti fitur ini.** R-11 menetapkan
bentuknya; R-12 menutup jalan keluarnya. Tanpa R-12, seseorang menambahkan
`komitmen_bebas: str` "untuk pengguna yang kesulitan", dan enam bulan kemudian
seluruh data penelitian berupa untai bebas yang tidak menanggung bukti apa pun.

**R-18 diuji sebagai ketiadaan.** C-15 melarang membuatnya *"kosong pun
tidak"*, dan fitur inilah yang paling mengundangnya — jurnal belajar dengan
rekapitulasi adalah tempat lencana terasa wajar.

## Keadaan yang wajib ditangani

| Keadaan | Perilaku yang dituntut |
|---|---|
| Pengguna tanpa prioritas manajerial | Feed kosong beserta sebabnya, bukan feed acak. Prioritas ditetapkan saat *onboarding* (FR-A03) |
| Butir habis untuk hari itu | Feed kosong beserta keterangan, bukan butir yang diulang |
| Butir berlisensi tertutup | Metadata dan parafrase saja; teks penuh tidak pernah dibentuk |
| *Knowledge check* belum berisi | Butir tetap tayang; rantainya berhenti di FR-H02, dan itu dinyatakan |
| Komitmen tanpa isyarat | Ditolak — bukan disimpan sebagai komitmen lemah |
| Tenggat lewat tanpa jawaban | Status tetap "sedang berjalan"; sistem tidak menyimpulkan sendiri |
| Pengguna tanpa persetujuan telemetri | Seluruh fitur tetap berjalan; hanya perekamannya dilewati (FR-A05, C-04) |

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| FR-G01 s.d. G09 | D-01 Bagian 6 Modul G |
| FR-H01 s.d. H07 | D-01 Bagian 6 Modul H |
| Bentuk FR-H03 | D-11 Bagian 3.5; Gollwitzer (1999); Gollwitzer & Sheeran (2006) |
| Dasar FR-H01, FR-H02 | D-11 Bagian 3.5; Roediger & Karpicke (2006) |
| Pagu tayang | D-01 FR-G05; tetapan fitur 010 |
| Larangan gamifikasi | `constitution.md` C-15; D-01 Bagian 4.2 |
