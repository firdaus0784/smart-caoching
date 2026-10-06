# Spec: 033-pengaturan-dan-penarikan-data

| | |
|---|---|
| Kebutuhan | FR-A06, NFR-09, RE-04; KM-02; C-04, C-05, C-13, C-17, C-20 |
| Dokumen terkait | D-01 Bagian 7 dan 8 · D-05 S-14 · D-14 Bagian 3.1, 4.5, 5.1 dan KM-02 · D-04 KA-03, KA-06 · spec fitur 029, 030, 034 |
| Status | **Gerbang 4 lolos** — 6 Oktober 2026 (KB-213). Tujuh dari tujuh tugas selesai |

## Mengapa fitur ini diusulkan sekarang

Sejak fitur 034, data perilaku sungguhan tersimpan: peristiwa telemetri,
riwayat pertanyaan, butir yang tampil dan ditolak, profil sekolah. NFR-09
menjanjikan **hak menarik data, dipenuhi ≤ 14 hari**, dan D-14 sudah
menyebut jalurnya — `DELETE /api/v1/saya/data` — tetapi tidak ada yang
membangunnya. Tabel-tabel itu **tambah-saja, ditegakkan peladen**: tidak satu
peran aplikasi pun dapat menghapus apa pun. Tanpa fitur ini, janji pada naskah
persetujuan tidak dapat ditepati sama sekali, bukan sekadar lambat.

Pilot tidak boleh dimulai sebelum janji itu dapat ditepati. Baris 031 masih
tertahan TK-71; 032 dan 035 tidak menyangkut hak peserta.

Bersamanya dibangun S-14 Pengaturan: memperbarui profil dan prioritas
(FR-A06) — yang hari ini hanya dapat diisi sekali, saat aktivasi — serta
melihat dan mengubah persetujuan dari satu tempat.

## Data milik seorang pengguna hari ini

Dipetakan dari katalog basis data, bukan dari dokumen:

| Tempat | Pemilik dicatat sebagai | Sifat |
|---|---|---|
| `akun.pengguna`, `akun.sesi` | `id`, `pseudonim` | Akun dan sesi |
| `pengguna.profil_sekolah` | pseudonim | Dapat ditimpa |
| `pengguna.prioritas_manajerial`, `pengguna.persetujuan` | pseudonim | Tambah-saja |
| `riwayat.percakapan`, `riwayat.giliran` | pseudonim | Tambah-saja; memuat teks pertanyaan |
| `penemuan.tayang_harian`, `penemuan.belum_relevan` | pseudonim | Tambah-saja; memuat teks alasan |
| `telemetri.peristiwa` | pseudonim | Tambah-saja |
| `pseudonim.peta_pseudonim` (basis data terpisah) | `id_pengguna` ↔ `pseudonim` | Kunci pemetaan, tidak terjangkau aplikasi (C-05) |
| Log operasional | `id_akun` hanya pada penahanan akun | Di luar basis data |

## Di luar cakupan

- Notifikasi — belum ada kanal (BT-21); S-14 tidak menampilkan pengaturan
  yang tidak mengatur apa pun
- Pernyataan status keberlanjutan (BT-22) — menunggu BT-07
- Masa simpan terjadwal (KA-06) — menunggu kebijakan privasi ET-05
- Penarikan oleh tim atas permintaan di luar aplikasi — jalurnya sama
  (perkakas), tetapi prosedurnya milik dokumen etik
- Ekspor data milik pengguna — tidak diminta D-01
- Data kurator pada jejak kurasi — milik peran kerja, bukan peserta

## Kebutuhan (EARS) yang tidak bergantung pada pertanyaan

| ID | Kebutuhan |
|---|---|
| R-01 | **KETIKA** pengguna meminta penarikan, sistem **HARUS** menghentikan perekaman telemetri baginya pada permintaan berikutnya, sebelum penghapusan apa pun berjalan (C-04) |
| R-02 | Penghapusan **HARUS** keras — baris dihapus, bukan ditandai (KM-02) — dan **HARUS** mencakup setiap tempat pada tabel di atas yang termasuk cakupan P-2 |
| R-03 | Setiap permintaan **HARUS** tercatat dengan waktu diminta dan waktu dipenuhi, agar ≤ 14 hari NFR-09 dapat ditagih |
| R-04 | Peran yang menghapus **TIDAK BOLEH** dipegang jalur penjawaban (C-17) maupun peran aplikasi yang sudah ada; tambah-saja tabel lain tetap ditegakkan peladen |
| R-05 | Permintaan penarikan **TIDAK BOLEH** dapat dibatalkan diam-diam oleh sistem, dan **HARUS** dapat diminta dari S-14 tanpa menghubungi siapa pun (RE-04) |
| R-06 | Konfirmasi **HARUS** menyebut apa yang dihapus dan apa yang tidak, dengan dua pilihan setara bentuknya — tanpa rasa bersalah maupun rasa kehilangan sebagai pendorong (D-05 Bagian 10, RE-04) |
| R-07 | **KETIKA** pengguna memperbarui profil atau prioritas dari S-14, aturan dan penyimpanannya **HARUS** sama dengan aktivasi (fitur 030) — satu jalur validasi |
| R-08 | Bentuk permintaan dan tanggapan `DELETE /saya/data` **HARUS** ditulis ke D-14 Bagian 4.5 sebelum kodenya (C-20) |
| R-09 | Log operasional **TIDAK BOLEH** mencatat pseudonim maupun isi data yang dihapus; yang dicatat hanya jumlah baris per tabel |

## Pertanyaan terbuka

Tiap pertanyaan disertai anjuran; anjuran bukan putusan.

**P-1 · Siapa yang menghapus.**

| Pilihan | Arti |
|---|---|
| A | Rute menghapus seketika lewat peran penghapus yang **terjangkau aplikasi**. Cepat, tetapi celah pada aplikasi kini dapat menghapus data penelitian siapa pun — sifat tambah-saja yang dijaga empat fitur runtuh pada satu kredensial |
| B | Rute **mencatat permintaan** dan seketika mencabut persetujuan serta sesi. Penghapusan keras dijalankan tim lewat perkakas (`python -m perkakas.penarikan`) dengan kredensial `peran_penarikan` yang **tidak ada pada layanan aplikasi** — pola yang sama dengan `peran_pengelola_akun` fitur 029. Tagihan ≤ 14 hari terbaca dari tabel permintaan |
| C | B, ditambah perkakas dijalankan otomatis terjadwal — menuntut penjadwal yang belum ada (antrean tugas, D-04) |

**Anjuran: B.** NFR-09 memberi 14 hari justru agar penghapusan dapat
diperiksa manusia; R-01 tetap seketika karena pencabutan persetujuan sudah
berjalan pada hak yang ada.

**P-2 · Cakupan penghapusan.**

| Pilihan | Arti |
|---|---|
| A | Data penelitian saja — `telemetri.peristiwa`. Riwayat, profil, dan penemuan tetap; akun tetap aktif |
| B | **Seluruh data milik pengguna** pada tabel di atas, termasuk riwayat dan teks alasan; akun dinonaktifkan dan barisnya dihapus, pemetaan pseudonim dihapus pada basis data pseudonim. Yang tersisa hanya baris permintaan tanpa pseudonim: nomor, waktu diminta, waktu dipenuhi, jumlah baris per tabel |
| C | B, tetapi akun tetap dan dapat dipakai lagi dengan data kosong |

**Anjuran: B.** Riwayat dan alasan memuat teks tulisan peserta — bagian
paling pribadi dari data itu. Layanan ini ada untuk penelitian; peserta yang
menarik datanya keluar dari penelitian, dan C membuka pertanyaan apakah
data barunya ikut penelitian.

**P-3 · Catatan persetujuan.** Catatan persetujuan adalah bukti bahwa data
dikumpulkan dengan izin. Menghapusnya membuat data yang **sudah dianalisis
sebelum penarikan** tidak dapat dipertanggungjawabkan; menyimpannya
menyisakan jejak bahwa orang ini pernah ikut.

**Anjuran: putusan tim etik** — agen tidak memilih. Sampai diputus, catatan
persetujuan **dihapus bersama** pada pilihan P-2 B dan baris permintaan
tanpa pseudonim menjadi buktinya; perubahan ke arah menyimpan lebih mudah
daripada sebaliknya.

**P-4 · Kalimat penjelasan penarikan.** Kalimat yang menyebut apa yang
dihapus dan akibatnya adalah bagian janji kepada peserta, sejajar dengan
naskah persetujuan ET-02 yang tidak ditulis agen (KB-164).

| Pilihan | Arti |
|---|---|
| A | Agen menulis mikrokopi S-14 seluruhnya, diperiksa C-13 |
| B | **Agen menulis mikrokopi pengaturan; kalimat penjelasan penarikan dibaca dari berkas naskah milik tim** — pola fitur 030; tanpa berkas, tombol penarikan tetap ada dan menampilkan daftar data yang dihapus, dibangkitkan dari tabel di atas |

**Anjuran: B.**

**P-5 · Letak S-14.** Tombol "Pengaturan" pada navigasi Beranda · Tanya
menjadikannya tiga, atau satu tombol di samping "Keluar". **Anjuran:** di
samping "Keluar" — navigasi utama tetap dua, sesuai D-05 Bagian 4.

## Putusan Gerbang 1 (KB-204)

Pemegang Gerbang 1–4 memilih anjuran pada setiap pertanyaan:

| Pertanyaan | Putusan |
|---|---|
| P-1 | **B** — rute mencatat permintaan dan seketika mencabut sesi; penghapusan keras oleh perkakas tim dengan `peran_penarikan` yang tidak ada pada layanan aplikasi |
| P-2 | **B** — seluruh data milik pengguna, akun, dan pemetaan pseudonim; tersisa baris permintaan tanpa pseudonim |
| P-3 | Catatan persetujuan **dihapus bersama** sampai tim etik memutus lain (TK-75) |
| P-4 | **B** — kalimat penjelasan penarikan dibaca dari berkas naskah milik tim; agen menulis mikrokopi pengaturan |
| P-5 | Tombol Pengaturan di samping Keluar; navigasi utama tetap dua |

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | C-04; FR-J05 |
| R-02 | KM-02; NFR-09 |
| R-03 | NFR-09 |
| R-04 | C-17; R-05 fitur 034; ADR-06 |
| R-05, R-06 | RE-04; D-05 Bagian 10 |
| R-07 | FR-A06; fitur 030 |
| R-08 | C-20; AG-02 |
| R-09 | C-05; KM-03 |

## Kriteria penerimaan

- [x] P-1 s.d. P-5 diputus pada Gerbang 1
- [ ] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [ ] Penghapusan diuji terhadap peladen PostgreSQL: setiap tabel dalam cakupan kosong dari pemilik itu, tabel lain dan pemilik lain utuh
- [ ] `peran_penarikan` tidak terjangkau layanan aplikasi — diuji
- [ ] `make check` lulus enam gerbang
