# Spec: 026-penyematan-korpus

| | |
|---|---|
| Kebutuhan | R-06 fitur 019; C-09, C-02, C-03, C-12; ADR-05, ADR-12 |
| Dokumen terkait | D-07 Bagian 3.3 dan 4.4, D-10 Bagian 3 dan 4, D-14 Bagian 5 |
| Temuan asal | **TK-57** `docs/D00.md` Bagian 7.12 |
| Status | **Gerbang 1 lolos** — 23 September 2026, nol pertanyaan terbuka (KB-110). Menunggu Gerbang 2 |

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
| R-11 | Nama bidang **HARUS** mengikuti `docs/D04.md` Bagian 7.2: `segmen_teks.vektor_sematan` dan `segmen_teks.versi_model_sematan` |

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

## Keputusan Gerbang 1

### K-1 · Jalur ini tinggal di `src/ingest/`

**Diputus pemegang Gerbang 1–4, 23 September 2026.**

Tepi `ingest → llm` dan `ingest → nlp` sudah ada dan sudah tertulis pada
`AGENTS.md`, sehingga tidak satu pun aturan arah perlu ditambah. Dua
kemungkinan lain ditolak: `src/rag/` akan memberi hak tulis kepada lapisan
yang C-17 justru batasi, dan `src/penyimpanan/` lapisan di bawah yang tidak
boleh memanggil `llm`.

### K-2 · Versi indeks berupa cap waktu UTC pembangunan, bukan cacah naik

**Diputus agen.** D-07 Bagian 3.3 menuntut *"setiap pembangunan ulang
menghasilkan nomor versi"*, dan RI-11 menuntut penyimpanan sementara
kedaluwarsa ketika indeks dibangun ulang. Keduanya menuntut satu sifat:
**nilainya berubah pada tiap pembangunan, dan tidak pernah terpakai ulang.**

Cacah naik menuntut keadaan tersimpan, dan keadaan tersimpan dapat hilang
atau disetel ulang. Cacah yang tersetel ulang **memakai kembali nomor versi
yang sudah pernah dipakai** — tanpa galat, dan dua percobaan berbeda
kemudian tercatat pada versi indeks yang sama. Itu kegagalan yang lebih buruk
daripada tidak punya versi sama sekali.

Cap waktu tidak menuntut keadaan tersimpan dan tidak dapat terpakai ulang.
Bentuknya `<indeks>-<YYYYMMDDTHHMMSSZ>`, UTC mengikuti KM-01.

**Yang membuat keputusan ini salah:** bila dua pembangunan indeks dapat
selesai dalam detik yang sama. Bila itu terjadi, bentuknya diperhalus, bukan
diganti menjadi cacah.

Bentuk ini juga **berbeda dari untai yang diserahkan pemanggil** hari ini
(`uji-1`, `leksikal-7`), sehingga keduanya tidak dapat tertukar saat dibaca
pada catatan percobaan D-10 L1.

### K-3 · Versi penyemat disimpan sebagai kolom — dan itu bukan keputusan baru

**Sudah ditetapkan `docs/D04.md` Bagian 7.2 sebelum proyek ini dimulai.**
Baris `segmen_teks` di sana berbunyi:

> `id, id_dokumen, urutan, teks, vektor_sematan, versi_model_sematan`

Pertanyaan P-3 pada rancangan spec ini **keliru diajukan sebagai pertanyaan
terbuka**. Jawabannya sudah ada, dan yang kurang adalah pembacaan dokumen
pemiliknya. Dicatat apa adanya alih-alih diperbaiki diam-diam.

Kolom per baris juga bentuk yang lebih kuat bagi R-09: indeks yang bercampur
dua model terdeteksi dengan `SELECT DISTINCT versi_model_sematan`, dan
kebenarannya tinggal **bersama datanya**. Tabel metadata tersendiri dapat
hanyut dari baris yang digambarkannya, dan proyek ini sudah mencatat bentuk
hanyut itu berkali-kali.

### K-4 · Fitur 019 menyimpang dari D-04, dan fitur ini yang meluruskannya

Ditemukan saat menjawab K-3. `perkakas/basis_data/05-kolom-vektor.sql`
menamai kolomnya **`vektor`**, sedangkan D-04 Bagian 7.2 menetapkan
**`vektor_sematan`**; dan **`versi_model_sematan` tidak pernah dibuat sama
sekali**. Kedua nama itu tidak muncul di satu baris kode pun — hanya pada
D-04 baris 178.

`AGENTS.md` menetapkan nama bidang mengikuti `docs/D14.md` Bagian 5. D-14
tidak menamai kedua bidang ini, dan D-04 Bagian 7.2 yang menamainya —
sehingga D-04 yang berwenang di sini. Tercatat sebagai **TK-60**.

Meluruskannya tugas fitur ini, bukan tambalan pada fitur 019 yang sudah lolos
Gerbang 4. `plan.md` yang menetapkan caranya: penggantian nama kolom
menyentuh `05-kolom-vektor.sql`, `SumberVektor`, dan berkas uji, dan
**besarnya perubahan itu wajib dinyatakan di muka** — `plan.md` fitur 019
dua kali menyatakan blast radius di bawah kenyataan (KB-094, KB-100).

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
| R-11 | D-04 Bagian 7.2; TK-60 |

## Kriteria penerimaan

- [ ] R-01 s.d. R-10 punya uji yang gagal sebelum implementasi
- [ ] Uji mutasi disusun pada `plan.md` dan dilaporkan apa adanya, termasuk
      yang tidak menyala beserta sebabnya
- [ ] **M-7 fitur 019 dapat dipasang dan menyala** — ia tidak dapat dipasang
      sama sekali sebelum fitur ini
- [ ] `make check` lulus enam gerbang; cakupan tidak turun
- [ ] `HasilSumber.versi_penyemat` docstring diperbarui: setengah R-06 yang
      dinyatakan terbuka di sana kini tertutup
- [ ] TK-57 dan **TK-60** berpindah ke **Selesai** pada `docs/D00.md` Bagian 7.12
