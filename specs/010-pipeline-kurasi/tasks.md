# Tasks: 010-pipeline-kurasi

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 (KB-042) |
| Plan | `plan.md`, lolos Gerbang 2 (KB-042) |
| Status | **Lolos Gerbang 4** (KB-043) |
| Jumlah tugas | **6** |
| Ketergantungan baru | **Nol** |

## Fase A · Butir dan penyaringan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `butir.py` — dua belas bidang D-06 Bagian 5 | **Uji: bidang dibaca dari `docs/D06.md`, bukan disalin ke uji.** Uji: `KategoriMasalah` fitur 003 dipakai ulang, tidak ditulis ulang. Uji: bidang wajib tanpa bawaan | R-01 | [x] — dua belas bidang dari D-06; satu tambahan (`id_butir`) disebut namanya, bukan diizinkan sebagai "tambahan" |
| A-2 | `tetapan.py` + `saring.py` — L1, L2, L3, dan L4 tiga keadaan | **Uji: L4 `MENUNGGU` tidak masuk antrean DAN tidak dibuang.** Uji: L3 menolak `dicabut` **dan** `diubah`; hanya `berlaku` yang lolos. Uji: L1 membuang tanpa menyimpan | R-03 s.d. R-06, R-12 | [x] — L4 `MENUNGGU`; rumah tetapan keempat terdaftar pada pemeriksa C-16; M-2, M-3, M-4 menyala |

**A-2 adalah tempat pola "tiga keadaan" menahan hal yang berbeda dari lima
kali sebelumnya**: bukan laporan yang keliru melainkan pilihan yang tidak
boleh diambil tanpa dasar. D-06 menyebut kedua akibat yang salah — meloloskan
membanjiri kurator yang hanya punya 4 jam per minggu; membuang mengosongkan
feed dan memicu titik kritis T5 — dan tidak menyebut mana yang lebih ringan.

## Fase B · Putusan, jejak, dan penarikan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | `putusan.py` — empat putusan, TL-01 s.d. TL-11, `ButirTayang` | **Uji: `ButirTayang` tidak dapat dibentuk tanpa putusan setujui.** Uji: penolakan menolak untai bebas. Uji: keempat putusan setara, `tunda` membawa waktu kembali | R-02, R-07, R-08 | [x] — `ButirTayang` berpagar bentuk; C-07 lapis kedua pada gerbang putusan; M-1 dan M-6 menyala |
| B-2 | `jejak.py` — siapa, kapan, apa, alasan | **Uji: jejak tidak memuat nama kurator.** Uji: keempat bidang FR-I05 wajib. Uji: tambah-saja — permukaan tanpa cara menyunting maupun menghapus, mengikuti `JejakArea` fitur 002 | R-09, R-13 | [x] — empat bidang FR-I05, peran bukan nama; pendeteksi data pribadi disatukan ke `src/ingest/data_pribadi.py`; M-9 menyala |
| B-3 | Penarikan butir tayang (D-06 Bagian 7.5) | **Uji: butir tayang ditarik ketika regulasi sumbernya menjadi `dicabut` ATAU `diubah`.** Uji: data sumber diperbarui menandai perlu tinjauan, tidak menarik | R-10 | [x] — `dicabut` dan `diubah` keduanya menarik; pembaruan data menandai tanpa menarik; koleksi tidak dihapus; M-8 menyala |

**Koreksi B-2 saat implementasi.** Kolom uji semula berbunyi "tambah-saja
lewat `src/logbook/`". Itu keliru: `src/logbook/` menegakkan C-09 atas
**catatan percobaan** D-10, dan D-10 tidak memiliki buku bagi jejak kurasi.
Menulis jejak operasional ke sana akan mencampur rekaman penelitian dengan
data jalannya sistem. Sifat tambah-saja yang dituju tetap sama; yang berubah
adalah dari mana ia diwarisi — `JejakArea` fitur 002, yang permukaannya sudah
sengaja tidak menyediakan cara menyunting maupun menghapus.

**B-1 adalah C-06 itu sendiri.** `ButirTayang` hanya dibentuk di sini, dan
fitur 011 yang menayangkan feed kemudian tidak **memiliki cara** menayangkan
kandidat.

## Fase C · Antrean dan pemeriksanya

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | `antrean.py` — rasio dan pengereman | **Uji: dua hari melampaui ambang TIDAK mengerem; tiga hari mengerem.** Uji: K-C diperlambat lebih dulu. Uji: angka dibaca dari D-06 Bagian 8.3 | R-11, R-12 | [x] — tiga hari berturut, rentetan terputus oleh hari aman; K-C saja; paruh kedua pengereman dinyatakan tertahan BT-24; M-7 menyala |
| C-2 | Pemeriksa C-06 dan C-07; pemindahannya pada `daftar_pasal.py` | **Uji: `make compliance` menyusut dua — 14 lulus, 6 belum.** Uji: pemeriksa C-07 menyala pada ketiga lapis, masing-masing terpisah | R-02, R-05 | [x] — C-06 dua aturan; C-07 ketiga lapis terpisah, diuji atas pohon yang dirusak satu lapis pada satu waktu; tagihan 12 → 14 |

**C-1 diuji dari kedua arah.** "Melampaui → direm" lulus juga pada
implementasi yang mengerem pada hari pertama, dan pengereman yang terlalu
cepat menurunkan frekuensi K-C setiap kali antrean naik sehari — lalu feed
kekurangan isi.

**C-2 memeriksa C-07 pada tiga lapis**, bukan pada lapis yang fitur ini
bangun. Pasal yang dijaga tiga lapis dan diperiksa pada satu di antaranya
adalah pasal yang lolos ketika lapis itu dipindahkan.

## Verifikasi akhir

- [x] `make check` lulus 6 gerbang
- [x] `make compliance` **menyusut dua** — 14 lulus, 0 gagal, **6** belum
- [x] Kesembilan uji mutasi `plan.md` Bagian 5 dijalankan; hasilnya dilaporkan apa adanya — M-1 s.d. M-9 seluruhnya menyala, beserta sembilan mutasi tambahan
- [x] Cakupan uji tidak turun — 99,81 → 99,83 atas 2.611 pernyataan
- [x] **Nol ketergantungan baru**
- [x] `KategoriMasalah` dipakai ulang — bukan definisi kedua

## Yang tidak dikerjakan di sini

Skor relevansi L4 menunggu klasifikasi K1–K8 (fitur 017) **dan** ambang BT-24
bulan 3. FR-I04 menunggu FR-F07, yang menunggu rute fitur 021. Layar kurator
menunggu `web/`.

**Pipeline ini belum dapat mengisi antrean kurasi.** Yang berdiri sesudah
fitur ini adalah seluruh jalur sesudahnya, sehingga L4 mendarat pada bagian
yang sudah siap menerimanya.
