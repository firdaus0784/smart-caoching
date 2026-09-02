# L9 · Datasheet Korpus

Mengikuti kerangka `docs/D10.md` Bagian 5A — *Datasheets for Datasets*
(Gebru dkk. 2021) dan *Data Statements for NLP* (Bender & Friedman 2018),
rujukan pada D-11 Bagian 3.6.

## Mengapa berkas ini dibuat sebelum korpusnya ada

`docs/D10.md` Bagian 2 menjadwalkan L9 "bersamaan penyelesaian korpus".
Berkas ini dibuka lebih awal, dan alasannya sudah tertulis dua kali pada
proyek ini sendiri:

- L7 menyatakan pada kalimat pembukanya bahwa menyusun catatan penggunaan
  alat bantu AI di akhir "menghasilkan pernyataan yang tidak akurat".
- L8 dibuka terlambat dan harus disusulkan delapan langkah sekaligus
  (KB-065) — bukan karena kelalaian, melainkan karena catatan yang dibuka
  sesudah kejadiannya hanya dapat diisi dari ingatan.

Bagian **Proses pengumpulan** adalah bagian yang paling tidak dapat
direkonstruksi belakangan: cara perolehan, persetujuan pemilik dokumen, dan
rentang waktu hanya diketahui pasti oleh orang yang sedang mengumpulkannya.
Membukanya sebelum pengumpulan dimulai adalah satu-satunya cara ia terisi
benar.

## Sifat berkas ini

**Berbeda dari L1, L2, L4, dan L7, berkas ini bukan tambah-saja.** Ia
dokumen hidup yang bagian-bagiannya terisi bertahap sampai korpus selesai.
Yang tidak boleh adalah menghapus bagian yang sudah terisi tanpa mencatat
alasannya pada L4.

## Keadaan hari ini

**Belum ada satu dokumen pun terkumpul.** Yang ada baru daftar jenis
dokumen. Setiap bagian di bawah menyatakan sendiri apakah ia terisi,
sebagian, atau belum — dan yang belum menyebut apa yang menghalanginya.

---

## 1. Motivasi

| | |
|---|---|
| Untuk apa | Melatih model NER dan klasifikasi domain manajemen sekolah dasar Indonesia (FR-D01, FR-D02), dan menjadi korpus pengambilan bagi jalur penjawaban (FR-F) |
| Oleh siapa | Tim penelitian Hibah UPI, siklus 2026 |
| Dibiayai | Hibah UPI 2026 |
| Sasaran volume | KI-01: **1.000 dokumen teranotasi penuh** (wajib) dan **5.000 dokumen terkumpul/terindeks** (tambahan) |

## 2. Komposisi

**Terisi sebagian — jenis dokumen sudah diketahui, jumlahnya nol.**

| | |
|---|---|
| Dokumen terkumpul | **0** |
| Jenis dokumen teridentifikasi | **50** |
| Jenjang | Sekolah dasar |
| Wilayah | Kabupaten Sumedang (KT-01) |
| Rentang tahun | Belum ditetapkan |
| Distribusi label | Belum ada — menunggu anotasi |

### 2.1 Asal daftar jenis dokumen

Daftar berikut berasal dari kolom "Dari dokumen mana" pada lembar istilah
Pengisi B, batch kalibrasi ontologi 1 September 2026 (KB-073, KB-075).
Kolom itu terisi **50 dari 50 baris tanpa satu pun pengulangan**.

Ia sah meskipun kolom hubungan pada lembar yang sama dibuang seluruhnya:
cacat siklus pada KB-075 hanya menyentuh tabel hubungan, sedangkan kolom
ini berada pada tabel istilah dan berisi nama dokumen yang benar-benar
disimpan sekolah. Nilainya tidak diakui pada KB-073 karena penilaian saat
itu hanya menyentuh kolom istilah dan kolom hubungan.

**Batasnya dinyatakan terus terang:** daftar ini berasal dari **satu**
kepala sekolah di **satu** sekolah. Ia daftar awal yang wajib dilengkapi
dan dikoreksi oleh kepala sekolah lain sebelum dianggap mewakili.

### 2.2 Daftar jenis dokumen

Kolom "Data pribadi" adalah **dugaan awal berdasarkan nama dokumen**, bukan
hasil pemeriksaan isi. Ia wajib diperiksa manusia pada dokumen sungguhan
sebelum pengumpulan, dan bukan pengganti FR-B04 maupun gerbang karantina
FR-B05.

| # | Jenis dokumen | Diduga memuat data pribadi |
|---|---|---|
| 1 | Program Supervisi | PTK |
| 2 | Rapor Pendidikan | — |
| 3 | Dokumen Refleksi Rapor Pendidikan | — |
| 4 | Dokumen Visi-Misi Sekolah | — |
| 5 | Program Kerja Jangka Menengah | — |
| 6 | Program Kerja Tahunan | — |
| 7 | Rencana Kegiatan dan Anggaran Sekolah (RKAS) | — |
| 8 | Buku Induk Siswa | **peserta didik** |
| 9 | Buku Klaper Siswa | **peserta didik** |
| 10 | Buku Mutasi Siswa | **peserta didik** |
| 11 | Dokumen Hasil Refleksi Program Pengembangan Sekolah | — |
| 12 | Dokumen Pemetaan Kebutuhan dan Potensi Sekolah | — |
| 13 | Program PPDB/SPMB/Pendaftaran | **peserta didik** |
| 14 | SK Pembagian Tugas Mengajar | PTK |
| 15 | Daftar Hadir Guru dan Tendik | PTK |
| 16 | Program Supervisi Akademik | PTK |
| 17 | Buku Kas Umum (BKU) | — |
| 18 | Buku Pembantu Pajak/Bank | PTK |
| 19 | Surat Pertanggungjawaban (SPJ) Keuangan | PTK |
| 20 | Buku Inventaris Barang | — |
| 21 | Dokumen Pelaksanaan Pengembangan Kompetensi GTK | PTK |
| 22 | Buku Agenda Surat Masuk | — |
| 23 | Buku Agenda Surat Keluar | — |
| 24 | Buku Tamu | **tamu** |
| 25 | Notulen Rapat Dinas | PTK |
| 26 | Dokumen Perencanaan Sasaran Kinerja GTK | PTK |
| 27 | Dokumen Penilaian Sasaran Kinerja GTK | PTK |
| 28 | Kalender Pendidikan | — |
| 29 | Hasil Analisis Kalender Pendidikan | — |
| 30 | Capaian Pembelajaran | — |
| 31 | Rumusan Tujuan Pembelajaran | — |
| 32 | Alur Tujuan Pembelajaran | — |
| 33 | Program Tahunan (Prota) | — |
| 34 | Program Semester (Prosem) | — |
| 35 | Rencana Pelaksanaan Pembelajaran (RPP) | — |
| 36 | Bahan Ajar/Materi | — |
| 37 | Lembar Kerja Peserta Didik (LKPD) | — |
| 38 | Media Pembelajaran | — |
| 39 | Buku Pegangan Guru dan Siswa | — |
| 40 | Jurnal/Agenda Harian Guru | PTK |
| 41 | Daftar Hadir/Absensi Siswa | **peserta didik** |
| 42 | Daftar Nilai / Penilaian Hasil Belajar | **peserta didik** |
| 43 | Analisis Hasil Ulangan/Asesmen | **peserta didik** |
| 44 | Program Remedial dan Pengayaan | **peserta didik** |
| 45 | Buku Catatan Hambatan Belajar Siswa | **peserta didik, sensitif** |
| 46 | Program Bimbingan | **peserta didik, sensitif** |
| 47 | Program Kokurikuler | — |
| 48 | Program Ekstrakurikuler | — |
| 49 | Program Pembiasaan | — |
| 50 | Laporan Sumatif Akhir Semester (SAS) dan Hasil Analisisnya | **peserta didik** |

**Ringkasan dugaan:** 11 jenis diduga memuat data peserta didik, dua di
antaranya bersifat sensitif (hambatan belajar dan bimbingan); 10 jenis
diduga memuat data PTK; satu memuat data tamu. Sisanya diduga tidak.

Angka ini menegaskan D-01 Bagian 15 catatan (a): korpus dokumen manajerial
sekolah hampir pasti memuat data pribadi PTK dan peserta didik, sehingga
FR-B04 dan FR-B05 **prasyarat hukum, bukan fitur tambahan**.

## 3. Proses pengumpulan

**Belum dimulai. Terhalang ET-01.**

| | |
|---|---|
| Cara perolehan | Belum ditetapkan |
| Persetujuan pemilik dokumen | **Belum ada** |
| *Ethical clearance* (ET-01) | **Tidak ada catatan penyelesaian pada berkas mana pun** |
| Nota kesepahaman dengan dinas | Belum tercatat |
| Rentang waktu | Belum dimulai |

`docs/D01.md` Bagian 14 ET-01 menetapkan pengajuan *ethical clearance* ke
komite etik penelitian UPI oleh ketua peneliti **sebelum pengambilan data
(Bulan 1)**. Tidak ditemukan catatan bahwa ia selesai. Ketiadaan catatan
bukan bukti ia belum diurus — tetapi ia belum dapat dinyatakan selesai, dan
pengumpulan 11 jenis dokumen berisi data anak tidak boleh dimulai sebelum
kepastiannya ada.

`docs/D01.md` Bagian 15 catatan (b) menambahkan alasan kedua: jurnal
terindeks Scopus umumnya meminta nomor persetujuan etik dicantumkan dalam
naskah, dan mengurusnya di akhir penelitian tidak mungkin.

## 4. Praproses dan anonimisasi

**Perangkatnya sudah ada; belum dijalankan atas dokumen sungguhan.**

| | |
|---|---|
| Praproses | Fitur 015 selesai (FR-B01–B03) |
| Pendeteksi data pribadi | Fitur 015 selesai (FR-B04) — `periksa_data_pribadi` |
| Gerbang karantina | Fitur 002 selesai (FR-B05–B09, C-03) |
| Verifikasi manusia | Prosedurnya belum ditetapkan |
| Pemakaian atas data lapangan | Baru dua kali, keduanya atas lembar isian, bukan dokumen sekolah: KB-073 dan KB-075, seluruhnya nol temuan |

## 5. Anotasi

**Belum dimulai.**

| | |
|---|---|
| Pedoman | D-03 |
| Jumlah anotator | Belum ditetapkan |
| Kualifikasi | Belum ditetapkan |
| Kesepakatan | Belum diukur — FR-C02 menuntut Cohen's Kappa ≥ 0,70 klasifikasi dan F1 berpasangan ≥ 0,75 tepat / ≥ 0,85 longgar |
| Versi skema | D-03 |

## 6. Penggunaan yang dimaksudkan

Pelatihan model domain manajemen sekolah dasar Indonesia, dan pengambilan
bagi jalur penjawaban sistem *smart-coaching*.

## 7. Penggunaan di luar cakupan

Sama dengan LC-01 s.d. LC-06 pada `docs/D01.md`. Ditegaskan di sini:
korpus ini **tidak boleh** dipakai menilai kinerja kepala sekolah maupun
guru oleh instansi mana pun (RE-05).

## 8. Distribusi

Belum ditetapkan. Keputusan ini bergantung pada lisensi dokumen sumber dan
pada isi persetujuan pemilik dokumen, sehingga ia **tidak dapat diputuskan
sebelum Bagian 3 terisi**.

## 9. Pemeliharaan

Belum ditetapkan.

## 10. Pertimbangan etis

| | |
|---|---|
| Data pribadi | Lihat Bagian 2.2 — 11 jenis diduga memuat data peserta didik, dua bersifat sensitif |
| Keterwakilan wilayah | Korpus berasal dari **satu kabupaten** (KT-01), sehingga model yang dilatih di atasnya belum tentu berlaku untuk konteks lain. D-10 Bagian 5A menuntut hal ini dinyatakan jujur |
| Keterwakilan hari ini | Lebih sempit lagi: daftar jenis dokumennya berasal dari **satu sekolah** |
| Potensi penyalahgunaan | Penilaian kinerja individu (RE-05); pengungkapan hambatan belajar peserta didik dari dokumen jenis 45 dan 46 |

---

## Riwayat

| Tanggal | Perubahan | Sebab |
|---|---|---|
| 2 September 2026 | Berkas dibuka. Bagian 2 terisi sebagian dari daftar 50 jenis dokumen; Bagian 3 menyatakan ET-01 tanpa catatan penyelesaian | KB-076 |
