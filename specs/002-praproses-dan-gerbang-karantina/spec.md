# Spec: 002-praproses-dan-gerbang-karantina

| | |
|---|---|
| Kebutuhan | FR-B05, FR-B06, FR-B07, FR-B08, FR-B09 · FR-B01 s.d. FR-B04 diusulkan ditunda, lihat Di luar cakupan |
| Dokumen terkait | D-01 Modul B · D-04 ADR-06, ADR-12 · D-13 KD-01, KD-02, KD-08, KD-10, Bagian 6 · D-03 Bagian 12.6 |
| Pasal konstitusi yang menyentuh fitur ini | **C-03**, C-05, C-08, C-09, C-11, C-12, C-19 |
| Urutan pembangunan | 002 pada `docs/D12.md` Bagian 7 |
| Status | Menunggu Gerbang 1 |

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

- **FR-B01, FR-B02, FR-B03, FR-B04 diusulkan ditunda ke fitur tersendiri.**
  Keempatnya — pembacaan PDF/DOCX/XLSX, OCR, praproses Bahasa Indonesia, dan
  pendeteksi data pribadi — **masing-masing menuntut ketergantungan baru**,
  sehingga seluruhnya tertahan C-12 sampai penanggung jawab teknis menyetujui
  daftarnya. Menggabungkannya ke sini membuat fitur yang seluruh intinya dapat
  dibangun hari ini menunggu persetujuan yang belum diajukan. Ini pertanyaan
  Gerbang 1 nomor 1.
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
| R-01 | Layanan yang berperan sebagai jalur penjawaban **TIDAK BOLEH** memiliki kredensial yang dapat membaca area karantina. Pemisahan pada tingkat kredensial, bukan pada penyaringan kueri (C-03, ADR-06) |
| R-02 | **JIKA** layanan jalur penjawaban mencoba membaca area karantina, **MAKA** sistem **HARUS** menolak dan mencatat percobaannya |
| R-03 | **KETIKA** sebuah dokumen diunggah, sistem **HARUS** menempatkannya di area karantina, dan bukan di korpus |
| R-04 | Dokumen **TIDAK BOLEH** berpindah dari karantina ke korpus tanpa persetujuan seorang verifikator manusia yang tercatat (FR-B05, KD-02) |
| R-05 | **KETIKA** verifikator menolak sebuah dokumen, sistem **HARUS** menahannya di karantina beserta alasan penolakannya (FR-B07) |
| R-06 | Setiap dokumen **HARUS** membawa metadata asal: jenis, tahun, unit penerbit, tingkat kerahasiaan, status persetujuan pemilik (FR-B06) |
| R-07 | Setiap segmen **HARUS** membawa peringkat kepercayaan asal T1 s.d. T4, ditetapkan dari jenis sumbernya menurut D-13 Bagian 6 (FR-B09, KD-08) |
| R-08 | Peringkat kepercayaan **TIDAK BOLEH** dapat diubah oleh jalur penjawaban — ia ditetapkan saat masuk dan dibaca saja sesudahnya |
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

- [ ] R-01 s.d. R-12 masing-masing punya uji yang gagal sebelum implementasi
- [ ] **C-03 punya uji tersendiri**, dan `make compliance` berpindah dari
      "belum dapat diperiksa" menjadi "lulus" untuk pasal itu
- [ ] Daftar tagihan `make compliance` menyusut dari 13 menjadi 12
- [ ] Uji mutasi: pemisahan kredensial dilanggar secara buatan → `make check` gagal
- [ ] Tidak ada ketergantungan baru (C-12)
- [ ] Cakupan uji tidak turun (C-11)
- [ ] Setiap keluaran percobaan mencatat versi ke `logbook/` (C-09)

## Pertanyaan terbuka

Fitur ini **belum dapat diserahkan ke agen** sampai ketiganya dijawab.

1. **Apakah FR-B01 s.d. FR-B04 dipisahkan menjadi fitur tersendiri?**
   Rekomendasi: ya. Keempatnya tertahan C-12, dan menahan inti fitur bersamanya
   berarti tidak ada yang bergerak. Bila dijawab tidak, daftar ketergantungan
   wajib diajukan dan disetujui sebelum `plan.md` disusun.

2. **Berapa peran kredensial yang dibangun?** Sekurang-kurangnya dua: jalur
   penjawaban dan jalur verifikasi. D-13 KD-10 menyiratkan yang ketiga —
   layanan pemanggil LLM tanpa akses tulis, tanpa akses karantina, tanpa akses
   kunci pseudonim. Menjadikannya dua atau tiga adalah keputusan rancangan yang
   tidak boleh diambil diam-diam saat menulis kode, sebagaimana BT-14 pada
   fitur 001.

3. **Apakah peringkat T1 s.d. T4 ditetapkan otomatis dari jenis sumber, atau
   memerlukan penegasan manusia?** D-13 Bagian 6 memetakan peringkat ke asal,
   sehingga penetapan otomatis mungkin. Tetapi T3 mencakup "dokumen sekolah
   teranonimkan **dan terverifikasi**", dan kata kedua itu adalah keputusan
   manusia — sehingga peringkat tidak dapat sepenuhnya ditetapkan sebelum
   gerbang R-04 dilewati. Urutannya perlu ditegaskan.

Empat temuan AK-12 yang berbahan — TK-40, TK-41, TK-42, TK-47 — tidak
menghambat fitur ini. TK-41 menyentuhnya hanya pada bagian penjadwalan, yang
berada di luar cakupan.
