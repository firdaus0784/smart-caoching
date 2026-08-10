# Tasks: 004-pembagian-data-dan-metrik

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 |
| Plan | `plan.md`, lolos Gerbang 2 |
| Status | **Lolos Gerbang 3** — 10 Agustus 2026 (KB-028) |
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
| B-1 | Presisi, recall, F1 per kelas | **Uji terhadap contoh yang dihitung tangan.** Uji: kelas tanpa contoh → belum terhitung, bukan 0,0 | R-07, R-08 | [ ] |
| B-2 | Rerata makro dan mikro, keduanya dinamai | **Uji: satu kelas kacau menurunkan makro jauh lebih besar daripada mikro** | R-09 | [ ] |

## Fase C · Catatan percobaan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | Catatan L1 keempat belas bidang D-10 Bagian 3 | Uji: keempat belas ada; **uji: seed acak dan id pembagian data wajib**. Uji: percobaan gagal tetap tercatat | R-10, R-11, C-09 | [ ] |

## Verifikasi akhir

- [ ] `make check` lulus 6 gerbang
- [ ] `make compliance` tidak berubah — 8 lulus, 0 gagal, 12 belum
- [ ] Keenam uji mutasi `plan.md` Bagian 4 dijalankan dan dilaporkan
- [ ] Angka metrik diuji terhadap contoh yang dihitung tangan
- [ ] Cakupan uji tidak turun
- [ ] **Nol ketergantungan baru**
