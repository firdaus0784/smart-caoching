# Tasks: 007-pengambilan-hibrida

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 (KB-034) |
| Plan | `plan.md`, lolos Gerbang 2 (KB-034) |
| Status | Menunggu Gerbang 3 |
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
| B-2 | BM25 atas `stem`; `IndeksLeksikal` membawa versinya | **Uji: skor terhadap contoh yang dihitung tangan.** Uji: pasangan sama-stem beda-permukaan tetap ditemukan. Uji: indeks kosong menghasilkan hasil kosong, bukan galat | R-09, R-13 | [ ] |
| B-3 | *Reciprocal Rank Fusion* | **Uji: skor terhadap contoh hitung tangan yang membalik urutan kedua sumber.** **Uji: satu sumber ditolak.** Uji: setiap hasil membawa penyumbangnya | R-04, R-05, R-06 | [ ] |

**B-3 adalah tugas terpenting fitur ini.** RRF atas satu daftar mengembalikan
daftar itu — tanpa galat, dengan nama fungsi yang tetap berbunyi hibrida. Uji
yang membalik urutan wajib ada: penggabungan yang tidak pernah membalik apa
pun tidak dapat dibedakan dari penggabungan yang salah.

## Fase C · Kredensial, ambang, dan pemeriksanya

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | Penyusun hibrida: kredensial diperiksa **sebelum** sumber dijalankan | **Uji: `PEMANGGIL_LLM` tidak pernah menerima segmen metadata.** Uji: indeks yang tak dijangkau tidak dicari sama sekali. Uji: tidak menulis apa pun | R-07, R-14 | [ ] |
| C-2 | `AmbangKecukupan` yang menuntut `CatatanKalibrasi`; `PenilaianKecukupan` | **Uji: ambang tanpa catatan kalibrasi tidak dapat dibentuk.** Uji: tidak ada nilai bawaan. Uji: catatan wajib menyebut tanggal, *gold set*, pemutus | R-11, R-12 | [ ] |
| C-3 | Pemeriksa C-16 dan pemindahannya pada `daftar_pasal.py` | **Uji: `make compliance` menyusut satu — 10 lulus, 10 belum.** Uji: ketiga aturan menyala pada pohon yang sengaja dirusak | R-08, R-11 | [ ] |

**C-2 adalah tempat C-16 dipatuhi atau dilanggar diam-diam.** Ambang bawaan
"sementara" berjalan pada hari pertama, memberi angka masuk akal, dan tidak
seorang pun kembali kepadanya. Ambang di sini karena itu tidak dapat **disusun**
tanpa catatan kalibrasi — bukan gagal saat dijalankan.

**C-3 diuji terhadap pohon yang sengaja dirusak.** Pelajaran fitur 006:
pemeriksa yang terdaftar tetapi tidak memeriksa apa pun melapor LULUS dengan
cara yang persis sama dengan pemeriksa yang benar.

## Verifikasi akhir

- [ ] `make check` lulus 6 gerbang
- [ ] `make compliance` **menyusut satu** — 10 lulus, 0 gagal, **10** belum
- [ ] Kedelapan uji mutasi `plan.md` Bagian 6 dijalankan; hasilnya dilaporkan apa adanya
- [ ] Cakupan uji tidak turun
- [ ] **Nol ketergantungan baru**
- [ ] `AGENTS.md` memuat tepi `rag → nlp` beserta alasannya

## Yang tidak dikerjakan di sini

Sumber kandidat vektor, pemeringkat ulang lintas-enkoder, nilai ambang tinggi
dan menengah, dan penguatan kategori — seluruhnya **fitur 019**, tertahan pada
model sematan (C-12), pgvector (ADR-05), dan *gold set* BT-35 bulan 4–5.

Fitur ini membangun tempat bagi keempatnya dan membuat kekosongannya tidak
dapat diabaikan. Itu bedanya dengan menundanya diam-diam.
