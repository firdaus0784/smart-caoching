# Spec: 004-pembagian-data-dan-metrik

| | |
|---|---|
| Kebutuhan | **FR-D03, FR-D04, FR-D07** · FR-D01, FR-D02, FR-D05 dipisahkan ke fitur 017 |
| Dokumen terkait | **D-08 Bagian 4.2 dan PU-01** · D-10 Bagian 3 · D-01 Modul D |
| Pasal konstitusi | **C-09**, C-11, C-12, C-16 |
| Urutan pembangunan | 004 pada `docs/D12.md` Bagian 7, sesudah 016 |
| Ketergantungan | **Nol paket Python baru** |
| Status | Menunggu Gerbang 1 |

## Mengapa fitur ini dipisah, dan mengapa bagian ini lebih dulu

Fitur 004 menurut D-12 memuat FR-D01 sampai FR-D07 — model NER dan
klasifikasi dengan F1 ≥ 85%. **Modelnya tidak dapat dilatih sekarang**: tidak
ada satu pun dokumen teranotasi, dan anotasinya pekerjaan dua mahasiswa pada
bulan 2–4 yang baru dapat dimulai setelah mereka lulus uji kualifikasi
(FR-C09, fitur 003).

Yang **tidak** menunggu justru bagian yang wajib berdiri lebih dulu:

> **Pembagian dibekukan sebelum pelatihan pertama** (D-08 Bagian 4.2).

Kalimat itu menentukan urutannya. Membangun pembagian data setelah pelatihan
dimulai berarti pelatihan pertama berjalan atas pembagian yang disusun sambil
lalu — dan D-08 menyebutkan akibatnya dengan tepat: bila dua segmen dari
dokumen yang sama tersebar ke himpunan latih dan uji, **model akan tampak
lebih baik daripada kenyataannya**, dan itu "kekeliruan yang mudah terjadi dan
sulit terdeteksi setelahnya".

Pola yang sama dengan gerbang karantina yang mendahului pendeteksi data
pribadi (KB-010) dan batch pembanding yang mendahului pra-anotasi (fitur 003
C-3): pengendali dibangun sebelum yang dikendalikannya ada.

## Cakupan

| | Bagian | Menunggu korpus? |
|---|---|---|
| **1** | Pembagian data beku, metrik per kelas, catatan percobaan | **Tidak** |
| **2** | Model NER dan klasifikasi, prosedur latih ulang | **Ya** |

Bagian 2 diusulkan menjadi **fitur 017**.

## Di luar cakupan

- **Melatih model apa pun.** Menuntut korpus teranotasi.
- **Memilih model dasar praterlatih.** Keputusan bagian 2; memilihnya sekarang
  berarti memilih sebelum tahu bentuk korpusnya.
- **Menetapkan ambang F1.** Dimiliki D-01 FR-D01 (≥ 85%) dan D-08. C-16
  melarang menyetelnya di luar prosedur kalibrasi.
- **Indeks terpisah menurut lisensi** (FR-D06). Itu fitur 006.

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | Pembagian data **HARUS** dilakukan pada tingkat **dokumen**, bukan segmen (FR-D07, D-08 Bagian 4.2) |
| R-02 | Ketiga himpunan **TIDAK BOLEH** beririsan; satu dokumen tepat pada satu himpunan |
| R-03 | Porsi **HARUS** mengikuti D-08 Bagian 4.2 — latih 70%, validasi 15%, uji 15% — dan angkanya **TIDAK BOLEH** tertulis di lebih dari satu tempat (C-16) |
| R-04 | Pembagian **HARUS** dibekukan: ia membawa sidik daftar id dokumennya, dan **JIKA** korpus yang sama dibagi ulang dengan hasil berbeda, **MAKA** sistem **HARUS** menolaknya |
| R-05 | Pembuatan pembagian **HARUS** deterministik terhadap seed yang tercatat; pembagian yang tidak dapat diulang **TIDAK BOLEH** dihasilkan |
| R-06 | **KETIKA** himpunan uji dibaca, sistem **HARUS** mencatatnya; PU-01 menetapkan ia dibuka **satu kali** saat evaluasi akhir |
| R-07 | Metrik **HARUS** dilaporkan **per kelas**, bukan hanya rerata (FR-D04) |
| R-08 | **JIKA** sebuah kelas tidak memiliki satu pun contoh, **MAKA** metriknya **HARUS** dilaporkan belum terhitung — bukan 0,0 dan bukan 1,0 |
| R-09 | Rerata **HARUS** dinyatakan jenisnya — makro atau mikro — sebab keduanya berbeda tajam pada kelas yang tidak seimbang |
| R-10 | Catatan percobaan **HARUS** memuat keempat belas bidang D-10 Bagian 3, termasuk **seed acak dan id pembagian data** (FR-D03, C-09) |
| R-11 | Percobaan yang **gagal** **HARUS** tercatat, bukan hanya yang berhasil (D-10 Bagian 3) |

**R-06 adalah kebutuhan yang paling mudah dianggap berlebihan.** PU-01
berbunyi "data uji tidak pernah menyentuh proses pelatihan atau penyetelan",
dan pelanggarannya tidak pernah disengaja — ia terjadi ketika seseorang
"sekadar melihat" hasil uji untuk memilih konfigurasi berikutnya. Sesudah itu
angka pada naskah bukan lagi hasil pada data tersembunyi, dan tidak ada
satu pun jejak yang menunjukkannya.

**R-08 mengikuti bentuk yang sudah tiga kali terbukti** — `HasilSistem` fitur
015, `HasilKesepakatan` fitur 003, `bendera` fitur 016. Kelas tanpa contoh yang
dilaporkan F1 = 0,0 akan terbaca sebagai kelas yang modelnya gagal total, dan
tindak lanjutnya menjadi melatih ulang alih-alih menambah data.

## Keadaan yang wajib ditangani

| Keadaan | Perilaku yang dituntut |
|---|---|
| Dokumen muncul pada dua himpunan | Ditolak saat pembagian dibentuk |
| Korpus terlalu kecil untuk porsi D-08 | Ditolak dengan menyebut jumlah minimumnya |
| Pembagian ulang menghasilkan susunan berbeda | Ditolak; pembagian sudah beku |
| Himpunan uji dibaca kedua kalinya | Dicatat dan dilaporkan |
| Kelas tanpa contoh pada data acuan | Metrik belum terhitung |
| Kelas ada pada prediksi tetapi tidak pada acuan | Dilaporkan; ia halusinasi kelas |
| Percobaan gagal | Tetap tercatat, dengan dugaan penyebabnya |

## Kriteria penerimaan

- [ ] R-01 s.d. R-11 masing-masing punya uji yang gagal sebelum implementasi
- [ ] Uji bahwa dokumen tidak pernah berada pada dua himpunan (R-02)
- [ ] Uji bahwa pembagian ulang yang berbeda ditolak (R-04)
- [ ] Uji bahwa pembagian deterministik terhadap seed yang sama (R-05)
- [ ] Uji bahwa pembukaan himpunan uji tercatat (R-06)
- [ ] Uji bahwa kelas tanpa contoh dilaporkan belum terhitung (R-08)
- [ ] Angka metrik diuji terhadap **contoh yang dihitung tangan**
- [ ] Nol ketergantungan Python baru
- [ ] Cakupan uji tidak turun
- [ ] `make compliance` tidak berubah

## Pertanyaan bagi Gerbang 1

**Satu.** Apa yang terjadi ketika himpunan uji dibuka kedua kalinya (R-06)?

| | Pilihan | Akibat |
|---|---|---|
| **A** | Dicatat saja; pembukaan berikutnya tetap diizinkan | Jejaknya ada, penilaiannya pada manusia. Tidak menghalangi pekerjaan sah seperti mengulang evaluasi karena galat perkakas |
| **B** | Ditolak setelah pembukaan pertama | Menegakkan PU-01 keras. Menghalangi evaluasi ulang yang sah, dan penolakannya akan diakali dengan membuat pembagian baru |
| **C** | Dicatat, dan pembukaan kedua menandai catatan percobaannya | Jejaknya ada **dan** ikut pada laporan yang masuk naskah |

**Saran saya: C.** B ditolak karena penjagaan yang menghalangi pekerjaan sah
adalah penjagaan yang akan dilucuti — dan cara melucutinya, membuat pembagian
baru, justru menghapus jejaknya. A terlalu lunak: catatan yang tidak pernah
sampai ke laporan adalah catatan yang tidak ada yang membaca.
