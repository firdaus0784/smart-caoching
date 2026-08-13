# Plan: 021-rute-tanya

| | |
|---|---|
| Spec | `spec.md` |
| Ketergantungan baru | **Nol** — dan itu keputusan, bukan kebetulan |
| Lapisan baru | `src/api/` |

## 1 · Keputusan Gerbang 1 yang plan ini bersandar padanya

Keempat pertanyaan `spec.md` dijawab sesuai usulnya:

| | Jawaban |
|---|---|
| Letak `Peran` | `src/api/peran.py`. `src/kamus/` tetap milik D-14 **Bagian 5** |
| Tepi `api → llm` | **Dituliskan** pada `AGENTS.md`, beserta alasannya |
| Tepi ke `pengguna` dan `telemetri` | **Tidak** pada fitur ini |
| Tabel peran diisi penuh | **Ya**, seluruh rute D-14 Bagian 3 |

## 2 · Mengapa nol ketergantungan, padahal ini "rute"

Karena rute yang dibangun di sini **bukan lapisan HTTP-nya**. FastAPI sudah
disetujui pada `usulan-ketergantungan.md` Bagian 9.2 tetapi belum masuk
`ketergantungan-disetujui.toml`, dan berkas itu menyatakan dirinya keputusan
tim. Menambah barisnya untuk meloloskan `make check` membatalkan gunanya —
kalimat itu tertulis pada kepala berkasnya sejak fitur 001.

Yang dibangun adalah **isi rute**: kendali peran, urutan jalur, dan riwayat
percakapan. Ketika baris FastAPI masuk, adaptornya memanggil ketiganya dan
tidak memuat satu pun keputusan. Itu urutan yang benar juga seandainya
persetujuannya sudah ada: keputusan yang tinggal di dalam penangan HTTP hanya
dapat diuji lewat HTTP, dan uji yang menuntut peladen berjalan adalah uji yang
akan dilewati orang ketika sedang buru-buru.

## 3 · Bentuk yang menegakkan urutan

`susun` fitur 009 hanya menerima `JawabanTervalidasi`, dan `JawabanTervalidasi`
hanya dibentuk `validasi`. Rantai itu sudah menjaga tiga tahap terakhir. Yang
belum dijaga adalah tiga tahap pertama — tidak ada yang mencegah pemanggil
menyerahkan segmen karangannya sendiri ke `validasi`.

Karena itu keluaran jalur bertipe `HasilTanya`, dan `HasilTanya` **hanya
dibentuk `jawab()`**. Pemeriksanya melarang pembentukannya di mana pun pada
`src/` selain modulnya — bentuk yang sama dengan `KredensialPseudonim` (C-05),
bukan bentuk `ButirTayang` yang membatasi *di mana boleh*. Alasannya sejajar:
modul yang membentuk hasilnya sendiri sudah punya jalur yang tinggal dipanggil,
sehingga membentuknya sendiri selalu berarti melewati sesuatu.

`HasilTanya` membawa tiga hal: `Tanggapan` bila ada, alasan berhenti bila
tidak, dan **laporan pemeriksaan yang menunggu model**. Yang ketiga tidak boleh
larut ke dalam dua yang pertama — pemeriksaan yang menunggu model adalah utang
yang dapat ditagih, dan utang yang tidak muncul pada keluaran akan berhenti
ditagih.

## 4 · Tiga keadaan, bukan dua — kali kedelapan

`AlasanBerhenti` bernilai `DI_LUAR_DOMAIN`, `BUKTI_TIDAK_CUKUP`, dan
`DITAHAN_VALIDATOR`. Ketiganya menghasilkan `status_dasar` yang sama pada
tanggapan — D-14 Bagian 4.1 tidak menyediakan nilai keempat, dan AG-03 melarang
menambahnya. Yang berbeda adalah **apa yang harus diperbaiki**:

| Alasan | Yang salah | Yang memperbaikinya |
|---|---|---|
| `DI_LUAR_DOMAIN` | Tidak ada yang salah | — |
| `BUKTI_TIDAK_CUKUP` | Korpus kurang | Kurasi, fitur 010 |
| `DITAHAN_VALIDATOR` | Jawaban model tidak tersitasi | Pengambilan, **bukan validator** (C-16) |

Menyamakan ketiganya membuat ketiga perbaikan itu tidak dapat dibedakan pada
laporan mana pun — dan yang paling mungkin terjadi kemudian adalah tepat yang
C-16 larang: validator dilonggarkan karena penolakannya terlihat banyak, tanpa
seorang pun tahu berapa banyak di antaranya sebenarnya korpus yang kurang.

Pengguna tetap melihat satu pesan. Perbedaannya untuk yang memperbaiki sistem,
bukan untuk yang bertanya.

## 5 · Kendali peran dibaca dari dokumen

Tabel rute D-14 Bagian 3 dibaca **saat uji**, bukan disalin ke kode. Bentuk
yang sama dengan uji bidang D-06 (fitur 010), taksonomi D-01 Bagian 9 (fitur
012), dan bentuk tanggapan D-14 Bagian 4.1 (fitur 009).

Alasannya bukan kerapian. Tabel peran yang disalin akan benar pada hari ia
disalin, lalu D-14 bertambah satu rute dan tidak ada satu pun uji yang gagal —
rute baru itu berjalan tanpa peran karena tidak ada baris yang menolaknya.
Kegagalan yang tidak berbunyi.

Dua arah diperiksa, dan keduanya perlu:

1. **Setiap rute D-14 punya peran pada kode.** Menangkap rute yang bertambah.
2. **Setiap rute pada kode ada di D-14.** Menangkap rute yang dikarang —
   AG-02 melarangnya, dan larangan tanpa pemeriksa adalah kalimat.

## 6 · Riwayat menyimpan rujukan, bukan salinan

`Percakapan` menyimpan pertanyaan dan `id_pesan`; isinya disusun ulang saat
dibuka. Tanggapan yang tersimpan akan menua — status keberlakuan sitasinya
berubah ketika regulasinya dicabut, dan riwayat yang menayangkan salinan lama
melanggar C-07 lewat pintu yang tidak dijaga siapa pun.

Tambah-saja, mengikuti `JejakArea` (002), `JejakKurasi` (010), dan `Telemetri`
(012): permukaannya tidak menyediakan cara menyunting maupun menghapus.

Batas yang diakui terbuka: di memori. Penyimpanan tetapnya menunggu penggerak
PostgreSQL, dan itu bukan pekerjaan fitur ini.

## 7 · Rencana uji mutasi

Sembilan. Dilaporkan apa adanya, termasuk yang tidak menyala.

| | Mutasi | Wajib menyalakan |
|---|---|---|
| M-1 | `jawab()` memanggil model meski kecukupan rendah | Uji ketiadaan panggilan — bukan uji nilai kembalian |
| M-2 | `jawab()` menyusun tanggapan dari keluaran yang ditahan validator | Uji C-19 pada jalur |
| M-3 | Pemeriksaan domain dipindah ke **sesudah** pengambilan | Uji urutan; pengambilan tidak boleh berjalan atas pertanyaan di luar domain |
| M-4 | `HasilTanya` dapat dibentuk di luar modulnya | Pemeriksa bentuk |
| M-5 | Laporan pemeriksaan yang menunggu model dibuang dari `HasilTanya` | Uji FR-F16 |
| M-6 | Satu rute dihapus dari tabel peran | Pemeriksa arah 1 — dibaca dari D-14 |
| M-7 | Satu rute yang tidak ada di D-14 ditambahkan ke tabel | Pemeriksa arah 2 — AG-02 |
| M-8 | `AlasanBerhenti` dijadikan dua nilai | Uji tiga keadaan |
| M-9 | `Percakapan` menyimpan salinan `Tanggapan` | Uji R-13 |

**M-1 dan M-3 diuji sebagai ketiadaan panggilan.** Keduanya lulus pada
implementasi yang memanggil model lalu membuang hasilnya — nilai kembaliannya
sama persis. Yang membedakan hanya apakah panggilannya terjadi, dan itu hanya
terlihat dari adaptor tiruan yang menghitung.

## 8 · Cakupan uji

Tidak turun. Patokan berjalan: 99,853% atas 2.875 pernyataan.

## 9 · Yang dinyatakan tertunda, bukan dilewatkan

| | Menunggu |
|---|---|
| Adaptor HTTP | C-12 — baris FastAPI pada berkas persetujuan, keputusan tim |
| Penyimpanan riwayat | C-12 — penggerak PostgreSQL |
| FR-F12 jawaban terkurasi | Isi dari kurator |
| Sisi semantik pengambilan | Fitur 019 |
| VS-03, VS-05, VS-07 | Fitur 020 — dilaporkan, tidak disembunyikan |
| Penyaringan prioritas dan perekaman peristiwa | Fitur 011 |
