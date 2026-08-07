# Spec: 015-praproses-ocr-dan-data-pribadi

| | |
|---|---|
| Kebutuhan | FR-B01, FR-B02, FR-B03, FR-B04 — dipisahkan dari fitur 002 pada Gerbang 1 (KB-010) |
| Dokumen terkait | D-01 Modul B · D-03 Bagian 12.6, Bagian 15 · D-04 ADR-06 · D-06 kanal K-C · D-08 prosedur uji · D-13 KD-01 |
| Pasal konstitusi yang menyentuh fitur ini | **C-12**, C-03, C-09, C-10, C-11, C-13 |
| Urutan pembangunan | 015 pada `docs/D12.md` Bagian 7, sesudah 002, sebelum 003 |
| Status | **Lolos Gerbang 1** — 6 Agustus 2026. Ketergantungan disetujui (KB-017). Menunggu `plan.md` dan Gerbang 2 |

## Tujuan

Setelah fitur ini ada, sebuah berkas PDF, DOCX, XLSX, atau pindaian yang
diunggah menjadi **teks yang dapat ditelusuri kembali ke berkas asalnya
karakter demi karakter**, dengan pengenal berpola tetap sudah ditandai sebelum
seorang verifikator melihatnya.

Yang dibangun bukan anonimisasi otomatis yang dipercaya. FR-B05 sudah
menyatakan sebaliknya, dan fitur 002 sudah menegakkannya: hasilnya tetap
melewati manusia. Yang dibangun adalah **pengurangan beban verifikator** —
dokumen yang sampai kepadanya sudah bertanda pada tempat yang paling mungkin
memuat data pribadi, sehingga waktunya habis untuk menilai, bukan mencari.

Perhitungan D-03 Bagian 12.6 menjadikan ini bukan kenyamanan melainkan syarat
kapasitas.

## Apa yang sempat menahannya

Keempat kebutuhan menuntut ketergantungan baru, sehingga seluruhnya tertahan
C-12 sejak KB-010. `usulan-ketergantungan.md` pada folder ini adalah bahan
keputusannya, dan keputusannya sudah diambil — KB-017, tercatat pada Bagian
"Keputusan Gerbang 1" di bawah.

FR-B04 untuk pengenal berpola tetap tidak pernah tertahan: ia dikerjakan dengan
`re` pada pustaka baku, dan bentuk awalnya sudah ada pada
`src/ingest/jejak.py`.

## Di luar cakupan

- **Nama perorangan dan alamat.** FR-B04 menyebut keduanya, dan keduanya
  menuntut pengenalan entitas bernama. Model NER adalah fitur 004 (Bulan 4);
  fitur ini Bulan 3. **Fitur 015 tidak akan menyamarkan nama orang**, dan itu
  wajib tertulis pada D-01 serta pada uraian modulnya — bukan hanya pada
  logbook. Verifikator yang mengira nama sudah tersamarkan otomatis akan
  memeriksa lebih longgar, dan itu lebih buruk daripada tidak ada pendeteksi
  sama sekali. Diputus pada Gerbang 1 sebagai pilihan A; catatannya sudah masuk
  `docs/D01.md` beserta BT-70.
- **Menyetel ambang kepercayaan OCR.** C-16; kalibrasinya BT-29.
- **Antarmuka unggah.** Layar S-xx menunggu D-05. Fitur ini lapisan layanan.
- **Perbaikan mutu pindaian.** Deskewing, denoising, dan sejenisnya tidak
  dibangun sebelum ada bukti terukur bahwa mutu OCR memerlukannya.
- **Penyimpanan berkas asli.** Sudah menjadi milik `src/penyimpanan/` sejak
  fitur 002. Fitur ini membaca lewat lapisan itu, tidak membangun yang kedua.

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | **KETIKA** berkas PDF, DOCX, atau XLSX diunggah, sistem **HARUS** mengekstrak teksnya (FR-B01) |
| R-02 | **JIKA** sebuah berkas tidak dapat diurai, **MAKA** sistem **HARUS** menolaknya dengan pesan Bahasa Indonesia ≤ 20 kata tanpa istilah teknis, dan **TIDAK BOLEH** meloloskannya sebagai dokumen berteks kosong (C-13) |
| R-03 | Teks hasil ekstraksi **HARUS** menjadi satu-satunya rujukan indeks karakter; keluaran praproses **TIDAK BOLEH** menggantikannya (C-10) |
| R-04 | **KETIKA** berkas pindaian diunggah, sistem **HARUS** menjalankan OCR Bahasa Indonesia atasnya (FR-B02) |
| R-05 | Setiap keluaran OCR **HARUS** mencatat versi mesin OCR dan versi berkas model bahasanya ke `logbook/` (C-09) |
| R-06 | **JIKA** OCR gagal berjalan, **MAKA** dokumen **HARUS** ditahan di karantina, bukan diloloskan dengan teks kosong |
| R-07 | Modul praproses **HARUS** menyediakan tokenisasi, normalisasi, penghapusan stop-word, dan stemming Bahasa Indonesia (FR-B03) |
| R-08 | Keluaran praproses **HARUS** membawa pemetaan kembali ke indeks karakter teks asli, atau dinyatakan tegas sebagai keluaran yang tidak dapat dipetakan balik |
| R-09 | **KETIKA** teks dokumen tersedia, sistem **HARUS** mendeteksi NIK, NIP, NISN, NUPTK, nomor telepon, dan nomor rekening beserta rentang karakternya (FR-B04) |
| R-10 | Pendeteksi **HARUS** melaporkan temuan, **TIDAK BOLEH** memutuskan kelayakan dokumen — putusan itu milik gerbang fitur 002 |
| R-11 | Laporan pendeteksi **TIDAK BOLEH** memuat nilai yang dideteksinya pada log maupun pesan galat |
| R-12 | Uraian modul pendeteksi **HARUS** menyatakan jenis data pribadi yang **tidak** dideteksinya, dengan contoh |
| R-13 | Seluruh ketergantungan baru **HARUS** tercatat pada `ketergantungan-disetujui.toml` sebelum dipakai, termasuk ketergantungan di luar paket Python (C-12) |

**R-11 dan R-12 berpasangan, dan keduanya pelajaran fitur 002.** R-11 mencegah
pendeteksi menyalin data pribadi ke log — cacat yang paling mudah dibuat pada
modul semacam ini, dan akibatnya kebalikan persis dari maksudnya. R-12 mencegah
laporan bersih terbaca sebagai dokumen bersih; ini bentuk yang sama dengan
uraian pemeriksa pola adversarial yang menyebutkan enam contoh yang lolos.

**R-03 dan R-08 juga berpasangan.** Stemming mengubah panjang teks, sehingga
indeks karakter pada teks hasil praproses tidak menunjuk tempat yang sama pada
teks asli. C-10 mengikat rentang anotasi pada indeks karakter, dan D-03 Bagian
15 sudah menetapkan alasannya. Keluaran praproses berguna untuk pencarian, tidak
untuk menyiapkan bahan anotasi.

**R-13 lebih luas daripada kelihatannya.** Mesin OCR adalah program sistem,
bukan paket Python, sehingga pemeriksa R-18 tidak melihatnya. Kebutuhan ini
yang menutup celah itu, dan bentuk penutupannya diputus pada Gerbang 1:
`ketergantungan-disetujui.toml` bertambah bagian `[sistem]` yang dibandingkan
R-18 tiap `make check`.

## Keadaan yang wajib ditangani

| Keadaan | Perilaku yang dituntut |
|---|---|
| PDF terkunci kata sandi | Ditolak dengan pesan pengguna; tidak dicoba dibuka paksa |
| PDF tanpa lapisan teks | Diperlakukan sebagai pindaian, dialihkan ke jalur OCR |
| DOCX dengan perubahan terlacak | Teks yang diambil adalah teks final, dan keputusan itu dinyatakan pada uraian modul |
| XLSX berumus | Nilai terhitung yang diambil, bukan rumusnya |
| Berkas kosong atau nol bita | Ditolak; **tidak** diperlakukan sebagai dokumen berteks kosong |
| Mesin OCR tidak terpasang | Gagal tegas saat penyalaan, bukan diam-diam menghasilkan teks kosong |

Baris terakhir sengaja ada. Mesin OCR yang hilang adalah keadaan yang paling
mungkin terjadi pada penyebaran, dan kegagalan diam di sana menghasilkan korpus
berisi dokumen pindaian tanpa teks yang tak seorang pun sadari.

## Kriteria penerimaan

- [ ] R-01 s.d. R-13 masing-masing punya uji yang gagal sebelum implementasi
- [ ] Uji bahwa berkas rusak menghasilkan penolakan, bukan teks kosong (R-02, R-06)
- [ ] Uji bahwa indeks karakter hasil ekstraksi menunjuk tempat yang benar pada teks asli (R-03, C-10)
- [ ] Uji bahwa laporan pendeteksi tidak memuat nilai yang dideteksinya (R-11)
- [ ] Uji bahwa uraian modul menyebut jenis yang tidak dideteksinya (R-12) — bentuk yang sama dengan uji uraian pemeriksa pola fitur 002
- [ ] Seluruh ketergantungan tercatat pada `ketergantungan-disetujui.toml`, dan `make check` gagal bila ada yang tidak tercatat (R-13, C-12)
- [ ] Cakupan uji tidak turun (C-11)
- [ ] Setiap keluaran OCR mencatat versi ke `logbook/` (C-09, R-05)
- [ ] Setiap pesan galat pengguna ≤ 20 kata, tanpa istilah teknis (C-13)

## Keputusan Gerbang 1

Ketiganya diputus pemegang gerbang pada 6 Agustus 2026 dan tercatat pada
KB-017. Rinciannya beserta alternatif yang ditolak ada di sana; yang berikut
adalah akibatnya bagi spec ini.

**1 · Kelima ketergantungan disetujui.** `pypdf`, `python-docx`, `openpyxl`,
`PySastrawi`, `pytesseract`. Seluruh lisensi permisif dan diperiksa langsung ke
PyPI. R-01, R-04, dan R-07 tidak lagi tertahan.

**2 · FR-B04 dikerjakan untuk enam pola tetap saja** (pilihan A). Nama
perorangan dan alamat menunggu model NER fitur 004. Kekurangannya **sudah**
tertulis pada `docs/D01.md` sebagai catatan cakupan dan BT-70 — bukan hanya
pada logbook, dan itu syarat yang menyertai keputusannya. Kamus nama heuristik
ditolak: ia menghasilkan laporan yang terbaca lebih tebal daripada kenyataannya,
cacat yang sama dengan yang KB-013 tolak pada `tingkat_kerahasiaan`.

**3 · R-18 diperluas ke bagian `[sistem]`.** Versi mesin OCR dan sidik berkas
model bahasa dicatat pada `ketergantungan-disetujui.toml` dan dibandingkan tiap
`make check`. Ini yang membuat R-13 punya penegak, bukan hanya pernyataan.

### Yang tetap wajib diperiksa sebelum R-04 dikerjakan

Keberadaan berkas model Bahasa Indonesia `ind.traineddata` **belum**
terverifikasi dari sumbernya — permintaan ke GitHub raw ditolak kebijakan
jaringan (403) dan tidak diulang. Yang terverifikasi hanya lisensi repositori
`tessdata` (Apache-2.0). Tugas pertama pada fase OCR adalah memastikannya dan
mencatat sidiknya; bila berkasnya tidak tersedia, pekerjaan berhenti di situ
dan keputusan 1 ditinjau ulang untuk `pytesseract` saja.
