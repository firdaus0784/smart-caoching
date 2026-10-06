# Dokumentasi Teknis — Sistem Smart-Coaching Adaptif Berbasis NLP

| | |
|---|---|
| Komponen Berkas HKI | **#4 Dokumentasi teknis** — `docs/D10.md` Bagian 10A, `logbook/L10-berkas-hki.md` |
| Sumber bahan | `docs/D04.md` versi 0.8 (arsitektur) · `docs/D07.md` versi 0.3 (spesifikasi RAG) |
| Keadaan kode yang digambarkan | Commit `8790ce2`, 29 September 2026; Bagian 3, 8, dan 9 dimutakhirkan atas fitur 028 (T-9). Sebelumnya commit `8737068`, 28 September 2026, atas fitur 027. Sebelumnya commit `9c0b138`, 25 September 2026, atas TK-63 dan TK-64 |
| Status | **KERANGKA — menunggu tinjauan ketua peneliti** |
| Disusun oleh | Agen pengembang, atas perintah pemegang Gerbang 1–4 |

---

## Cara membaca dokumen ini

Dokumen ini akan dibaca pihak di luar tim. Karena itu **setiap komponen
diberi penanda keadaan**, dan penandanya diperiksa terhadap kode — bukan
disalin dari rencana:

| Penanda | Arti |
|---|---|
| **Terbangun** | Kode ada, diuji, dan lolos Gerbang 4 |
| **Sebagian** | Sebagian kode ada; bagian yang belum disebut pada barisnya |
| **Dirancang** | Ditetapkan pada D-04 atau D-07, **belum ada kode** |

Menyatakan komponen yang baru dirancang sebagai sudah terbangun adalah
pernyataan keliru kepada pihak luar. Penanda ini ada untuk mencegahnya.

Dokumen ini **tidak memuat nama orang**. Identitas pencipta dan pernyataan
kepemilikan adalah komponen #7, dan ditulis ketua peneliti.

---

## 1. Ringkasan teknis

Sistem pendamping (*coaching*) bagi kepala sekolah dasar yang menjawab
pertanyaan manajerial dengan **jawaban bersitasi**: setiap klaim yang
ditampilkan wajib merujuk segmen dokumen yang benar-benar diambil sistem, dan
kewajiban itu ditegakkan kode, bukan diserahkan kepada kepatuhan model bahasa.
Sumber: D-04 Bagian 1, D-07 Bagian 1.

Tiga ciri teknis yang membedakannya — **perumusan kebaruan resmi tetap
komponen #2 dan milik ketua peneliti**; yang di bawah ini hanya bahan:

1. **Validator sitasi di lapisan layanan** (ADR-04). Jawaban yang klaimnya
   tidak dapat ditelusuri ke segmen yang diambil dibuang sebelum sampai ke
   pengguna, apa pun isi keluaran model.
2. **Pemisahan indeks berdasarkan lisensi pada tingkat penyimpanan** (C-02,
   D-07 Bagian 3.1). Segmen berlisensi tertutup tidak dapat masuk konteks
   model karena kredensial pemanggil model tidak menjangkau indeksnya —
   ditolak peladen basis data, bukan disaring kueri.
3. **Gerbang anonimisasi dengan pemisahan kredensial** (ADR-06, C-03). Layanan
   penjawaban tidak memiliki akses ke area karantina sama sekali.

---

## 2. Penggerak dan prinsip arsitektur

Sumber: D-04 Bagian 2 dan 3.

| Kode | Penggerak | Akibat pada rancangan |
|---|---|---|
| PA-01 | Sitasi wajib, tanpa kecuali | Penegakan di lapisan layanan, bukan instruksi ke model |
| PA-02 | Data pribadi dalam dokumen sekolah | Anonimisasi menjadi gerbang wajib |
| PA-03 | Waktu dan tenaga terbatas | Komponen matang; satu bahasa di sisi belakang |
| PA-04 | Jaringan pengguna tidak stabil | Muatan ringan, tahan koneksi terputus |
| PA-05 | Kedaulatan data penelitian | Telemetri disimpan sendiri; kunci pseudonim terpisah |
| PA-06 | Kesiapan lapisan 2027–2028 | Titik sisip, bukan fitur setengah jadi |

Tujuh prinsip (AP-01 s.d. AP-07). Yang paling menentukan bentuk kode:
**AP-01 — aturan yang penting ditegakkan kode, bukan kebijakan.**

---

## 3. Wadah sistem

Sumber: D-04 Bagian 5. Kolom keadaan diperiksa terhadap commit `9c0b138`.

| Wadah | Teknologi | Keadaan | Keterangan |
|---|---|---|---|
| Aplikasi web | React + TypeScript, PWA | **Sebagian** | Layar Tanya (S-09) terbangun beserta keadaan memuat, kosong, galat, luring, dan tidak-ditemukan; draf pertanyaan bertahan saat koneksi putus; cangkang dapat terbuka tanpa koneksi; kebijakan keamanan konten membatasi seluruh sumber ke asal sendiri (fitur 027, lolos Gerbang 4 pada 28 September 2026). Riwayat percakapan tersambung (fitur 028). Layar S-01 Masuk dan tombol Keluar terbangun (fitur 029, lolos Gerbang 4 pada 4 Oktober 2026). Layar lain belum (fitur 013). Alur aktivasi J1 — persetujuan penelitian (S-02), pengenalan empat layar (S-03), profil dan prioritas (S-04) — terbangun (fitur 030, lolos Gerbang 4 pada 5 Oktober 2026); naskah persetujuan menunggu ET-02. Beranda (S-05) dan detail butir (S-06) dengan salinan luring, navigasi Beranda · Tanya, beserta layar kurator S-15 dan S-16 terbangun (fitur 013, lolos Gerbang 4 pada 5 Oktober 2026). Pengaturan (S-14) — sunting profil dan prioritas, persetujuan, dan penarikan data dengan konfirmasi dua pilihan setara — terbangun (fitur 033, lolos Gerbang 4 pada 6 Oktober 2026) |
| Panel internal | React | **Sebagian** | Antrean kurasi (S-15) dan penyuntingan butir (S-16) terbangun dalam aplikasi yang sama, dikenali dari peran akun (fitur 013, lolos Gerbang 4 pada 5 Oktober 2026); analitik penelitian (S-18) terbangun (fitur 035, **menunggu Gerbang 4**); aduan (S-17) belum (baris 036) |
| Layanan API | FastAPI | **Sebagian** | Rute `/api/v1/tanya` terbangun (fitur 021, 023). Riwayat percakapan kini tercatat dan tersaring pemilik berpseudonim; pertanyaan berdata pribadi ditolak sebelum dijawab; galat berbentuk D-14 Bagian 4.2 (fitur 028, lolos Gerbang 4 pada 1 Oktober 2026). Autentikasi terbangun (FR-A01, fitur 029, lolos Gerbang 4 pada 4 Oktober 2026): akun berpseudonim buatan tim, sandi `scrypt`, sesi di peladen yang dapat dicabut, kuki `HttpOnly`/`Secure`/`SameSite=Strict`; tanpa sesi sah setiap rute menjawab 401. Rute `/saya/profil`, `/saya/prioritas`, `/saya/persetujuan` terbangun (fitur 030, lolos Gerbang 4 pada 5 Oktober 2026). Rute beranda, detail butir, belum relevan, antrean kurasi, putusan, dan penarikan terbangun (fitur 013, lolos Gerbang 4 pada 5 Oktober 2026); kandidat hanya masuk lewat perkakas tim — sampai lapis relevansi L4 berjalan, kurator menjadi penyaringnya dalam batas pagu harian (TK-72 B). Peristiwa penelitian direkam pada rute yang sudah ada — sesi, Tanya, beranda, butir — hanya bagi pengguna yang menyetujui, dibaca ulang setiap permintaan sehingga pencabutan berlaku seketika; teks pengguna tersimpan sebagai ukurannya saja (fitur 034, lolos Gerbang 4 pada 6 Oktober 2026). Penarikan data (NFR-09): rute mencatat permintaan dan mencabut seluruh sesi seketika; penghapusan keras atas sepuluh tabel dijalankan perkakas tim dengan peran yang tidak dipegang layanan aplikasi (fitur 033, lolos Gerbang 4 pada 6 Oktober 2026). Analitik penelitian: ringkasan metrik D-01 Bagian 9.1 dihitung saat diminta — keaktifan, retensi berkohort, panjang sesi, rasio penemuan, metrik yang belum terukur beserta sebabnya — dan ekspor berkas berjejak (fitur 035, **menunggu Gerbang 4**) |
| Layanan NLP | Python | **Sebagian** | Praproses, OCR, dan deteksi data pribadi berpola terbangun (fitur 015); **model NER dan klasifikasi belum** (fitur 017) |
| Layanan RAG | Python | **Sebagian** | Lihat Bagian 4 |
| Pekerja latar | Python | **Sebagian** | Ingesti kanal dan penyematan korpus ada sebagai fungsi (fitur 002, 010, 026); **antrean tugas dan penjadwal belum** |
| Basis data | PostgreSQL 16 + pgvector 0.6.0 | **Terbangun** | Lima peran basis data, skema terpisah per area dan per indeks (fitur 024, 019, 026). Peran keenam `peran_riwayat` — hanya membaca dan menambah riwayat — dibangun fitur 028, lolos Gerbang 4 pada 1 Oktober 2026. Peran ketujuh dan kedelapan — `peran_autentikasi` dan `peran_pengelola_akun`, dipisah dengan hak per kolom — dibangun fitur 029, lolos Gerbang 4 pada 4 Oktober 2026. Peran kesembilan `peran_pengguna` — profil, prioritas tambah-saja, persetujuan yang hanya dapat dicabut — dibangun fitur 030, lolos Gerbang 4 pada 5 Oktober 2026. Peran kesepuluh sampai kedua belas — `peran_kurasi`, `peran_penayangan`, `peran_pengisi_antrean` — dibangun fitur 013, lolos Gerbang 4 pada 5 Oktober 2026; butir tayang hanya dapat merujuk putusan yang menyetujuinya, ditegakkan kunci asing. Peran ketiga belas `peran_telemetri` — hanya menambah dan membaca peristiwa, tanpa jalur ke basis data pseudonim — dibangun fitur 034, lolos Gerbang 4 pada 6 Oktober 2026. Peran keempat belas dan kelima belas — `peran_penarikan` pada basis data perilaku dan `peran_penarikan_pseudonim` pada basis data pseudonim, satu-satunya pemegang hapus, di luar layanan aplikasi — dibangun fitur 033, lolos Gerbang 4 pada 6 Oktober 2026. Peran keenam belas `peran_analitik` — membaca peristiwa dan menambah jejak ekspor, tanpa jangkauan akun maupun basis data pseudonim — dibangun fitur 035, **menunggu Gerbang 4** |
| Penyimpanan berkas | Sistem berkas, area karantina terpisah | **Sebagian** | Pemisahan area karantina dan korpus terbangun **pada basis data**; penyimpanan berkas asli pada sistem berkas belum |
| Perangkat anotasi | Label Studio, dipasang mandiri | **Sebagian** | Pembacaan ekspor terbangun (fitur 016); pemasangan perangkatnya pekerjaan operasi |

---

## 4. Alur pengambilan dan penjawaban

Sumber: D-07 Bagian 4. Sepuluh tahap; keadaan tiap tahap:

| Tahap | Isi | Keadaan | Keterangan |
|---|---|---|---|
| 1 | Pemeriksaan cakupan domain | **Terbangun** | Pertanyaan di luar domain ditolak sebelum pengambilan (fitur 009) |
| 2 | Pencocokan jawaban terkurasi | **Dirancang** | Tidak ditemukan pada jalur penjawaban; isinya pekerjaan kurator |
| 3 | Klasifikasi K1–K8 dan ekstraksi entitas | **Dirancang** | Menuntut model fitur 017 |
| 4 | Pengambilan hibrida BM25 + vektor | **Sebagian** | Kedua sumber terbangun dan diuji atas PostgreSQL; **bobot model penyemat sungguhan belum dipasang** — sisi vektor berjalan dengan penyemat tiruan |
| 5 | Penggabungan dan pemeringkatan ulang | **Terbangun** | *Reciprocal Rank Fusion*; tanpa model pemeringkat ulang, jalur mundur BT-30 **menyatakan dirinya** pada keluaran |
| 6 | Pemeriksaan keberlakuan regulasi | **Terbangun** | Regulasi berstatus dicabut tidak dipakai (C-07) |
| 7 | Penilaian kecukupan bukti | **Sebagian** | Logikanya terbangun; **ambangnya belum dikalibrasi** dan sengaja tidak diisi (C-16, fitur 025) |
| 8 | Penyusunan jawaban oleh model bahasa | **Sebagian** | Pembungkus tunggal dan pencatatan versi terbangun (ADR-11); **adaptor penyedia sungguhan belum** (ADR-12) |
| 9 | Validator sitasi | **Sebagian** | Enam dari sembilan pemeriksaan — lihat Bagian 5 |
| 10 | Penyajian | **Sebagian** | Bentuk tanggapan D-14 terbangun; layar Tanya menampilkannya dengan penanda dasar rujukan sebelum isi (fitur 027, lolos Gerbang 4) |

---

## 5. Validator sitasi

Sumber: D-07 Bagian 6.

| Kode | Pemeriksaan | Keadaan |
|---|---|---|
| VS-01 | Setiap klaim memiliki minimal satu rujukan segmen | **Terbangun** |
| VS-02 | Setiap rujukan ada di antara segmen yang diambil | **Terbangun** |
| VS-03 | Isi klaim didukung segmen yang dirujuk (kemiripan semantik) | **Dirancang** — menunggu bobot model dan kalibrasi |
| VS-04 | Tidak ada segmen indeks metadata sebagai dasar klaim | **Terbangun** |
| VS-05 | Tidak ada kalimat yang menyalin segmen melebihi batas | **Dirancang** — menunggu kalibrasi |
| VS-06 | Tidak ada segmen regulasi berstatus dicabut | **Terbangun** |
| VS-07 | Tidak ada nama perorangan dalam keluaran | **Dirancang** — menunggu model NER |
| VS-08 | Tidak ada klaim bersandar tunggal pada segmen T3 atau T4 | **Terbangun** |
| VS-09 | Keluaran memenuhi kontrak; tanpa instruksi atau tautan asing | **Terbangun** |

Ketiga pemeriksaan yang belum berjalan **tidak dianggap lulus**. Keadaannya
dilaporkan sebagai *belum dapat diperiksa* pada setiap tanggapan, sehingga
jawaban yang memuatnya tidak dapat terbaca sebagai tervalidasi penuh.

---

## 6. Keputusan arsitektur

Sumber: D-04 Bagian 8. Ringkasan satu baris; alasan lengkap ada pada D-04.

| ADR | Keputusan |
|---|---|
| ADR-01 | Model praterlatih Bahasa Indonesia untuk NER dan klasifikasi |
| ADR-02 | Model bahasa melalui API untuk penyusunan jawaban |
| ADR-03 | Pengambilan hibrida BM25 dan vektor |
| ADR-04 | Penegakan sitasi sebagai validator di lapisan layanan |
| ADR-05 | PostgreSQL tunggal dengan pgvector |
| ADR-06 | Anonimisasi sebagai gerbang dengan pemisahan penyimpanan |
| ADR-07 | Telemetri penelitian disimpan sendiri |
| ADR-08 | Label Studio dipasang mandiri untuk anotasi |
| ADR-09 | Aplikasi web progresif, bukan aplikasi *native* |
| ADR-10 | Satu repositori dan penyebaran terkontainerisasi sederhana |
| ADR-11 | Lapisan pembungkus tunggal untuk seluruh pemanggilan model |
| ADR-12 | Antarmuka abstrak dengan adaptor tiruan, tanpa penyedia konkret |
| ADR-13 | Permintaan berbentuk objek; konstruksi instruksi terkunci satu modul |

---

## 7. Keamanan dan privasi

Sumber: D-04 Bagian 10, `constitution.md`.

Sembilan belas dari dua puluh pasal konstitusi **diperiksa mesin** pada
setiap pemeriksaan mutu (`make compliance`). Pasal yang tersisa, C-01, belum
dapat diperiksa sebab menuntut VS-03.

Pemisahan yang **ditolak peladen basis data**, bukan hanya oleh kode
aplikasi — dibuktikan dengan uji yang menjalankan kueri terlarang dan
menuntut penolakan:

| Pemisahan | Pasal |
|---|---|
| Pemanggil model tidak menjangkau indeks metadata | C-02 |
| Layanan penjawaban tidak menjangkau area karantina | C-03 |
| Kunci pseudonim pada basis data terpisah, tidak terjangkau layanan aplikasi | C-05 |
| Jalur penjawaban tanpa hak tulis, termasuk hak tulis indeks | C-17 |
| Jalur penyematan menulis dua kolom vektor saja; tidak menjangkau korpus, karantina, maupun basis data pseudonim | C-03, C-05 |
| Peristiwa telemetri tambah-saja: tanpa hak ubah, hapus, maupun kosongkan; tanpa jangkauan skema lain dan basis data pseudonim (fitur 034) | C-04, C-05 |
| Hapus atas data pengguna hanya oleh dua peran perkakas penarikan, yang masing-masing tidak menjangkau basis data lainnya; bukti permintaan tidak dapat dihapus siapa pun (fitur 033) | C-05, C-17 |
| Peran analitik membaca peristiwa tanpa jangkauan akun, sehingga pemegang ekspor tidak dapat menautkan pseudonim ke akun; setiap ekspor tercatat tambah-saja (fitur 035) | C-05 |

Setiap peran juga diuji **berjalan** dengan haknya sendiri, bukan hanya
ditolak: pencarian vektor dan penyematan korpus masing-masing dijalankan
tersambung sebagai peran produksinya (TK-63, TK-64).

---

## 8. Mutu dan verifikasi

| Ukuran | Keadaan commit `6e16673` |
|---|---|
| Gerbang verifikasi V-01 s.d. V-06 | Lulus seluruhnya |
| Pasal konstitusi terperiksa mesin | 19 lulus, 0 gagal, 1 belum dapat diperiksa |
| Jumlah uji otomatis | 3.043 pada backend dan perkakas; 276 pada aplikasi web |
| Fitur lolos Gerbang 4 | 28 dari 36 (fitur 035 menunggu Gerbang 4) |
| Anggaran muat aplikasi web | 87.076 bait terkompresi dari batas 153.600 — batas **penetapan tim tanpa dasar literatur**, wajib diverifikasi di lokus pilot |

Setiap fitur melewati empat gerbang persetujuan manusia (spesifikasi,
rancangan, daftar tugas, verifikasi) dan uji mutasi yang dilaporkan apa
adanya, termasuk mutasi yang tidak menyala beserta sebabnya. Riwayat
keputusannya tercatat pada `logbook/L4-keputusan.md` secara tambah-saja.

---

## 9. Yang belum terbangun

Dinyatakan terpisah agar tidak tersamar di antara tabel di atas.

| Hal | Menunggu |
|---|---|
| Penerapan J4, koleksi dan pembaca sumber | Baris 031, 032 (KB-178) |
| Penilaian jawaban dan aduan kurator | Baris 036 (KB-215, TK-77) |
| Ekspor Parquet | Persetujuan paket `pyarrow` (C-12) |
| Penyaring relevansi otomatis L4 | Model klasifikasi (fitur 017) dan ambang BT-24; sementara itu kurator yang menyaring (TK-72 B) |
| Model NER dan klasifikasi | Korpus teranotasi dan izin etik ET-01 (fitur 017) |
| Isi ontologi | Putusan putaran pengisian (fitur 018) |
| VS-03, VS-05, VS-07 | Bobot model dan kalibrasi (fitur 020) |
| Ambang kecukupan bukti dan validator | *Gold set* BT-35 (fitur 025) |
| Adaptor penyedia model sungguhan | Keputusan penyedia (ADR-12) |
| Peristiwa yang hanya teramati peramban — lama baca, sitasi dibuka — sehingga rasio penuntasan belum terhitung | Putusan rute penerima peristiwa (TK-73) |

---

## 10. Yang perlu diputuskan ketua peneliti sebelum dokumen ini final

1. **Cakupan yang didaftarkan.** Apakah pendaftaran mencakup rancangan
   seutuhnya (termasuk yang berpenanda *Dirancang*), atau hanya yang
   berpenanda *Terbangun* dan *Sebagian* pada saat pendaftaran?
2. **Nama ciptaan** sebagaimana akan tercantum pada formulir.
3. **Diagram.** D-04 Bagian 5 merujuk diagram wadah yang tidak ada pada
   repositori. Diagram perlu dibuat sebelum dokumen ini final.
4. **Pemutakhiran penanda keadaan** tepat sebelum pengajuan — penanda di atas
   berlaku untuk commit `8790ce2` dan akan usang begitu fitur berikutnya
   selesai.
