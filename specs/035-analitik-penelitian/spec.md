# Spec: 035-analitik-penelitian

| | |
|---|---|
| Kebutuhan | FR-J03, FR-J04; D-01 Bagian 9.1; C-04, C-05, C-09, C-12, C-14, C-17, C-20 |
| Dokumen terkait | D-01 Bagian 9 dan 9.1 · D-04 ADR-07, peran Peneliti · D-05 S-18 · D-14 Bagian 3.4 dan 5.1 · spec fitur 012, 034, 033 |
| Status | **Gerbang 4 lolos** — 8 Oktober 2026 (KB-224). Tujuh dari tujuh tugas selesai |

## Mengapa fitur ini diusulkan sekarang

Sejak fitur 034 peristiwa penelitian tersimpan, dan sejak fitur 033 peserta
dapat menarik datanya. Yang belum ada adalah cara **tim membacanya**: tidak ada
rute analitik, tidak ada peran basis data peneliti, dan ekspor CSV fitur 012
(`src/telemetri/ekspor.py`) tidak dipanggil siapa pun. Tanpa fitur ini, data
pilot hanya dapat dibaca pengelola basis data dengan kueri tangan — jalan yang
tidak tercatat dan tidak dijaga hak per peran.

## Temuan yang diajukan bersama usulan ini

**TK-77 · Penilaian jawaban (FR-F07) tidak dimiliki baris mana pun.** D-14
Bagian 3.2 memuat `POST /api/v1/pesan/{id}/penilaian`, tetapi tidak satu baris
D-12 pun menyebut FR-F07. Aduan kurator (S-17, FR-I04) menindaklanjuti jawaban
yang **ditandai keliru** — tanpa rute penilaian, antrean aduan selalu kosong.
Rantainya tertulis: spec fitur 009 menyerahkannya ke fitur 010, spec 010 ke
fitur 021, dan spec 023 menundanya tanpa menyebut pemilik. Bentuknya sama
dengan TK-56 dan fitur 029: pekerjaan yang setiap baris anggap milik baris lain.

## Di luar cakupan

- Aduan kurator (S-17, FR-I04) — tertahan TK-77 (P-1)
- Ekspor Parquet — `pyarrow` belum disetujui (C-12); separuh CSV dibangun,
  separuh Parquet tetap dinyatakan tertahan seperti pada fitur 012
- Metrik yang peristiwanya belum terekam: rasio penuntasan, penelusuran sumber
  (TK-73), verifikasi dan komitmen (baris 031), akurasi QA berdasarkan umpan
  balik (TK-77) — **ditampilkan sebagai "belum terukur" beserta sebabnya**,
  tidak diisi nol
- Analitik lintas siklus 2028 dan pembandingnya
- Pemetaan pseudonim ke identitas (FR-J06) — milik ketua peneliti, di luar
  sistem

## Kebutuhan (EARS) yang tidak bergantung pada pertanyaan

| ID | Kebutuhan |
|---|---|
| R-01 | Rute analitik **HARUS** hanya terbuka bagi peran `peneliti`; peran lain 403 (D-14 Bagian 3.4) |
| R-02 | Peran basis data analitik **HARUS** hanya membaca `telemetri.peristiwa`; **TIDAK BOLEH** menjangkau akun, profil, riwayat, maupun basis data pseudonim — pemegang ekspor tidak dapat menautkan pseudonim ke akun (C-05) |
| R-03 | Metrik **HARUS** dihitung dari peristiwa saat diminta, bukan disimpan sebagai angka turunan (spec fitur 034, "di luar cakupan") |
| R-04 | Metrik yang peristiwanya belum terekam **HARUS** dinyatakan belum terukur beserta sebabnya; **TIDAK BOLEH** tampil sebagai nol |
| R-05 | Peristiwa bertanda `versi_aplikasi = pengembangan` **TIDAK BOLEH** tercampur dengan data pilot pada metrik maupun ekspor tanpa dinyatakan (integritas S-18) |
| R-06 | Ekspor **HARUS** berupa CSV fitur 012 — kolom diturunkan dari model `Peristiwa`, tanpa `id_pengguna` |
| R-07 | Pemilihan beranda dan jawaban **TIDAK BOLEH** membaca hasil analitik (C-14); analitik tidak menulis apa pun (C-17) |
| R-08 | Bentuk tanggapan kedua rute **HARUS** ditulis ke D-14 sebelum kodenya (C-20) |

## Pertanyaan terbuka

Tiap pertanyaan disertai anjuran; anjuran bukan putusan.

**P-1 · Cakupan baris 035.**

| Pilihan | Arti |
|---|---|
| A | 035 utuh — analitik dan aduan; aduan dibangun tanpa sumber dan antreannya selalu kosong |
| B | **035 analitik saja.** Aduan dan penilaian FR-F07 menjadi **baris D-12 baru 036** (penilaian jawaban dan aduan kurator) — penyisipan baris menuntut putusan Anda |
| C | 035 analitik saja; aduan tetap pada 035 sebagai sisa, menunggu TK-77 |

**Anjuran: B.** Pola C sudah lima kali dipecah karena baris "berjalan"
berbulan-bulan (KB-032).

**P-2 · Isi ringkasan S-18.**

| Bagian | Isi yang dianjurkan |
|---|---|
| Keterlibatan | Pengguna aktif harian dan mingguan (pseudonim berbeda yang berperistiwa), retensi D1/D7/D30, panjang sesi dari `session_end` |
| Penemuan | Rasio penemuan `discovery_opened` / `discovery_served` |
| Belum terukur | Lima metrik di atas, masing-masing dengan sebabnya |
| Integritas | Jumlah peristiwa per kode, per versi aplikasi, per versi model; rentang waktu; peristiwa `pengembangan` dipisah |

**Retensi** perlu definisi yang dapat ditagih. **Anjuran:** pengguna dihitung
pada kohort hari pertamanya berperistiwa (tanggal WIB); "kembali pada hari ke-N"
berarti berperistiwa **pada tanggal kohort + N**, bukan "pada atau sesudahnya".
Kohort yang belum berumur N hari dikeluarkan dari penyebut, bukan dihitung
tidak kembali.

**P-3 · Bentuk ekspor.** **Anjuran:** `POST /analitik/ekspor` dengan
`{"dari": "YYYY-MM-DD", "sampai": "YYYY-MM-DD"}` (tanggal WIB, inklusif),
menjawab berkas CSV untuk diunduh; peristiwa `pengembangan` dikeluarkan kecuali
diminta tegas. Parquet tetap tertahan C-12.

**P-4 · Ekspor dan penarikan data.** Berkas ekspor berpindah ke luar sistem;
peserta yang kemudian menarik datanya tetap ada di berkas itu, dan NFR-09 tidak
dapat ditepati bagi salinan yang tidak diketahui.

| Pilihan | Arti |
|---|---|
| A | Tanpa catatan — tanggung jawab tim sepenuhnya |
| B | **Setiap ekspor tercatat** — nomor, waktu, rentang, jumlah baris, pseudonim akun peneliti (bukan isinya). `perkakas.penarikan daftar` menyebut nomor ekspor yang rentangnya memuat peristiwa permintaan tertunda, agar tim tahu berkas mana yang harus dibersihkan |
| C | B, ditambah ekspor ditolak selama ada permintaan penarikan tertunda |

**Anjuran: B**; prosedur membersihkan berkas di luar sistem tetap milik tim
etik, sejajar TK-76.

**P-5 · Layar.** Peneliti dikenali dengan cara kurator dikenali (K-8 fitur
013): 403 pada ringkasan akun dan pada antrean kurasi, lalu `GET
/analitik/ringkas`. **Anjuran:** S-18 satu halaman tanpa navigasi pengguna,
dengan tombol unduh CSV per rentang tanggal; angka ditampilkan sebagai tabel,
bukan grafik — tanpa pustaka grafik baru (C-12).

## Putusan Gerbang 1 (KB-215)

Pemegang Gerbang 1–4 memilih anjuran pada setiap pertanyaan:

| Pertanyaan | Putusan |
|---|---|
| P-1 | **B** — 035 analitik saja; baris D-12 **036** "Penilaian jawaban dan aduan kurator" disisipkan (D-12 0.38) |
| P-2 | Isi ringkasan sesuai anjuran; retensi berkohort tanggal WIB, kembali **tepat** pada hari ke-N, kohort yang belum berumur N dikeluarkan dari penyebut |
| P-3 | Ekspor CSV `{"dari", "sampai"}` tanggal WIB inklusif; peristiwa `pengembangan` dikeluarkan kecuali diminta; Parquet tetap tertahan C-12 |
| P-4 | **B** — setiap ekspor tercatat; `perkakas.penarikan daftar` menyebut ekspor yang rentangnya memuat peristiwa permintaan tertunda |
| P-5 | S-18 satu halaman tabel, tanpa pustaka grafik baru; peneliti dikenali seperti kurator |

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | D-14 Bagian 3.4; D-04 peran Peneliti |
| R-02 | C-05; KA-03; D-14 `pengguna.pseudonim` |
| R-03 | Spec fitur 034 |
| R-04 | D-01 Bagian 9.1; pola `parquet_tertahan` fitur 012 |
| R-05 | D-05 S-18 "integritas telemetri"; K-4 fitur 034 |
| R-06 | FR-J03; fitur 012 |
| R-07 | C-14; C-17 |
| R-08 | C-20 |

## Kriteria penerimaan

- [x] P-1 s.d. P-5 diputus pada Gerbang 1
- [ ] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [ ] Peran analitik diuji terhadap peladen: membaca peristiwa, ditolak di tempat lain
- [ ] Retensi diuji dengan kohort buatan yang jawabannya dihitung tangan
- [ ] `make check` lulus enam gerbang
