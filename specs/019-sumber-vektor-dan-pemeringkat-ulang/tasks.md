# Tasks: 019-sumber-vektor-dan-pemeringkat-ulang

| | |
|---|---|
| Spec | Gerbang 1 lolos 20 September 2026 |
| Plan | Gerbang 2 lolos 20 September 2026 |
| Gerbang 3 | Lolos 20 September 2026 |
| Status | **Gerbang 4 lolos** — 23 September 2026. Sembilan dari sembilan tugas selesai (KB-106) |
| Kebutuhan | ADR-03 sisi semantik, ADR-05, ADR-12; BT-30; C-02, C-08, C-09, C-12 |

Satu tugas = satu commit. Uji ditulis lebih dulu. `make check` lulus sebelum
tiap tugas dinyatakan selesai — dijalankan sebagai perintah berdiri sendiri,
tanpa pipa (KB-080).

---

## T-1 · `SumberKandidat.cari` menjadi asinkron — sendirian

**Kebutuhan:** Keputusan Gerbang 1 nomor 1.

Tidak ada sumber baru ditambahkan pada tugas ini. `cari` menjadi `async def`;
`bm25.py` menyesuaikan; `ambil_hibrida` menjadi asinkron dan menunggu
pemanggilan sumbernya; uji dibungkus `jalankan()`.

Selesai bila: **jumlah uji yang lulus sama persis sebelum dan sesudah**, dan
cakupan tidak turun.

> `ambil_hibrida` berubah **bentuknya**, bukan **isinya**. Bila isinya ternyata
> perlu berubah, itu temuan — berhenti, catat, ajukan lewat Gerbang 2
> tersendiri.

---

## T-2 · Rangkaian uji kontrak `SumberKandidat` dijadikan berparameter

**Kebutuhan:** R-01.

Masih **satu pelaksana** (BM25). Tugas ini membuktikan perubahan bentuk uji
tidak mengubah hasilnya, sebelum pelaksana kedua ditambahkan pada T-5.

> Bila satu uji perlu diubah agar berparameter, itu **temuan** — catat, jangan
> rapikan. Uji yang bergantung pada pelaksana tertentu adalah uji yang selama
> ini menguji pelaksana, bukan kontrak. Pelajaran T-2 fitur 024.

---

## T-3 · `src/llm/sematan.py` — antarmuka dan tiruan deterministik

**Kebutuhan:** R-02, R-06, R-08; C-08, C-09, ADR-12.

`Penyemat` abstrak dengan `versi`, `dimensi`, dan `sematkan` asinkron.
`PenyematTiruan` memetakan teks ke vektor tetap lewat fungsi hash.

Wajib: **tiruannya menyatakan dirinya tiruan pada `versi` yang dikeluarkannya.**
Penyemat buatan sendiri yang "mirip semantik" menghasilkan angka kemiripan
yang tidak berarti apa-apa sambil terbaca seperti berfungsi.

Letaknya di `src/llm/` bukan pilihan: `periksa_impor_penyedia` hanya
mengizinkan pustaka model di sana.

---

## T-4 · Migrasi kolom vektor dan pencocokan dimensi

**Kebutuhan:** R-04, R-08; Keputusan Gerbang 1 nomor 3.

`perkakas/basis_data/05-kolom-vektor.sql` — `CREATE EXTENSION IF NOT EXISTS
vector` dan kolom `vektor vector(N)` pada `segmen_teks` di skema
`indeks_utama` dan `indeks_metadata`. Idempoten, sejajar keempat berkas
persiapan fitur 024.

Dimensi dinyatakan **satu tempat**, dan ketidakcocokan antara dimensi penyemat
dan dimensi kolom ditolak **saat penyusunan** — bukan saat kueri pertama,
ketika pemanggilnya sudah di lingkungan sungguhan.

---

## T-5 · `SumberVektor` — lulus rangkaian uji kontrak yang sama

**Kebutuhan:** R-01, R-03; C-02.

`indeks_tujuan` diperiksa terhadap kredensial **sebelum** kueri dijalankan,
bentuk yang sama dengan sumber BM25 — menyaring hasilnya sesudah pencarian
berjalan adalah penyaringan saat kueri, dan C-02 kalimat kedua menolaknya.

Selesai bila `SumberVektor` lulus rangkaian T-2 **tanpa satu pun uji diubah**.

---

## T-6 · Segmen tanpa vektor: dikeluarkan, dan jumlahnya dilaporkan

**Kebutuhan:** Keadaan wajib ditangani.

Indeks yang separuh terisi sambil terbaca penuh adalah bentuk kekeliruan yang
sama dengan uji yang dilewati tanpa dilaporkan. Jumlahnya dibawa keluar, tidak
hanya dicatat ke log.

---

## T-7 · Pemeringkat ulang dan jalur mundur yang menyatakan dirinya

**Kebutuhan:** R-05; BT-30.

BT-30 sudah memutuskan bentuknya: tanpa model lintas-enkoder, tahap 5 memakai
urutan hasil penggabungan apa adanya. Yang tugas ini tambahkan:
**ketiadaannya tercatat pada keluaran.**

Jalur mundur yang diam tidak dapat dibedakan dari pemeringkat ulang yang
berjalan dan kebetulan tidak mengubah urutan — dan kedua keadaan itu menuntut
tindakan yang berbeda.

---

## T-8 · Uji mutasi M-1 s.d. M-8 dijalankan dan dilaporkan apa adanya

**Kebutuhan:** `plan.md` Bagian 6.3.

Yang tidak menyala **tetap dilaporkan beserta sebabnya**, bukan dihapus dari
daftar.

> Bila sebuah mutasi diam, yang **pertama** diperiksa adalah apakah mutasinya
> terlalu lemah — bukan langsung menambah uji. Pelajaran M-3 fitur 024:
> memberi hak `USAGE` tanpa `SELECT` bukan pelanggaran, sehingga diamnya benar
> dan yang salah mutasinya.

---

## T-9 · Berkas persiapan ekstensi beserta batas kode/operasi

**Kebutuhan:** ADR-05; TK-56.

`README.md` pada `perkakas/basis_data/` bertambah bagian pemasangan ekstensi.
Batasnya dituliskan sejajar T-9 fitur 024: **menulis kueri vektornya kode;
memasang ekstensinya operasi.**

---

## Urutan dan alasannya

T-1 dan T-2 mendahului T-3 s.d. T-5 dengan sengaja: keduanya tidak menyentuh
vektor sama sekali, sehingga bila kontrak `SumberKandidat` ternyata tidak pas
bagi sumber asinkron, hal itu terlihat dengan dua tugas sudah aman di
belakang. Bentuk yang sama dengan T-1/T-2 fitur 024, dan alasan yang sama.

T-4 mendahului T-5 karena `SumberVektor` tidak dapat diuji atas peladen
sebelum kolomnya ada.

## Yang menghentikan pekerjaan, bukan yang memperlambatnya

| Keadaan | Yang dilakukan |
|---|---|
| Kontrak `SumberKandidat` tidak pas bagi sumber asinkron | Berhenti, ajukan lewat Gerbang 2 tersendiri |
| Satu uji T-2 perlu diubah | Berhenti, catat sebagai temuan sebelum mengubah |
| Godaan menetapkan ambang agar sistem menjawab | **Berhenti.** C-16, dan R-07 spec menegaskan fitur ini tidak menyentuh ambang mana pun |
