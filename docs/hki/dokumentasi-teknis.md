# Dokumentasi Teknis — Sistem Smart-Coaching Adaptif Berbasis NLP

| | |
|---|---|
| Komponen Berkas HKI | **#4 Dokumentasi teknis** — `docs/D10.md` Bagian 10A, `logbook/L10-berkas-hki.md` |
| Sumber bahan | `docs/D04.md` versi 0.8 (arsitektur) · `docs/D07.md` versi 0.3 (spesifikasi RAG) |
| Keadaan kode yang digambarkan | Commit `9c0b138`, 25 September 2026; Bagian 3 dan 7 dimutakhirkan atas TK-63 dan TK-64 |
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
| Aplikasi web | React + TypeScript, PWA | **Dirancang** | Direktori `web/` belum berisi berkas (fitur 013) |
| Panel internal | React | **Dirancang** | Belum ada kode |
| Layanan API | FastAPI | **Sebagian** | Rute `/api/v1/tanya` dan riwayat percakapan terbangun (fitur 021, 023); **autentikasi belum ada** (FR-A01) |
| Layanan NLP | Python | **Sebagian** | Praproses, OCR, dan deteksi data pribadi berpola terbangun (fitur 015); **model NER dan klasifikasi belum** (fitur 017) |
| Layanan RAG | Python | **Sebagian** | Lihat Bagian 4 |
| Pekerja latar | Python | **Sebagian** | Ingesti kanal dan penyematan korpus ada sebagai fungsi (fitur 002, 010, 026); **antrean tugas dan penjadwal belum** |
| Basis data | PostgreSQL 16 + pgvector 0.6.0 | **Terbangun** | Lima peran basis data, skema terpisah per area dan per indeks (fitur 024, 019, 026) |
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
| 10 | Penyajian | **Sebagian** | Bentuk tanggapan D-14 terbangun; tampilan menunggu `web/` |

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

Setiap peran juga diuji **berjalan** dengan haknya sendiri, bukan hanya
ditolak: pencarian vektor dan penyematan korpus masing-masing dijalankan
tersambung sebagai peran produksinya (TK-63, TK-64).

---

## 8. Mutu dan verifikasi

| Ukuran | Keadaan commit `9c0b138` |
|---|---|
| Gerbang verifikasi V-01 s.d. V-06 | Lulus seluruhnya |
| Pasal konstitusi terperiksa mesin | 19 lulus, 0 gagal, 1 belum dapat diperiksa |
| Jumlah uji otomatis | 2.176 |
| Fitur lolos Gerbang 4 | 21 dari 26 |

Setiap fitur melewati empat gerbang persetujuan manusia (spesifikasi,
rancangan, daftar tugas, verifikasi) dan uji mutasi yang dilaporkan apa
adanya, termasuk mutasi yang tidak menyala beserta sebabnya. Riwayat
keputusannya tercatat pada `logbook/L4-keputusan.md` secara tambah-saja.

---

## 9. Yang belum terbangun

Dinyatakan terpisah agar tidak tersamar di antara tabel di atas.

| Hal | Menunggu |
|---|---|
| Antarmuka pengguna dan panel internal | Tim antarmuka (fitur 013) |
| Model NER dan klasifikasi | Korpus teranotasi dan izin etik ET-01 (fitur 017) |
| Isi ontologi | Putusan putaran pengisian (fitur 018) |
| VS-03, VS-05, VS-07 | Bobot model dan kalibrasi (fitur 020) |
| Ambang kecukupan bukti dan validator | *Gold set* BT-35 (fitur 025) |
| Autentikasi | Belum ada baris pembangunan yang menjadwalkannya (FR-A01) |
| Adaptor penyedia model sungguhan | Keputusan penyedia (ADR-12) |

---

## 10. Yang perlu diputuskan ketua peneliti sebelum dokumen ini final

1. **Cakupan yang didaftarkan.** Apakah pendaftaran mencakup rancangan
   seutuhnya (termasuk yang berpenanda *Dirancang*), atau hanya yang
   berpenanda *Terbangun* dan *Sebagian* pada saat pendaftaran?
2. **Nama ciptaan** sebagaimana akan tercantum pada formulir.
3. **Diagram.** D-04 Bagian 5 merujuk diagram wadah yang tidak ada pada
   repositori. Diagram perlu dibuat sebelum dokumen ini final.
4. **Pemutakhiran penanda keadaan** tepat sebelum pengajuan — penanda di atas
   berlaku untuk commit `9c0b138` dan akan usang begitu fitur berikutnya
   selesai.
