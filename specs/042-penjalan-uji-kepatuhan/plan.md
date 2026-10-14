# Plan: 042-penjalan-uji-kepatuhan

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 14 Oktober 2026 (KB-313); P-1 s.d. P-6 sesuai anjuran |
| Perubahan atas fitur yang lolos Gerbang 4 | Tidak ada. Uji merakit aplikasi bersesinya sendiri dengan `susun_untuk_pengembangan`; `perkakas/jalankan_lokal.py` tidak disentuh |
| Status | **Menunggu Gerbang 4** — 14 Oktober 2026 (KB-320). Enam dari enam tugas selesai |
| Kebutuhan | R-01 s.d. R-07 `spec.md`; D-08 Bagian 8; D-13 Bagian 8; D-09 PS-01, PS-14; NFR-21, NFR-22; C-02 s.d. C-06, C-09, C-17, C-18, C-20 |

## 1. Letak dan batas

```
perkakas/kepatuhan/
  __init__.py
  __main__.py       python -m perkakas.kepatuhan jalankan --lingkungan … --id-percobaan …
  hasil.py          keadaan, hasil per UK, laporan, kode keluar, baris L1
  daftar.py         UK-01 s.d. UK-15; empat yang belum dapat diperiksa beserta sebabnya
  basis_data.py     UK-02, UK-04, UK-08, UK-09 — percobaan dalam transaksi yang dibatalkan
  proses.py         UK-10, UK-12, UK-13 — pemeriksa dan validator atas kode terpasang
  api.py            UK-05, UK-07, UK-14, UK-15 — API yang berjalan, akun uji
docs/                        D-08 Bagian 8; D-13 Bagian 8; D-09 Bagian 2.1, 4.1; D-10 Bagian 3; D-00
```

**Tidak disentuh:** `src/` seluruhnya, `web/`, `perkakas/basis_data/`, dan
`perkakas/jalankan_lokal.py`.
Tanpa rute, peran, hak, atau paket baru (R-07): `asyncpg` dan `httpx` sudah
ketergantungan langsung. Penjalan **tidak memegang hak sendiri**: ia
tersambung sebagai peran yang diujinya.

## 2. K-1 · Keadaan dan laporan (R-01, R-02, R-05)

`Keadaan` tiga nilai: `LULUS`, `GAGAL`, `BELUM`. Satu `HasilUK` per UK:
kode, keadaan, rincian berpengenal — peran, tabel, rute, kode SQLSTATE,
kode HTTP. Rincian tidak pernah memuat sandi, kuki, atau isi baris.

**Daftar UK dibaca uji dari D-08 Bagian 8 dan D-13 Bagian 8**, tidak disalin
dari ingatan. Laporan selalu memuat kelima belasnya, berurutan.

| Kode keluar | Arti |
|---|---|
| 0 | Lolos — kelima belas lulus |
| 1 | Sedikitnya satu gagal |
| 2 | Masukan tidak sah; tidak ada yang dijalankan |
| 4 | Tidak ada yang gagal, tetapi ada yang belum dapat diperiksa — **tidak lolos** |

Keadaan keseluruhan dihitung dari satu fungsi: lolos hanya bila kelima
belasnya `LULUS` (R-02).

## 3. K-2 · Pemeriksaan basis data (R-03, R-04, P-2 A)

Setiap percobaan: sambungan baru sebagai peran yang diuji, transaksi dibuka,
satu pernyataan dijalankan, **transaksi selalu dibatalkan** — juga bila
pernyataan berhasil. Pernyataan tulis memakai `WHERE false` atau nilai yang
tidak mungkin ada, sehingga peladen memeriksa hak tanpa menyentuh baris.

| UK | Peran | Percobaan | Lulus bila |
|---|---|---|---|
| UK-02 | `peran_penjawaban`, `peran_pemanggil_llm`, `peran_penyematan`, `peran_pengindeks` | `SELECT` atas `karantina.dokumen_sumber` dan `karantina.penerimaan` | 42501 |
| UK-04 | dua belas peran layanan aplikasi dan RAG (Bagian 3.1) | tersambung ke basis data pseudonim | 42501 |
| UK-08 | `peran_kurasi` | `INSERT` butir tayang tanpa putusan | 23503 — kunci asing menolak |
| UK-08 | `peran_penayangan` | `INSERT` butir tayang | 42501 |
| UK-09 | `peran_pemanggil_llm` | `INSERT`, `UPDATE … WHERE false`, `DELETE … WHERE false` atas korpus dan indeks utama; `SELECT` karantina; tersambung ke basis data pseudonim | 42501 |

Lulus **hanya** pada SQLSTATE yang tertulis. Pernyataan yang berhasil, galat
lain, dan sambungan yang gagal dicatat **gagal** dengan sebabnya (R-03).
UK-08 sengaja berbeda: kurator berhak menyisipkan butir tayang, sehingga yang
diuji adalah kunci asing yang menuntut putusan menyetujui.

### 3.1 Peran layanan aplikasi

Diambil dari perakitan aplikasi `perkakas/jalankan_lokal.py` dan tabel peran
`perkakas/basis_data/README.md`: `peran_autentikasi`, `peran_riwayat`,
`peran_pengguna`, `peran_kurasi`, `peran_penayangan`, `peran_telemetri`,
`peran_penilaian`, `peran_pembaca_sumber`, `peran_koleksi`,
`peran_analitik`, `peran_penjawaban`, `peran_pemanggil_llm`. Uji memastikan
setiap konstanta `PERAN_*` yang dipakai `perkakas/jalankan_lokal.py` ada di
daftar ini, sehingga peran baru pada aplikasi tidak luput dari UK-04.

### 3.2 Alamat dan kredensial

`PGHOST`, `PGPORT` bagi basis data perilaku; `PGHOST_PSEUDONIM`,
`PGPORT_PSEUDONIM` bila basis data pseudonim berada di peladen lain. Sandi
dibaca `asyncpg` dari `PGPASSFILE` sebagaimana libpq; penjalan **tidak**
menerima sandi lewat argumen maupun variabel buatannya sendiri.

## 4. K-3 · Pemeriksaan dalam proses (P-5 A)

| UK | Yang dijalankan | Lulus bila |
|---|---|---|
| UK-10 | Pemeriksa pemisahan instruksi `make check` atas kode yang terpasang | Nol temuan |
| UK-12 | VS-09 `periksa_penyimpangan` atas keluaran rekaan bertautan asing dan atas keluaran rekaan berinstruksi | Keduanya ditolak |
| UK-13 | VS-08 `periksa_peringkat_klaim` atas klaim rekaan yang bersandar tunggal pada segmen T3, lalu T4 | Keduanya ditolak |

Versi kode yang tercatat menyatakan apakah pohon kerja berubah (`+ubahan`,
fitur 040), sebab pemeriksaan ini membaca kode di tempat penjalan berjalan.

## 5. K-4 · Pemeriksaan API (P-3 A)

Masukan dari lingkungan: `KEPATUHAN_API` (alamat dasar), `KEPATUHAN_AKUN`
(id akun uji), `KEPATUHAN_KUKI` (nilai kuki sesi akun uji). Bila salah satu
tidak ada, keempat UK API **belum dapat diperiksa** dengan sebab itu.

**Kewarasan lebih dulu.** `GET /api/v1/saya/profil` dengan kuki wajib 200.
Bila tidak, keempat UK API **gagal** — tanpanya, alamat yang salah akan
menghasilkan 404 pada setiap rute dan terbaca "tidak terjangkau".

| UK | Percobaan | Lulus bila |
|---|---|---|
| UK-07 | Setiap rute D-14 Bagian 3 berperan selain `publik`, **tanpa** kuki | 401 bagi setiap rute |
| UK-15 | Setiap rute D-14 Bagian 3 berperan selain `publik`, `semua`, dan `pengguna`, **dengan** kuki akun uji | 403 bagi setiap rute |
| UK-14 | `POST /api/v1/tanya` dengan pertanyaan rekaan bernomor NIK rekaan | Ditolak, dan tanggapannya tidak memuat nomor itu |
| UK-05 | Persetujuan akun uji dibaca lebih dulu — bila aktif, UK-05 belum dapat diperiksa. Lalu `GET /api/v1/sumber/{id}` atas satu dokumen korpus; peristiwa berpseudonim akun uji dihitung sebagai `peran_analitik` | Nol peristiwa |

Daftar rute dibaca dari tabel D-14 Bagian 3 saat berjalan, sehingga rute baru
langsung diuji (D-14 AG-05). Parameter `{id}` diisi `uji-kepatuhan`; badan
permintaan kosong, sehingga rute yang lalai memeriksa peran berhenti di
validasi alih-alih mengubah data. Rute yang belum terpasang (404) dicatat
pada rincian dan tidak dihitung pelanggaran, karena kewarasan sudah
memastikan alamatnya benar.

**Satu perubahan yang tak terhindarkan, dinyatakan** (R-04): setiap
permintaan berkuki memperbarui waktu aktif terakhir sesi akun uji — sesi yang
dibuat operator, bukan penjalan. Penjalan tidak masuk, tidak keluar, dan
tidak memanggil rute yang mengubah data akun uji.

## 6. K-5 · Catatan L1 (P-4 A, R-06)

Satu baris L1 per putaran lewat `tambah_baris`, seperti fitur 040:
`id_percobaan` (`EXP-2026-nnn`, ditolak bila terpakai), `tugas` =
`kepatuhan`, `lingkungan`, kelima bidang `Versi` — `versi_kode` dari `git`,
selebihnya `belum-berlaku` — `hasil` per UK berkeadaan dan berincian,
`status` `gagal` bila ada yang gagal dan `berhasil` bila tidak, `catatan`
sebab gagal. **Akar logbook bukan argumen baris perintah**; uji memanggil
`utama(…, akar_logbook=…)`.

## 7. K-6 · Kontrak

- **D-08 Bagian 8**: aturan pelaksanaan — penjalan, tiga keadaan, kode
  keluar, SQLSTATE yang diterima per UK, peran per UK, rute dari D-14,
  perubahan sesi akun uji.
- **D-13 Bagian 8**: UK-09 s.d. UK-15 dijalankan penjalan yang sama.
- **D-09 Bagian 2.1** PS-01 dan PS-14, **Bagian 4.1** langkah 5: bukti adalah
  laporan penjalan berkode keluar 0 beserta baris L1-nya; akun uji kepatuhan
  dibuat operator sebelum langkah 5.
- **D-10 Bagian 3** `tugas` bertambah `kepatuhan`.
- **D-00** register.

## 8. Keputusan rancangan Gerbang 2

| Kode | Pertanyaan | Putusan |
|---|---|---|
| K-1 | Keadaan dan laporan | Bagian 2 — tiga keadaan; kode keluar 4 bagi belum lengkap; UK dari dokumen |
| K-2 | Basis data | Bagian 3 — transaksi selalu dibatalkan; SQLSTATE tertulis per UK; peran aplikasi dicocokkan dengan perakitan |
| K-3 | Dalam proses | Bagian 4 — pemeriksa dan validator yang sama |
| K-4 | API | Bagian 5 — kewarasan lebih dulu; rute dari D-14; badan kosong; perubahan sesi dinyatakan |
| K-5 | Catatan | Bagian 6 — L1 seperti fitur 040 |
| K-6 | Kontrak | Bagian 7 |

## 9. Uji

### 9.1 Di dalam `make check`

- Kerangka: daftar UK sama dengan D-08 dan D-13; keadaan keseluruhan; kode
  keluar; L1 berbidang versi lengkap; laporan dan L1 tanpa kuki
- Basis data atas PostgreSQL **sebagai peran sungguhan**: seluruh UK
  basis data lulus; percobaan yang semestinya berhasil — misalnya
  `peran_verifikasi` membaca karantina — dilaporkan **gagal** lewat mesin
  yang sama; percobaan sisip yang berhasil tidak meninggalkan baris
- Dalam proses: ketiganya lulus; validator yang dilonggarkan dilaporkan gagal
- API atas **aplikasi bersesi yang berjalan** di `127.0.0.1` lewat uvicorn,
  tersambung ke PostgreSQL, dengan akun uji buatan `perkakas.akun`: keempat
  UK lulus; aplikasi tiruan yang menjawab 200 bagi segalanya dilaporkan gagal;
  kewarasan yang gagal; akun berpersetujuan menjadikan UK-05 belum dapat
  diperiksa

### 9.2 Di luar `make check`

Lingkungan pengembangan bersesi: PostgreSQL dan `make jalan` bersesi; akun
uji dibuat dengan `perkakas.akun`, masuk untuk memperoleh kuki; penjalan
dijalankan lewat baris perintah; jumlah baris tabel yang disentuh dibandingkan
sebelum dan sesudah. Keluaran ke `bukti/`.

### 9.3 Uji mutasi

| Kode | Mutasi | Uji yang wajib merah |
|---|---|---|
| M-1 | Galat apa pun pada percobaan hak dihitung lulus | R-03 |
| M-2 | Transaksi percobaan tidak dibatalkan | R-04 |
| M-3 | Belum dapat diperiksa terhitung lulus pada keseluruhan | R-02 |
| M-4 | Satu UK hilang dari daftar | R-01 |
| M-5 | Kewarasan API dilewati | K-4 |
| M-6 | Kuki tercetak pada rincian | R-05 |
| M-7 | Putaran tidak tercatat ke L1 | R-06 |
| M-8 | Persetujuan akun uji tidak diperiksa pada UK-05 | K-4 |

## 10. Urutan tugas

| Tugas | Isi |
|---|---|
| T-1 | Kontrak: D-08 Bagian 8; D-13 Bagian 8; D-09; D-10 Bagian 3; D-00 |
| T-2 | Kerangka: keadaan, daftar, laporan, kode keluar, L1, perkakas; M-3, M-4, M-6, M-7 |
| T-3 | Pemeriksaan basis data; M-1, M-2 |
| T-4 | Pemeriksaan dalam proses |
| T-5 | Pemeriksaan API; M-5, M-8 |
| T-6 | Bukti, penutupan: L8, HKI, L4; status menunggu Gerbang 4 |

## 11. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Penjalan tampak perlu hak atau peran sendiri | Berhenti; R-07 |
| Pemeriksaan tampak perlu membuat atau menghapus data | Berhenti; P-2 A |
| UK tampak perlu dinyatakan lulus tanpa percobaan | Berhenti; R-02 |
| Rute atau bidang tanggapan tampak perlu ditambah | Berhenti; C-20 |
| Pemeriksaan sungguhan menemukan pelanggaran pada kode yang ada | Laporkan apa adanya; catat sebagai TK; jangan longgarkan |
