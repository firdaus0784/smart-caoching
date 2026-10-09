# Spec: 037-perkakas-ingesti

| | |
|---|---|
| Kebutuhan | FR-B01, FR-B04, FR-B05, FR-B06, FR-B07, FR-B08; C-02, C-03, C-05, C-17, C-20 |
| Dokumen terkait | D-01 Modul B, BT-70 · D-03 Bagian 3 dan token penyamaran · D-04 Bagian 7.2 (`dokumen_sumber`, `jejak_area`), ADR-06, KA-04 · D-07 Bagian 3.1 dan 3.2 · D-13 KD-02, KD-10, Bagian 6 · D-14 Bagian 3 (peran `verifikator`) dan 5.1 · spec fitur 002, 015, 024, 026, 032 · TK-83 |
| Status | **Diajukan ke Gerbang 1** — 9 Oktober 2026 (KB-254) |

## Mengapa fitur ini diusulkan sekarang

Fitur 032 lolos Gerbang 4, dan pembaca sumbernya hanya berguna bila korpus
berisi dokumen. Sejauh ini isi korpus pada mesin pengembangan ditanam
pengelola, sebab **tidak ada jalan sah dari berkas sumber ke korpus PostgreSQL**:

- Gerbang ingesti fitur 002 menyimpan keadaannya — metadata dokumen karantina,
  temuan pola adversarial, tinjauan, putusan, dan `jejak_area` — **di memori**.
  Perkakas yang dijalankan per perintah kehilangan seluruhnya sebelum
  verifikator sempat menilai.
- Tidak satu peran basis data pun memegang `DELETE` atas
  `karantina.dokumen_sumber`, sehingga `setujui()` sebagai `peran_verifikasi`
  ditolak peladen. Sebaliknya hak bawaan memberi verifikator `INSERT` dan
  `UPDATE` atas karantina, padahal kodenya menyatakan verifikator sengaja
  tidak menulis karantina. Kredensial ingesti dan penarikan tidak berpasangan
  dengan peran mana pun (TK-83).

Pemegang gerbang memutus TK-83 dengan menyisipkan baris D-12 037 (KB-247).

## Temuan yang diajukan bersama usulan ini

**TK-84 · Penarikan persetujuan pemilik tidak mencabut segmen dokumen dari
indeks.** `cabut_persetujuan()` memindahkan dokumen dari korpus ke karantina,
tetapi pengambilan vektor (fitur 019) membaca `segmen_teks` pada kedua indeks
**tanpa** menautkannya ke korpus. Segmen dokumen yang persetujuannya ditarik
tetap dapat diambil, masuk konteks model, dan dikutip. Uraian `gerbang.py`
sejak fitur 002 menyerahkan pencabutan itu kepada fitur 006 dan 007, tetapi
tidak satu pun membangunnya. Tidak berdampak hari ini, sebab belum ada jalur
yang menulis segmen dari korpus. Begitu ada, penarikan persetujuan tampak
tuntas padahal tidak (P-3).

## Di luar cakupan

- **Rute unggah atau verifikasi.** D-14 Bagian 3 tidak memuatnya, dan baris
  ini perkakas tim (AG-02). Peran `verifikator` tetap tanpa layar.
- **Segmentasi dan penempatan segmen ke indeks.** D-07 Bagian 3.2 adalah
  pemiliknya. Lihat P-4.
- **Penyematan.** Sudah dibangun fitur 026 atas segmen yang ada.
- **Pengenalan nama perorangan dan alamat.** Menunggu model NER (fitur 017,
  BT-70). Selama itu verifikasi manusia yang menahannya (FR-B05).
- **Formulir persetujuan pemilik (ET-02).** Milik tim etik. Perkakas mencatat
  status persetujuan yang tim nyatakan, tidak menilainya.
- **Pengubahan status keberlakuan.** Sudah dipegang perintah `status` perkakas
  kurasi (fitur 013, TK-81 A).

## Kebutuhan (EARS) yang tidak bergantung pada pertanyaan

| ID | Kebutuhan |
|---|---|
| R-01 | Dokumen masuk **HARUS** selalu ke karantina; perkakas **TIDAK BOLEH** menyediakan jalan menaruh dokumen langsung di korpus (FR-B07, ADR-06) |
| R-02 | Ketiga gerbang fitur 002 — persetujuan pemilik (ET-04), verifikasi anonimisasi manusia (FR-B05), dan tinjauan temuan pola adversarial (FR-B08) — **HARUS** tetap berdiri sendiri, dengan aturan yang sama persis dengan `src/ingest/gerbang.py`. Fitur ini memindahkan keadaannya ke peladen, bukan menulis ulang aturannya |
| R-03 | **KETIKA** dokumen yang sama diunggah ulang, tinjauan sebelumnya **HARUS** batal, juga sesudah perkakas berhenti dan dijalankan lagi (fitur 002, jalan pintas unggah-ulang) |
| R-04 | Setiap perintah **HARUS** tersambung sebagai peran basis data yang sesuai dengan kredensial kodenya. Hak yang tidak dibutuhkan perintahnya **HARUS** ditolak peladen, bukan hanya oleh kode, dan diuji dengan penolakan (C-03, pelajaran TK-63 dan TK-64) |
| R-05 | Peran pengambilan, pemanggil model, penyematan, pembaca sumber, dan peran aplikasi lainnya **TIDAK BOLEH** menjangkau tabel karantina mana pun yang dibuat fitur ini (C-03, KA-04) |
| R-06 | Pemindahan ke korpus **HARUS** tercatat bersama metadata asalnya dan baris `jejak_area` dalam satu pernyataan; gagal salah satunya berarti tidak satu pun tersimpan (TK-82 A, R-11 fitur 002) |
| R-07 | Alasan putusan dan catatan tinjauan **TIDAK BOLEH** memuat data pribadi berpola. Perkakas **HARUS** menolaknya tanpa mengutipnya, dan **TIDAK BOLEH** menulis teks dokumen, kutipan temuan, maupun nilai data pribadi ke log (KM-03, D-14 `jejak_area.alasan`) |
| R-08 | Teks dokumen karantina **HARUS** hanya dapat ditampilkan kepada perintah berperan verifikasi, ke keluaran baku perkakas. Ia tidak ditulis ke berkas maupun log oleh perkakas |
| R-09 | Penarikan persetujuan **HARUS** berlaku seketika, tanpa kredensial verifikator, dan **HARUS** mengeluarkan dokumen dari korpus; persetujuan ulang hanya lewat unggahan ulang beserta persetujuan baru (KB-014) |
| R-10 | Fitur ini **TIDAK BOLEH** menambah rute, mengubah bentuk tanggapan `/tanya`, maupun memberi jalur penjawaban kemampuan menulis (C-17, C-20). Setiap tabel baru **HARUS** ditulis ke D-14 Bagian 5.1 dan D-04 Bagian 7.2 sebelum kodenya |

## Pertanyaan terbuka

Tiap pertanyaan disertai anjuran; anjuran bukan putusan.

**P-1 · Tempat keadaan gerbang.** Perkakas dijalankan per perintah: `terima`
hari ini, `setujui` lusa oleh orang lain.

| Pilihan | Arti |
|---|---|
| A | **Catatan tambah-saja di skema `karantina`**: metadata dokumen karantina (`Dokumen`), temuan pola (jenis dan letak), tinjauan, putusan, dan `jejak_area` D-04 Bagian 7.2. Gerbang membaca keadaannya dari peladen setiap perintah. Bidang `dokumen_sumber` D-14 Bagian 5.1 — `status_anonimisasi`, `status_persetujuan_pemilik`, `area_simpan` — diwujudkan sebagai catatan, bukan kolom yang disunting |
| B | Satu proses perkakas interaktif yang hidup dari `terima` sampai `setujui`; keadaan hilang bila proses berhenti |
| C | Satu perintah `masukkan` yang menjalankan `terima` lalu `setujui` sekaligus |

**Anjuran: A.** B membuat verifikasi bergantung pada satu terminal yang tidak
boleh ditutup. C meniadakan verifikasi sebagai langkah tersendiri, dan itu
yang FR-B05 larang. Tambah-saja karena jejak putusan yang dapat disunting tidak
membuktikan apa pun.

**P-2 · Peta peran basis data** (TK-83). Kode memiliki tiga kredensial bagi
dokumen: ingesti (menulis karantina), verifikasi (membaca karantina dan korpus,
menulis korpus), penarikan (membaca korpus, menulis karantina).

| Pilihan | Arti |
|---|---|
| A | **Tiga peran, satu per kredensial.** `peran_ingesti` baru: menambah dan mengganti dokumen karantina beserta catatannya, tanpa membaca isi dokumen. `peran_verifikasi` diperketat: hak tambah dan ubah atas karantina dicabut, diberi **hapus saja** atas `karantina.dokumen_sumber` — memindahkan berarti mengeluarkan, bukan menyunting. `peran_penarikan_dokumen` baru: hapus atas korpus, tambah atas karantina |
| B | Satu peran `peran_ingesti` bagi seluruh perintah |
| C | Pemindahan menyalin tanpa menghapus dari karantina, sehingga verifikator tidak perlu hak hapus |

**Anjuran: A.** B menyatukan pengunggah dan penilai, padahal fitur 002
memisahkannya agar verifikator tidak dapat menyunting bahan yang sedang
dinilainya. C membuat satu dokumen berada di dua area, dan `area_simpan`
kehilangan arti.

**P-3 · TK-84 — penarikan persetujuan dan segmen indeks.**

| Pilihan | Arti |
|---|---|
| A | **Penarikan menghapus segmen dokumen dari kedua indeks** dalam pernyataan yang sama dengan pemindahannya. Peran penarikan dokumen memegang hapus atas kedua tabel `segmen_teks`, tanpa hak baca teks segmen |
| B | Segmen ditandai ditarik dan pengambilan menyaringnya |
| C | Dicatat sebagai TK terbuka; fitur ini tidak menyentuh indeks |

**Anjuran: A.** B adalah penyaringan saat kueri, bentuk yang D-07 Bagian 3.1
tolak bagi lisensi karena satu kueri yang lupa menyaring tidak menghasilkan
galat apa pun. C membiarkan penarikan tampak tuntas padahal tidak.

**P-4 · Segmentasi dan penempatan ke indeks.** Dokumen yang disetujui masuk
korpus tanpa segmen, sehingga belum dapat diambil maupun dibaca teks bagiannya
pada S-10. D-07 Bagian 3.2 menetapkan aturannya: 300–500 kata, tumpang tindih
50–80 kata, batas alami pasal dan ayat, penanda bagian wajib.

| Pilihan | Arti |
|---|---|
| A | **Baris D-12 baru 038 "Segmentasi dan penempatan indeks"**, dikerjakan sesudah 037; 037 berhenti di korpus |
| B | Masuk cakupan 037 |
| C | Tanpa pemilik; dicatat sebagai TK terbuka |

**Anjuran: A.** Segmentasi adalah pekerjaan mutu pengambilan milik D-07, dengan
uji dan mutasinya sendiri, dan C-16 menunjuknya sebagai tempat perbaikan bila
validator terlalu sering menolak. Menyatukannya dengan peta peran C-03 membuat
satu fitur menjaga dua hal yang berbeda sifatnya. Baris D-12 baru hanya sah
atas putusan Anda.

**P-5 · Penyamaran otomatis saat menerima (FR-B04).** Pendeteksi enam pengenal
berpola (fitur 015) melapor letak, tidak menyamarkan; penyamarannya belum
dibangun. D-03 sudah menetapkan tokennya: `[NIK]`, `[NIP]`, `[NISN]`,
`[NUPTK]`, `[TELEPON]`, `[REKENING]`.

| Pilihan | Arti |
|---|---|
| A | **`terima` menyamarkan keenam jenis berpola dengan token D-03 sebelum teks disimpan di karantina.** Teks asli tidak tersimpan di mana pun; jumlah samaran per jenis tercatat tanpa nilainya. Verifikator menilai hasil penyamaran |
| B | `terima` menyimpan teks asli; pendeteksi hanya melaporkan letak kepada verifikator, penyamaran manual oleh tim |
| C | Tanpa pendeteksi pada fitur ini |

**Anjuran: A.** FR-B04 berbunyi "mendeteksi dan menyamarkan … sebelum dokumen
masuk ke korpus", dan FR-B05 meminta manusia memverifikasi **hasil**
anonimisasi. Nilai yang tidak pernah disimpan tidak dapat bocor dari karantina
(KM-03). Batasnya dinyatakan kepada verifikator setiap kali: nama dan alamat
tidak tersamarkan (BT-70).

**P-6 · Pelaku pada jejak.** `jejak_area.id_pelaku` mencatat siapa yang
menerima, menyetujui, menolak, atau menarik.

| Pilihan | Arti |
|---|---|
| A | **Kode anggota tim berpola nama akun** (`^[a-z]{2,8}-[0-9]{3}$`, bentuk `pengguna.id`), bukan nama orang. Pasangannya dengan orang dipegang tim di luar sistem, seperti akun peserta (P-1 A fitur 029) |
| B | Nama lengkap anggota tim |

**Anjuran: A.** Jejak tetap dapat dipertanggungjawabkan lewat daftar tim,
tanpa basis data menyimpan nama orang yang tidak memerlukannya.

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | FR-B07; ADR-06; R-03 fitur 002 |
| R-02 | FR-B05; FR-B08; ET-04; fitur 002 |
| R-03 | FR-B08; KD-01; fitur 002 |
| R-04 | C-03; TK-63; TK-64; TK-83 |
| R-05 | C-03; KA-04; KD-10 |
| R-06 | FR-B06; TK-82 A; R-11 fitur 002 |
| R-07 | KM-03; D-14 Bagian 5.1 |
| R-08 | FR-B05; KM-03 |
| R-09 | ET-04; KB-014 |
| R-10 | C-17; C-20; AG-02 |

## Kriteria penerimaan

- [ ] P-1 s.d. P-6 diputus pada Gerbang 1
- [ ] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [ ] Hak setiap peran diuji terhadap peladen: perintahnya berjalan dengan
      haknya sendiri, dan hak yang tidak dibutuhkannya ditolak
- [ ] Keadaan gerbang bertahan antarperintah, diuji terhadap PostgreSQL
- [ ] `make check` lulus enam gerbang
