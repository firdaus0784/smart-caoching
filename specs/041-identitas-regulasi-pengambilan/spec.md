# Spec: 041-identitas-regulasi-pengambilan

| | |
|---|---|
| Kebutuhan | TK-88; FR-F02, FR-F11; ADR-03; D-08 Bagian 6; C-02, C-16, C-18, C-20 |
| Dokumen terkait | D-07 Bagian 3.2, 3.3, 4.3, 4.4, 7 · D-08 Bagian 5.3, 6 · D-04 ADR-03 · D-06 · spec fitur 026, 032, 038, 039, 040 |
| Status | **Menunggu Gerbang 4** — 13 Oktober 2026 (KB-309). Empat dari empat tugas selesai |

## Mengapa fitur ini diusulkan sekarang

Pemotong fitur 038 menaruh judul, nomor, dan tahun regulasi hanya pada segmen
`Pembukaan`. Segmen `Pasal n` memuat isi pasalnya saja. Indeks leksikal
dibangun dari teks segmen (`bangun_indeks`, fitur 007), dan catatan metadata
korpus — tempat judul tersimpan — tidak ikut dicari.

Akibatnya pertanyaan yang menyebut nomor regulasi mencocokkan nomornya pada
pembukaan, bukan pada pasal yang ditanyakan. Bukti fitur 040, atas data
rekaan, memperlihatkannya: bila banyak regulasi berjudul serupa, recall
pertanyaan bernomor turun dari 20/20 menjadi 0/20, dan pasal sasaran berada
di peringkat 10 di belakang sembilan pembukaan berjudul serupa (TK-88).

Kelas pertanyaan ini berambang 95% pada D-08 Bagian 6 — lebih tinggi dari
pertanyaan lain, dan menjadi alasan ADR-03 memilih BM25. Ambang kecukupan
BT-29 dikalibrasi atas pengambilan yang berlaku saat kalibrasi; perbaikan
sesudahnya membatalkan kalibrasi itu. Karena itu TK-88 diputus lebih dulu
(KB-301, KB-302).

**D-07 Bagian 4.3 tidak menutupnya.** Ekstraksi entitas di sana
*"memperkuat pencarian leksikal"* agar pertanyaan bernomor *"menemukan
dokumen itu"* — dokumen, bukan pasalnya. Ia juga menunggu model NER fitur
017. Pasal yang ditanyakan tetap tidak memuat nomornya.

## Yang tidak dikerjakan fitur ini, dinyatakan di muka

- **Ambang, bobot, faktor pengali, atau angka penyetelan apa pun.** C-16
  kalimat kedua menyuruh memperbaiki pengambilan; bukan berarti boleh
  menyetel pengambilan dengan angka yang tidak dimiliki dokumen mana pun.
- **Penguatan entitas D-07 Bagian 4.3.** Menuntut model NER fitur 017.
- **Isi *gold set*.** Bukti memakai *gold set* rekaan yang dinyatakan rekaan,
  seperti fitur 040.
- **Kalibrasi BT-29.** Milik fitur 025, sesudah fitur ini.

## Kebutuhan (EARS) yang tidak bergantung pada pertanyaan

| ID | Kebutuhan |
|---|---|
| R-01 | Pertanyaan yang menyebut identitas sebuah regulasi **HARUS** dapat menemukan pasal regulasi itu tanpa bergantung pada segmen pembukaan. Ini dibuktikan dengan perkakas evaluasi fitur 040 atas korpus rekaan yang memuat regulasi berjudul serupa, sebelum dan sesudah perbaikan, dengan *gold set* beku yang sama |
| R-02 | Aturannya **HARUS** ditulis pada D-07 Bagian 3 sebelum kode; D-07 pemilik strategi pengambilan |
| R-03 | Perbaikan **TIDAK BOLEH** memasang ambang, bobot, faktor pengali, maupun angka penyetelan lain (C-16); pengambilan tetap BM25 dan RRF D-07 Bagian 4.4 |
| R-04 | Versi indeks yang tercatat (RT-05, C-09) **HARUS** berbeda bila aturan penyusunan bahan pencarian berbeda, agar putaran U3 sebelum dan sesudah perbaikan tidak terbaca sebagai indeks yang sama |
| R-05 | Pemisahan lisensi (C-02), kelayakan bahan fitur 039, dan letak konten hasil pengambilan dalam permintaan model (C-18) **TIDAK BOLEH** berubah |
| R-06 | Fitur ini **TIDAK BOLEH** menambah rute, bidang tanggapan `/tanya`, maupun paket (C-12, C-20) |

## Pertanyaan terbuka

Tiap pertanyaan disertai anjuran; anjuran bukan putusan.

**P-1 · Bentuk perbaikan.**

| Pilihan | Arti |
|---|---|
| A | **Identitas sebagai bagian teks pencarian, tidak disimpan pada segmen.** Indeks leksikal dibangun dari identitas dokumen ditambah teks segmen. Yang tidak berubah: `segmen_teks.teks`, teks yang dikirim ke model, yang ditampilkan pembaca sumber, dan yang diperiksa validator. Tanpa pengindeksan ulang di peladen; indeks leksikal di memori dibangun ulang dari muatan |
| B | Identitas ditulis ke awal teks segmen saat pengindeksan fitur 038. Sederhana, tetapi mengubah teks yang dikirim ke model, yang ditampilkan pembaca sumber, yang dihitung batas 500 kata D-07 Bagian 3.2, dan yang diperiksa VS-05. Seluruh dokumen wajib diindeks ulang |
| C | Perluasan dokumen saat pengambilan: pembukaan yang terambil menarik pasal-pasal dokumennya. Ini menuntut aturan berapa pasal dan pada peringkat berapa — angka penyetelan yang dilarang R-03 |
| D | Tidak diperbaiki; dinyatakan sebagai keterbatasan pada D-08 Bagian 12 |

**Anjuran: A.** Hanya pilihan ini yang memperbaiki pencarian tanpa mengubah
apa yang dibaca model, kurator, dan kepala sekolah. Pilihan B membuat teks
yang dikutip berbeda dari teks dokumennya.

**P-2 · Sumber identitas.**

| Pilihan | Arti |
|---|---|
| A | **Judul pada catatan metadata korpus** (fitur 032), diisi tim lewat `terima --judul` dan dibaca pemuat fitur 039 |
| B | Baris-baris segmen pembukaan. Otomatis, tetapi bagian "Mengingat" menyebut nomor regulasi **lain**, sehingga setiap pasal ikut cocok dengan nomor yang dirujuk pembukaannya, bukan nomor yang dimilikinya |
| C | Bidang `nomor` baru pada catatan metadata. Tepat, tetapi menuntut kolom, hak peladen, isian perkakas, dan perubahan D-14 Bagian 5 |

**Anjuran: A.** Judul sudah wajib dan tersimpan, dan ia satu-satunya sumber
yang menyebut identitas dokumen itu sendiri.

**P-3 · Bentuk judul regulasi.** Pilihan P-2 A hanya membantu bila judul
regulasi memuat nomor dan tahunnya.

| Pilihan | Arti |
|---|---|
| A | **Ditegakkan saat menerima.** Dokumen berjenis `regulasi_resmi` ditolak bila judulnya tidak memuat pola `Nomor … Tahun …`. Polanya ditulis pada D-06 dan diputus di Gerbang 1 ini, bukan dikarang agen saat implementasi. Dokumen yang sudah di korpus tidak tersentuh |
| B | Pedoman pada D-06 tanpa ditegakkan |

**Anjuran: A.** Pedoman yang tidak ditegakkan berakhir pada judul ringkas
seperti "Juknis BOS". Pertanyaan bernomor atas dokumen itu tetap gagal, dan
tidak ada yang tahu sebabnya.

**P-4 · Sisi vektor.**

| Pilihan | Arti |
|---|---|
| A | **Leksikal saja.** ADR-03 menyerahkan nomor regulasi pada sisi leksikal. Penyematan fitur 026 tidak berubah |
| B | Kedua sisi: teks yang disematkan juga memuat identitas. Ini mengubah fitur 026, yang sudah lolos Gerbang 4, dan menuntut penyematan ulang |

**Anjuran: A.** ADR-03: *"Vektor saja — gagal pada nomor regulasi."*
Memperbaiki sisi yang memang ditugasi nomor sudah cukup. Sisi vektor dapat
ditinjau bersama ADR-12.

**P-5 · Cakupan dokumen.**

| Pilihan | Arti |
|---|---|
| A | **Seluruh dokumen kedua indeks.** Panduan resmi dan artikel juga ditanya dengan namanya; D-07 Bagian 7 menampilkan "judul ringkas atau nomor regulasi" sebagai nama dokumen |
| B | Hanya `regulasi_resmi` |

**Anjuran: A.** Satu aturan bagi semua jenis lebih mudah diperiksa daripada
dua. Pembatasan pada regulasi membiarkan masalah yang sama pada panduan
bernomor, seperti petunjuk teknis.

## Putusan Gerbang 1 (KB-304)

Pemegang Gerbang 1–4 memilih anjuran pada setiap pertanyaan:

| Pertanyaan | Putusan |
|---|---|
| P-1 | **A** — identitas dokumen ikut teks pencarian leksikal, tidak disimpan pada segmen; yang dibaca model, kurator, dan pengguna tidak berubah |
| P-2 | **A** — identitas diambil dari judul pada catatan metadata korpus |
| P-3 | **A** — judul `regulasi_resmi` wajib memuat pola `Nomor … Tahun …`, ditegakkan saat menerima; polanya pada D-06; dokumen yang sudah di korpus tidak tersentuh |
| P-4 | **A** — sisi leksikal saja; penyematan fitur 026 tidak berubah |
| P-5 | **A** — seluruh dokumen kedua indeks |

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | TK-88; D-08 Bagian 6; ADR-03 |
| R-02 | D-07 Bagian 3; `AGENTS.md` alur kerja |
| R-03 | C-16 |
| R-04 | D-07 Bagian 3.3 (RT-05); C-09 |
| R-05 | C-02, C-18; spec fitur 039 |
| R-06 | C-12, C-20 |

## Kriteria penerimaan

- [x] P-1 s.d. P-5 diputus pada Gerbang 1
- [x] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [x] Bukti sebelum dan sesudah atas PostgreSQL sebagai peran sungguhan,
      dengan *gold set* rekaan beku yang sama dan dinyatakan rekaan
- [x] `make check` lulus enam gerbang
