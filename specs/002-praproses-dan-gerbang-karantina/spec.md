# Spec: 002-praproses-dan-gerbang-karantina

| | |
|---|---|
| Kebutuhan | FR-B05, FR-B06, FR-B07, FR-B08, FR-B09 · FR-B01 s.d. FR-B04 dipindahkan ke fitur 015 |
| Dokumen terkait | D-01 Modul B · D-04 ADR-06, ADR-12 · D-13 KD-01, KD-02, KD-08, KD-10, Bagian 6 · D-03 Bagian 12.6 |
| Pasal konstitusi yang menyentuh fitur ini | **C-03**, C-05, C-08, C-09, C-11, C-12, C-19 |
| Urutan pembangunan | 002 pada `docs/D12.md` Bagian 7 |
| Status | **Lolos Gerbang 1** — 5 Agustus 2026. Menunggu `plan.md` dan Gerbang 2 |

## Tujuan

Setelah fitur ini ada, sebuah dokumen tidak dapat berpindah dari area karantina
ke korpus tanpa seorang manusia menyetujuinya, dan **layanan RAG tidak memiliki
kredensial untuk membaca area karantina sama sekali** — bukan tidak boleh,
melainkan tidak bisa.

Ini yang membedakan C-03 dari penandaan status. ADR-06 menolak penandaan status
dengan alasan yang tegas: satu kekeliruan kueri meloloskan dokumen mentah. Yang
dibangun di sini adalah ketidakmampuan, bukan larangan.

Fitur ini juga memberi setiap segmen **peringkat kepercayaan asal** (T1 s.d. T4,
D-13 Bagian 6). Tanpa peringkat itu, C-19 dan FR-F15 tidak punya bahan untuk
ditegakkan kelak pada fitur 008 — validator sitasi akan memeriksa keberadaan
segmen tanpa dapat memeriksa kelayakannya.

## Mengapa fitur ini tidak lagi tertahan

KB-005 menunda fitur 002 karena TK-41: kapasitas verifikasi anonimisasi belum
pernah dihitung, dan merencanakan gerbang yang kapasitasnya tidak diketahui
mengulang kekeliruan yang D-06 Bagian 8 hindari untuk kurasi.

Keadaan itu sudah berubah. D-03 Bagian 12.6 memuat perhitungannya, dan yang
tersisa adalah **BT-62 dan BT-63** — keduanya pertanyaan penjadwalan dan volume,
bukan pertanyaan rancangan. Membedakannya penting:

| Bergantung pada BT-62/BT-63 | Tidak bergantung |
|---|---|
| Berapa dokumen yang dapat diverifikasi per minggu | Bahwa dokumen tak terverifikasi tidak dapat dibaca layanan RAG |
| Apakah volume KI-01 tercapai dalam Fase 2 | Bagaimana persetujuan verifikator dicatat dan tidak dapat dipalsukan |
| Berapa verifikator diperlukan | Bahwa penolakan mengembalikan dokumen ke karantina |

Kolom kanan adalah isi fitur ini. Menundanya sampai BT-62 diputus berarti
menunda pekerjaan yang tidak menunggu apa pun.

## Di luar cakupan

Batas ini yang menjaga fitur tetap dapat diselesaikan.

- **FR-B01, FR-B02, FR-B03, FR-B04 dibangun pada fitur 015**, diputuskan
  Gerbang 1. Keempatnya — pembacaan PDF/DOCX/XLSX, OCR, praproses Bahasa
  Indonesia, dan pendeteksi data pribadi — masing-masing menuntut
  ketergantungan baru, sehingga seluruhnya tertahan C-12 sampai penanggung
  jawab teknis menyetujui daftarnya.

  **Akibat yang wajib disadari:** tanpa FR-B04, fitur ini membangun gerbang
  bagi anonimisasi yang belum ada. Itu disengaja dan bukan cacat urutan —
  gerbanglah yang menentukan apa yang boleh lewat, dan membangunnya lebih dulu
  berarti pendeteksi data pribadi lahir ke dalam sistem yang sudah menahannya.
  Urutan sebaliknya menghasilkan pendeteksi yang keluarannya tidak ada yang
  memeriksa.
- **Basis data sungguhan.** Pemisahan kredensial dibangun terhadap antarmuka
  abstrak dengan penyimpan tiruan deterministik, mengikuti ADR-12 yang sudah
  terbukti pada fitur 001. Penyetelan PostgreSQL dan peran basis datanya adalah
  pekerjaan penyebaran (D-09), bukan pekerjaan fitur ini.
- **Antarmuka verifikator.** Layar S-xx untuk verifikasi belum ada pada D-05.
  Fitur ini menyediakan lapisan layanannya; layarnya menunggu D-05.
- **Menyetel ambang pendeteksi pola adversarial.** C-16 menetapkan ambang hanya
  disetel lewat prosedur kalibrasi. Fitur ini membangun mekanismenya dengan
  ambang yang dinyatakan sebagai nilai awal, bukan hasil kalibrasi.
- **Perbaikan dokumen apa pun.** Fitur ini kode.

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | Sistem **HARUS** memiliki tiga peran kredensial terpisah: jalur penjawaban, jalur verifikasi, dan pemanggil LLM. Pemisahan pada tingkat kredensial, bukan pada penanda status (C-03, ADR-06) |
| R-01a | Peran jalur penjawaban dan peran pemanggil LLM **TIDAK BOLEH** memiliki kredensial yang dapat membaca area karantina (KD-10) |
| R-01b | Peran pemanggil LLM **TIDAK BOLEH** memiliki akses tulis ke penyimpanan mana pun, dan **TIDAK BOLEH** menjangkau kunci pemetaan pseudonim (KD-10, NFR-21, C-05) |
| R-02 | **JIKA** layanan jalur penjawaban mencoba membaca area karantina, **MAKA** sistem **HARUS** menolak dan mencatat percobaannya |
| R-03 | **KETIKA** sebuah dokumen diunggah, sistem **HARUS** menempatkannya di area karantina, dan bukan di korpus |
| R-04 | Dokumen **TIDAK BOLEH** berpindah dari karantina ke korpus tanpa persetujuan seorang verifikator manusia yang tercatat (FR-B05, KD-02) |
| R-05 | **KETIKA** verifikator menolak sebuah dokumen, sistem **HARUS** menahannya di karantina beserta alasan penolakannya (FR-B07) |
| R-06 | Setiap dokumen **HARUS** membawa metadata asal: jenis, tahun, unit penerbit, tingkat kerahasiaan, status persetujuan pemilik (FR-B06) |
| R-07 | **KETIKA** sebuah dokumen masuk, sistem **HARUS** menetapkan peringkat kepercayaan asal T1 s.d. T4 dari jenis sumbernya menurut D-13 Bagian 6 (FR-B09, KD-08) |
| R-07a | **SELAMA** sebuah dokumen berada di karantina, peringkatnya **TIDAK BOLEH** terbaca oleh jalur penjawaban — peringkat T3 baru sah setelah gerbang R-04 dilewati, karena D-13 Bagian 6 mendefinisikan T3 sebagai dokumen sekolah teranonimkan **dan terverifikasi** |
| R-08 | Peringkat kepercayaan **TIDAK BOLEH** dapat diubah oleh jalur penjawaban maupun pemanggil LLM — ia ditetapkan saat masuk, disahkan oleh verifikasi, dan dibaca saja sesudahnya |
| R-09 | **KETIKA** sebuah dokumen diperiksa pola instruksi adversarial dan ditemukan pola, sistem **HARUS** menahannya untuk ditinjau manusia, bukan sekadar mencatatnya (FR-B08, KD-01) |
| R-10 | **JIKA** pemeriksa pola adversarial gagal berjalan, **MAKA** dokumen **HARUS** ditahan, bukan diloloskan |
| R-11 | Setiap perpindahan dokumen antar-area **HARUS** tercatat: siapa, kapan, dari mana ke mana, dengan alasannya |
| R-12 | Catatan pada R-11 **TIDAK BOLEH** memuat data pribadi dari isi dokumen |

R-10 mengikuti pelajaran yang berulang sepanjang fitur 001: pemeriksa yang gagal
lalu diperlakukan sebagai lulus adalah laporan palsu, dan laporan palsu
menghentikan kewaspadaan. Di sini akibatnya bukan gerbang yang keliru lulus
melainkan dokumen yang disusupi masuk korpus.

R-12 ada karena R-11 adalah tempat data pribadi paling mudah bocor tanpa
disadari: alasan penolakan verifikator secara alami berbunyi "memuat NIK pada
halaman 3", dan godaan menyalin potongannya besar.

## Keadaan yang wajib ditangani

**Tidak berlaku pada fitur ini.** Lapisan layanan tanpa antarmuka pengguna;
layar verifikator menunggu D-05.

## Kriteria penerimaan

- [ ] R-01 s.d. R-12, termasuk R-01a, R-01b, dan R-07a, masing-masing punya uji yang gagal sebelum implementasi
- [ ] **C-03 punya uji tersendiri**, dan `make compliance` berpindah dari
      "belum dapat diperiksa" menjadi "lulus" untuk pasal itu
- [ ] Daftar tagihan `make compliance` menyusut dari 13 menjadi 12
- [ ] Uji mutasi: pemisahan kredensial dilanggar secara buatan → `make check` gagal
- [ ] Uji tersendiri bahwa peringkat T3 tidak terbaca jalur penjawaban selama dokumen di karantina (R-07a)
- [ ] Tidak ada ketergantungan baru (C-12)
- [ ] Cakupan uji tidak turun (C-11)
- [ ] Setiap keluaran percobaan mencatat versi ke `logbook/` (C-09)

## Keputusan Gerbang 1

Ketiganya diputus 5 Agustus 2026 oleh pemegang Gerbang 1–4 (KB-001), dicatat
pada `logbook/L4` KB-010. **Tidak ada pertanyaan terbuka yang tersisa**, sehingga
fitur ini memenuhi syarat templat untuk diserahkan ke agen.

**1 · FR-B01 s.d. FR-B04 dipisah menjadi fitur 015.** Keempatnya tertahan C-12;
menahan inti fitur bersamanya berarti tidak ada yang bergerak. `docs/D12.md`
Bagian 7 bertambah satu baris.

**2 · Tiga peran kredensial**, bukan dua: jalur penjawaban, jalur verifikasi,
dan pemanggil LLM. D-13 KD-10 sudah menyebut peran ketiga secara tegas —
tanpa akses tulis, tanpa akses karantina, tanpa akses kunci pseudonim.
Menambahkannya belakangan berarti mengubah pemisahan yang sudah terpasang,
dan itu jenis perubahan yang paling mudah keliru. Membangunnya sekarang
sekaligus menyiapkan C-05 dan NFR-21 bagi fitur 012.

**3 · Peringkat ditetapkan saat masuk; T3 sah hanya setelah verifikasi.**
Peringkat ditetapkan dari jenis sumber sejak dokumen tiba, sehingga pemeriksa
pola adversarial punya sinyal asal justru pada tahap dokumen belum dipercaya.
Tetapi D-13 Bagian 6 mendefinisikan T3 sebagai dokumen sekolah teranonimkan
**dan terverifikasi**, dan kata kedua itu keputusan manusia — sehingga
peringkat dokumen di karantina tidak pernah terbaca jalur penjawaban.

Wujudnya pada R-01, R-01a, R-01b, R-07, R-07a, dan R-08.

## Yang tetap menunggu rapat tim

Tidak satu pun menghambat fitur ini.

- **BT-62 dan BT-66** — kekurangan anggaran waktu yang menyatu. Menyentuh
  penjadwalan verifikasi, bukan rancangan gerbangnya.
- **BT-63** — laju verifikasi anonimisasi dari batch kalibrasi.
- **BT-64** — arti `klaim[].peringkat_kepercayaan` pada tanggapan. Menyentuh
  fitur 008 dan 009; fitur ini hanya menetapkan peringkat pada segmen, bukan
  menampilkannya pada klaim.
