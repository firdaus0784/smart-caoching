# Spec: 007-pengambilan-hibrida

| | |
|---|---|
| Kebutuhan | **ADR-03** · FR-F02 · D-07 Bagian 3.2, 3.3, 4.4, 4.6 |
| Dokumen terkait | **D-07 Bagian 4** · D-04 ADR-03, ADR-05, ADR-12 · D-14 Bagian 5 |
| Pasal konstitusi | **C-16**, C-02, C-11, C-12, C-17 |
| Urutan pembangunan | 007 pada `docs/D12.md` Bagian 7, sesudah 006 |
| Ketergantungan | **Nol paket Python baru** |
| Status | Menunggu Gerbang 1 |

## Tujuan

Sesudah fitur ini, sebuah pertanyaan dapat berubah menjadi daftar segmen
berperingkat: dua sumber kandidat mencari secara terpisah, hasilnya digabung
dengan *Reciprocal Rank Fusion*, dan yang diteruskan hanya 5–8 teratas. Yang
belum ada sebelumnya bukan pencariannya melainkan **bentuk yang membuat
pencarian dapat diperiksa** — sumber mana menyumbang segmen mana, indeks mana
yang dijangkau kredensial pemanggilnya, dan angka mana yang belum dikalibrasi.

## Mengapa fitur ini hampir tidak tertahan siapa pun

Empat fitur terakhir terbelah karena separuhnya menunggu orang di luar agen
(KB-010, KB-022, KB-028, KB-032). Fitur ini **sebagian besar tidak**, dan
sebabnya satu kalimat pada fitur 015 yang ditulis dua hari lalu:

> Kegunaan keluaran modul ini dibatasi tegas: **untuk pencarian**, bukan untuk
> menyiapkan bahan anotasi. — `src/nlp/praproses/stemming.py`

Praproses Bahasa Indonesia sudah berdiri, dan `Token.stem` sudah dinyatakan
sebagai bidang yang dipakai pencarian. BM25 adalah rumus, bukan model — ia
tidak menuntut bobot praterlatih, tidak menuntut korpus besar untuk diuji, dan
tidak menuntut satu pun paket baru. *Reciprocal Rank Fusion* juga rumus.

Yang tertahan hanya dua hal, dan keduanya nyata:

| Tertahan | Menunggu |
|---|---|
| Sumber kandidat **vektor** | Model sematan — ketergantungan baru (C-12) dan pgvector (ADR-05, D-09) |
| **Ambang kecukupan bukti** | BT-29, kalibrasi terhadap *gold set* BT-35 (bulan 4–5) — C-16 |

Bagian yang tertahan diusulkan menjadi **fitur 019**.

## Bahaya yang membentuk seluruh spesifikasi ini

ADR-03 menolak dua hal dengan tegas: **vektor saja** (gagal pada nomor
regulasi) dan **leksikal saja** (gagal pada parafrase pengguna). Fitur ini
membangun sisi leksikalnya lebih dulu.

Karena itu ada satu keadaan yang wajib mustahil: **sistem yang berjalan
dengan satu sumber saja dan tampak hibrida.** Penggabungan atas satu daftar
menghasilkan daftar itu sendiri — tanpa galat, tanpa peringatan, dengan nama
fungsi yang tetap berbunyi "hibrida". Itu bentuk kegagalan yang persis sama
dengan TA-01: laporan bersih yang tidak memeriksa apa pun.

**R-05 menutupnya**: penggabungan menolak dipanggil dengan kurang dari dua
sumber. Hari ketika sumber vektor lupa dipasang, sistem berhenti — bukan
diam-diam menjadi mesin pencari kata kunci yang ADR-03 tolak.

## Cakupan

| | Bagian | Menunggu? |
|---|---|---|
| **1** | Indeks segmen, BM25 atas stem, RRF, pembatasan kredensial, bentuk penilaian kecukupan | **Tidak** |
| **2** | Sumber vektor, model sematan, pemeringkat ulang lintas-enkoder, kalibrasi ambang | **Ya** |

Bagian 2 diusulkan menjadi **fitur 019**.

## Di luar cakupan

- **Menetapkan ambang kecukupan bukti.** D-07 Bagian 4.6 menyerahkannya ke
  BT-29 melalui kalibrasi terhadap *gold set*; C-16 melarang menyetelnya di
  luar prosedur itu. Fitur ini membangun tempatnya, **kosong**, dan membuat
  kekosongan itu tidak dapat diabaikan (R-11).
- **Penguatan kategori** (D-07 Bagian 4.4 baris terakhir). "Dikalibrasi pada
  BT-29" — sama seperti di atas.
- **Pemeriksaan cakupan domain** (tahap 1), **jawaban terkurasi** (tahap 2),
  **pemahaman pertanyaan** (tahap 3). Ketiganya mendahului pengambilan pada
  alur D-07 Bagian 4, tetapi bukan pengambilan. Tahap 3 menuntut model NER
  fitur 017.
- **Pemeriksaan keberlakuan** (tahap 6) dan **penyusunan jawaban** (tahap 8).
  Milik fitur 009; C-07 dan FR-F14 diwujudkan di sana.
- **Validator sitasi** (tahap 9). Fitur 008.
- **Segmentasi dokumen** (D-07 Bagian 3.2, 300–500 kata). Ia menyiapkan bahan,
  bukan mengambilnya, dan menuntut struktur dokumen yang belum ada sebab
  korpus belum terisi. Fitur ini menerima segmen sebagai masukan.
- **PostgreSQL dan pgvector.** ADR-12: antarmuka abstrak dengan pelaksana
  tiruan deterministik; penyebaran adalah pekerjaan D-09.
- **Menulis berkas indeks.** C-17 melarang akses tulis dari jalur penjawaban.

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | Pengambilan **HARUS** berjalan atas **segmen**, bukan dokumen utuh (D-07 Bagian 3.2) |
| R-02 | Setiap sumber kandidat **HARUS** mengembalikan daftar berperingkat, dan peringkatnya **HARUS** sama pada masukan yang sama |
| R-03 | **JIKA** dua kandidat berskor sama, **MAKA** urutannya **HARUS** diputus secara tetap dan dinyatakan — **TIDAK BOLEH** mengikuti urutan sisipan |
| R-04 | Penggabungan **HARUS** memakai *Reciprocal Rank Fusion* (D-07 Bagian 4.4; Cormack dkk. 2009), bukan pembobotan manual |
| R-05 | **JIKA** penggabungan dipanggil dengan kurang dari dua sumber, **MAKA** sistem **HARUS** menolaknya — **TIDAK BOLEH** mengembalikan urutan sumber tunggal |
| R-06 | Setiap hasil gabungan **HARUS** membawa daftar sumber yang menyumbangkannya beserta peringkatnya pada masing-masing sumber |
| R-07 | Pengambilan **HARUS** menuntut kredensial; segmen dari indeks yang **tidak** dijangkau kredensial itu **TIDAK BOLEH** muncul pada hasil (C-02, FR-D06) |
| R-08 | Jumlah kandidat per sumber dan jumlah segmen diteruskan **HARUS** mengikuti D-07 Bagian 4.4, dan angkanya **TIDAK BOLEH** tertulis di lebih dari satu tempat (C-16) |
| R-09 | BM25 **HARUS** mencocokkan atas `stem`, bukan `permukaan` (D-07 Bagian 3.3, FR-B03) |
| R-10 | **JIKA** sebuah segmen tidak memiliki penanda bagian, **MAKA** ia **TIDAK BOLEH** dapat diindeks — D-14 Bagian 5 menyatakannya wajib, dan FR-F11 gagal tanpanya |
| R-11 | Penilaian kecukupan bukti **TIDAK BOLEH** dapat dijalankan tanpa ambang hasil kalibrasi BT-29; **ambang bawaan TIDAK BOLEH ada** (C-16) |
| R-12 | Ambang yang dipakai **HARUS** membawa asal-usulnya — tanggal kalibrasi, *gold set* yang dipakai, dan pemutusnya (C-16, C-09) |
| R-13 | Setiap hasil pengambilan **HARUS** membawa versi indeks yang melayaninya (D-07 Bagian 3.3, RT-05) |
| R-14 | Pengambilan **TIDAK BOLEH** menulis apa pun (C-17) |

### Tiga kebutuhan yang paling mudah dianggap berlebihan

**R-05** dijelaskan di atas: tanpanya, sistem satu sumber tetap berjalan dan
tetap bernama hibrida.

**R-06** terlihat seperti kelengkapan diagnostik. Ia bukan. Tanpa daftar
penyumbang, tidak ada cara membedakan segmen yang ditemukan **kedua** sumber
dari segmen yang ditemukan satu sumber pada peringkat tinggi — padahal
perbedaan itulah yang membuat RRF berguna, dan ia pula yang akan dibaca saat
BT-29 mengalibrasi. Hasil tanpa penyumbang adalah hasil yang kalibrasinya
harus menebak.

**R-11 adalah inti fitur ini bagi C-16.** Bentuk yang lazim — ambang bawaan
yang "sementara" — akan berjalan pada hari pertama, memberi angka yang masuk
akal, dan tidak seorang pun akan mengalibrasinya. C-16 melarang menyetel
ambang di luar BT-29, dan cara paling sunyi melanggarnya bukan menyetel angka
melainkan **menuliskan angka awal yang tak pernah ditinjau**. Karena itu
penilaian kecukupan di sini tidak dapat dibentuk tanpa catatan kalibrasi —
bukan gagal saat dijalankan, melainkan tidak dapat disusun sama sekali.

Pola yang sama dengan `Kredensial` fitur 002: *"Parameter berbawaan `None`
akan berubah menjadi 'tanpa kredensial berarti tanpa batas' pada pemanggilan
pertama yang lupa mengisinya."*

## Keadaan yang wajib ditangani

| Keadaan | Perilaku yang dituntut |
|---|---|
| Kueri kosong atau hanya spasi | Ditolak saat pengambilan dipanggil |
| Indeks tidak memuat satu pun segmen | Hasil kosong, **bukan** galat — korpus kosong adalah keadaan sah |
| Tidak ada segmen yang cocok | Hasil kosong; penilaian kecukupan menyimpulkan tidak ditemukan |
| Penggabungan dipanggil satu sumber | **Ditolak** (R-05) |
| Sebuah sumber mengembalikan daftar kosong | Diterima; ia tetap terhitung sebagai sumber yang berpartisipasi |
| Dua sumber mengembalikan segmen yang sama | Satu hasil, dua penyumbang, skor RRF terjumlah |
| Dua kandidat berskor sama | Urutan diputus `id_segmen` menaik, dan itu dinyatakan (R-03) |
| Kredensial tidak menjangkau indeks metadata | Segmen metadata tidak muncul pada hasil sama sekali |
| Segmen tanpa penanda bagian | Ditolak saat diindeks (R-10) |
| Ambang belum dikalibrasi | Penilaian kecukupan **tidak dapat dibentuk** (R-11) |
| Kandidat lebih sedikit daripada jumlah yang diteruskan | Seluruhnya diteruskan; bukan diisi sampai penuh |

## Kriteria penerimaan

- [ ] R-01 s.d. R-14 masing-masing punya uji yang gagal sebelum implementasi
- [ ] Skor BM25 diuji terhadap **contoh yang dihitung tangan**, bukan terhadap keluaran implementasi sendiri
- [ ] Skor RRF diuji terhadap contoh yang dihitung tangan, termasuk satu contoh yang **membalik urutan** kedua sumber — sebab RRF yang tidak pernah membalik apa pun tidak dapat dibedakan dari penggabungan yang salah
- [ ] Uji bahwa penggabungan satu sumber ditolak (R-05)
- [ ] Uji bahwa kredensial `PEMANGGIL_LLM` tidak pernah menerima segmen metadata (R-07, C-02)
- [ ] Uji bahwa penilaian kecukupan tidak dapat dibentuk tanpa catatan kalibrasi (R-11)
- [ ] Nol ketergantungan Python baru
- [ ] Cakupan uji tidak turun
- [ ] **`make compliance` menyusut satu**: C-16 berpindah dari `fitur_pengunci="007 …"` menjadi `pemeriksa=`

## Pertanyaan bagi Gerbang 1

**Satu.** `docs/D14.md` Bagian 5 menyatakan `segmen_teks.penanda_bagian`
**wajib** — "Pasal, ayat, atau subjudul. Wajib; tanpanya FR-F11 gagal".
`SegmenTerindeks` yang dibangun fitur 006 **tidak memilikinya**. Ditambahkan
sekarang atau ditunda?

| | Pilihan | Akibat |
|---|---|---|
| **A** | Ditambahkan sekarang, wajib | Model sejalan dengan D-14. Uji fitur 006 disesuaikan — satu penolong, satu tempat |
| **B** | Ditambahkan sekarang, boleh kosong | Sejalan dengan namanya saja. Segmen tanpa penanda tetap terindeks, dan kegagalan FR-F11 muncul pada fitur 009 |
| **C** | Ditunda ke fitur 009 yang memakainya | Pengambilan mengembalikan segmen yang tidak dapat disitasi, dan itu baru ketahuan dua fitur kemudian |

**Saran saya: A.** Fitur ini adalah pemakai pertama segmen. Segmen yang
diambil tetapi tidak dapat disitasi adalah segmen yang gagal pada titik kritis
T2 (D-02) — dan C memindahkan penemuan kegagalannya ke fitur 009, ketika
indeksnya mungkin sudah terisi. B lebih buruk daripada C: ia menambahkan
bidang yang menenangkan tanpa menegakkan apa pun.

**Dua.** Nilai konstanta *k* pada RRF. D-07 Bagian 4.4 menyebut metodenya
tetapi tidak nilainya. Menuliskan 60 — nilai pada Cormack dkk. 2009, sumber
yang D-07 dan ADR-03 kutip — apakah "menyetel ambang" yang C-16 larang?

| | Pilihan | Akibat |
|---|---|---|
| **A** | Pakai 60, dinyatakan sebagai nilai dari sumber yang dikutip, ditinjau pada BT-29 | Penggabungan dapat berjalan dan diuji sekarang. Angkanya dapat ditelusuri ke satu makalah |
| **B** | Tunda sampai BT-29 | RRF tidak dapat dijalankan sama sekali, sehingga seluruh Bagian 1 ikut tertahan |

**Saran saya: A**, dengan satu syarat: nilainya berada pada rumah tetapan yang
sama dengan angka D-07 lainnya, dan uraiannya menyebut makalahnya, bukan
"nilai umum". C-16 melarang menyetel ambang **di luar prosedur kalibrasi**;
menyalin nilai dari sumber yang dokumen pengendalinya kutip bukan menyetel,
melainkan mengutip. Bedanya nyata dan wajib terbaca dari kodenya — bila tidak
terbaca, ia menjadi angka yang disetel seseorang.

**Tiga.** Bentuk sumber vektor sebelum modelnya ada. R-05 menuntut dua sumber;
sumber kedua belum dapat dibangun.

| | Pilihan | Akibat |
|---|---|---|
| **A** | Antarmuka `SumberKandidat` + pelaksana tiruan deterministik pada `tests/` | Mengikuti ADR-12, sudah terbukti dua kali (fitur 002, fitur 015). Tiruannya tidak ikut terkirim |
| **B** | Pelaksana vektor kosong pada `src/` yang mengembalikan daftar kosong | Ia **memenuhi** R-05 tanpa mencari apa pun — persis kegagalan yang R-05 tutup |
| **C** | Tunda seluruh penggabungan ke fitur 019 | RRF tidak diuji sampai bulan 5, padahal ia rumus murni yang dapat diuji hari ini |

**Saran saya: A.** B ditolak tegas: pelaksana kosong pada `src/` adalah cara
R-05 dilanggar sambil tampak dipatuhi.

## Pertanyaan bagi Gerbang 2

**Empat.** `src/rag/` perlu mengimpor `src/nlp/praproses/` — BM25 mencocokkan
atas `stem` (R-09, D-07 Bagian 3.3). **Tepi `rag → nlp` tidak tertulis pada
`AGENTS.md`.** Yang tertulis hanya `api → {nlp, rag, ingest}` dan
`ingest → nlp`.

`AGENTS.md` sendiri menyatakan mengapa hal ini tidak boleh lewat diam-diam:

> Tepi itu ada karena … ia dituliskan agar impornya terbaca sebagai rancangan,
> bukan sebagai kebiasaan yang tidak dijelaskan dokumen mana pun.

**Saran saya:** tepinya ditambahkan ke `AGENTS.md` secara tegas — `rag` boleh
memanggil `nlp`, satu jurusan; `nlp` tidak memanggil `rag`. Alasannya sudah
tertulis pada fitur 015 (`stemming.py`: keluarannya "untuk pencarian"), dan
pencarian tinggal di `rag`. Preseden bentuknya: penambahan `src/penyimpanan/`
pada Gerbang 2 fitur 002.

Bila jawabannya tidak, satu-satunya jalan lain adalah menyalin praproses ke
`src/rag/` — dua tempat yang akan berbeda, dan yang berbeda adalah yang tidak
diperbarui.
