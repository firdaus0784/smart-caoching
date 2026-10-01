# Spec: 028-penyambungan-riwayat-percakapan

| | |
|---|---|
| Kebutuhan | FR-F09; C-05, C-14, C-17, C-20; KM-01, KM-03; TK-65, TK-66, TK-67, TK-68 |
| Dokumen terkait | D-14 Bagian 3.2, 4.1, 4.2, 4.3, 5 (versi 0.7) · D-05 S-09 (versi 0.3) · D-12 baris 028 |
| Status | **Gerbang 4 lolos** — 1 Oktober 2026 (KB-149). Gerbang 1 lolos KB-138 |

## Tujuan

FR-F09: *"Sistem menyimpan riwayat percakapan dan memungkinkan pengguna
melanjutkan sesi sebelumnya."*

Rute pembacanya terpasang sejak fitur 023, dan `Percakapan.catat` sudah ada —
tetapi **tidak ada jalur yang menulis riwayat** (TK-65). Penangan
`POST /api/v1/tanya` menjawab lalu selesai, dan permintaannya tidak dapat
menyebut percakapan mana yang dilanjutkan. Kedua rute riwayat karena itu
selalu mengembalikan daftar kosong.

Fitur ini menyambungkan penulis dan pembacanya: `/tanya` mencatat giliran pada
percakapan yang disebut permintaan, dan layar Tanya dapat melanjutkan
percakapan sebelumnya.

## Dua temuan yang ditemukan saat menyusun spesifikasi ini

**TK-67 · Riwayat tidak mengenal pemiliknya.** D-14 Bagian 4.3 menyatakan
`GET /api/v1/percakapan` mengembalikan percakapan *"milik penanya"*. Kodenya
mengembalikan **seluruh** pengenal percakapan (`sorted(percakapan)`), dan
`PenentuIdentitas` hanya mengembalikan peran, bukan siapa penanyanya. Selama
riwayat tidak pernah ditulis, selisih ini tidak berakibat. **Begitu fitur ini
menulis riwayat, setiap pengguna akan melihat daftar pertanyaan pengguna
lain.** Menyambungkan penulis tanpa menutup ini lebih dulu adalah kebocoran
yang dibangun dengan sengaja.

**TK-68 · `/tanya` tidak memeriksa data pribadi.** Pendeteksi FR-B04 hanya
dipanggil pada `Percakapan.catat`, telemetri, dan jejak ingesti. Pertanyaan
yang memuat NIK atau nomor telepon diteruskan ke jalur penjawab apa adanya,
termasuk ke permintaan model. Begitu fitur ini menyambungkan pencatatan,
pertanyaan semacam itu akan **dijawab tetapi gagal dicatat** — dan pilihan
antara keduanya bukan keputusan pelaksana (P-6).

## Di luar cakupan

- **Autentikasi** (FR-A01, layar S-01). Fitur ini membangun *tempat*
  kepemilikan, bukan cara membuktikan siapa pengguna (lihat P-1)
- **Konteks antargiliran.** Giliran sebelumnya **tidak** ikut memengaruhi
  jawaban berikutnya (R-07). Jawaban yang disesuaikan dengan riwayat
  pertanyaan seseorang adalah personalisasi berbasis riwayat, yang C-14 tunda
  ke siklus 2027
- **Penyimpanan salinan tanggapan.** Riwayat menyimpan pertanyaan dan
  `id_pesan`, tidak pernah tanggapannya (D-14 Bagian 4.3, C-07)
- Penghapusan data pengguna (`DELETE /api/v1/saya/data`, NFR-09) — rute dan
  fiturnya sendiri
- Rute baru maupun bidang tanggapan `/tanya` baru (AG-02, C-20). Bidang
  **permintaan** `id_percakapan` ditambahkan, dan ditulis ke D-14 lebih dulu
  (R-04, P-2)

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | **KETIKA** `POST /api/v1/tanya` menghasilkan tanggapan, sistem **HARUS** mencatat satu giliran — pertanyaan, `id_pesan`, dan waktu UTC — pada percakapan yang disebut permintaan (FR-F09, TK-65) |
| R-02 | **KETIKA** permintaan `/tanya` menyebut percakapan milik pengguna lain, sistem **HARUS** menolaknya dengan galat Bagian 4.2 `SUMBER_TIDAK_ADA`, status 404 — bentuk yang sama dengan membaca percakapan yang tidak dikenal. Pengenal yang belum pernah dipakai membuka percakapan baru. **Batas yang diakui:** karena pengenal baru diterima, penolakan ini mengungkap bahwa sebuah pengenal sudah dipakai; batas itu ditanggung keacakan UUID v4 (R-16) dan pengenal yang tidak pernah ditampilkan kepada pengguna lain |
| R-03 | `GET /api/v1/percakapan` **HARUS** hanya mengembalikan percakapan milik penanya, dan `GET /api/v1/percakapan/{id}` **HARUS** menolak percakapan milik orang lain dengan bentuk yang sama dengan R-02 (D-14 Bagian 4.3, TK-67) |
| R-04 | Bentuk permintaan `/tanya` **HARUS** ditulis ke D-14 **sebelum** kodenya diubah (D-12 baris 028) |
| R-05 | Jalur penjawaban **TIDAK BOLEH** memperoleh hak tulis. Penulisan riwayat **HARUS** dilakukan lapisan HTTP sesudah tanggapan tersusun, dengan kredensial yang bukan milik jalur penjawaban (C-17) |
| R-06 | Pengenal pemilik **TIDAK BOLEH** berupa identitas langsung pengguna, dan **TIDAK BOLEH** tersimpan bersama pemetaan pseudonimnya (C-05) |
| R-07 | Jawaban **TIDAK BOLEH** dipengaruhi giliran sebelumnya pada percakapan yang sama. Pertanyaan yang sama pada percakapan baru dan pada percakapan lama **HARUS** melewati jalur yang sama dengan masukan yang sama (C-14) |
| R-08 | Giliran yang tercatat **TIDAK BOLEH** dapat disunting maupun dihapus lewat permukaan mana pun yang dibangun fitur ini (tambah-saja, `src/api/percakapan.py`) |
| R-09 | Layar Tanya **HARUS** dapat melanjutkan percakapan: pertanyaan berikutnya menyebut percakapan yang sama, dan pertanyaan-pertanyaan sebelumnya pada percakapan itu tampak. Membuka pertanyaan lama **HARUS** berarti **bertanya ulang**, bukan menampilkan jawaban tersimpan (D-14 Bagian 4.3, C-07) |
| R-10 | Seluruh teks layar baru **HARUS** lolos pemeriksa C-13 yang dibangun fitur 027 |
| R-11 | `src/` di luar `src/api/` dan `src/penyimpanan/` **TIDAK BOLEH** berubah — terutama `src/rag/` dan `src/llm/` |
| R-12 | Riwayat **HARUS** tersimpan pada PostgreSQL, pada tabel yang ditulis ke D-14 Bagian 5 lebih dulu. Peran basis data penulisnya **HANYA** boleh membaca dan menambah baris tabel riwayat — tanpa ubah, hapus, maupun kosongkan — dan penolakan itu **HARUS** diuji terhadap peladen (P-3, R-08) |
| R-13 | Riwayat **HARUS** bertahan ketika peladen aplikasi dimulai ulang (P-3, FR-F09) |
| R-14 | Seluruh galat ketiga rute terpasang **HARUS** berbentuk D-14 Bagian 4.2 — `galat.kode`, `pesan_pengguna`, `id_jejak`. `id_jejak` **HARUS** tercatat pada log operasional bersama rincian teknisnya, dan log itu **TIDAK BOLEH** memuat data pribadi (P-4, TK-66) |
| R-15 | **KETIKA** pertanyaan memuat data pribadi berpola, `/tanya` **HARUS** menolaknya dengan galat `VALIDASI_GAGAL` **sebelum** jalur penjawab dipanggil. Pertanyaan itu **TIDAK BOLEH** sampai ke model, riwayat, maupun log, dan pesannya meminta pengguna menghapus nomor tersebut tanpa mengutipnya (P-6, TK-68, KM-03) |
| R-16 | `id_percakapan` **HARUS** berbentuk UUID versi 4, dibangkitkan klien. Bentuk lain ditolak `VALIDASI_GAGAL`, sehingga pengenal yang mudah ditebak tidak dapat dipakai (P-2) |
| R-17 | Penentu identitas **HARUS** mengembalikan pengenal pemilik berpseudonim di samping peran. Titik jalan pengembangan memakai **satu** pemilik tetap yang menyatakan dirinya sebagai pengembangan (P-1, TK-67) |

## Keputusan Gerbang 1

Diputus pemegang Gerbang 1–4 pada 28 September 2026: **"Gerbang 1 lolos,
sesuai anjuran"** bagi P-1 s.d. P-6 (KB-138). Keenamnya pilihan A.

| | Putusan | Kebutuhan yang lahir |
|---|---|---|
| P-1 | Tempat kepemilikan dibangun sekarang; autentikasi kelak mengisinya | R-17 |
| P-2 | Klien membangkitkan `id_percakapan` sebagai bidang permintaan | R-02, R-16; D-14 Bagian 4.1 |
| P-3 | PostgreSQL, peran tambah-saja | R-12, R-13 |
| P-4 | TK-66 dikerjakan bersama, seluruh rute terpasang | R-14 |
| P-5 | Riwayat pada layar S-09 | R-09; D-05 S-09 |
| P-6 | Pertanyaan berdata pribadi ditolak sebelum dijawab | R-15 |

R-02 dirumuskan ulang saat putusan dicatat: rumusan semula menolak pula
pengenal "yang tidak dikenal", padahal di bawah P-2 A pengenal yang belum
dipakai justru membuka percakapan baru. Batas yang menyertainya dinyatakan
pada barisnya.

## Pertanyaan yang sudah diputus

Disimpan apa adanya agar alasan tiap putusan tetap terbaca.

**P-1 · Kepemilikan riwayat tanpa autentikasi (TK-67).**
Riwayat per pengguna menuntut sistem tahu siapa penanyanya, dan FR-A01 belum
dibangun.

| Pilihan | Arti |
|---|---|
| A | Fitur ini membangun **tempat kepemilikan**: penentu identitas mengembalikan pengenal pemilik berpseudonim di samping peran, dan riwayat terikat padanya. Titik jalan pengembangan memakai satu pemilik tetap. Kepemilikan diuji dengan dua pemilik tiruan. Autentikasi kelak mengisi tempat itu tanpa menyentuh riwayat |
| B | Fitur 028 ditunda sampai fitur autentikasi dibangun; baris autentikasi disisipkan ke D-12 lebih dulu |
| C | Riwayat bersama tanpa pemilik — **ditolak**; itu kebocoran TK-67 |

**Anjuran: A.** B menahan FR-F09 di belakang pekerjaan yang belum
terjadwal, sedangkan A menutup TK-67 sekarang dan membuat autentikasi kelak
tinggal mengisi satu tempat. Konsekuensinya dinyatakan: **sampai autentikasi
ada, aplikasi tetap tidak layak dihadapkan ke jaringan publik** — keadaan yang
sudah berlaku hari ini.

**P-2 · Siapa membuat pengenal percakapan baru.**
C-20 melarang menambah bidang tanggapan `/tanya`, sehingga peladen tidak dapat
begitu saja mengembalikan pengenal percakapan yang ia buat.

| Pilihan | Arti |
|---|---|
| A | **Klien membangkitkan** pengenal acak (UUID v4) dan mengirimnya sebagai bidang permintaan `id_percakapan`. Giliran pertama mengikatnya ke pemilik; percakapan milik orang lain ditolak (R-02). Tanpa bidang tanggapan baru, tanpa rute baru |
| B | Peladen membangkitkan dan mengembalikannya sebagai bidang tanggapan `/tanya` baru — menuntut persetujuan C-20 atas bentuk tempat C-02, C-07, dan C-19 diwujudkan |
| C | Rute baru `POST /api/v1/percakapan` — menuntut perubahan D-14 Bagian 3 (AG-02) |

**Anjuran: A.** Ia satu-satunya pilihan yang tidak menyentuh bentuk tanggapan
maupun daftar rute. Pengenal yang ditebak orang lain tidak memberi apa pun:
R-02 menolaknya dengan bentuk yang sama dengan pengenal yang tidak ada.

**P-3 · Penyimpanan riwayat.**
`src/api/percakapan.py` menyimpan di memori, dengan catatan *"penyimpanan
tetapnya menunggu penggerak PostgreSQL"*. Penggerak itu sudah ada sejak fitur
024.

| Pilihan | Arti |
|---|---|
| A | PostgreSQL: dua tabel baru pada kamus data D-14 Bagian 5, peran basis data baru yang hanya dapat **menambah** giliran (tanpa hak ubah maupun hapus, R-08), dan penolakan hak diuji terhadap peladen — pola fitur 024 dan 026 |
| B | Tetap di memori; penyimpanan tetap menjadi fitur tersendiri |

**Anjuran: A.** Riwayat yang hilang setiap kali peladen dimatikan tidak
memungkinkan pengguna "melanjutkan sesi sebelumnya" dalam arti yang dapat
diandalkan kepala sekolah. Sifat tambah-saja juga lebih kuat bila ditegakkan
peladen basis data daripada hanya oleh ketiadaan metode.

**P-4 · TK-66 dikerjakan bersama.**
Peladen mengembalikan galat `{"pesan": …}`, bukan bentuk D-14 Bagian 4.2
(`galat.kode`, `pesan_pengguna`, `id_jejak`). D-14 Bagian 4.3 menuntut
percakapan yang tidak dikenal dijawab dengan bentuk Bagian 4.2, sehingga
R-02 dan R-03 tidak dapat dipenuhi tanpanya.

| Pilihan | Arti |
|---|---|
| A | Seluruh galat ketiga rute terpasang mengikuti Bagian 4.2. `id_jejak` dibangkitkan per permintaan dan ditulis ke log operasional bersama rincian teknisnya, tanpa data pribadi |
| B | Hanya galat rute riwayat yang mengikuti Bagian 4.2; TK-66 selebihnya tetap terbuka |

**Anjuran: A.** Dua bentuk galat pada satu peladen adalah bentuk yang layar
harus tebak. Layar web fitur 027 tidak membaca badan galat, sehingga
perubahan ini tidak mengubah apa yang dilihat pengguna.

**P-5 · Tempat riwayat pada layar.**
D-05 tidak memiliki layar riwayat; S-09 sendiri bernama "Tanya (percakapan)".

| Pilihan | Arti |
|---|---|
| A | Pada S-09: blok "Pertanyaan sebelumnya" pada percakapan yang sedang berjalan, dan daftar percakapan terdahulu yang dapat dibuka. Mengetuk pertanyaan lama mengisinya ke isian untuk **dikirim ulang** — tidak ada jawaban lama yang ditampilkan. D-05 S-09 dimutakhirkan lebih dulu |
| B | Fitur ini hanya backend; tampilan riwayat menyusul pada fitur 013 |

**Anjuran: A.** Tanpa tampilan, FR-F09 tetap tidak terpenuhi bagi pengguna,
dan penulis yang dibangun tanpa pembaca adalah bentuk TK-57 dan TK-65 yang
sudah dua kali dicatat.

**P-6 · Pertanyaan yang memuat data pribadi (TK-68).**
Riwayat menolak pertanyaan berdata pribadi (KM-03), sedangkan jalur penjawab
tidak memeriksanya sama sekali.

| Pilihan | Arti |
|---|---|
| A | `/tanya` menolak pertanyaan berdata pribadi berpola **sebelum** jalur penjawab dipanggil, dengan galat Bagian 4.2 `VALIDASI_GAGAL` dan pesan yang meminta pengguna menghapus nomor tersebut. Pertanyaan itu tidak sampai ke model maupun riwayat |
| B | Pertanyaan tetap dijawab; hanya pencatatan gilirannya yang dilewati |

**Anjuran: A.** B menjawab sambil diam-diam tidak mencatat — kebalikan
"tolak, jangan saring" yang KM-03 tetapkan — dan tetap meneruskan NIK ke
permintaan model. A menutup keduanya dengan satu pemeriksaan pada titik
masuk. Batasnya diakui: pendeteksi hanya mengenal pola tetap; nama orang
tidak terdeteksi (catatan cakupan FR-B04, BT-70).

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | FR-F09; TK-65 |
| R-02, R-03 | D-14 Bagian 4.3; TK-67 |
| R-04 | D-12 baris 028; C-20 |
| R-05 | C-17 |
| R-06 | C-05 |
| R-07 | C-14; D-01 Bagian 4.2 |
| R-08 | `src/api/percakapan.py`; KM-02 |
| R-09 | FR-F09; D-14 Bagian 4.3; C-07 |
| R-10 | C-13; NFR-19 |
| R-11 | C-17, C-18 |
| R-12, R-13 | FR-F09; P-3; KM-02 |
| R-14 | D-14 Bagian 4.2; TK-66 |
| R-15 | KM-03; FR-B04; TK-68 |
| R-16 | P-2 |
| R-17 | FR-A01 di luar cakupan; C-05; TK-67 |

## Kriteria penerimaan

- [x] Keenam pertanyaan diputus pada Gerbang 1, dan kebutuhan bagi P-3, P-4,
      P-6 ditulis sebelum `plan.md`
- [ ] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [ ] Kepemilikan diuji dengan dua pemilik: pemilik B tidak dapat membaca,
      menulis ke, maupun mengetahui keberadaan percakapan pemilik A
- [ ] Bila P-3 A: penolakan hak diuji terhadap peladen PostgreSQL, dengan
      sebab penolakan diperiksa (`permission denied`), bukan hanya galatnya
- [ ] Uji mutasi disusun pada `plan.md` dan dilaporkan apa adanya
- [ ] `git diff` atas `src/rag/` dan `src/llm/` sejak Gerbang 3: kosong (R-11)
- [ ] `make check` lulus enam gerbang
