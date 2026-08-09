# Usulan Ketergantungan Fitur 003

Pemasangan dan penyesuaian perangkat anotasi — FR-C01 s.d. FR-C10.

| | |
|---|---|
| Status | **Disetujui** — 6 Agustus 2026, keputusan KB-020. Pilihan A; nol ketergantungan Python baru |
| Tanggal | 6 Agustus 2026 |
| Rujukan | `docs/D04.md` ADR-08 · `docs/D03.md` · `ketergantungan-disetujui.toml` |

**Usul pokoknya satu kalimat: nol ketergantungan Python baru.**

---

## 1. Yang sudah diputuskan sebelum dokumen ini

ADR-08 menetapkan **Label Studio, dipasang mandiri**. Dua alternatifnya sudah
ditolak dan alasannya tercatat: membangun perangkat anotasi sendiri
(berminggu-minggu tanpa nilai ilmiah) dan layanan anotasi awan (dokumen
sekolah keluar dari kendali tim, melanggar PA-02).

Yang belum diputuskan adalah **bagaimana ia dipasang**, dan itu pertanyaan
C-12 yang sesungguhnya.

---

## 2. Tiga cara memasangnya, dan biayanya

Diperiksa langsung ke PyPI pada 6 Agustus 2026.

| | Cara | Ketergantungan Python baru |
|---|---|---|
| **A** | Label Studio berjalan sebagai **layanan terpisah**; kode kita membaca berkas ekspornya | **Nol** |
| **B** | `label-studio-sdk` dipasang untuk berbicara dengan API-nya | **24 paket langsung** |
| **C** | `label-studio` dipasang ke dalam proyek | **58 paket langsung** |

`label-studio` 1.23.0 berlisensi Apache-2.0. `label-studio-sdk` 2.1.0 **tidak
menyatakan lisensinya pada metadata PyPI** — tidak ada penggolong lisensi, dan
tidak ada berkas lisensi yang terdaftar. Bila B dipilih, seseorang perlu
memastikannya dari repositorinya lebih dulu.

### Mengapa A, dan tegas

Titik nol kita hari ini **26 paket terkunci**. Pilihan C melipatgandakannya
lebih dari tiga kali untuk perangkat yang **tidak dijalankan sistem sama
sekali** — Label Studio dipakai anotator lewat peramban, bukan dipanggil kode
kita. Ketergantungan yang tidak pernah diimpor kode mana pun adalah beban
tanpa manfaat, dan setiap paket di dalamnya menjadi permukaan yang wajib
diperiksa pemindai keamanan V-05.

Pilihan B lebih ringan tetapi menjawab kebutuhan yang belum ada. Kita tidak
memerlukan percakapan dengan API-nya; yang kita perlukan adalah **membaca
hasil anotasi**, dan hasilnya berbentuk JSON biasa yang `json` pada pustaka
baku sudah cukup membacanya.

**Bila kelak automasi API benar-benar diperlukan** — misalnya untuk FR-C10,
menyisipkan pra-anotasi secara otomatis — B diajukan ulang saat itu, dengan
kebutuhan yang sudah nyata. Menambahkannya sekarang berarti menyetujui
24 paket untuk pekerjaan yang belum ada bentuknya.

---

## 3. Yang tetap dibangun sendiri, dan tidak menuntut apa pun

Enam dari sepuluh kebutuhan **tidak** dapat diserahkan ke Label Studio, dan
keenamnya dapat ditulis dengan pustaka baku:

| Kebutuhan | Mengapa dibangun sendiri |
|---|---|
| FR-C02 | Cohen's Kappa dan F1 berpasangan menurut **aturan D-03 Bagian 11** — pencocokan tepat dan longgar didefinisikan tim, bukan oleh perangkat mana pun |
| FR-C06 | Ekspor JSONL/CoNLL beserta berkas pedoman; bentuk bawaan Label Studio tidak memuat pedomannya |
| FR-C08 | Penomoran versi skema dan penandaan batch terdampak — ADR-08 sudah menyatakan bidang ini mungkin perlu ditambahkan pada tahap ekspor |
| FR-C09 | Uji kualifikasi anotator pada set kalibrasi |
| FR-C10 | Penyisihan batch tanpa pra-anotasi sebagai pembanding *automation bias* |
| FR-C07 | Papan pemantauan (prioritas S) |

Perhitungan Kappa dan F1 memakai aritmetika biasa. Menambah pustaka statistik
untuk dua rumus yang muat dalam tiga puluh baris berarti menukar kejelasan
dengan ketergantungan — dan rumusnya justru bagian yang paling perlu terbaca,
sebab angkanya masuk ke naskah.

---

## 4. Ketergantungan sistem, dan pelajaran dari fitur 015

Label Studio menjadi **ketergantungan sistem**, sama kedudukannya dengan
Tesseract: berada di luar `uv.lock`, dan versinya menentukan bentuk data yang
kita baca.

Bedanya satu, dan penting: Tesseract menentukan **isi** korpus, Label Studio
menentukan **bentuk** berkas ekspornya. Yang kedua gagal dengan berisik —
berkas yang bentuknya berubah tidak dapat diurai — sedangkan yang pertama
gagal diam-diam. Karena itu ia tidak menuntut sidik berkas, cukup versinya.

**Usul:** `ketergantungan-disetujui.toml` bertambah `[sistem.label_studio]`
berisi versi yang dipakai, dan R-18 membandingkannya dengan cara yang sudah
dibangun pada fitur 015. Perkakasnya sudah ada; yang ditambahkan hanya
barisnya.

---

## 5. Yang saya minta Anda putuskan

| | Pertanyaan | Saran |
|---|---|---|
| 1 | Cara pemasangan Label Studio — A, B, atau C? | **A** — layanan terpisah, nol ketergantungan Python |
| 2 | `[sistem.label_studio]` ditambahkan dan diperiksa R-18? | **Ya**, mengikuti bentuk yang sudah ada |

---

## 6. Yang belum terverifikasi

- **Lisensi `label-studio-sdk` tidak dinyatakan pada PyPI.** Hanya relevan
  bila B dipilih; bila A dipilih, ia tidak menjadi soal sama sekali.
- **Bentuk berkas ekspor Label Studio 1.23 belum diperiksa langsung.** Tugas
  pertama fitur 003 adalah memeriksanya dan menyimpan satu contoh sebagai
  bahan uji — bentuk yang ditebak dari dokumentasi adalah bentuk yang akan
  berbeda dari kenyataannya.

Tidak ada paket dipasang. `uv.lock` tidak disentuh.
