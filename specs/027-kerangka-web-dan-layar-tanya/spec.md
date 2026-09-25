# Spec: 027-kerangka-web-dan-layar-tanya

| | |
|---|---|
| Kebutuhan | ADR-09; FR-F01, FR-F05, FR-F06, FR-F09, FR-F10, FR-F14; NFR-02, NFR-11, NFR-13, NFR-19; C-13, C-14, C-15, C-20 |
| Dokumen terkait | D-05 Bagian 4, 6 (S-09), 7, 8, 10, 11 · D-07 Bagian 4 tahap 10 dan Bagian 7 · D-14 Bagian 4.1 dan 4.2 |
| Status | **Gerbang 1 lolos** — 25 September 2026 (KB-124). **Usulan perubahan cakupan menunggu putusan (TK-65)** |

## Tujuan

Direktori `web/` belum ada. Sistem hanya dapat dicoba lewat `curl`, dan
tidak seorang kepala sekolah pun dapat melihat bagian yang menjadi kebaruan
penelitian ini: jawaban yang **menyatakan dasar rujukannya sebelum isinya**,
dan penolakan jujur "tidak ditemukan dasar rujukan" yang tampil sebagai
jawaban sah, bukan pesan galat.

Fitur ini membangun kerangka aplikasi web dan **satu irisan utuh**: layar S-09
Tanya beserta riwayat percakapannya, tersambung ke rute yang sudah ada.

## Mengapa satu irisan, bukan seluruh layar

Dari 29 rute D-14 Bagian 3, **tiga** yang terpasang hari ini:
`POST /api/v1/tanya`, `GET /api/v1/percakapan`, dan
`GET /api/v1/percakapan/{id}`. Dari 18 layar D-05 Bagian 4, hanya S-09 yang
seluruh blok intinya dapat diisi data sungguhan.

Layar tanpa rute hanya dapat dibangun di atas bentuk data yang **ditebak**,
dan tebakan itu kelak dibongkar ketika rutenya dibangun. Layar lain menyusul
bersama rutenya masing-masing.

## Di luar cakupan

- Layar S-01 s.d. S-08 dan S-10 s.d. S-18 — rutenya belum ada
- **Layar masuk dan autentikasi** — FR-A01 belum dibangun modul mana pun;
  aplikasi ini **tidak** memalsukannya (R-17)
- Blok 6 S-09 selain "Salin ringkasan": *Simpan* dan *Nilai jawaban* menuntut
  rute yang belum ada
- Blok 8 S-09 (tawaran lanjutan, FR-G09) dan tindakan "Laporkan bahwa ini
  seharusnya ada" — rutenya belum ada
- Saran pertanyaan pada keadaan tidak-ditemukan — bentuk tanggapan D-14 tidak
  memuatnya, dan C-20 melarang menambah bidang (lihat P-2)
- Perubahan backend apa pun — tanpa rute baru, tanpa bidang baru (C-20)
- Penyajian `klaim[].peringkat_kepercayaan` — TK-40 belum memutuskan artinya,
  dan D-05 S-09 tidak memintanya ditampilkan
- Penyebaran ke lingkungan sungguhan — pekerjaan operasi (D-09)

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | Sistem **HARUS** menyediakan aplikasi web pada `web/` — React dan TypeScript sesuai ADR-09 — yang menyajikan layar S-09 Tanya |
| R-02 | Susunan blok jawaban **HARUS** mengikuti D-05 S-09: pertanyaan, **penanda dasar rujukan sebelum isi jawaban**, ringkasan tindakan paling banyak tiga butir, penjelasan, dasar rujukan, dan penafian yang **selalu tampak** |
| R-03 | Penanda dasar rujukan **HARUS** berupa teks, bukan warna saja (AK-04), dan **TIDAK BOLEH** memuat angka probabilitas (FR-F06) |
| R-04 | **KETIKA** `status_dasar` bernilai `tidak_ditemukan`, susunan blok **HARUS** sama dengan keadaan normal dan hanya isinya yang berbeda — keadaan sah, bukan pesan galat (KL-G, AI-05) |
| R-05 | **KETIKA** `status_dasar` bernilai `di_luar_domain`, sistem **HARUS** menampilkan `penjelasan` dari tanggapan apa adanya |
| R-06 | Setiap baris dasar rujukan **HARUS** memuat judul dokumen, tahun, dan bagian; sitasi berstatus bukan `berlaku` **HARUS** menampilkan penanda keberlakuan; `catatan_keberlakuan` yang terisi **HARUS** tampil (D-07 Bagian 7, FR-F14) |
| R-07 | `bacaan_lanjutan` **HARUS** tampil pada blok terpisah beserta keterangan bahwa isinya tidak dipakai menyusun jawaban (D-07 Bagian 7, FR-D06) |
| R-08 | Layar S-09 **HARUS** menangani keadaan KL-A, KL-B, KL-D, KL-E, dan KL-G D-05 Bagian 7. KL-C dan KL-F **tidak berlaku** bagi S-09 — lihat bagian Keadaan |
| R-09 | Pertanyaan yang sedang diketik **TIDAK BOLEH** hilang karena koneksi terputus atau halaman dimuat ulang (D-05 Bagian 8, NFR-13) |
| R-10 | **KETIKA** backend mengembalikan galat, sistem **HARUS** menampilkan kalimat manusia beserta satu tindakan pemulihan, **tanpa** kode galat maupun istilah teknis (KL-D, D-14 Bagian 4.2) |
| R-11 | Sistem **HARUS** menampilkan daftar percakapan dan membuka satu percakapan dari daftar itu (FR-F09) |
| R-12 | Seluruh teks antarmuka **HARUS** memenuhi NFR-19 dan tiga larangan D-05 Bagian 10, dan **HARUS** diperiksa mesin — bukan dibaca mata (C-13) |
| R-13 | Antarmuka **HARUS** memenuhi AK-01 s.d. AK-05 D-05 Bagian 11: huruf dasar ≥ 16px, kontras WCAG 2.1 AA, sasaran ketuk ≥ 44×44px, makna tidak hanya lewat warna, teks alternatif |
| R-14 | Muat awal **HARUS** ≤ 5 detik pada jaringan 3G (NFR-02). `plan.md` menetapkan ukuran pengganti yang dapat diperiksa mesin |
| R-15 | Cangkang aplikasi **HARUS** dapat terbuka tanpa koneksi, sehingga KL-E dapat tampil pada telepon yang sinyalnya hilang (ADR-09) |
| R-16 | Sistem **TIDAK BOLEH** menambah rute, mengubah bidang tanggapan, maupun mengubah backend dalam bentuk apa pun (C-20, AG-02, AG-03) |
| R-17 | Aplikasi **TIDAK BOLEH** memalsukan autentikasi: tanpa layar masuk tiruan, tanpa token maupun sandi yang disimpan. Identitas ditentukan backend |
| R-18 | Aplikasi **TIDAK BOLEH** memuat apa pun dari pihak ketiga saat berjalan — tanpa CDN, tanpa fon jarak jauh, tanpa analitik (PA-05, D-04 Bagian 4) |
| R-19 | `make check` **HARUS** memeriksa `web/`: tipe, uji, kunci ketergantungan npm terhadap persetujuan (V-04), dan bahasa antarmuka (C-13). Gerbang yang lulus tanpa melihat `web/` adalah laporan palsu |
| R-20 | Tidak ada unsur gamifikasi maupun personalisasi berbasis riwayat dalam bentuk apa pun (C-14, C-15) |

## Keadaan yang wajib ditangani

| Keadaan | Perilaku pada S-09 |
|---|---|
| KL-A Memuat | Kerangka blok jawaban, bukan pemutar berputar |
| KL-B Kosong pertama kali | Menjelaskan apa yang dapat ditanyakan dan bahwa setiap jawaban menyebut dasarnya |
| KL-C Kosong karena habis | **Tidak berlaku** — Tanya tidak memiliki isi yang dapat habis |
| KL-D Galat sistem | "Ada gangguan di sistem kami. Yang Anda ketik sudah tersimpan." beserta tindakan *coba lagi* |
| KL-E Luring | "Sedang tidak terhubung." Draf pertanyaan tersimpan; tidak ada yang hilang |
| KL-F Antrean kirim | **Tidak berlaku** — D-05 Bagian 8 menetapkan pertanyaan S-09 disimpan sebagai **draf**, bukan dikirim otomatis. Pertanyaan yang terkirim sendiri berjam-jam kemudian akan mengejutkan penanyanya |
| KL-G Tidak ditemukan dasar | Susunan sama dengan jawaban normal; penanda "Tidak ditemukan dasar rujukan" |

## Keputusan Gerbang 1

Diputus pemegang Gerbang 1–4 pada 25 September 2026, keduanya mengikuti
anjuran.

**K-1 · Bentuk riwayat percakapan dituliskan ke D-14 Bagian 4.3.**
Dikerjakan: D-14 naik ke 0.6. Bentuknya didokumentasikan apa adanya dari
kode, tidak diubah.

**K-2 · Mikrokopi tidak-ditemukan memakai kalimat pertama D-05 Bagian 10
saja.** Kalimat kedua dicatat sebagai BT-71 pada D-05, menunggu bidang saran
pertanyaan yang menuntut persetujuan C-20.

## Usulan perubahan sesudah Gerbang 1 — menunggu putusan

**TK-65 ditemukan saat mengerjakan K-1: riwayat percakapan tidak pernah
ditulis.** `Percakapan.catat` hanya dipanggil dari uji; penangan `/tanya`
tidak mencatat giliran; bentuk permintaannya tidak memuat pengenal
percakapan. Pada aplikasi yang berjalan, kedua rute riwayat selalu
mengembalikan daftar kosong.

R-11 karena itu **tidak dapat dipenuhi** tanpa mengubah backend, dan R-16
melarangnya. `AGENTS.md` melarang mengubah `spec.md` saat implementasi tanpa
persetujuan, sehingga R-11 **belum** diubah di atas. Usulan:

- **R-11 dikeluarkan dari fitur 027** — irisan menjadi layar Tanya saja;
- penyambungan riwayat menjadi baris pembangunan tersendiri, sebab ia
  menuntut bidang permintaan baru yang harus ditulis ke D-14 lebih dulu.

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | ADR-09 |
| R-02, R-03, R-04 | D-05 Bagian 6 S-09; D-07 Bagian 4 tahap 10; FR-F05, FR-F06 |
| R-05 | FR-F13 |
| R-06, R-07 | D-07 Bagian 7; FR-F11, FR-F14, FR-D06 |
| R-08 | D-05 Bagian 7 |
| R-09, R-15 | D-05 Bagian 8; NFR-13 |
| R-10 | D-05 Bagian 7 KL-D dan Bagian 10; D-14 Bagian 4.2 |
| R-11 | FR-F09 |
| R-12 | C-13, NFR-19, D-05 Bagian 10 |
| R-13 | D-05 Bagian 11; NFR-11 |
| R-14 | NFR-02 |
| R-16 | C-20 |
| R-17 | FR-A01 di luar cakupan |
| R-18 | PA-05; D-04 Bagian 4 |
| R-19 | TA-01; KB-122 (TK-64) |
| R-20 | C-14, C-15 |

## Kriteria penerimaan

- [ ] R-01 s.d. R-20 punya uji yang gagal sebelum implementasi
- [ ] Uji mutasi disusun pada `plan.md` dan dilaporkan apa adanya
- [ ] `make check` lulus enam gerbang **dan terbukti membaca `web/`**: mutasi
      pada kode `web/` wajib menjatuhkan gerbang
- [ ] Layar dicoba ujung ke ujung terhadap `make jalan`, bukan hanya terhadap
      tiruan
- [ ] Tidak ada satu baris pun berubah di `src/`
