# Spec: 023-lapisan-http

| | |
|---|---|
| Kebutuhan | FR-F01, FR-F09; kendali peran D-14 Bagian 3 |
| Dokumen terkait | D-14 Bagian 3 dan 4.1, D-05 Bagian 7, D-13 KD-09 |
| Pasal konstitusi yang menyentuh fitur ini | C-13, C-17, C-20 |
| Status | Gerbang 1, 2, dan 3 lolos — KB-070 |

## Tujuan

Sesudah fitur ini, sistem **dapat dinyalakan sebagai peladen** dan menerima
pertanyaan lewat jaringan. Fitur 021 sudah membangun seluruh isi rute —
kendali peran, urutan jalur penjawaban, riwayat percakapan — dan sengaja
berhenti sebelum kerangkanya, sebab `fastapi` belum ada pada berkas
persetujuan. Barisnya masuk pada 31 Agustus 2026 (KB-067), dan yang tersisa
adalah lapisan tipis yang menyambungkannya.

Nilai fitur ini bukan menambah kemampuan melainkan **membuat yang sudah ada
dapat dijalankan**. Sampai hari ini seluruh jalur penjawaban hanya dapat
dipanggil dari dalam uji; sesudah fitur ini ia dapat dipanggil dari luar
proses, dan itulah pembeda antara pustaka dan aplikasi.

## Prinsip yang menentukan seluruh rancangan

`plan.md` fitur 021 sudah menetapkannya sebelum kerangkanya ada, dan fitur ini
terikat padanya:

> Adaptornya memanggil ketiganya dan **tidak memuat satu pun keputusan**.
> Keputusan yang tinggal di dalam penangan HTTP hanya dapat diuji lewat HTTP,
> dan uji yang menuntut peladen berjalan adalah uji yang dilewati orang ketika
> sedang buru-buru.

Akibat praktisnya tegas: setiap penangan pada fitur ini **hanya** menerjemahkan
— permintaan menjadi panggilan, hasil menjadi tanggapan. Tidak ada penyaringan,
tidak ada penentuan urutan, tidak ada pemilihan bentuk galat. Yang tampak perlu
diputuskan di dalam penangan adalah tanda bahwa ia kurang pada lapisan di
bawahnya, dan diperbaiki di sana.

## Di luar cakupan

Disebutkan tegas beserta sebabnya masing-masing. Yang tidak disebut sebabnya
akan dikerjakan seseorang karena mengira ia terlupa.

- **Autentikasi dan sesi** (FR-A01, rute `/api/v1/auth/*`). Tidak ada modul
  yang membangunnya, dan fitur ini **tidak** membuatnya secara diam-diam.
  Akibatnya dinyatakan pada R-04: identitas pemanggil wajib diserahkan
  penyusun aplikasi, dan tanpa itu aplikasi **tidak dapat disusun sama
  sekali**. Peladen ini karena itu belum layak dihadapkan ke jaringan publik,
  dan itu keadaan yang dinyatakan, bukan yang disembunyikan.
- **Seluruh rute D-14 di luar Bagian 3.2** — profil, prioritas, persetujuan,
  kurasi, anotasi, telemetri. Isinya sebagian sudah ada pada `src/pengguna/`
  dan `src/telemetri/`, tetapi menyambungkan semuanya sekaligus menghasilkan
  satu fitur yang tidak dapat ditinjau dalam satu duduk. Ia dipecah, mengikuti
  pemisahan yang sama pada fitur 003, 009, dan 002.
- **`POST /api/v1/pesan/{id}/penilaian`** (FR-F07). Penilaian jawaban belum
  memiliki modul penyimpannya.
- **Penyimpanan sesungguhnya.** Aplikasi tetap berjalan di atas
  `PenyimpanTiruan`. Implementasi PostgreSQL belum dimiliki baris urutan
  pembangunan mana pun — temuan tersendiri, dicatat terpisah.
- **Sumber vektor** (019) dan **VS-03/05/07** (020). Jalur penjawaban tetap
  berhenti pada pemeriksaan yang menunggu model, dan peladen melaporkannya apa
  adanya lewat `menunggu_model` yang sudah dibawa `HasilTanya`.

## Kebutuhan (EARS)

**R-01.** KETIKA permintaan `POST /api/v1/tanya` diterima, sistem WAJIB
memanggil `boleh()` dengan pola jalur D-14 **sebelum** memanggil apa pun yang
lain, dan menolak permintaan yang perannya tidak berhak.

**R-02.** KETIKA peran pemanggil berhak, sistem WAJIB memanggil
`Jalur.jawab()` satu kali dan mengembalikan `Tanggapan` yang dihasilkannya
**tanpa mengubah satu bidang pun**.

**R-03.** SELAMA jalur penjawaban mengembalikan `HasilTanya` yang membawa
`alasan_berhenti`, sistem WAJIB tetap mengembalikan status HTTP 200 beserta
bentuk tanggapan D-14 yang sama — sebab D-14 menetapkan keadaan
`tidak_ditemukan` dan `di_luar_domain` memakai bentuk yang sama dengan jawaban
yang sah, dan status galat akan membuat layar menampilkannya sebagai kegagalan
sistem.

**R-04.** Sistem WAJIB menuntut penyusun aplikasi menyerahkan penentu identitas
pemanggil. JIKA penentu tidak diserahkan, MAKA aplikasi tidak dapat disusun.

**R-05.** KETIKA permintaan `GET /api/v1/percakapan/{id}` diterima, sistem
WAJIB mengembalikan giliran percakapan **tanpa tanggapan yang tersimpan** —
`Giliran` fitur 021 memang tidak memilikinya, dan bentuk itu yang menjaga C-07:
tanggapan yang tersimpan menua, dan riwayat yang menayangkannya kembali
menjawab berdasarkan keberlakuan yang sudah lewat.

**R-06.** JIKA permintaan tidak lengkap atau ditolak, MAKA pesan galat kepada
pengguna WAJIB berbahasa Indonesia, ≤ 20 kata, tanpa istilah teknis, tanpa kode
galat, dan tanpa memuat kembali nilai yang ditolak.

**R-07.** Sistem TIDAK BOLEH mendaftarkan rute yang tidak ada pada D-14 Bagian
3 — termasuk rute pemeriksaan kesehatan, dokumentasi otomatis, dan rute bantu
lain yang lazim disediakan kerangka web.

## Keadaan yang wajib ditangani

| Keadaan | Yang wajib terjadi |
|---|---|
| Peran tidak berhak | Ditolak sebelum jalur penjawaban tersentuh |
| Peran tidak dikenal | Ditolak; `boleh()` sudah menolak rute tak dikenal |
| Pertanyaan kosong | Ditolak dengan pesan R-06 |
| Pertanyaan memuat data pribadi | Ditolak lapisan di bawahnya; pesannya diteruskan apa adanya |
| Jalur berhenti tanpa jawaban | 200, bentuk D-14, `alasan_berhenti` terbawa |
| Percakapan tidak ditemukan | Ditolak dengan pesan R-06 |

## Pertanyaan yang wajib dijawab Gerbang 1

Tidak ada. Ketiganya yang semula terbuka sudah terjawab:

1. **Kerangka web** — `fastapi` disetujui KB-044, dituliskan KB-067.
2. **Bentuk identitas pemanggil** — dijawab R-04: diserahkan penyusun, tanpa
   nilai baku. Aplikasi yang memiliki identitas baku akan dijalankan dengan
   identitas baku itu.
3. **Status HTTP bagi jawaban yang tertahan** — dijawab R-03: tetap 200,
   mengikuti D-14 yang menetapkan bentuk tanggapan seragam.

## Ketertelusuran

| Kebutuhan | Diwujudkan |
|---|---|
| FR-F01 | R-01, R-02, R-03 |
| FR-F09 | R-05 |
| D-14 Bagian 3 | R-01, R-07 |
| D-14 Bagian 4.1 | R-02, R-03 |
| C-13, NFR-19 | R-06 |
| C-17 | R-07 dan seluruh prinsip "tanpa keputusan" |
| C-20 | R-02, R-07 |
