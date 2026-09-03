# Spec: 024-penyimpanan-postgresql

| | |
|---|---|
| Kebutuhan | ADR-05, ADR-06, ADR-12; C-03, C-05; KA-04 |
| Dokumen terkait | D-04 ADR-05 dan ADR-06, D-09 Bagian 4, D-14 Bagian 5 |
| Pasal konstitusi yang menyentuh fitur ini | C-03, C-05, C-12 |
| Status | **Gerbang 1 lolos** — 3 September 2026, nol pertanyaan terbuka. Menunggu Gerbang 2 |
| Temuan pemicu | TK-56 |

## Tujuan

Sesudah fitur ini, data yang disimpan sistem **bertahan setelah layanan
dimatikan**. Hari ini seluruhnya hilang: `src/penyimpanan/` hanya memiliki
antarmuka abstrak `PenyimpanDasar` dan `PenyimpanTiruan` yang menyimpan dalam
ingatan proses.

Nilai fitur ini bukan menambah kemampuan melainkan **membuat yang sudah ada
bertahan**. Seluruh aturan aksesnya sudah dibangun dan diuji sejak fitur 002;
yang belum ada adalah pelaksana yang memakai basis data sesungguhnya.

## Mengapa pekerjaan ini tidak dimiliki siapa pun sampai hari ini

Dicatat karena bentuk kekosongannya berulang dan layak dikenali:

1. **ADR-05 memutuskan** PostgreSQL + pgvector sebagai basis data.
2. **ADR-12 menetapkan pola** antarmuka abstrak dengan pelaksana tiruan, tanpa
   penyedia konkret — dan menyatakan sendiri bahwa *"adaptor nyata pertama
   menjadi penguji abstraksi ini"*.
3. **Uraian `tiruan.py` menyerahkan** pekerjaan PostgreSQL kepada D-09.
4. **D-09 tidak menyebut PostgreSQL satu kali pun.**

Keputusannya ada, polanya ada, penyerahannya ada — dan penerimanya tidak ada.
Penyerahan yang menunjuk dokumen tanpa memeriksa dokumen itu menerimanya
menghasilkan pekerjaan yang tampak sudah berumah, padahal tidak.

## Di luar cakupan

Disebutkan tegas beserta sebabnya. Yang tidak disebut sebabnya akan dikerjakan
seseorang karena mengira ia terlupa.

- **Penyediaan dan pengoperasian peladen basis data** — pemasangan, cadangan,
  pemulihan, penyetelan kinerja. Itu memang pekerjaan D-09, dan pembedaannya
  dengan fitur ini tegas: **menulis adaptornya adalah kode; menyediakan
  peladennya adalah operasi.** Kekeliruan TK-56 lahir justru dari kaburnya
  batas ini.
- **Penyimpanan vektor `pgvector`.** Menunggu model sematan (fitur 019).
  Skema tabelnya disiapkan agar penambahannya tidak mengubah pemanggil, tetapi
  kolom vektornya belum diisi.
- **Pemindahan data dari penyimpan tiruan.** Tidak ada data yang perlu
  dipindahkan; isi tiruan hilang bersama prosesnya sejak semula.
- **Penyimpanan kunci pseudonim.** C-05 menuntutnya berada pada basis data
  **terpisah** dan tidak terjangkau layanan aplikasi. Fitur ini menegakkan
  keterpisahan itu pada bentuk sambungannya, tetapi penyediaan basis data
  keduanya adalah pekerjaan D-09.

## Kebutuhan (EARS)

**R-01.** Sistem WAJIB menyediakan pelaksana `PenyimpanDasar` yang menyimpan
data pada PostgreSQL, dan pelaksana itu WAJIB lulus rangkaian uji yang sama
dengan `PenyimpanTiruan` tanpa satu pun uji diubah.

**R-02.** KETIKA sebuah metode penyimpanan dipanggil, pelaksana WAJIB memeriksa
kredensial **sebelum** menyentuh data — termasuk sebelum memeriksa keberadaan
dokumen.

**R-03.** JIKA pemanggil tidak memiliki kredensial atas suatu area, MAKA
tanggapan sistem WAJIB sama persis baik dokumen itu ada maupun tidak ada.

**R-04.** Sambungan bagi jalur penjawaban WAJIB tidak memiliki hak baca atas
area karantina pada tingkat **basis data**, bukan hanya pada tingkat kode.

**R-05.** Sambungan bagi kunci pseudonim WAJIB terpisah dari sambungan data
perilaku, dan kedua sambungan itu TIDAK BOLEH dapat disusun dari satu
konfigurasi yang sama.

**R-06.** SELAMA peladen basis data belum tersedia, sistem WAJIB tetap dapat
dijalankan memakai `PenyimpanTiruan`, dan pemilihan pelaksana WAJIB dilakukan
pemanggil — bukan ditentukan pelaksana itu sendiri.

**R-07.** Nama tabel dan kolom WAJIB mengikuti kamus data D-14 Bagian 5, dalam
Bahasa Indonesia.

**R-08.** Setiap akses tercatat sebagaimana `CatatanAkses` sudah menetapkan,
tanpa mengubah bentuk catatannya.

## Keadaan yang wajib ditangani

| Keadaan | Yang wajib terjadi |
|---|---|
| Kredensial tidak menjangkau area | Ditolak, tanggapan seragam |
| Dokumen tidak ada pada area yang boleh dibaca | Galat "tidak ada" — hanya di sini |
| Peladen basis data tidak dapat dihubungi | Galat yang menyebut keadaannya, bukan galat kredensial |
| Pemindahan antar area | Menuntut hak baca asal **dan** hak tulis tujuan |
| Sambungan putus di tengah penulisan | Penulisan tidak setengah jadi |

## Keputusan Gerbang 1

Diputus pemegang Gerbang 1–4 pada 3 September 2026. Dicatat pula pada KB-077.

**1 · Satu peladen, dua basis data.** C-05 dan ADR-05 didamaikan pada tingkat
basis data, bukan peladen: satu peladen PostgreSQL menaungi dua basis data
terpisah — satu bagi data perilaku dan korpus, satu bagi kunci pemetaan
pseudonim. Keduanya disusun dari **dua konfigurasi sambungan yang berdiri
sendiri**, sehingga tidak ada satu konfigurasi pun yang dapat menghasilkan
keduanya.

Alternatif dua peladen ditolak bukan karena keamanannya kurang melainkan
karena biaya penyediaannya tidak sebanding pada TKT 3, dan karena keterpisahan
yang C-05 tuntut sudah tegak pada tingkat basis data. Bila siklus berikutnya
menaikkan tuntutannya, perpindahan ke dua peladen tidak mengubah kode
pemanggil — hanya konfigurasinya.

**2 · Karantina dipisah dengan skema terpisah _sekaligus_ pengguna basis data
terpisah.** Bukan salah satu. ADR-06 menolak penandaan status, dan C-03
berbunyi "kredensial berbeda, bukan penanda status" — pengguna basis data
terpisah itulah yang mewujudkan kata "kredensial" secara harfiah. Skema
terpisah ditambahkan di atasnya agar hak akses dapat dinyatakan sekali pada
tingkat skema, bukan diulang tabel demi tabel; hak yang harus diulang adalah
hak yang suatu hari terlupa pada satu tabel.

Biayanya diakui terus terang: penyediaan basis data menjadi lebih panjang —
D-09 wajib membuat pengguna basis data beserta pernyataan hak aksesnya, dan
penyiapan pada mesin pengembangan bertambah langkahnya. Itu harga yang
diterima sadar, bukan yang terlewat dihitung.

**3 · Penyesuaian `PenyimpanDasar` wajib melewati Gerbang 2 tersendiri.**
Ditegaskan sebagaimana diusulkan. Adaptor ini adalah penguji abstraksi
sebagaimana ADR-12 perkirakan; bila abstraksinya tidak pas, yang berubah
adalah kontrak yang lima modul sudah pakai. Perubahan semacam itu diajukan
dan menunggu, tidak diperbaiki sambil jalan.

**Tidak ada kebutuhan R-01 s.d. R-08 yang berubah karena ketiga keputusan
ini.** Ketiganya mengunci *cara* R-04 dan R-05 diwujudkan, bukan *apa* yang
dituntut. Dicatat karena kebutuhan yang diam-diam bergeser saat gerbang
ditutup adalah kekeliruan yang sulit terlihat belakangan.

## Ketertelusuran

| Kebutuhan | Diwujudkan |
|---|---|
| ADR-05 | R-01, R-07 |
| ADR-06, C-03, KA-04 | R-02, R-03, R-04 |
| C-05 | R-05 |
| ADR-12 | R-01, R-06, Keputusan Gerbang 1 nomor 3 |
| C-12 | Nol ketergantungan baru — `asyncpg` sudah pada berkas persetujuan |
| D-14 Bagian 5 | R-07 |
