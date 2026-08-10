# Tasks: 004-pembagian-data-dan-metrik

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 |
| Plan | `plan.md`, lolos Gerbang 2 |
| Status | **Lolos Gerbang 4** — 10 Agustus 2026 (KB-029). Tujuh tugas selesai |
| Cakupan | **Bagian 1 saja** — model NER dan klasifikasi menjadi fitur 017 |
| Jumlah tugas | **7** |
| Ketergantungan baru | **Nol** |

## Fase A · Pembagian data

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `PembagianData` — tipe beku, hanya menerima id dokumen | **Uji: ketiga himpunan tidak beririsan.** Uji: tipe tidak menerima segmen | R-01, R-02 | [x] |
| A-2 | Porsi D-08 sebagai tetapan tunggal | Uji: porsi sama persis dengan D-08 Bagian 4.2, dibaca dari dokumennya. **Uji: tidak ada angka porsi di luar satu tempat** | R-03, C-16 | [x] — sapuan porsi dan sapuan ambang fitur 003 disatukan; tabrakan nilai 0,70 diakui |
| A-3 | Pembuatan pembagian deterministik terhadap seed | **Uji: seed sama → susunan sama; seed berbeda → susunan berbeda.** Uji: korpus terlalu kecil ditolak dengan menyebut jumlah minimumnya | R-05 | [x] |
| A-4 | **Pembekuan: sidik daftar id, dan pembagian ulang yang berbeda ditolak** | Uji: sidik berubah bila satu dokumen berpindah himpunan | R-04 | [x] |
| A-5 | **Himpunan uji di balik metode yang mencatat pembukaannya** | **Uji: uji tidak dapat dibaca tanpa tercatat.** Uji: pembukaan kedua menaikkan hitungan | R-06 | [x] — dicatat, bukan dilarang (KB-028 pilihan C); sapuan AST menjaga jalur sahnya |

**A-5 adalah tugas terpenting fitur ini.** PU-01 dilanggar tanpa niat:
seseorang "sekadar melihat" hasil uji untuk memilih konfigurasi berikutnya,
dan sesudah itu angka pada naskah bukan lagi hasil pada data tersembunyi.
Tidak ada satu pun jejak yang menunjukkannya kecuali yang dibangun di sini.

## Fase B · Metrik per kelas

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | Presisi, recall, F1 per kelas | **Uji terhadap contoh yang dihitung tangan.** Uji: kelas tanpa contoh → belum terhitung, bukan 0,0 | R-07, R-08 | [x] |
| B-2 | Rerata makro dan mikro, keduanya dinamai | **Uji: satu kelas kacau menurunkan makro jauh lebih besar daripada mikro** | R-09 | [x] — mikro 0,90 lawan makro 0,47 pada data yang sama |

## Fase C · Catatan percobaan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | Catatan L1 keempat belas bidang D-10 Bagian 3 | Uji: keempat belas ada; **uji: seed acak dan id pembagian data wajib**. Uji: percobaan gagal tetap tercatat | R-10, R-11, C-09 | [x] |

## Verifikasi akhir

- [x] `make check` lulus 6 gerbang
- [x] `make compliance` tidak berubah — 8 lulus, 0 gagal, 12 belum
- [x] Keenam uji mutasi `plan.md` Bagian 4 dijalankan; seluruhnya menyala
- [x] Angka metrik diuji terhadap contoh yang dihitung tangan
- [x] Cakupan uji tidak turun — 99% atas 1.506 pernyataan
- [x] **Nol ketergantungan baru** — tetap 10 langsung, 26 terkunci

## Dua uji mutasi yang tidak menyala, dan apa yang ditemukannya

Keduanya menemukan celah pada **uji saya**, bukan pada mutasinya, dan
keduanya jenis kegagalan yang sama — uji yang memeriksa besaran turunan yang
terlalu kasar.

| Mutasi | Yang luput |
|---|---|
| Sisa pembulatan dibuang ke himpunan uji | Uji memeriksa **jumlah total** dokumen, dan total tetap utuh ke mana pun sisanya jatuh. Padahal ke mana ia jatuh menentukan porsi: melemparkannya ke uji membuat himpunan uji melar melampaui 15% D-08 |
| Sidik dihitung dari jumlah, bukan isi | Uji memindahkan satu dokumen antar-himpunan, yang **juga mengubah jumlahnya**. Yang tidak tertutup: pertukaran dua dokumen — jumlahnya persis sama, isinya berubah — dan itu justru bentuk yang muncul ketika seseorang membagi ulang dengan seed berbeda |

Dua uji ditambahkan; kedua mutasi kemudian menyala.

## Yang menunggu fitur 017

Model NER dan klasifikasi (FR-D01, FR-D02) beserta prosedur latih ulang
(FR-D05) menunggu korpus teranotasi. Seluruh perkakas yang mereka butuhkan
sudah berdiri: pembagian beku, lemari himpunan uji, metrik per kelas, dan
catatan percobaan.
