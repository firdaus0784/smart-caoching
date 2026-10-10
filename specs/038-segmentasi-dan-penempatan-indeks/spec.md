# Spec: 038-segmentasi-dan-penempatan-indeks

| | |
|---|---|
| Kebutuhan | FR-D06, FR-F11; C-02, C-03, C-16, C-17, C-19, C-20 |
| Dokumen terkait | D-06 KL-01, KL-02 · D-07 Bagian 3.1, 3.2, 3.3 · D-13 Bagian 6 · D-14 Bagian 5.1 (`segmen_teks`, `dokumen_sumber.lisensi`) · spec fitur 006, 007, 019, 026, 032, 037 · TK-86 |
| Status | **Diajukan ke Gerbang 1** — 10 Oktober 2026 (KB-265) |

## Mengapa fitur ini diusulkan sekarang

Sejak fitur 037, dokumen masuk korpus lewat gerbang sungguhan, tetapi tanpa
segmen: pengambilan tidak menemukannya, dan pembaca sumber (fitur 032) selalu
menjawab "teks bagian ini tidak tersedia". Segmentasi tidak dimiliki baris
mana pun sampai pemegang gerbang menyisipkan baris 038 (P-4 A fitur 037,
KB-255). D-07 Bagian 3.2 sudah menetapkan aturannya; yang belum ada adalah
pelaksananya dan jalan sah menuju indeks.

## Temuan yang diajukan bersama usulan ini

**TK-86 · `peran_verifikasi` dapat menulis kedua indeks.** Hak bawaan skema
pada `02-skema-dan-hak.sql` memberi `peran_verifikasi` `INSERT` dan `UPDATE`
atas setiap tabel baru di `indeks_utama` dan `indeks_metadata`, sehingga ia
memegang keduanya atas `segmen_teks`. Kredensial kodenya `VERIFIKASI` justru
tanpa hak tulis indeks, dan peran yang sama membaca karantina: ia dapat
menaruh teks karantina langsung ke indeks utama, yang dibaca pemanggil model —
jalan memutar C-03 yang tidak melewati gerbang mana pun. Bentuknya sama dengan
TK-83: kode dan peladen berselisih, dan tidak ada uji yang tersambung sebagai
peran itu untuk menulis segmen. Ditemukan saat menyusun usulan ini, lewat
katalog hak peladen (P-2).

## Di luar cakupan

- **Penyematan.** Fitur 026 sudah membangun jalurnya; model sematan sungguhan
  menunggu keputusan penyedia (ADR-12). Segmen baru tersimpan tanpa vektor.
- **Perakitan jalur penjawab dari PostgreSQL** — memuat segmen untuk BM25,
  menyusun bahan validator. Tidak dimiliki baris ini.
- **Pengenalan struktur dengan model** (tata letak, tabel, gambar). Hanya
  pengenalan judul bagian berpola.
- **Penyetelan ukuran segmen.** Angkanya milik D-07 Bagian 3.2, dan
  perubahannya lewat dokumen itu, bukan lewat kode (C-16).

## Kebutuhan (EARS) yang tidak bergantung pada pertanyaan

| ID | Kebutuhan |
|---|---|
| R-01 | Segmentasi **HARUS** mengikuti D-07 Bagian 3.2: batas alami lebih dulu, ukuran sasaran 300–500 kata, tumpang tindih 50–80 kata bila satu bagian dipecah, dan bagian yang lebih pendek dari sasaran berdiri sendiri, tidak digabung |
| R-02 | Setiap segmen **HARUS** membawa penanda bagian yang menunjuk sesuatu (FR-F11); segmen tanpa penanda **TIDAK BOLEH** tersimpan |
| R-03 | Indeks tujuan **HARUS** ditetapkan saat masuk dari lisensi sumbernya, lewat `lisensi_dari_metadata` dan `indeks_bagi` fitur 006 apa adanya; lisensi yang kosong atau tidak dikenali **HARUS** berarti tertutup (KL-01, C-02) |
| R-04 | Hanya dokumen yang berada di korpus yang **BOLEH** disegmentasi; dokumen karantina **TIDAK BOLEH** sampai ke indeks mana pun (C-03) |
| R-05 | Penulisan segmen satu dokumen **HARUS** satu pernyataan: seluruh segmennya tersimpan, atau tidak satu pun |
| R-06 | Segmentasi **HARUS** deterministik: teks dan metadata yang sama menghasilkan segmen dan pengenal yang sama |
| R-07 | Teks segmen **TIDAK BOLEH** ditulis ke log (KM-03); perkakas melaporkan jumlah, bukan isi |
| R-08 | Fitur ini **TIDAK BOLEH** menambah rute maupun mengubah bentuk `/tanya` (C-20), dan **TIDAK BOLEH** memberi jalur penjawaban hak tulis (C-17) |

## Pertanyaan terbuka

Tiap pertanyaan disertai anjuran; anjuran bukan putusan.

**P-1 · Cara memotong.**

| Pilihan | Arti |
|---|---|
| A | **Otomatis menurut D-07 Bagian 3.2.** Batas alami dikenali dari judul bagian berpola — `BAB`, `Bagian`, `Pasal`, ayat `(1)`, butir bernomor, subjudul baris pendek. Bagian yang melampaui 500 kata dipecah dengan tumpang tindih; penanda bagian diambil dari judulnya, dengan nomor potongan bila dipecah. Dokumen tanpa judul dikenali dipotong menurut ukuran saja, berpenanda `Bagian 1`, `Bagian 2`, dan seterusnya. Perkakas menyediakan pratinjau sebelum menulis |
| B | Tim menandai batas bagian di dalam berkas; perkakas hanya memotong pada tanda itu |
| C | A, ditambah persetujuan manusia atas hasil pemotongan sebelum segmen masuk indeks |

**Anjuran: A.** Aturannya sudah ditetapkan D-07; pemotongan yang deterministik
dapat diulang dan diuji, sedangkan penandaan tangan berbeda di tiap orang.
Pratinjau memberi tim tempat memeriksa tanpa menambah gerbang keempat.

**P-2 · Kapan dan dengan peran apa — termasuk TK-86.**

| Pilihan | Arti |
|---|---|
| A | **Perintah perkakas tersendiri `indeks --id`, peran baru `peran_pengindeks`**: membaca teks dan metadata korpus, menambah segmen ke kedua indeks, menghapus segmen dokumen itu untuk pengindeksan ulang; tanpa karantina dan tanpa kolom vektor. Hak tambah dan ubah `peran_verifikasi` atas kedua indeks dicabut, juga pada hak bawaan skema (TK-86) |
| B | Di dalam persetujuan: dokumen masuk korpus beserta segmennya dalam pernyataan yang sama, sebagai `peran_verifikasi` yang memegang hak tambah indeks |
| C | Seperti A, tetapi hak verifikator atas indeks dibiarkan |

**Anjuran: A.** Verifikasi menilai anonimisasi; pengindeksan pekerjaan mesin
yang dapat diulang ketika D-07 berubah tanpa persetujuan ulang. Peran yang
membaca karantina tidak semestinya menulis indeks yang dibaca model. Selama
celah antara persetujuan dan pengindeksan, dokumen tampil tanpa teks — keadaan
yang sudah ditangani pembaca sumber.

**P-3 · Sumber lisensi.** Segmen membawa lisensi, tetapi gerbang ingesti tidak
pernah mencatatnya, dan D-14 menyebut `dokumen_sumber.lisensi` — "kosong
berarti tidak dapat tayang" (KL-02).

| Pilihan | Arti |
|---|---|
| A | **Dicatat saat `terima`** (`--lisensi`, keterangan dari metadata sumber), tersimpan pada penerimaan dan catatan metadata korpus; dibaca `lisensi_dari_metadata` saat pengindeksan. Dokumen lama tanpa keterangan berlisensi tertutup |
| B | Diisi saat `indeks` |
| C | Disimpulkan dari jenis sumber — ditolak D-06 KL-01, disebut agar lengkap |

**Anjuran: A.** Lisensi adalah metadata asal, sejajar dengan penerbit dan
tahun, dan yang paling tahu adalah orang yang memegang berkas sumbernya saat
mengunggah. Menambah kolom pada catatan fitur 037 adalah perubahan kontrak
yang ditulis lebih dulu ke D-14.

**P-4 · Peringkat kepercayaan dan status pada segmen.** D-14 menyebut
`segmen_teks.peringkat_kepercayaan`; tabelnya tidak memiliki kolom itu, dan
D-07 Bagian 3.2 menyebut jenis sumber dan status keberlakuan sebagai metadata
segmen.

| Pilihan | Arti |
|---|---|
| A | **Diturunkan saat dibaca**, tidak disimpan pada segmen: peringkat dari jenis pada catatan metadata korpus (`peringkat_bagi`, D-13 Bagian 6), status dari catatan status korpus. D-14 menyatakannya sebagai bidang turunan |
| B | Disimpan pada segmen saat diindeks |

**Anjuran: A.** Satu sumber kebenaran: status regulasi berubah lewat perkakas
kurasi tanpa pengindeksan ulang, dan peringkat tidak dapat berselisih dengan
jenis dokumennya.

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | D-07 Bagian 3.2 |
| R-02 | FR-F11; D-14 Bagian 5.1 `segmen_teks.penanda_bagian` |
| R-03 | FR-D06; D-06 KL-01; C-02; fitur 006 |
| R-04 | C-03; fitur 037 |
| R-05 | Pola atomik fitur 032 dan 037 |
| R-06 | Pengulangan pengindeksan; uji |
| R-07 | KM-03 |
| R-08 | C-17; C-20 |

## Kriteria penerimaan

- [ ] P-1 s.d. P-4 diputus pada Gerbang 1
- [ ] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [ ] Hak peran yang menulis segmen diuji terhadap peladen, termasuk
      penolakan bagi peran yang tidak semestinya menulisnya
- [ ] Pembaca sumber menampilkan teks bagian dokumen yang disegmentasi
- [ ] `make check` lulus enam gerbang
