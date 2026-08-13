# Spec: 003-perangkat-anotasi

| | |
|---|---|
| Kebutuhan | FR-C01 s.d. FR-C10 · pembacaan ekspor dipindahkan ke fitur 016 (KB-022) |
| Dokumen terkait | D-01 Modul C · **D-03 Bagian 5, 10, 11, 12** · D-04 ADR-08, Bagian 7.2 · D-10 · D-11 Bagian 3.2 |
| Pasal konstitusi yang menyentuh fitur ini | **C-10**, C-09, C-11, C-12, C-16 |
| Urutan pembangunan | 003 pada `docs/D12.md` Bagian 7, sesudah 015 |
| Status | **Lolos Gerbang 2** — 6 Agustus 2026. Cakupan dipersempit ke bagian 1 (KB-022); pembacaan ekspor menjadi fitur 016 |
| Ketergantungan | **Nol paket Python baru** — disetujui KB-020 |

## Tujuan

Setelah fitur ini ada, dua anotator dapat menganotasi dokumen yang sama dan
**angka kesepakatan mereka dapat dihitung menurut aturan D-03 Bagian 11** —
bukan menurut aturan bawaan perangkat mana pun.

Itu perbedaan yang menentukan seluruh fitur ini. Label Studio dapat
menampilkan angka kesepakatan sendiri, dan angkanya akan salah untuk maksud
kita: D-03 Bagian 11 **menolak Cohen's Kappa bagi anotasi rentang** dengan
alasan yang tertulis — jumlah "kesempatan" tidak terdefinisi ketika anotator
menentukan sendiri di mana rentang dimulai, sehingga peluang kesepakatan acak
tidak dapat dihitung. Angka yang dihasilkan terlihat meyakinkan tetapi tidak
bermakna, dan angka itulah yang akan masuk naskah.

Yang dibangun karena itu bukan perangkat anotasi. Yang dibangun adalah
**lapisan yang membaca hasil anotasi dan menghitungnya dengan benar.**

## Yang dikerjakan Label Studio, dan yang tidak

ADR-08 sudah menetapkan pemasangannya mandiri. KB-020 menetapkan ia berjalan
sebagai **layanan terpisah**: kode kita tidak mengimpornya, tidak
memanggilnya, hanya membaca berkas ekspornya.

| Dikerjakan Label Studio | Dikerjakan fitur ini |
|---|---|
| Antarmuka pelabelan (FR-C01) | Skema label sebagai tipe, berversi (FR-C04, C-05, C-08) |
| Penugasan dokumen ke anotator | Kesepakatan menurut D-03 Bagian 11 (FR-C02) |
| Antarmuka adjudikasi | Pencatatan putusan adjudikasi (FR-C03) |
| — | Ekspor JSONL/CoNLL beserta pedoman (FR-C06) |
| — | Uji kualifikasi anotator (FR-C09) |
| — | Penyisihan batch pembanding *automation bias* (FR-C10) |
| — | Papan pemantauan (FR-C07, prioritas S) |

## Di luar cakupan

- **Memasang Label Studio.** Itu pekerjaan penyebaran (D-09), bukan kode.
  Fitur ini menyediakan pembaca ekspornya dan mencatat versinya.
- **Mengubah ambang kesepakatan.** D-03 Bagian 11 menetapkan Kappa ≥ 0,70,
  F1 tepat ≥ 0,75, F1 longgar ≥ 0,85. C-16 melarang menyetelnya di luar
  prosedur kalibrasi.
- **Mengubah definisi kategori K1 s.d. K8.** Dimiliki D-03 Bagian 5. Fitur ini
  mewujudkannya sebagai tipe, tidak menafsirkannya.
- **Antarmuka papan pemantauan.** FR-C07 berprioritas S; fitur ini menyediakan
  perhitungannya, layarnya menunggu D-05.
- **Pra-anotasi otomatis itu sendiri.** Ia menuntut model NER fitur 004.
  Fitur ini membangun **penandaan status pra-anotasi dan batch pembanding**,
  sehingga ketika pra-anotasi datang, pengendaliannya sudah berdiri lebih
  dulu — urutan yang sama dengan gerbang karantina mendahului anonimisasi.

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | Skema label entitas **HARUS** memuat delapan label FR-C04 sebagai tipe, bukan untai bebas |
| R-02 | Skema kategori **HARUS** memuat K1 s.d. K8 sesuai D-03 Bagian 5, sebagai tipe |
| R-03 | Setiap skema **HARUS** membawa nomor versi, dan versinya **HARUS** ikut pada setiap anotasi yang memakainya (FR-C08) |
| R-04 | **KETIKA** versi skema naik, sistem **HARUS** menandai batch terdampak sebagai perlu anotasi ulang; korpus **TIDAK BOLEH** memuat dua versi skema tanpa penandaan (FR-C08) |
| R-05 | Rentang anotasi entitas **HARUS** memakai indeks karakter pada teks kanonik (C-10, D-03 Bagian 15) |
| R-06 | **JIKA** rentang anotasi tidak cocok dengan teks kanonik yang dirujuknya, **MAKA** sistem **HARUS** menolaknya, bukan memperbaikinya diam-diam |
| R-07 | Kesepakatan klasifikasi **HARUS** dihitung dengan Cohen's Kappa; keseluruhan dan per kategori (D-03 Bagian 11) |
| R-08 | Kesepakatan anotasi rentang **HARUS** dihitung dengan F1 berpasangan pada dua tingkat — pencocokan tepat dan longgar — dan **TIDAK BOLEH** memakai Cohen's Kappa (D-03 Bagian 11, D-11 Bagian 3.2) |
| R-09 | Uraian modul perhitungan **HARUS** menyatakan mengapa Kappa tidak dipakai bagi rentang, dengan rujukan ke pemiliknya |
| R-10 | Ekspor **HARUS** tersedia dalam JSONL dan CoNLL, **beserta berkas pedoman anotasi yang berlaku** (FR-C06) |
| R-11 | Ekspor **HARUS** membawa versi skema; berkas ekspor tanpa versi **TIDAK BOLEH** dihasilkan |
| R-12 | Setiap dokumen **HARUS** membawa status pra-anotasinya (FR-C10) |
| R-13 | **KETIKA** pra-anotasi dipakai pada sebuah batch, sistem **HARUS** menyisihkan sebagian batch tanpa pra-anotasi sebagai pembanding (FR-C10) |
| R-14 | Uji kualifikasi **HARUS** menilai anotator terhadap kunci jawaban dengan ambang D-03 Bagian 13: F1 longgar ≥ 0,80 dan Kappa kategori ≥ 0,70 (FR-C09) |
| R-15 | Catatan batch **HARUS** memuat seluruh bidang D-03 Bagian 11 dan tercatat ke `logbook/` (C-09) |
| R-16 | Versi Label Studio yang dipakai **HARUS** tercatat pada `ketergantungan-disetujui.toml` dan diperiksa R-18 (KB-020) |

**R-08 dan R-09 berpasangan, dan keduanya inti fitur ini.** R-08 menetapkan
perhitungannya; R-09 menetapkan bahwa alasannya tertulis pada kodenya. Tanpa
R-09, pembaca berikutnya yang melihat dua ukuran berbeda untuk dua jenis tugas
akan menyeragamkannya — dan penyeragaman itu justru kekeliruan yang D-03
Bagian 11 tolak dengan dua rujukan literatur.

**R-06 mengikuti pelajaran fitur 015.** Rentang yang tidak cocok diperbaiki
diam-diam adalah rentang yang menunjuk kata lain tanpa satu galat pun — bentuk
kegagalan yang sama dengan stemming yang menimpa permukaan.

**Pembetulan rujukan R-14 (13 Agustus 2026, AK-14, KB-051).** R-14 semula
menyebut *"D-03 Bagian 12"*. Ambangnya tidak ada di sana: Bagian 12 adalah
beban kerja dan jadwal; F1 longgar ≥ 0,80 dan Kappa kategori ≥ 0,70 berdiri
pada **Bagian 13**. Yang keliru rujukannya, bukan nilainya — dan itu sebabnya
ia lolos sampai audit: kode yang mengambil angkanya membaca Bagian 13 dengan
benar sementara spesifikasinya menunjuk halaman lain. Butir C-1 `tasks.md`
sudah menandainya saat implementasi dan tidak mengubah `spec.md` sendiri;
pembetulan ini menutup penandaan itu. Tercatat sebagai TK-55 pada `docs/D00.md`
Bagian 7.12.

**R-13 membangun pengendalian sebelum yang dikendalikannya ada.** Pra-anotasi
menunggu fitur 004, tetapi *automation bias* yang dikendalikannya muncul pada
hari pertama pra-anotasi dipakai. Menambahkan pengendalinya belakangan berarti
batch pertama berjalan tanpa pembanding.

## Keadaan yang wajib ditangani

| Keadaan | Perilaku yang dituntut |
|---|---|
| Berkas ekspor Label Studio bentuknya berubah | Gagal tegas saat diurai, bukan mengurai sebagian |
| Anotasi merujuk dokumen yang tidak ada | Ditolak; anotasi tanpa dokumen tidak dapat diperiksa siapa pun |
| Dua anotator, satu dokumen, versi skema berbeda | Ditolak dari perhitungan kesepakatan, dan ditandai — bukan dihitung seolah setara |
| Hanya satu anotator pada dokumen anotasi ganda | Kesepakatan tidak dihitung; dilaporkan sebagai kurang bahan, bukan sebagai kesepakatan sempurna |
| Batch tanpa satu pun anotasi ganda | Kesepakatan dilaporkan **belum dapat dihitung**, bukan nol dan bukan satu |

Baris terakhir sengaja ada. Kesepakatan yang dilaporkan 1,0 karena tidak ada
yang dibandingkan adalah angka yang akan masuk naskah sebagai bukti mutu.
Bentuk yang sama dengan `terperiksa` pada pemeriksa ketergantungan sistem
fitur 015, dan dengan "belum dapat diperiksa" pada `make compliance`.

## Kriteria penerimaan

- [ ] R-01 s.d. R-16 masing-masing punya uji yang gagal sebelum implementasi
- [ ] Uji bahwa rentang yang tidak cocok ditolak, bukan diperbaiki (R-06)
- [ ] **Uji bahwa Cohen's Kappa tidak dipakai bagi anotasi rentang** (R-08) — dinyatakan sebagai sifat modul, bukan sebagai satu pemanggilan
- [ ] Uji bahwa uraian modul menyebut alasannya beserta rujukannya (R-09)
- [ ] Uji bahwa batch tanpa anotasi ganda dilaporkan belum dapat dihitung
- [ ] Perhitungan Kappa dan F1 diuji terhadap **contoh yang dihitung tangan**, bukan terhadap keluaran dirinya sendiri
- [ ] Nol ketergantungan Python baru (C-12, KB-020)
- [ ] Cakupan uji tidak turun (C-11)
- [ ] `make compliance` tidak berubah — fitur ini tidak memindahkan pasal mana pun

## Keputusan Gerbang 1

Bentuk berkas ekspor Label Studio 1.23 belum diperiksa langsung, dan ADR-08
menyebut dua kemungkinan tanpa memutuskan: bidang `versi_skema`, `bendera`,
dan `status_pra_anotasi` dibawa Label Studio sendiri, atau ditambahkan pada
tahap ekspor.

**Keputusan: fitur ini dibangun dalam dua bagian yang dipisahkan tegas**
(KB-021).

| | Bagian | Menunggu bahan? |
|---|---|---|
| **1** | Perhitungan — Kappa, F1 berpasangan, uji kualifikasi, skema berversi | **Tidak.** Aturannya lengkap pada D-03 |
| **2** | Pembacaan ekspor — pemetaan bidang, penandaan pra-anotasi | **Ya.** Menunggu satu contoh ekspor sungguhan |

Yang menentukan pemisahan ini: **bagian 1 tidak menyentuh bentuk data Label
Studio sama sekali.** Ia bekerja atas tipe milik kita sendiri, dan pemetaan
dari bentuk ekspor ke tipe itu adalah pekerjaan bagian 2. Membangunnya
terbalik akan membuat tipe kita menyerupai bentuk ekspor — dan bentuk ekspor
milik perangkat yang versinya dapat berubah tanpa kita.

**Bagian 2 tidak dimulai sebelum satu contoh ekspor sungguhan ada pada
`tests/bahan/`.** Menebaknya dari dokumentasi sudah dua kali terbukti keliru
pada fitur 015 — `paragraph.text` python-docx bukan teks final, dan XLSX
tidak menyimpan hasil hitungan rumusnya. Keduanya baru ketahuan saat bahan
uji sungguhan dibuat.

Bila contoh ekspornya tidak dapat diperoleh pada siklus ini, bagian 1 tetap
selesai dan bagian 2 menjadi butir terbuka — sama dengan pola yang KB-018
tetapkan bagi OCR.
