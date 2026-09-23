# Spec: 026-penyematan-korpus

| | |
|---|---|
| Kebutuhan | R-06 fitur 019; C-09, C-02, C-03, C-12; ADR-05, ADR-12 |
| Dokumen terkait | D-07 Bagian 3.3 dan 4.4, D-10 Bagian 3 dan 4, D-14 Bagian 5 |
| Temuan asal | **TK-57** `docs/D00.md` Bagian 7.12 |
| Status | **Menunggu Gerbang 1** |

## Tujuan

Fitur 019 membangun sisi semantik **pembacaan**: `SumberVektor` mencari
segmen terdekat dengan kueri. Sisi **penulisannya** tidak dibangun siapa pun.
Vektor pada `indeks_utama.segmen_teks.vektor` dan pasangannya di
`indeks_metadata` hari ini diisi oleh perkakas SQL dan oleh berkas uji —
bukan oleh kode yang disebarkan.

Akibatnya bukan soal kerapian. R-06 fitur 019 berbunyi: *"Penyemat WAJIB
mencatat nama dan versi model pada setiap keluaran yang dipakai **membentuk
indeks**"*. Tidak ada pembentukan indeks, sehingga tidak ada yang mencatat
apa pun. **Indeks dapat dibangun dua kali dengan model berbeda tanpa satu
catatan pun yang membedakannya**, dan percobaan D-10 L1 yang membandingkan
keduanya membandingkan sesuatu yang tidak diketahui apa yang berubah.

Fitur ini menambahkan jalur penyematan korpus: membaca segmen yang belum
tersemat, menyematkannya lewat `Penyemat`, menuliskan vektornya, dan
**mencatat versi penyemat beserta versi indeks yang dihasilkannya**.

## Bagaimana temuan ini ditemukan, dan mengapa itu dicatat di sini

Bukan lewat pembacaan. Uji mutasi **M-7** fitur 019 berbunyi "versi penyemat
tidak masuk keluaran", dan ketika hendak dipasang ternyata **tidak ada yang
dapat dimutasi**: `Penyemat.versi` hanya muncul pada satu pesan galat
pemasangan. Mutasi yang tidak dapat dipasang adalah pernyataan bahwa sifatnya
belum ada.

Fitur 019 menutup sisi pencariannya dengan `HasilSumber.versi_penyemat`, dan
menyatakan terus terang pada docstring bidang itu bahwa **setengah R-06 tetap
terbuka**. Fitur ini menutup setengah yang lain.

## Bentuk yang sudah ada, dan yang karenanya tidak perlu dibangun ulang

| Sudah ada | Dari | Yang fitur ini pakai |
|---|---|---|
| `Penyemat`, `VersiPenyemat`, `PenyematTiruan` | 019 T-3 | Antarmuka penyematan; pelaksana tiruan bagi uji |
| Kolom `vektor vector(N)` pada kedua skema | 019 T-4 | Sasaran tulis |
| `pastikan_dimensi_cocok`, `dimensi_kolom` | 019 T-4 | Penolakan ketidakcocokan saat penyusunan |
| `PenyimpanPostgres`, kredensial per area | 024 | Akses tulis dengan kredensial yang benar |
| `src/logbook/` penulis tambah-saja | 002 | Pencatatan C-09 |
| `HasilSumber.segmen_tanpa_vektor` | 019 T-6 | Angka yang fitur ini turunkan ke nol |

**Fitur ini karena itu tidak memperkenalkan satu pun konsep baru.** Ia
menyambungkan yang sudah ada. Bila ternyata ia menuntut perubahan pada
`Penyemat` atau pada `PenyimpanDasar`, itu temuan — abstraksinya yang salah,
dan perubahannya melewati Gerbang 2 tersendiri.

## Apa yang dapat dibangun sekarang, dan apa yang tidak

**Dapat, seluruhnya.** Jalur penyematan dapat dibangun dan diuji ujung ke
ujung dengan `PenyematTiruan`, persis sebagaimana `SumberVektor` dibangun dan
diuji tanpa model sungguhan. Bobot model tidak menghalangi fitur ini.

**Tidak dapat.** Menyatakan indeks produksi sudah tersemat — itu menunggu
bobot model sungguhan dan korpus yang belum ada. Fitur ini membangun
**jalurnya**, bukan mengisinya.

Pembedaan itu dinyatakan di muka karena ia yang menentukan apakah fitur ini
tertahan atau tidak. Ia **tidak** tertahan.

## Di luar cakupan

- Adaptor penyemat sungguhan (`sentence-transformers`) — pustakanya sudah
  disetujui dan terpasang, tetapi memilih model dan mengunduh bobotnya
  keputusan tim, bukan keputusan fitur ini
- Menyetel ambang mana pun — C-16, dan fitur 025 yang memilikinya
- Penjadwalan otomatis penyematan ulang — ia operasi (D-09), bukan kode
- Mengubah bentuk tanggapan `/api/v1/tanya` — C-20
- Menyematkan segmen karantina — C-03 melarangnya, dan kredensialnya memang
  tidak menjangkau
- Membangun antarmuka bagi jalur ini — tidak ada rute baru; D-14 Bagian 3
  tidak memuatnya, dan AG-02 melarang menambahnya

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | Sistem **HARUS** menyediakan jalur yang membaca segmen ber-`vektor` NULL pada satu indeks, menyematkannya, dan menuliskan hasilnya |
| R-02 | **KETIKA** sebuah pembangunan indeks selesai, sistem **HARUS** mencatat nama penyemat, versi penyemat, versi indeks yang dihasilkan, jumlah segmen tersemat, dan waktu UTC ke `logbook/` |
| R-03 | **JIKA** dimensi penyemat tidak sama dengan dimensi kolom, **MAKA** sistem **TIDAK BOLEH** menulis satu baris pun, dan **HARUS** menolak sebelum penyematan dimulai |
| R-04 | Penyemat **HARUS** diserahkan pemanggil, sebagaimana R-02 fitur 019 — jalur ini **TIDAK BOLEH** menyusun penyematnya sendiri |
| R-05 | **SELAMA** penyematan berjalan, segmen yang gagal disemat **HARUS** ditinggalkan `NULL` dan jumlahnya dilaporkan; ia **TIDAK BOLEH** ditulis dengan vektor pengganti |
| R-06 | Jalur ini **HARUS** menyematkan `indeks_utama` dan `indeks_metadata` **terpisah**, dengan kredensial masing-masing — C-02 memisahkan pada tingkat indeks, bukan saat kueri |
| R-07 | Jalur ini **TIDAK BOLEH** menjangkau area karantina dalam bentuk apa pun — C-03 |
| R-08 | Menjalankan ulang jalur ini atas indeks yang sudah tersemat penuh **HARUS** aman dan **TIDAK BOLEH** menulis ulang vektor yang sudah ada, kecuali diminta tegas |
| R-09 | **JIKA** versi penyemat berbeda dari versi yang tercatat bagi indeks itu, **MAKA** sistem **HARUS** menolak penyematan sebagian, sebab indeks bercampur dua model tidak dapat dibandingkan jaraknya |
| R-10 | Fitur ini **TIDAK BOLEH** mengubah `SumberVektor`, `ambil_hibrida`, maupun bentuk `HasilSumber` |

## Keadaan yang wajib ditangani

| Keadaan | Yang wajib terjadi |
|---|---|
| Indeks kosong sama sekali | Selesai tanpa galat; catatan menyebut nol segmen |
| Seluruh segmen sudah tersemat | Selesai tanpa menulis; catatan menyebut nol segmen baru |
| Penyemat berdimensi lain daripada kolom | Ditolak sebelum satu baris pun ditulis (R-03) |
| Indeks sudah tersemat dengan model lain | Ditolak dengan pesan yang menyebut kedua versi (R-09) |
| Sambungan putus di tengah | Segmen yang sudah tertulis tetap sah; sisanya tetap `NULL` dan terhitung |
| Kredensial tidak menjangkau indeks sasaran | Ditolak peladen, bukan disaring kode |
| Segmen bertext kosong | Dilewati dan dihitung, bukan disemat menjadi vektor nol |

## Pertanyaan terbuka

Ditulis di sini alih-alih ditebak. **Fitur dengan pertanyaan terbuka tidak
diserahkan ke agen** — ketiganya menuntut putusan Gerbang 1.

**P-1 · Di mana jalur ini tinggal?** Tiga kemungkinan, dan masing-masing
membawa akibat arah impor yang berbeda:
(a) `src/rag/indeks/` — dekat dengan yang membacanya, tetapi memberi `rag`
hak tulis, dan C-17 melarang akses tulis **dari jalur penjawaban**; jalur ini
bukan jalur penjawaban, tetapi kedekatannya mengundang keliru baca.
(b) `src/penyimpanan/` — dekat dengan yang menulisnya, dan kredensialnya
sudah di sana; tetapi ia lapisan di bawah dan tidak boleh memanggil `llm`.
(c) `src/ingest/` — ia yang sudah memanggil `llm` dan `nlp`, dan penyematan
adalah kelanjutan alami penerimaan korpus. **Anjuran saya: (c)**, sebab
tepinya sudah ada dan tidak satu pun aturan arah perlu ditambah.

**P-2 · Apa yang menjadi "versi indeks"?** `HasilSumber.versi_indeks` sudah
dipakai sejak fitur 007 dan hari ini diserahkan pemanggil sebagai untai.
Sesudah fitur ini, versi itu **dihasilkan** oleh pembangunan indeks. Yang
perlu diputus: bentuknya — cap waktu, cacah naik, atau ringkasan isi — dan
siapa yang menyimpannya. Untai yang dikarang pemanggil dan untai yang
dihasilkan pembangunan tidak boleh sama bentuknya, sebab keduanya akan
tertukar.

**P-3 · R-09 menuntut versi penyemat tersimpan per indeks. Di mana?**
Kolom pada tabel indeks akan berulang di tiap baris; tabel metadata indeks
tersendiri belum ada pada D-14 Bagian 5, dan menambahnya menyentuh kamus
data. Perlu putusan, dan bila jawabannya tabel baru maka D-14 ikut berubah.

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01, R-02 | R-06 fitur 019; C-09; TK-57 |
| R-03 | R-08 fitur 019 |
| R-04 | R-02 fitur 019 |
| R-06 | C-02, FR-D06 |
| R-07 | C-03, ADR-06 |
| R-09 | D-07 Bagian 3.3 — jarak hanya bermakna di dalam satu ruang sematan |
| R-10 | ADR-12: abstraksi diuji pelaksana, bukan diubah olehnya |

## Kriteria penerimaan

- [ ] R-01 s.d. R-10 punya uji yang gagal sebelum implementasi
- [ ] Uji mutasi disusun pada `plan.md` dan dilaporkan apa adanya, termasuk
      yang tidak menyala beserta sebabnya
- [ ] **M-7 fitur 019 dapat dipasang dan menyala** — ia tidak dapat dipasang
      sama sekali sebelum fitur ini
- [ ] `make check` lulus enam gerbang; cakupan tidak turun
- [ ] `HasilSumber.versi_penyemat` docstring diperbarui: setengah R-06 yang
      dinyatakan terbuka di sana kini tertutup
- [ ] TK-57 berpindah ke **Selesai** pada `docs/D00.md` Bagian 7.12
