# Spec: 015-praproses-ocr-dan-data-pribadi

| | |
|---|---|
| Kebutuhan | FR-B01, FR-B02, FR-B03, FR-B04 — dipisahkan dari fitur 002 pada Gerbang 1 (KB-010) |
| Dokumen terkait | D-01 Modul B · D-03 Bagian 12.6, Bagian 15 · D-04 ADR-06 · D-06 kanal K-C · D-08 prosedur uji · D-13 KD-01 |
| Pasal konstitusi yang menyentuh fitur ini | **C-12**, C-03, C-09, C-10, C-11, C-13 |
| Urutan pembangunan | 015 pada `docs/D12.md` Bagian 7, sesudah 002, sebelum 003 |
| Status | **Menunggu Gerbang 1.** Tertahan C-12 sampai `usulan-ketergantungan.md` diputus |

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

## Yang menahannya, dan apa yang tidak tertahan

Keempat kebutuhan menuntut ketergantungan baru, sehingga seluruhnya tertahan
C-12 (KB-010). `usulan-ketergantungan.md` pada folder ini adalah bahan
keputusannya.

**Yang tidak tertahan:** FR-B04 untuk pengenal berpola tetap. Ia dikerjakan
dengan `re` pada pustaka baku, dan bentuk awalnya sudah ada pada
`src/ingest/jejak.py`. Bila persetujuan C-12 tertunda, bagian ini tetap dapat
dibangun lebih dulu.

## Di luar cakupan

- **Nama perorangan dan alamat.** FR-B04 menyebut keduanya, dan keduanya
  menuntut pengenalan entitas bernama. Model NER adalah fitur 004 (Bulan 4);
  fitur ini Bulan 3. **Fitur 015 tidak akan menyamarkan nama orang**, dan itu
  wajib tertulis pada D-01 serta pada uraian modulnya — bukan hanya pada
  logbook. Verifikator yang mengira nama sudah tersamarkan otomatis akan
  memeriksa lebih longgar, dan itu lebih buruk daripada tidak ada pendeteksi
  sama sekali. Keputusannya menunggu Gerbang 1.
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
yang menutup celah itu — dan bentuk penutupannya adalah pertanyaan 3 pada
`usulan-ketergantungan.md`.

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

## Pertanyaan Gerbang 1

Tiga, dan ketiganya sudah tersusun sebagai bahan keputusan pada
`usulan-ketergantungan.md`:

1. **Ketergantungan mana yang disetujui** (C-12). Tanpa jawabannya, R-01, R-04,
   dan R-07 tidak dapat dikerjakan.
2. **Bagaimana kekurangan FR-B04 ditangani** — nama perorangan dan alamat
   menunggu fitur 004. Saran: dinyatakan tegas di D-01, bukan ditutupi kamus
   nama heuristik.
3. **Bagaimana ketergantungan sistem diawasi** — perluasan R-18 ke bagian
   `[sistem]`, atau tidak.

Pertanyaan 2 dan 3 **bukan pertanyaan ketergantungan** dan tidak hilang bila
jawaban pertanyaan 1 adalah menolak seluruhnya.
