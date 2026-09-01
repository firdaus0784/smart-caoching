# Spec: 024-penyimpanan-postgresql

| | |
|---|---|
| Kebutuhan | ADR-05, ADR-06, ADR-12; C-03, C-05; KA-04 |
| Dokumen terkait | D-04 ADR-05 dan ADR-06, D-09 Bagian 4, D-14 Bagian 5 |
| Pasal konstitusi yang menyentuh fitur ini | C-03, C-05, C-12 |
| Status | Menunggu Gerbang 1 |
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

## Pertanyaan yang wajib dijawab Gerbang 1

1. **Satu basis data atau dua?** C-05 menuntut kunci pseudonim terpisah dari
   data perilaku. ADR-05 menyebut "satu PostgreSQL". Keduanya dapat didamaikan
   dengan dua basis data pada satu peladen, atau dua peladen. **Pilihan ini
   menentukan bentuk konfigurasi dan tidak boleh diputuskan saat menulis kode.**

2. **Pemisahan area karantina diwujudkan bagaimana?** ADR-06 menolak penandaan
   status; pilihannya antara pengguna basis data terpisah dengan hak berbeda,
   atau skema terpisah. Keduanya memenuhi C-03; yang pertama lebih tegas dan
   lebih mahal disiapkan.

3. **Adaptor ini menguji abstraksi — apa yang terjadi bila tidak pas?**
   ADR-12 sudah memperkirakan kemungkinan ini dan menetapkan setiap penyesuaian
   dicatat, bukan diperbaiki diam-diam. Perlu ditegaskan bahwa penyesuaian
   `PenyimpanDasar` yang lahir dari sini **wajib melewati Gerbang 2 tersendiri**,
   sebab ia mengubah kontrak yang lima modul sudah pakai.

## Ketertelusuran

| Kebutuhan | Diwujudkan |
|---|---|
| ADR-05 | R-01, R-07 |
| ADR-06, C-03, KA-04 | R-02, R-03, R-04 |
| C-05 | R-05 |
| ADR-12 | R-01, R-06, pertanyaan Gerbang 1 nomor 3 |
| C-12 | Nol ketergantungan baru — `asyncpg` sudah pada berkas persetujuan |
| D-14 Bagian 5 | R-07 |
