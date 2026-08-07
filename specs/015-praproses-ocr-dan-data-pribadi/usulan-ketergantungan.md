# Usulan Ketergantungan Fitur 015

Praproses, OCR, dan pendeteksi data pribadi — FR-B01 s.d. FR-B04.

| | |
|---|---|
| Status | **Usulan. Menunggu persetujuan penanggung jawab teknis (C-12)** |
| Tanggal | 6 Agustus 2026 |
| Disusun oleh | Agen, atas penugasan KB-010 |
| Rujukan | `docs/D12.md` Bagian 7 · `ketergantungan-disetujui.toml` · KB-010 |

Fitur 015 tertahan C-12 sejak dipisahkan dari fitur 002 (KB-010): keempat
kebutuhannya menuntut ketergantungan baru, dan tidak satu pun boleh dipasang
tanpa keputusan Anda. Dokumen ini adalah bahan keputusan itu — bukan
pemasangan, bukan kode.

Titik nol hari ini: **lima ketergantungan langsung**, 18 paket terkunci.

---

## 1. Apa yang dituntut tiap kebutuhan

| Kebutuhan | Isi | Dapat dikerjakan tanpa ketergantungan baru? |
|---|---|---|
| FR-B01 | Unggahan PDF, DOCX, XLSX, dan gambar pindaian | **Tidak.** Ketiganya format biner berspesifikasi panjang; menulis pengurainya sendiri jauh lebih mahal daripada menerimanya |
| FR-B02 | OCR dokumen pindaian berbahasa Indonesia | **Tidak.** Menuntut mesin OCR beserta model bahasanya |
| FR-B03 | Tokenisasi, normalisasi, stop-word, stemming Bahasa Indonesia | **Sebagian.** Tokenisasi dan normalisasi dapat ditulis sendiri; stemming Bahasa Indonesia tidak — algoritmanya berbasis kamus |
| FR-B04 | Deteksi NIK, NIP, NISN, NUPTK, **nama perorangan**, nomor telepon, **alamat**, nomor rekening | **Sebagian, dan ini yang perlu Anda perhatikan** — lihat Bagian 4 |

---

## 2. Yang diusulkan

Lima ketergantungan langsung. Seluruh keterangan di bawah **diperiksa langsung
ke PyPI pada 6 Agustus 2026**, bukan dikutip dari ingatan.

| Paket | Versi | Lisensi | Untuk | Menarik masuk |
|---|---|---|---|---|
| `pypdf` | 6.15.0 | BSD-3-Clause | PDF | — (tanpa ketergantungan wajib pada Python 3.12) |
| `python-docx` | 1.2.0 | MIT | DOCX | `lxml` (BSD-3-Clause) |
| `openpyxl` | 3.1.5 | MIT | XLSX | `et-xmlfile` (MIT) |
| `PySastrawi` | 1.2.1 | MIT | Stemming dan stop-word Bahasa Indonesia | — (tanpa ketergantungan) |
| `pytesseract` | 0.3.13 | Apache-2.0 | OCR | `Pillow` (MIT-CMU) |

Bertambah: **5 langsung, 3 transitif baru** (`lxml`, `et-xmlfile`, `Pillow`).
`packaging` dan `typing_extensions` sudah ada pada kunci hari ini.

Seluruh lisensi permisif. Tidak ada copyleft, tidak ada lisensi yang menuntut
pembukaan kode turunan — penting bagi luaran HKI penelitian ini.

### FR-B04 tidak menambah ketergantungan apa pun

Pendeteksi pola untuk NIK, NIP, NISN, NUPTK, nomor telepon, dan nomor rekening
ditulis sendiri. Keenamnya berformat baku dan berdigit tetap; `re` pada pustaka
baku memadai, dan `src/ingest/jejak.py` sudah memuat bentuk awalnya.

---

## 3. Satu hal yang bukan paket Python, dan karena itu berbahaya

`pytesseract` **bukan** mesin OCR. Ia pembungkus tipis atas program
**Tesseract** yang dipasang di tingkat sistem operasi, beserta berkas model
bahasa `ind.traineddata` yang diunduh terpisah.

Artinya tiga hal:

1. **`uv.lock` tidak melihatnya.** Pemeriksa R-18 membandingkan pohon paket
   Python. Tesseract dan berkas modelnya berada di luar jangkauannya, sehingga
   versi yang berubah diam-diam tidak akan tertangkap `make check`.
2. **Hasil OCR bergantung pada versi mesin dan model.** C-09 menuntut setiap
   keluaran eksperimen mencatat versinya. Bila versi Tesseract tidak tercatat,
   hasil OCR tidak dapat diulang — dan korpus yang tidak dapat diulang
   membatalkan klaim reproduktibilitas pada naskah.
3. **Lisensinya perlu dicatat terpisah.** Tesseract dan repositori `tessdata`
   berlisensi Apache-2.0 — repositori `tessdata` saya periksa langsung pada 6
   Agustus 2026 dan berkas LICENSE-nya memang Apache License 2.0.

**Usul saya:** bila OCR disetujui, `ketergantungan-disetujui.toml` bertambah
satu bagian `[sistem]` yang mencatat versi Tesseract dan sidik berkas
`ind.traineddata`, dan pemeriksa R-18 diperluas membandingkannya. Tanpa itu,
kita memasang komponen yang menentukan isi korpus di luar seluruh gerbang yang
sudah dibangun.

---

## 4. Yang perlu Anda ketahui sebelum memutuskan: FR-B04 tidak dapat dipenuhi penuh pada fitur 015

FR-B04 menyebut delapan hal. Enam berpola tetap. **Dua tidak: nama perorangan
dan alamat.** Keduanya menuntut pengenalan entitas bernama — dan model NER
adalah **fitur 004, Bulan 4**, sedangkan fitur 015 dijadwalkan **Bulan 3**.

Urutan itu bukan kekeliruan; ia konsekuensi dari D-12 yang menempatkan gerbang
lebih dulu. Tetapi akibatnya nyata dan wajib dinyatakan: **fitur 015 tidak akan
menyamarkan nama orang.**

Tiga cara menanganinya:

| | Cara | Akibat |
|---|---|---|
| **A** | Fitur 015 menangani enam pola tetap saja. Nama dan alamat menunggu fitur 004. FR-B04 ditandai terpenuhi sebagian, tertulis di D-01 | Jujur. FR-B05 — verifikasi manusia — memang sudah berdiri sebagai penjaga terakhir, dan D-01 memang menyatakan anonimisasi otomatis tidak dianggap cukup |
| **B** | Tambahkan pustaka NER siap pakai sekarang | Menarik masuk `torch` atau `spacy` beserta modelnya — pohon ketergantungan berlipat, dan model prapelatihan Bahasa Indonesia untuk domain sekolah belum tentu lebih baik daripada model fitur 004 yang dilatih pada korpus sendiri |
| **C** | Daftar nama heuristik atau kamus nama Indonesia | **Saya menyarankan menolak ini.** Ia akan melewatkan banyak nama dan menandai banyak kata biasa, sementara laporannya terbaca seperti perlindungan. Ini persis cacat yang KB-013 tolak pada `tingkat_kerahasiaan`: bidang yang terbaca sebagai perlindungan padahal tidak menahan apa pun |

**Saran saya: A.** Dengan satu syarat yang saya anggap tidak dapat ditawar —
kekurangannya ditulis pada D-01 dan pada uraian modulnya, bukan hanya di sini.
Verifikator yang mengira nama sudah tersamarkan otomatis akan memeriksa lebih
longgar, dan itu membuat keadaan lebih buruk daripada tidak ada pendeteksi sama
sekali.

---

## 5. Satu batasan teknis yang mengikat, terlepas dari pilihan Anda

C-10 menuntut rentang anotasi memakai **indeks karakter**. Stemming dan
penghapusan stop-word mengubah panjang teks, sehingga indeks pada teks hasil
praproses **tidak menunjuk tempat yang sama** pada teks asli.

Maka: teks asli adalah satu-satunya rujukan indeks. Keluaran praproses
disimpan terpisah dan tidak pernah menggantikannya. Ini akan tertulis pada
`plan.md` fitur 015 dan bukan hal yang perlu Anda putuskan — tetapi ia
menjelaskan mengapa `PySastrawi` dipakai untuk pencarian, bukan untuk
menyiapkan bahan anotasi.

---

## 6. Yang saya minta Anda putuskan

| | Pertanyaan | Saran saya |
|---|---|---|
| 1 | Kelima paket disetujui? | Ya, kelimanya |
| 2 | OCR disetujui beserta konsekuensi ketergantungan sistem pada Bagian 3? | Ya, **bersama** perluasan R-18 ke bagian `[sistem]`. Menyetujui OCR tanpa itu berarti komponen penentu isi korpus berada di luar seluruh gerbang |
| 3 | FR-B04: pilihan A, B, atau C? | **A**, dengan kekurangannya tertulis pada D-01 |
| 4 | PDF: `pypdf` saja, atau `pdfplumber` bila mutu ekstraksinya kurang? | `pypdf` lebih dulu — nol ketergantungan wajib. `pdfplumber` (MIT, menarik `pdfminer.six` + `pypdfium2` + `Pillow`) ditinjau ulang **bila diukur kurang**, bukan diputuskan sekarang dari dugaan |

---

## 7. Yang belum terverifikasi

Dinyatakan agar tidak terbaca sebagai fakta terperiksa:

- **Keberadaan dan ukuran `ind.traineddata` tidak dapat saya periksa langsung
  pada sesi ini** — permintaan ke GitHub raw ditolak kebijakan jaringan (403),
  dan saya tidak mengulanginya. Yang terverifikasi hanyalah lisensi repositori
  `tessdata` (Apache-2.0). **Sebelum menyetujui butir 2, seseorang perlu
  memastikan berkas model Bahasa Indonesia benar-benar tersedia dan mencatat
  sidiknya.**
- **Mutu OCR Tesseract atas dokumen manajerial sekolah Indonesia belum
  diukur.** Tidak ada angka dalam dokumen ini yang menyatakan ia memadai.
  Pengukurannya milik prosedur uji D-08.
- **Mutu ekstraksi `pypdf` atas dokumen ber-tabel belum diukur** — dasar
  pertanyaan 4.

Tidak ada paket yang dipasang. `uv.lock` dan `ketergantungan-disetujui.toml`
tidak disentuh.
