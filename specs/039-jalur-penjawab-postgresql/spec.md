# Spec: 039-jalur-penjawab-postgresql

| | |
|---|---|
| Kebutuhan | FR-F02, FR-F03, FR-F11, FR-F14, FR-D06; KL-01, KL-04, KL-07; C-02, C-07, C-16, C-17, C-19, C-20 |
| Dokumen terkait | D-07 Bagian 3.3, 4, 4.5, 4.6 · D-14 Bagian 4.1, 4.10, 5.1 · D-13 Bagian 6 · D-06 aturan pelaksanaan KL-01 · spec fitur 006, 007, 019, 021, 032, 038 · TK-81, TK-87 |
| Status | **Diajukan ke Gerbang 1** — 13 Oktober 2026 (KB-277) |

## Mengapa fitur ini diusulkan sekarang

Sejak fitur 038, segmen dokumen korpus terisi di kedua indeks dan terbaca
pembaca sumber. Jalur penjawab tidak memakainya. `make jalan` memasang
`PenjawabBelumSiap`, yang selalu menjawab tidak ditemukan, dan `Jalur`
(fitur 021) hanya dirakit di uji dengan bahan buatan. Tidak ada kode yang
memuat segmen dari PostgreSQL untuk pengambilan leksikal, yang menyusun bahan
validator dari catatan korpus, atau yang menyusun sitasi dari metadata dokumen.
Baris 039 disisipkan atas putusan pemegang gerbang (KB-275, KB-276).

## Yang tidak dapat diselesaikan fitur ini

Dinyatakan lebih dulu, agar cakupan tidak terbaca lebih besar dari
kenyataannya. **Sesudah fitur ini pun jalur penjawab belum menghasilkan satu
jawaban pun**, karena tiga hal di luar baris ini:

| Penghalang | Pemiliknya | Wujudnya pada kode |
|---|---|---|
| Ambang kecukupan bukti | Kalibrasi BT-29 atas *gold set* BT-35 (fitur 025) | `AmbangKecukupan` tidak dapat dibentuk tanpa catatan kalibrasi yang menyebut BT-29 |
| Model sematan dan model penjawab | Keputusan penyedia ADR-12 | Penggabungan menolak kurang dari dua sumber (ADR-03); sumber vektor menuntut penyemat sungguhan |
| VS-03, VS-05, VS-07 | Fitur 020 | Jawaban yang sah tetap berhenti sebagai `MENUNGGU_PEMERIKSAAN_MODEL` |

Fitur ini tidak menyentuh satu pun dari ketiganya, dan tidak membuat
pengganti sementara bagi satu pun (C-16).

## Temuan yang diajukan bersama usulan ini

**TK-87 · Daftar putih lisensi membaca awalan, bukan pengenal lisensi**
(D-00 Bagian 7.12, KB-276). `lisensi_dari_metadata` fitur 006 menganggap
terbuka setiap keterangan berawalan `cc-by`, sehingga `CC-BY-NC-ND 4.0`,
`CC-BY-NC 4.0`, dan `CC-BY-SA 4.0` masuk indeks utama — teksnya dikirim ke
model dan ditampilkan. Sebaliknya `CC BY 4.0` terbaca tertutup karena spasi.
Fitur 006 sudah lolos Gerbang 4; perubahannya ditanyakan pada P-6.

**Celah kontrak · Korpus tidak menyimpan tautan sumber asli.** D-14 Bagian
4.10 menyatakannya terang: *"korpus tidak menyimpannya"*. Kontrak `/tanya`
memuat `sitasi[].tautan` dan `bacaan_lanjutan[].tautan`, dan KL-04 mewajibkan
tautan ke sumber asli pada setiap tayangan. `BacaanLanjutan.tautan` wajib
berisi, sehingga tanpa tautan tidak satu bacaan lanjutan pun dapat disusun.
Ditanyakan pada P-5.

## Di luar cakupan

- Kalibrasi ambang, model sematan dan penjawab, VS-03/05/07 — lihat tabel di
  atas.
- Jawaban terkurasi tahap 2 (FR-F12) dan klasifikasi tahap 3 (fitur 017).
- Titik jalan penyebaran (D-09). `make jalan` tetap alat pengembangan.
- Rute baru dan bidang baru pada tanggapan `/tanya` (C-20).

## Kebutuhan (EARS) yang tidak bergantung pada pertanyaan

| ID | Kebutuhan |
|---|---|
| R-01 | Teks segmen yang dapat masuk konteks model **HARUS** dimuat dengan kredensial yang tidak menjangkau indeks metadata (`PEMANGGIL_LLM`, `peran_pemanggil_llm`) — C-02 pada tingkat sambungan, bukan penyaringan sesudah memuat |
| R-02 | Peringkat kepercayaan segmen **HARUS** diturunkan dari jenis pada catatan metadata korpus terbaru lewat `peringkat_bagi`, tidak disimpan pada segmen (P-4 A fitur 038, D-13 Bagian 6) |
| R-03 | Segmen regulasi berstatus `dicabut` **HARUS** dikeluarkan dari bahan penyusunan (D-07 Bagian 4.5, C-07); status `diubah` **HARUS** membawa rujukan penggantinya ke sitasi (FR-F14) |
| R-04 | Hanya segmen dokumen yang berada di korpus yang **BOLEH** dimuat; segmen yang dokumennya tidak lagi di korpus **TIDAK BOLEH** sampai ke bahan (C-03, TK-84) |
| R-05 | Pemuatan **TIDAK BOLEH** menulis apa pun (C-17), menambah rute, maupun mengubah bentuk `/tanya` (C-20) |
| R-06 | Versi indeks **HARUS** tercatat pada setiap tanggapan (RT-05); pemuatan ulang **HARUS** atomik — indeks lama melayani sampai yang baru siap (D-07 Bagian 3.3) |
| R-07 | Perakitan jalur **HARUS** menolak berjalan tanpa ambang berasal BT-29, penyemat, dan pembungkus model yang diserahkan pemanggil — tanpa nilai bawaan (C-16) |
| R-08 | Teks segmen **TIDAK BOLEH** ditulis ke log (KM-03) |

## Pertanyaan terbuka

Tiap pertanyaan disertai anjuran; anjuran bukan putusan.

**P-1 · Cakupan.**

| Pilihan | Arti |
|---|---|
| A | **Pemuat, bahan, perakit, dan perkakas pencarian.** Pemuat segmen dan catatan korpus dari PostgreSQL; bahan validator dan sitasi; perakit `Jalur` yang menuntut ambang, penyemat, dan pembungkus dari pemanggil. Titik jalan tetap `PenjawabBelumSiap` sampai BT-29 dan ADR-12. Ditambah perintah perkakas yang menjalankan **satu sumber leksikal** atas korpus dan mencetak dokumen, penanda, dan skor — tanpa teks, tanpa model, tanpa jawaban — sebagai bahan penyusunan *gold set* BT-35 |
| B | A tanpa perkakas pencarian |
| C | A, ditambah titik jalan memakai `Jalur` dengan ambang sementara dan model tiruan — bertentangan dengan C-16, disebut agar lengkap |
| D | Tunda seluruhnya sampai BT-29 dan ADR-12 diputus |

**Anjuran: A.** Aturan pemuatan — C-02 pada sambungan, tahap 6, keberlakuan,
peringkat — dapat diuji terhadap peladen sekarang, dan kalibrasi BT-29 sendiri
menuntut pengambilan atas korpus sungguhan. Perkakas satu sumber tidak
melanggar ADR-03: ia tidak menjawab, dan penggabungan hibrida tetap menolak
satu sumber. Tim dapat memeriksa apakah pasal yang semestinya ditemukan
memang ditemukan, sebelum *gold set* dibekukan.

**P-2 · Indeks leksikal.**

| Pilihan | Arti |
|---|---|
| A | **Dibangun di memori dari PostgreSQL**, satu per indeks tujuan, lewat praproses fitur 015 apa adanya. Versi indeks = sidik isi segmen yang dimuat; dibangun ulang bila sidiknya berubah, dan indeks lama melayani sampai yang baru siap |
| B | BM25 di PostgreSQL (`tsvector`) — praproses Bahasa Indonesia FR-B03 tidak berjalan di peladen, sehingga indeks dan kueri melewati dua jalur berbeda |
| C | Tabel indeks leksikal tersimpan, dibangun perintah `indeks` fitur 038 |

**Anjuran: A.** Praproses tetap satu tempat (FR-B03), dan sidik isi membuat
versi indeks deterministik: korpus yang sama, versi yang sama, tanpa tabel
nomor versi baru. Ukuran korpus pilot memungkinkannya; bila kelak tidak,
pilihan C dapat diajukan tanpa mengubah kontrak sumber.

**P-3 · Keberlakuan pada bahan.** Sitasi dan bahan validator menuntut status
keberlakuan; D-14 Bagian 5.1 menyatakan tanpa catatan berarti belum diketahui,
bukan `berlaku` (TK-81 A), sedangkan D-07 Bagian 4.5 hanya memeriksa segmen
regulasi.

| Pilihan | Arti |
|---|---|
| A | **Regulasi tanpa catatan status dan regulasi dicabut dikeluarkan dari bahan**; dokumen bukan regulasi bernilai `berlaku`, sebab keberlakuan hanya bermakna bagi regulasi (D-07 Bagian 4.5, KL-07). D-14 Bagian 5.1 dijelaskan lebih dulu |
| B | Setiap dokumen, regulasi atau bukan, wajib bercatatan status; tanpanya dikeluarkan |
| C | Regulasi tanpa status dianggap berlaku — ditolak TK-81 A, disebut agar lengkap |

**Anjuran: A.** Aturan yang sama dengan pembaca sumber fitur 032, yang hanya
menahan teks regulasi tanpa status. Pilihan B memaksa kurator mencatat status
pada artikel dan laporan, yang tidak pernah diubah atau dicabut.

**P-4 · Dokumen tidak publik dan dokumen sekolah.** Pembaca sumber tidak
menampilkan teks dokumen yang tingkat kerahasiaannya bukan `publik` atau yang
berjenis dokumen sekolah: cakupan persetujuan pemiliknya bagi penayangan
kepada peserta lain milik tim etik (ET-04). Jalur penjawab akan mengirim
teksnya ke model dan menayangkan parafrasenya.

| Pilihan | Arti |
|---|---|
| A | **Dikeluarkan dari bahan konteks**, aturan yang sama dengan pembaca sumber — satu tempat, dipakai keduanya — sampai ET-04 diputus |
| B | Dipakai bila lisensinya terbuka |

**Anjuran: A.** Parafrase tetap penayangan isi kepada peserta lain; aturan yang
berbeda di dua tempat membuat dokumen yang sama tertutup di pembaca sumber dan
terbuka di jawaban.

**P-5 · Tautan sumber asli (KL-04).**

| Pilihan | Arti |
|---|---|
| A | **Dicatat saat menerima** (`terima --tautan`, opsional), tersimpan pada penerimaan dan catatan metadata korpus, sama dengan lisensi pada fitur 038. Sitasi membawanya bila ada; dokumen indeks metadata tanpa tautan tidak menjadi bacaan lanjutan. D-14 ditulis lebih dulu |
| B | Tanpa tautan: `sitasi[].tautan` selalu kosong, bacaan lanjutan tidak pernah terisi |
| C | Tautan internal ke pembaca sumber — bukan sumber asli, tidak memenuhi KL-04 |

**Anjuran: A.** KL-04 menuntut jalan ke sumber yang sah, dan bacaan lanjutan
adalah satu-satunya tempat sumber indeks metadata (D-14 Bagian 4.1). Yang
paling tahu tautannya adalah pengunggah, saat berkasnya di tangan.

**P-6 · TK-87 — daftar putih lisensi.** Mengubah fitur 006, yang sudah lolos
Gerbang 4.

| Pilihan | Arti |
|---|---|
| A | **Pengenal dinormalisasi** (huruf, spasi, garis bawah, versi), lalu dicocokkan persis. Terbuka hanya CC0, CC BY tanpa tambahan, domain publik, PDDL, dan ODC-BY; **NC, ND, SA, dan selebihnya tertutup**. Segmen yang sudah terindeks dipindah lewat pengindeksan ulang perintah `indeks` |
| B | Seperti A, tetapi CC BY-SA terbuka |
| C | Hanya NC dan ND ditutup, tanpa normalisasi |

**Anjuran: A.** Aturan pelaksanaan KL-01 pada D-06: *"kekeliruan ke arah ini
hanya mengurangi jumlah butir, sedangkan kekeliruan ke arah sebaliknya
menggugurkan publikasi."* Jawaban model adalah turunan; ND melarangnya, NC
bergantung pada pemanfaatan hasil penelitian kelak, dan SA menuntut turunan
berlisensi sama — tiga hal yang bukan wewenang agen menilainya. Normalisasi
membuat `CC BY 4.0` terbaca seperti yang dimaksud penulisnya.

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | C-02; FR-D06; `PEMANGGIL_LLM` fitur 006 |
| R-02 | D-13 Bagian 6; P-4 A fitur 038; FR-F15 |
| R-03 | D-07 Bagian 4.5; C-07; FR-F14; KL-07 |
| R-04 | C-03; TK-84; fitur 037, 038 |
| R-05 | C-17; C-20 |
| R-06 | D-07 Bagian 3.3; RT-05 |
| R-07 | C-16; BT-29; ADR-12 |
| R-08 | KM-03 |

## Kriteria penerimaan

- [ ] P-1 s.d. P-6 diputus pada Gerbang 1
- [ ] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [ ] Pemuatan diuji terhadap peladen sebagai peran sungguhan, termasuk
      penolakan teks indeks metadata bagi pemuat konteks
- [ ] `make check` lulus enam gerbang
