# Spec: 030-aktivasi-persetujuan-dan-profil

| | |
|---|---|
| Kebutuhan | FR-A02, FR-A03, FR-A04, FR-A05, FR-A06; NFR-19; C-04, C-05, C-13, C-14, C-20; TK-50 |
| Dokumen terkait | D-05 Bagian 4.1 dan 5.1 (S-02, S-03, S-04, alur J1) · D-14 Bagian 3.1 · D-01 Bagian 13 (ET-01, ET-02) · D-12 Bagian 7 |
| Status | **Gerbang 4 lolos** — 5 Oktober 2026 (KB-176). Enam dari enam tugas selesai |

## Mengapa fitur ini diusulkan, dan mengapa bukan 013 utuh

Fitur 029 membuka pintu masuk. D-05 Bagian 5.1 menetapkan apa yang terjadi
sesudahnya:

```
S-01 Masuk → S-02 Persetujuan → S-03 Pengenalan → S-04 Profil → S-09 Tanya
```

Hari ini pengguna yang masuk langsung mendarat di S-09. Tiga akibatnya:

- **C-04 tidak dapat dipenuhi di lapangan.** Gerbang perekaman telemetri
  (fitur 012) membaca `KeadaanPersetujuan`, tetapi tidak ada layar maupun rute
  yang mengambil persetujuan itu. Telemetri karena itu tidak dapat dinyalakan
  bagi siapa pun tanpa melanggar C-04.
- **Prioritas manajerial tidak pernah terisi**, sehingga feed fitur 011
  (FR-G01) menyaring terhadap himpunan kosong.
- Model profil, prioritas, dan persetujuan fitur 022 **tidak memiliki
  penyimpanan maupun rute** — sisi belakangnya baru berupa model.

Baris 013 pada D-12 berbunyi "Penyempurnaan antarmuka dan keadaan layar" dan
mencakup enam belas layar tersisa. Sebagian besar tertahan hal yang berbeda:
S-05 s.d. S-08 dan S-11 s.d. S-13 menunggu korpus butir yang terkurasi, S-15
s.d. S-18 menunggu peran internal, dan S-10 menunggu pembaca dokumen.
Menggarapnya sebagai satu fitur mengulang pola yang sudah lima kali dipecah
(KB-032): fitur yang separuhnya menunggu tercatat "berjalan" berbulan-bulan.

Diusulkan: **baris 030 disisipkan sebelum 013**, memuat alur aktivasi J1
saja; 013 dipersempit menjadi layar sisanya. Penyisipan dan penyempitan baris
adalah keputusan tim; barisnya tidak ditulis sebelum disetujui.

## Di luar cakupan

- S-05 s.d. S-08 dan S-10 s.d. S-18 — tetap pada 013
- Pengubahan profil sesudah aktivasi (FR-A06, layar S-14) — rutenya dibangun di
  sini, layarnya tidak; lihat P-6
- Pencabutan persetujuan dan penarikan data (`DELETE /api/v1/saya/data`,
  NFR-09) — menuntut peran basis data tersendiri yang dapat menghapus, dan itu
  keputusan tersendiri
- `src/rag/` dan `src/llm/` — tidak disentuh

## Kebutuhan (EARS) yang tidak bergantung pada pertanyaan

| ID | Kebutuhan |
|---|---|
| R-01 | Bentuk permintaan dan tanggapan `GET`/`PUT /api/v1/saya/profil`, `PUT /api/v1/saya/prioritas`, dan `POST /api/v1/saya/persetujuan` **HARUS** ditulis ke D-14 Bagian 4 **sebelum** kodenya (C-20) |
| R-02 | Profil, prioritas, dan persetujuan **HARUS** dimiliki pseudonim akun dari sesi sah, bukan nama akun maupun identitas langsung (C-05, KB-162 butir 3) |
| R-03 | **KETIKA** pengguna menolak persetujuan penelitian, fitur inti — Tanya, riwayat, profil — **HARUS** tetap dapat dipakai, dan telemetri **TIDAK BOLEH** merekam apa pun baginya (FR-A05, C-04) |
| R-04 | Setiap catatan persetujuan **HARUS** menyebut versi naskah yang ditampilkan kepadanya; persetujuan tanpa versi naskah ditolak |
| R-05 | Profil awal **TIDAK BOLEH** meminta lebih dari enam isian; prioritas **HARUS** berjumlah tiga sampai lima (FR-A02, FR-A03) |
| R-06 | Pengenalan **TIDAK BOLEH** melebihi empat layar, dan **HARUS** memuat pernyataan bahwa sistem adalah alat bantu, bukan penentu keputusan (FR-A04) |
| R-07 | Alur aktivasi **HARUS** tampil hanya bagi pengguna yang belum menyelesaikannya, dan **HARUS** berakhir di S-09, bukan di beranda (D-05 Bagian 5.1) |
| R-08 | Bidang teks bebas profil **HARUS** melewati pendeteksi data pribadi FR-B04 (KM-03) |
| R-09 | Seluruh kalimat layar baru **HARUS** lolos pemeriksa C-13 |
| R-10 | Profil dan prioritas **TIDAK BOLEH** dipakai untuk memengaruhi jawaban Tanya (C-14) — penyaringannya milik feed, bukan jalur penjawaban |

## Pertanyaan terbuka

Tiap pertanyaan disertai anjuran; anjuran bukan putusan.

**P-1 · Naskah persetujuan S-02 (ET-02).** Isi lembar informasi dan formulir
persetujuan adalah kewajiban ketua peneliti (ET-02) dan bergantung pada
*ethical clearance* (ET-01). Agen tidak boleh mengarangnya: persetujuan atas
naskah karangan bukan persetujuan.

| Pilihan | Arti |
|---|---|
| A | S-02 dibangun dengan naskah dibaca dari **berkas berversi yang diisi tim** (misalnya `web/public/naskah/persetujuan-v1.md`). Selama berkas itu belum ada, S-02 menyatakan naskah belum tersedia, persetujuan tidak dapat diberikan, dan telemetri tetap mati — C-04 terjaga dengan sendirinya |
| B | S-02 ditunda sampai naskah ET-02 tersedia; aktivasi dimulai dari S-03 |

**Anjuran: A.** Layarnya dapat dibangun dan diuji tanpa menunggu, dan yang
menunggu hanya satu berkas — bukan satu fitur.

**P-2 · Isi empat layar pengenalan S-03.** D-05 tidak memuat kalimatnya.
**Anjuran:** agen menyusun draf dari FR-A04, D-05 Bagian 2, dan AI-04, lalu
**draf itu diputus pada Gerbang 2** bersama rencananya — pernyataan tentang
batas sistem adalah janji kepada kepala sekolah, bukan mikrokopi biasa.

**P-3 · TK-50: `akreditasi` atau `jalur_akreditasi`.** FR-A02 meminta
"akreditasi"; D-04 menulis `profil_sekolah.akreditasi`; D-14 menulis
`profil_sekolah.jalur_akreditasi` bernilai `visitasi`/`automasi`. Keduanya
**bukan hal yang sama**: yang pertama lazimnya peringkat, yang kedua jalur
proses akreditasi. Kode fitur 022 mengikuti D-14.

| Pilihan | Arti |
|---|---|
| A | Ikuti D-14 (`jalur_akreditasi`) — sesuai AGENTS.md; D-04 diselaraskan |
| B | Tambah `peringkat_akreditasi` — isian ketujuh, melanggar batas enam FR-A02 kecuali isian lain dilepas |

**Anjuran: A**, kecuali tim memang membutuhkan peringkat — maka itu perubahan
FR-A02, bukan keputusan agen.

**P-4 · Kapan aktivasi dianggap selesai.** **Anjuran:** sesudah S-04
tersimpan. Persetujuan boleh ditolak (R-03), sehingga ia tidak dapat menjadi
syaratnya; pengenalan tidak meninggalkan data. Penanda "sudah aktif" dibaca
dari ada tidaknya profil, bukan bendera tersendiri.

**P-5 · Persetujuan ditolak, lalu berubah pikiran.** Tanpa S-14, pengguna
yang menolak tidak memiliki jalan kembali. **Anjuran:** S-02 menyediakan
tautan dari layar Tanya ("Pengaturan persetujuan") yang membuka S-02 lagi;
pencabutan sesudah setuju ikut ditangani di sana — `persetujuan.dicabut_pada`
sudah ada pada D-14 Bagian 5.1 dan menghentikan perekaman seketika (FR-J05).

**P-6 · FR-A06 — mengubah profil kapan saja.** **Anjuran:** rute `PUT`
dibangun di sini karena S-04 memakainya; layar pengubahannya tetap S-14 pada
013. Profil yang diubah lewat S-04 ulang tidak perlu layar baru.

**P-7 · Pemetaan fitur 022.** Model fitur 022 memakai `id_pengguna`.
**Anjuran:** nilainya diisi pseudonim akun (R-02), nama bidangnya tetap
mengikuti D-14; tidak ada perubahan enum maupun nama.

## Putusan Gerbang 1 (KB-165)

Pemegang Gerbang 1–4 menjawab **"setuju"** atas laporan yang menyebut baris
D-12 dan anjuran tiap pertanyaan. Seluruh anjuran berlaku:

| Pertanyaan | Putusan |
|---|---|
| P-1 | **A** — S-02 dibangun; naskah dibaca dari berkas berversi yang diisi tim; tanpa berkas itu persetujuan tidak dapat diberikan dan telemetri tetap mati |
| P-2 | Agen menyusun draf empat layar S-03; drafnya diputus pada Gerbang 2 |
| P-3 | **A** — ikuti D-14 (`jalur_akreditasi`); D-04 diselaraskan |
| P-4 | Aktivasi selesai sesudah S-04 tersimpan; dibaca dari ada tidaknya profil |
| P-5 | Tautan dari layar Tanya membuka S-02 lagi; pencabutan ditangani di sana |
| P-6 | Rute `PUT` dibangun di sini; layar S-14 tetap pada 013 |
| P-7 | `id_pengguna` fitur 022 diisi pseudonim akun; nama bidang tetap |

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | D-14 Bagian 3.1; C-20 |
| R-02 | C-05; KA-03; KB-162 |
| R-03 | FR-A05; C-04; FR-J05 |
| R-04 | ET-02; `CatatanPersetujuan.versi_naskah` fitur 022 |
| R-05 | FR-A02; FR-A03 |
| R-06 | FR-A04; AI-04 |
| R-07 | D-05 Bagian 5.1; titik kritis T1 |
| R-08 | FR-B04; KM-03 |
| R-09 | C-13; NFR-19 |
| R-10 | C-14 |

## Kriteria penerimaan

- [x] Baris D-12 030 dan penyempitan 013 disetujui; P-1 s.d. P-7 diputus pada Gerbang 1
- [ ] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [ ] Penolakan hak diuji terhadap peladen PostgreSQL dengan sebabnya
- [ ] Uji mutasi disusun pada `plan.md` dan dilaporkan apa adanya
- [ ] `make check` lulus enam gerbang
