# Tasks: 007-pengambilan-hibrida

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 (KB-034) |
| Plan | `plan.md`, lolos Gerbang 2 (KB-034) |
| Status | **Lolos Gerbang 4** — 12 Agustus 2026 (KB-035). Tujuh tugas selesai |
| Jumlah tugas | **7** |
| Ketergantungan baru | **Nol** |

## Fase A · Bahan yang dicari

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `penanda_bagian` wajib pada `SegmenTerindeks`; uji fitur 006 disesuaikan | **Uji: segmen tanpa penanda bagian tidak dapat dibentuk.** Uji: penanda kosong atau hanya spasi ditolak | R-10 | [x] — dipangkas saat masuk; `min_length` sendirian meloloskan `" "` |
| A-2 | `tetapan.py` — angka D-07 Bagian 4.4 dan konstanta RRF, masing-masing menyebut sumbernya; masuk `RUMAH_TETAPAN` | Uji: setiap tetapan punya uraian yang menyebut dokumen atau makalahnya. Uji: tidak ada angka D-07 di berkas lain | R-08 | [x] — kekosongan ambang kecukupan ikut diuji; ia bukan keadaan sementara |

**A-1 memperbaiki kelalaian fitur 006, bukan menambah kemewahan.** D-14
Bagian 5 menyatakan `segmen_teks.penanda_bagian` wajib — "tanpanya FR-F11
gagal" — dan `SegmenTerindeks` dibangun tanpanya. Segmen yang diambil tetapi
tidak dapat disitasi gagal pada titik kritis T2 (D-02).

## Fase B · Mencari dan menggabungkan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | `Kandidat` dan antarmuka `SumberKandidat`; tiruan deterministik pada `tests/` | Uji: peringkat sama pada masukan sama. **Uji: seri diputus `id_segmen`, bukan urutan sisipan** | R-01, R-02, R-03 | [x] — tiruannya tinggal di `tests/`, dan itu penegakan R-05 bukan kerapian |
| B-2 | BM25 atas `stem`; `IndeksLeksikal` membawa versinya | **Uji: skor terhadap contoh yang dihitung tangan.** Uji: pasangan sama-stem beda-permukaan tetap ditemukan. Uji: indeks kosong menghasilkan hasil kosong, bukan galat | R-09, R-13 | [x] — skor 0,8631 diturunkan tangan; k1 dan b pindah ke rumah tetapan |
| B-3 | *Reciprocal Rank Fusion* | **Uji: skor terhadap contoh hitung tangan yang membalik urutan kedua sumber.** **Uji: satu sumber ditolak.** Uji: setiap hasil membawa penyumbangnya | R-04, R-05, R-06 | [x] — SEG-A jatuh dari peringkat 1 ke 3; contoh itu yang membuktikan penggabungannya menggabungkan |

**B-3 adalah tugas terpenting fitur ini.** RRF atas satu daftar mengembalikan
daftar itu — tanpa galat, dengan nama fungsi yang tetap berbunyi hibrida. Uji
yang membalik urutan wajib ada: penggabungan yang tidak pernah membalik apa
pun tidak dapat dibedakan dari penggabungan yang salah.

## Fase C · Kredensial, ambang, dan pemeriksanya

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | Penyusun hibrida: kredensial diperiksa **sebelum** sumber dijalankan | **Uji: `PEMANGGIL_LLM` tidak pernah menerima segmen metadata.** Uji: indeks yang tak dijangkau tidak dicari sama sekali. Uji: tidak menulis apa pun | R-07, R-14 | [x] — diuji lewat `dipanggil`, bukan lewat "hasilnya kosong" |
| C-2 | `AmbangKecukupan` yang menuntut `CatatanKalibrasi`; `PenilaianKecukupan` | **Uji: ambang tanpa catatan kalibrasi tidak dapat dibentuk.** Uji: tidak ada nilai bawaan. Uji: catatan wajib menyebut tanggal, *gold set*, pemutus | R-11, R-12 | [x] — tidak dapat **disusun** tanpa kalibrasi, bukan gagal saat dijalankan |
| C-3 | Pemeriksa C-16 dan pemindahannya pada `daftar_pasal.py` | **Uji: `make compliance` menyusut satu — 10 lulus, 10 belum.** Uji: ketiga aturan menyala pada pohon yang sengaja dirusak | R-08, R-11 | [x] — 10 lulus / 0 gagal / 10 belum; buku besar tagihan pindah ke berkasnya sendiri |

**C-2 adalah tempat C-16 dipatuhi atau dilanggar diam-diam.** Ambang bawaan
"sementara" berjalan pada hari pertama, memberi angka masuk akal, dan tidak
seorang pun kembali kepadanya. Ambang di sini karena itu tidak dapat **disusun**
tanpa catatan kalibrasi — bukan gagal saat dijalankan.

**C-3 diuji terhadap pohon yang sengaja dirusak.** Pelajaran fitur 006:
pemeriksa yang terdaftar tetapi tidak memeriksa apa pun melapor LULUS dengan
cara yang persis sama dengan pemeriksa yang benar.

## Verifikasi akhir

- [x] `make check` lulus 6 gerbang
- [x] `make compliance` **menyusut satu** — 10 lulus, 0 gagal, **10** belum — separuh dari dua puluh
- [x] Kedelapan uji mutasi `plan.md` Bagian 6 dijalankan; **seluruhnya menyala** — pertama kalinya sejak fitur 003
- [x] Cakupan uji tidak turun — 99,78% atas 1.925 pernyataan; penanda dinaikkan ke 99,77
- [x] **Nol ketergantungan baru** — tetap 10 langsung, 26 terkunci
- [x] `AGENTS.md` memuat tepi `rag → nlp` beserta alasannya

## Hasil kedelapan uji mutasi

| | Mutasi | Uji yang menyala |
|---|---|---|
| M-1 | `gabung_peringkat` menerima satu sumber | 3 uji, termasuk `test_satu_sumber_ditolak` |
| M-2 | RRF memakai `1/peringkat` | 2 uji — contoh hitung tangan dan uji penyebut |
| M-3 | BM25 mencocokkan `permukaan` | 2 uji — pasangan sama-stem dan ketiga imbuhan |
| M-4 | Seri diputus urutan sisipan | 2 uji, pada `kandidat` dan pada `bm25` |
| M-5 | Kredensial diperiksa sesudah pencarian | 3 uji, seluruhnya lewat pencacah `dipanggil` |
| M-6 | `penanda_bagian` berbawaan `""` | 2 uji |
| M-7 | `AmbangKecukupan` berkalibrasi berbawaan | 2 uji |
| M-8 | `penyumbang` hanya sumber peringkat terbaik | 3 uji |

**Seluruh delapan menyala, dan tidak satu pun menuntut uji tambahan.** Itu
pertama kalinya sejak fitur 003 — pada 003, 004, dan 016 sebagian mutasi tidak
menyala dan menyingkap celah pada ujinya, bukan pada mutasinya.

Dua celah tetap ditemukan pada fitur ini, hanya bukan lewat mutasi:
sapuan R-08 menolak letak `JUMLAH_SEGMEN_RELEVAN_MINIMUM`, dan uji hitungan
tagihan fitur 006 menolak angka yang sudah usang. Keduanya penjagaan yang
sudah ada dan menyala tepat waktu.

## Yang tidak dikerjakan di sini

Sumber kandidat vektor, pemeringkat ulang lintas-enkoder, nilai ambang tinggi
dan menengah, dan penguatan kategori — seluruhnya **fitur 019**, tertahan pada
model sematan (C-12), pgvector (ADR-05), dan *gold set* BT-35 bulan 4–5.

Fitur ini membangun tempat bagi keempatnya dan membuat kekosongannya tidak
dapat diabaikan. Itu bedanya dengan menundanya diam-diam.
