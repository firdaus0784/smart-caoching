# Spec: 013-kurasi-dan-penemuan-harian

| | |
|---|---|
| Kebutuhan | FR-G01, FR-G02, FR-G03, FR-G04, FR-G05, FR-G07, FR-G08; FR-I01, FR-I02, FR-I03, FR-I06, FR-I07; NFR-19; C-02, C-03, C-06, C-07, C-13, C-14, C-15, C-20 |
| Dokumen terkait | D-05 Bagian 4, 5.3, 6, 7, 8 (S-05, S-06, S-15, S-16) · D-06 Bagian 5 dan 7 · D-14 Bagian 3.3 dan 3.4 · D-12 Bagian 7 |
| Status | **Gerbang 1 lolos** — 5 Oktober 2026 (KB-178). Gerbang 2 dan 3 atas pendelegasian KB-168 (KB-179) |

## Mengapa fitur ini diusulkan, dan mengapa bukan 013 sisa utuh

Sesudah fitur 030, pengguna yang masuk melewati aktivasi dan mendarat di
Tanya. Baris 013 pada D-12 sekarang memuat **lima belas layar**: S-05 s.d.
S-08 dan S-10 s.d. S-18. Baru 9 dari 29 rute D-14 Bagian 3 yang terpasang.

Pemeriksaan atas sisi belakang yang sudah ada menemukan urutan ketergantungan
yang tidak tertulis di mana pun:

- **Beranda tidak memiliki sumber butir.** Model `ButirTayang` (fitur 010)
  hanya lahir dari gerbang putusan kurator — itu wujud C-06. Tetapi tidak ada
  penyimpanan butir tayang, tidak ada penyimpanan antrean kurasi, dan tidak
  ada layar tempat kurator memutus. S-05 yang dibangun lebih dulu akan
  **selalu kosong di lapangan**, dan satu-satunya cara mengisinya adalah jalan
  pintas yang melewati kurator.
- **Peran internal tidak lagi tertahan.** Sejak fitur 029 setiap akun membawa
  peran (`kurator`, `peneliti`, dan seterusnya), sehingga hambatan "menunggu
  peran internal" pada catatan D-12 KB-165 sudah gugur bagi S-15 dan S-16.
- **Pemeriksaan pemahaman S-07 tidak memiliki sumber soal.** Fitur 011
  menetapkan 1–3 soal (R-09) dan umpan balik berujukan (R-10), tetapi tidak
  ada model soal, dan tidak ada dokumen yang menyebut siapa menulisnya.
- **Wireframe S-08 dan S-12 tertinggal dari TK-51.** D-05 menggambar komitmen
  sebagai "isian tunggal, teks bebas" dan alasan "tidak jadi" sebagai opsional;
  fitur 011 membangun dua bidang isyarat–tindakan dan alasan wajib (R-11, R-12,
  R-14; KB-059). Dicatat sebagai **TK-71**.

Diusulkan: 013 dipersempit lagi menjadi **irisan tegak dari putusan kurator
sampai beranda** — S-15, S-16, S-05, S-06 — dan sisanya menjadi baris baru
(P-1). Penyempitan dan penyisipan baris adalah keputusan tim; barisnya tidak
ditulis ke D-12 sebelum disetujui.

## Di luar cakupan

- S-07, S-08, S-12, S-13 (penerapan J4) — menunggu P-1 dan TK-71
- S-10 pembaca sumber, S-11 koleksi tersimpan, `POST /butir/{id}/simpan`
- S-14 pengaturan dan `DELETE /api/v1/saya/data` (NFR-09)
- S-17 aduan jawaban, S-18 analitik penelitian
- Penarikan butir tayang (`POST /kurasi/{id}/tarik`, FR-I06) — lihat P-5
- Perekaman telemetri peristiwa penemuan — lihat P-6
- Pengisian antrean dari dokumen sungguhan — korpus milik tim
- `src/rag/` dan `src/llm/` — tidak disentuh; tidak ada pemanggilan model pada
  jalur feed

## Kebutuhan (EARS) yang tidak bergantung pada pertanyaan

| ID | Kebutuhan |
|---|---|
| R-01 | Bentuk tanggapan `GET /api/v1/beranda`, `GET /api/v1/butir/{id}`, `POST /api/v1/butir/{id}/tolak`, `GET /api/v1/kurasi/antrean`, dan `POST /api/v1/kurasi/{id}/putusan` **HARUS** ditulis ke D-14 Bagian 4 **sebelum** kodenya (C-20) |
| R-02 | Butir **TIDAK BOLEH** tampil pada beranda maupun detail tanpa putusan kurator yang menyetujuinya; rute pengguna **HARUS** membaca dari penyimpanan butir tayang saja, bukan dari antrean (C-06) |
| R-03 | Kredensial layanan yang menayangkan butir **TIDAK BOLEH** dapat menulis butir tayang maupun membaca antrean; penolakannya **HARUS** datang dari peladen basis data, bukan dari kode (C-03, ADR-06) |
| R-04 | **JIKA** regulasi sumber butir tidak berstatus berlaku pada saat putusan, **MAKA** persetujuan **HARUS** ditolak dengan menyebut TL-04 (C-07, lapis kedua fitur 010) |
| R-05 | Beranda **HARUS** disaring terhadap prioritas manajerial pengguna dan **TIDAK BOLEH** menayangkan lebih dari `PAGU_TAYANG_PER_PENGGUNA` butir baru per hari (FR-G01, FR-G05) |
| R-06 | **JIKA** butir berlisensi tertutup, **MAKA** layar dan tanggapan **TIDAK BOLEH** menawarkan teks penuh maupun unduhan (FR-G08, C-02) |
| R-07 | **KETIKA** pengguna menyatakan "belum relevan", sistem **HARUS** mencatat alasannya tanpa data pribadi, dan butir itu **TIDAK BOLEH** tampil lagi baginya (FR-G07, KM-03) |
| R-08 | Penyaringan beranda **TIDAK BOLEH** bergantung pada riwayat baca, buka, atau tolak pengguna lain maupun dirinya sendiri, selain mengecualikan butir yang ia tolak (C-14) |
| R-09 | Rute kurasi **HARUS** hanya terbuka bagi peran `kurator`; rute penemuan hanya bagi `pengguna` (D-14 Bagian 3, AG-02) |
| R-10 | Setiap putusan kurator **HARUS** tercatat pada jejak audit fitur 010 dengan pseudonim kurator, bukan nama akunnya (FR-I05, C-05) |
| R-11 | S-05 dan S-06 **HARUS** menangani ketujuh keadaan D-05 Bagian 7; S-15 dan S-16 sekurangnya KL-A, KL-B, KL-D |
| R-12 | Seluruh kalimat layar baru **HARUS** lolos pemeriksa C-13 |
| R-13 | Sistem **TIDAK BOLEH** membuat tabel, bidang, atau tampilan poin, lencana, runtun, maupun papan peringkat (C-15) |

## Pertanyaan terbuka

Tiap pertanyaan disertai anjuran; anjuran bukan putusan.

**P-1 · Irisan 013 dan pemecahan sisanya.**

| Pilihan | Arti |
|---|---|
| A | 013 = **S-15, S-16, S-05, S-06** beserta penyimpanan antrean dan butir tayang. Sisanya menjadi empat baris baru sesudah 013: **penerapan J4** (S-07, S-08, S-12, S-13), **koleksi dan pembaca sumber** (S-10, S-11), **pengaturan dan penarikan data** (S-14, NFR-09), **aduan dan analitik** (S-17, S-18) |
| B | 013 = sisi pengguna J3 + J4 (S-05 s.d. S-08, S-12) lebih dulu; butir dimuat lewat perkakas baris perintah tim |
| C | 013 dibiarkan memuat kelima belas layar |

**Anjuran: A.** Hanya A yang membuat beranda berisi lewat jalur sah, dan hanya
A yang membuktikan C-06 dari ujung ke ujung lewat HTTP. B menjadikan C-06
bergantung pada siapa yang menjalankan perkakas; C mengulang pola KB-032.

**P-2 · Penyimpanan antrean dan butir tayang.** Belum ada satu pun tabel.
**Anjuran:** skema `kurasi` tersendiri dengan dua peran basis data — peran
kurasi menulis putusan dan butir tayang, peran penayangan hanya membaca butir
tayang. Antrean memuat kandidat **yang sudah lolos penyaringan L1–L3**, bukan
dokumen karantina; kedua peran tidak menjangkau area karantina (C-03).
Pengisian antrean lewat perkakas tim di luar layanan aplikasi, sama dengan
pembuatan akun pada fitur 029.

**P-3 · Kalimat "mengapa relevan" (`alasan_relevansi`).** D-06 Bagian 5
mencontohkan kalimat yang menyebut keadaan sekolah tertentu ("akreditasi
berikutnya jatuh pada semester ini"), tetapi `ButirPengetahuan` menyimpan
**satu kalimat per butir** yang ditulis kurator. Kalimat per pengguna menuntut
penyusunan otomatis pada jalur feed — pemanggilan model baru dan wilayah
personalisasi (C-14).

| Pilihan | Arti |
|---|---|
| A | Satu kalimat per butir, ditulis kurator terhadap **kategori prioritas** ("Sekolah Anda menetapkan supervisi akademik sebagai prioritas…"); tampil apa adanya |
| B | Kalimat disusun per pengguna dari profilnya |

**Anjuran: A.** Feed hanya menayangkan butir dalam prioritas pengguna, sehingga
kalimat berbasis kategori tetap benar bagi setiap pembacanya. B diajukan
sebagai fitur tersendiri bila tim menghendakinya.

**P-4 · Batas "hari" bagi pagu tayang.** Waktu disimpan UTC, tetapi "butir
hari ini" berganti pada tengah malam waktu pengguna. **Anjuran:** batas hari
dihitung pada WIB (Asia/Jakarta) — **penetapan tim, tanpa dasar literatur** —
dan diganti bila lokus pilot berada di zona lain.

**P-5 · Penarikan butir yang sudah tayang (FR-I06).** Logikanya sudah ada
pada fitur 010, rutenya belum. **Anjuran:** dibangun di sini bila P-1 = A —
butir tayang tanpa jalan menariknya membuat regulasi yang dicabut sesudah
penayangan tetap tampil sampai seseorang menyunting basis data dengan tangan.

**P-6 · Telemetri penemuan.** Rasio penemuan (D-01 Bagian 9.1) dihitung dari
peristiwa buka butir, tetapi gerbang perekaman fitur 012 belum memiliki
penyimpanan. **Anjuran:** di luar cakupan, diajukan sebagai baris tersendiri
sebelum pilot. Mencatatnya di sini menambah penyimpanan ketiga pada satu fitur.

**P-7 · Simpanan luring S-05 dan S-06 (D-05 Bagian 8).** **Anjuran:** termasuk,
memakai penyimpanan peramban yang sudah dipakai S-09 fitur 027, tanpa
ketergantungan baru. Butir terkurasi bukan data pribadi, sehingga menyimpannya
pada peramban tidak menyentuh KM-03.

## Temuan yang diajukan bersama usulan ini

**TK-71 · Wireframe S-08 dan S-12 pada D-05 tertinggal dari TK-51.** S-08
masih "isian tunggal — teks bebas, tanpa batas minimum"; S-12 menulis alasan
"tidak jadi" sebagai opsional. Fitur 011 membangun yang sebaliknya, sesuai
KB-059. Tidak menyentuh irisan anjuran P-1 A, tetapi wajib diputus sebelum
baris penerapan J4 dibuka — D-05 tidak diubah agen tanpa putusan itu.

## Putusan Gerbang 1 (KB-178)

Pemegang Gerbang 1–4 menjawab **"setuju dan lanjutkan"** atas laporan yang
menyebut penyempitan baris, baris baru, dan anjuran tiap pertanyaan. Seluruh
anjuran berlaku:

| Pertanyaan | Putusan |
|---|---|
| P-1 | **A** — 013 = S-15, S-16, S-05, S-06. Empat baris baru sesudah 013: penerapan J4, koleksi dan pembaca sumber, pengaturan dan penarikan data, aduan dan analitik |
| P-2 | Skema `kurasi` tersendiri; peran kurasi menulis, peran penayangan hanya membaca butir tayang; keduanya tanpa jangkauan karantina; antrean diisi perkakas tim |
| P-3 | **A** — satu kalimat per butir, ditulis kurator terhadap kategori prioritas; tidak disusun per pengguna |
| P-4 | Batas hari pagu tayang pada WIB (Asia/Jakarta) — penetapan tim, tanpa dasar literatur |
| P-5 | Penarikan butir tayang (`POST /api/v1/kurasi/{id}/tarik`, FR-I06) **masuk cakupan** — butir "Di luar cakupan" yang menyebutnya gugur oleh putusan ini |
| P-6 | Telemetri penemuan di luar cakupan; menjadi baris tersendiri sebelum pilot |
| P-7 | Simpanan luring S-05 dan S-06 termasuk, memakai penyimpanan peramban fitur 027 |

TK-71 tetap terbuka dan diputus sebelum baris penerapan J4 dibuka.

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | D-14 Bagian 3.3 dan 3.4; C-20 |
| R-02 | C-06; FR-I03; `ButirTayang` fitur 010 |
| R-03 | C-03; ADR-06 |
| R-04 | C-07; FR-I02; D-06 Bagian 7.4 TL-04 |
| R-05 | FR-G01; FR-G05; R-01, R-05, R-06 fitur 011 |
| R-06 | FR-G08; C-02 |
| R-07 | FR-G07; KM-03 |
| R-08 | C-14; D-01 Bagian 4.2 |
| R-09 | D-14 Bagian 3; AG-02 |
| R-10 | FR-I05; C-05 |
| R-11 | D-05 Bagian 7 |
| R-12 | C-13; NFR-19 |
| R-13 | C-15 |

## Kriteria penerimaan

- [x] Penyempitan 013 dan baris baru disetujui; P-1 s.d. P-7 diputus pada Gerbang 1
- [ ] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [ ] R-02 dan R-03 diuji terhadap peladen PostgreSQL dengan sebab penolakannya
- [ ] Uji mutasi disusun pada `plan.md` dan dilaporkan apa adanya
- [ ] Bukti ujung ke ujung: butir yang belum diputus tidak tampil; sesudah disetujui kurator, tampil pada beranda pengguna berprioritas sesuai
- [ ] `make check` lulus enam gerbang
