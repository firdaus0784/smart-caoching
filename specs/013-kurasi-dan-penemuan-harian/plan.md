# Plan: 013-kurasi-dan-penemuan-harian

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 5 Oktober 2026 (KB-178); P-1 s.d. P-7 sesuai anjuran |
| Status | **Lolos Gerbang 2–3** atas pendelegasian KB-168 — 5 Oktober 2026 (KB-179). Sembilan tugas pada `tasks.md` |
| Kebutuhan | R-01 s.d. R-13 `spec.md`; FR-G01 s.d. G05, G07, G08; FR-I01 s.d. I03, I05 s.d. I07; C-02, C-03, C-05, C-06, C-07, C-13, C-14, C-15, C-20 |

## 1. Letak dan batas

```
perkakas/basis_data/
  01-peran-dan-basis-data.sql   + peran_kurasi, peran_penayangan, peran_pengisi_antrean
  09-kurasi.sql                 baru — skema kurasi dan penemuan, hak per kolom
perkakas/kurasi.py              baru — perkakas tim: isi antrean, perbarui status regulasi
src/penyimpanan/kurasi.py       baru — PenyimpanKurasi, memori dan PostgreSQL
src/penyimpanan/penemuan.py     baru — PenyimpanPenemuan, memori dan PostgreSQL
src/api/kurasi.py               baru — penerjemah tiga rute D-14 3.4
src/api/penemuan.py             baru — penerjemah tiga rute D-14 3.3
src/api/aplikasi.py             pemasangan kedua kelompok rute bila penyimpannya diberikan
src/api/peran.py                POLA_* bagi enam rute, diambil dari PETA_RUTE
web/src/penemuan/               S-05 Beranda, S-06 Detail butir
web/src/kurasi/                 S-15 Antrean, S-16 Penyuntingan
web/src/Aplikasi.tsx            navigasi Beranda · Tanya; cangkang internal kurator
docs/                           D-14 4.6, 4.7, 5.1; D-04 7.3; D-05 S-05, S-15, S-16
```

**Model fitur 010 dan 011 dipakai, tidak ditulis ulang.** `ButirPengetahuan`,
`Putusan`, `terapkan()`, `ButirTayang`, `tinjau()`, `JejakKurasi`,
`susun_feed()`, dan `tandai_belum_relevan()` sudah menegakkan C-06, lapis kedua
C-07, pagu tayang, lisensi tertutup, dan penolakan data pribadi. Rute hanya
menerjemahkan; penyimpan hanya menyimpan.

**`src/penyimpanan/` tidak mengimpor `ingest` maupun `pengguna`.** Penyimpan
menerima dan mengembalikan baris berbentuk JSON beserta kolom kuncinya;
pembentukan model berlangsung di `src/api/`, yang memiliki tepi ke keduanya.
Penyimpanan tetap lapisan di bawah, bukan sejajar (AGENTS.md).

**Tidak ada tepi arsitektur baru.** `api → ingest`, `api → pengguna`, dan
`pengguna → ingest` sudah tertulis.

**`src/rag/`, `src/llm/`, dan `src/telemetri/` tidak disentuh.** Jalur feed
tidak memanggil model (P-3).

## 2. Penyimpanan — K-1, K-2

### 2.1 Tabel

```sql
kurasi.kandidat (
  id_butir text PRIMARY KEY, butir jsonb,      -- ButirPengetahuan apa adanya
  sumber jsonb,                                -- judul, penerbit, tahun, tautan (K-3)
  status_keberlakuan text NULL,                -- salinan yang dapat diperbarui (K-4)
  masuk_pada timestamptz, kembali_pada date NULL
)
kurasi.putusan (
  nomor bigint identity, id_butir text, jenis text, peran text,
  pseudonim_kurator text, alasan text, waktu timestamptz
)                                              -- tambah-saja: jejak FR-I05 (K-5)
kurasi.penarikan (
  nomor bigint identity, id_butir text, pemicu text, tindakan text,
  peran text NULL, pseudonim_kurator text NULL,  -- keduanya kosong: otomatis (K-4)
  alasan text, waktu timestamptz
)                                              -- tambah-saja
kurasi.butir_tayang (
  id_butir text PRIMARY KEY, butir jsonb, sumber jsonb,
  nomor_putusan bigint REFERENCES kurasi.putusan,
  tayang_pada timestamptz,
  ditarik_pada timestamptz NULL, alasan_tarik text NULL,
  perlu_tinjauan_pada timestamptz NULL
)
penemuan.tayang_harian (
  id_pengguna text, tanggal date,              -- tanggal WIB (P-4)
  id_butir text, urutan smallint, ditayangkan_pada timestamptz,
  PRIMARY KEY (id_pengguna, id_butir)          -- satu butir tayang sekali saja
)
penemuan.belum_relevan (
  nomor bigint identity, id_pengguna text, id_butir text, alasan text, waktu timestamptz
)
```

`kurasi.putusan` dan `kurasi.penarikan` bersama-sama menjadi jejak FR-I05.
Penarikan **tidak** dicatat sebagai jenis putusan kelima: `JenisPutusan`
memuat empat nilai D-06 Bagian 7.3, dan mengubah daftar enum dilarang
AGENTS.md. Nilai `pemicu` dan `tindakan` mengikuti `Pemicu` dan
`TindakanPenarikan` fitur 010 apa adanya. `butir_tayang` hanya dapat ditulis
bersama baris putusan yang menyetujuinya, dalam satu transaksi.

### 2.2 K-1 · Tiga peran basis data

| Peran | Dipakai | Hak | Yang ditolak peladen |
|---|---|---|---|
| `peran_pengisi_antrean` | perkakas tim | `kandidat`: `INSERT`, `SELECT`, `UPDATE (status_keberlakuan)`; `butir_tayang`: `SELECT`, `UPDATE (ditarik_pada, alasan_tarik)`; `penarikan`: `INSERT` | menambah butir tayang; mengubah isi kandidat; menulis putusan |
| `peran_kurasi` | rute kurator | `kandidat`: `SELECT`, `UPDATE (kembali_pada)`; `putusan`, `penarikan`: `SELECT`, `INSERT`; `butir_tayang`: `SELECT`, `INSERT`, `UPDATE (ditarik_pada, alasan_tarik, perlu_tinjauan_pada)` | menambah kandidat — penyaringan L1–L3 tidak dapat dilewati dari layar; skema `penemuan` |
| `peran_penayangan` | rute pengguna | `butir_tayang`: `SELECT`; `penemuan.*`: `SELECT`, `INSERT` | **seluruh** `kandidat`, `putusan`, `penarikan`; menulis `butir_tayang` (R-02, R-03) |

Ketiganya tanpa `CONNECT` ke basis data pseudonim (C-05), tanpa hak atas
skema `karantina` maupun `korpus` (C-03), dan tanpa `DELETE` maupun
`TRUNCATE`. Pemilik baris `penemuan` dan `pseudonim_kurator` berpola
`^psd_[a-z]{16}$`, dipasang ulang tiap kali berkas dijalankan (KB-158).

**Anjuran: tiga peran.** Peran penayangan yang dapat membaca antrean adalah
C-06 yang dijaga kode saja; peran kurasi yang dapat menambah kandidat
membuat L1–L3 dapat dilewati dari layar kurator.

### 2.3 K-2 · Butir hari ini dicatat, bukan dihitung ulang

`GET /beranda` pertama pada satu tanggal WIB memilih butir lewat
`susun_feed()` dan **mencatatnya** pada `tayang_harian`; pemanggilan
berikutnya pada tanggal yang sama membaca catatan itu. Tanpa catatan, muat
ulang memilih butir lain, dan pagu tiga butir per hari tidak bermakna.

Butir yang **pernah** tayang bagi pengguna tidak dipilih lagi (spec fitur
011: "bukan butir yang diulang"), dan kunci utama tabel menolaknya pada
peladen. Butir yang ditolak pengguna tidak tampil lagi (R-07). Butir yang
ditarik keluar dari beranda pada saat berikutnya dibaca.

## 3. K-3 · Blok sumber S-06

D-05 S-06 blok 7 menuntut nama, penerbit, tahun, dan tautan sumber (KL-04).
`ButirPengetahuan` hanya membawa `id_dokumen_sumber`, dan model `Dokumen`
tidak memiliki tautan. **Anjuran:** perkakas pengisi antrean menyertakan
salinan **metadata** sumber pada kandidat. Peran penayangan dengan demikian
tidak pernah membaca `korpus.dokumen_sumber`, yang kolom `isi`-nya memuat
teks penuh — termasuk teks berlisensi tertutup (C-02).

`tautan` boleh kosong. Bila lisensinya tertutup, S-06 menampilkan tautan ke
halaman penerbit bila ada, tetapi **tidak pernah** tautan unduhan maupun
"baca teks lengkap" (R-06). Yang menentukan `boleh_teks_penuh` fitur 011,
bukan layar.

## 4. K-4 · Status regulasi yang dapat diperbarui

Lapis kedua C-07 pada `terapkan()` memeriksa `status_keberlakuan` butir saat
diputus. Pemeriksaan itu hanya berarti bila statusnya **terkini**: uraian
`putusan.py` sendiri menyebut regulasi yang dicabut selama butir menunggu di
antrean.

**Anjuran:** `python -m perkakas.kurasi status --dokumen <id> --status
<berlaku|diubah|dicabut>` memperbarui salinan status pada setiap kandidat
bersumber dokumen itu, dan **menarik otomatis** setiap butir tayang
bersumber dokumen itu lewat `tinjau(pemicu=REGULASI_SUMBER_BERUBAH)` — D-06
Bagian 7.5: *"Ditarik otomatis"*. Rute putusan kemudian membangun
`ButirPengetahuan` dengan status terkini, dan `terapkan()` menolaknya dengan
TL-04 (R-04).

Pendeteksian otomatis perubahan regulasi **tidak** dibangun: siapa yang
memantau Lembaran Negara adalah urusan D-06, bukan kode ini.

## 5. K-5 · Jejak: peran **dan** pseudonim — membaca R-10

`JejakKurasi` fitur 010 mencatat **peran saja**. Uraiannya menolak nama dan
data pribadi kurator (C-05, KM-03); pada waktu itu belum ada akun, sehingga
satu-satunya pengganti nama yang tersedia adalah peran.

R-10 spec ini meminta jejak "dengan pseudonim kurator, bukan nama akunnya",
dan D-04 Bagian 7.3 memuat `jejak_kurasi.id_kurator`. Sejak fitur 029 setiap
akun membawa pseudonim acak yang tidak mengidentifikasi orangnya — bentuk
yang C-05 sendiri sahkan bagi data perilaku.

**Anjuran:** baris `kurasi.putusan` membawa keduanya. `peran` tetap
`PeranKurasi` (dari `Putusan`), `pseudonim_kurator` dari sesi — **tidak
pernah** `pengguna.id` (`ks-017`) maupun nama. `JejakKurasi` memori tidak
diubah; empat bidang FR-I05 dan aturan alasannya (kode TL bagi penolakan,
catatan wajib selebihnya, tanpa data pribadi) dipakai sebelum baris ditulis.
Keduanya tidak bertentangan: fitur 010 menolak **orang**, bukan pseudonim.
D-04 diselaraskan: `id_kurator` menjadi `peran, pseudonim_kurator`.

## 6. Bentuk rute — K-6, R-01

Ditulis ke D-14 Bagian 4.6 dan 4.7 **sebelum** kodenya.

### 6.1 Penemuan (D-14 3.3)

| Rute | Permintaan | Berhasil |
|---|---|---|
| `GET /api/v1/beranda` | — | 200 `{"keadaan": "berisi" \| "belum_ada_prioritas" \| "belum_ada_butir" \| "habis", "butir": [ringkas…]}` |
| `GET /api/v1/butir/{id}` | — | 200 butir lengkap |
| `POST /api/v1/butir/{id}/tolak` | `{"alasan": "…"}` | 200, bentuk `GET /beranda` |

- **Ringkas:** `id_butir`, `jenis_sumber`, `judul`, `alasan_relevansi`,
  `perkiraan_waktu_baca`, `kategori`.
- **Lengkap:** ringkas ditambah `inti_temuan`, `implikasi_tindakan`,
  `tenggat_terkait`, `boleh_teks_penuh`, `sumber {judul, penerbit, tahun,
  tautan}`.
- **Keadaan** membedakan KL-B dan KL-C tanpa layar menebak:
  `belum_ada_prioritas` — aktivasi belum selesai; `belum_ada_butir` — belum
  pernah ada butir bagi prioritasnya; `habis` — tidak ada butir baru hari ini
  sesudah sebelumnya pernah ada.
- `GET /butir/{id}` menjawab **hanya** butir yang pernah tayang bagi
  pemanggil dan belum ditarik; selebihnya 404 `SUMBER_TIDAK_ADA` dengan satu
  bentuk bagi "tidak dikenal", "belum tayang baginya", dan "ditarik" — sama
  dengan R-02 fitur 023. Butir tertarik pada koleksi milik baris 032.
- `kategori` dikirim sebagai kode; layar menampilkan label D-03 (K-7 fitur
  030).

### 6.2 Kurasi (D-14 3.4)

| Rute | Permintaan | Berhasil |
|---|---|---|
| `GET /api/v1/kurasi/antrean` | — | 200 `{"menunggu": [kandidat…], "tayang": [tayang…]}` |
| `POST /api/v1/kurasi/{id}/putusan` | lihat di bawah | 200, bentuk `GET /antrean` |
| `POST /api/v1/kurasi/{id}/tarik` | `{"pemicu": "…", "catatan": "…", "status_terkini"?: "…", "angka_berubah_bermakna"?: bool}` | 200, bentuk `GET /antrean` |

Badan putusan, satu dari empat — `extra="forbid"`, sehingga bidang yang
bukan milik jenisnya ditolak, sama dengan `Putusan`:

```json
{"jenis": "setujui", "catatan": "…"}
{"jenis": "sunting_lalu_setujui", "catatan": "…",
 "suntingan": {"judul": "…", "alasan_relevansi": "…", "inti_temuan": "…", "implikasi_tindakan": ["…"]}}
{"jenis": "tolak", "alasan_tolak": "TL-04"}
{"jenis": "tunda", "catatan": "…", "kembali_pada": "2026-10-12"}
```

- **K-6 · `tayang` pada tanggapan antrean.** Penarikan menuntut kurator
  melihat butir yang sedang tayang, dan D-14 Bagian 3 tidak memuat rute lain
  yang mendaftarnya. **Anjuran:** daftar kedua pada tanggapan yang sama;
  menambah rute dilarang AG-02.
- Suntingan hanya mengganti **empat bidang parafrase** — bidang yang D-06
  Bagian 7.3 sebut. Lisensi, sumber, kategori, dan jenis sumber tidak dapat
  disunting dari layar: menggantinya mengubah butir, bukan parafrasenya.
- Kandidat bertunda tidak tampil sampai `kembali_pada` (WIB).
- Persetujuan yang ditolak lapis C-07 menjawab 400 `VALIDASI_GAGAL` dengan
  kalimat yang menyebut alasan penolakan regulasi (R-04).
- Kurator tidak menerima `pseudonim_kurator` pada tanggapan mana pun.

## 7. Alur layar — K-7, K-8

### 7.1 Pengguna

```
aktivasi selesai (fitur 030)  ─► S-09 Tanya         (R-07 fitur 030 tetap)
pembukaan berikutnya          ─► S-05 Beranda
navigasi bawah                :  Beranda · Tanya
S-05 ─► S-06 ─► kembali ke S-05
```

**K-7 · Navigasi dua tujuan, bukan tiga.** D-05 Bagian 3.1 menetapkan
Beranda, Tanya, Milik saya. "Milik saya" memuat koleksi, komitmen, dan
jurnal — seluruhnya milik baris 031 dan 032. **Anjuran:** tujuan itu tidak
tampil sampai isinya ada; tujuan kosong adalah kerangka yang menjanjikan
fitur yang belum dibangun.

S-05 memuat butir hari ini dan jalur cepat ke Tanya. Pengingat komitmen milik
baris 031. S-06 mengikuti urutan blok D-05 Bagian 6; tombol pada blok 8
hanya **Belum relevan** — Simpan milik 032, knowledge check milik 031.
"Belum relevan" membuka satu isian alasan, wajib (FR-G07, fitur 011).

### 7.2 Kurator

**K-8 · Cangkang mengenali kurator tanpa rute baru.** `GET /saya/profil`
menjawab 403 bagi peran selain `pengguna`. Cangkang kemudian mencoba `GET
/kurasi/antrean`; 200 membuka S-15, selainnya menampilkan pesan
`TIDAK_BERWENANG` beserta tombol keluar. Rute "siapa saya" tidak ditambahkan
(AG-02).

S-15 mengikuti D-05 Bagian 6: satu baris per butir, dikelompokkan menurut
kategori, memuat judul, jenis sumber, lisensi, dan status regulasi.
**Skor relevansi tidak tampil**: ambang dan skor L4 belum dikalibrasi
(BT-24), dan angka yang belum berdasar tidak boleh menjadi dasar putusan.
Tombol: Setujui · Sunting · Tolak · Tunda — keempatnya setara, sebab D-06
Bagian 7.3 memberi keempatnya akibat yang berbeda. Tolak membuka pilihan kode
TL; label TL-11 ditampilkan **tanpa** contoh bersingkatan "BAN-S/M" (C-13),
kodenya tetap. Daftar kedua "Sedang tayang" menyediakan Tarik.

S-16 menyunting empat bidang parafrase, lalu Simpan dan setujui.

## 8. Simpanan luring — P-7

Butir hari ini beserta isi lengkapnya disimpan pada simpanan lokal peramban
sesudah dimuat (D-05 Bagian 8), dengan pola `draf.ts`: penulisan yang gagal
tidak menjatuhkan layar dan tidak diaku tersimpan. Luring: S-05 menampilkan
salinan terakhir beserta keterangan KL-E; S-06 dapat dibaca dari salinan.
Salinan dihapus saat keluar, seperti draf (K-6 fitur 029). Layar kurator
**tidak** disimpan luring: putusan menuntut keadaan antrean terkini.

## 9. Keputusan rancangan Gerbang 2

| Kode | Pertanyaan | Anjuran |
|---|---|---|
| K-1 | Peran basis data | **Tiga peran** — Bagian 2.2 |
| K-2 | Butir hari ini | **Dicatat** pada `tayang_harian`, satu butir tayang sekali — Bagian 2.3 |
| K-3 | Metadata sumber S-06 | **Salinan metadata** pada kandidat; penayangan tidak membaca korpus — Bagian 3 |
| K-4 | Status regulasi terkini | **Perkakas `status`**, menarik otomatis butir tayang — Bagian 4 |
| K-5 | Isi jejak kurasi | **Peran dan pseudonim kurator** — Bagian 5 |
| K-6 | Daftar tayang bagi penarikan | **Pada tanggapan antrean** — Bagian 6.2 |
| K-7 | Navigasi pengguna | **Beranda · Tanya**; "Milik saya" menunggu isinya — Bagian 7.1 |
| K-8 | Cangkang kurator | **Dikenali dari 403 lalu 200**, tanpa rute baru — Bagian 7.2 |

## 10. Uji

### 10.1 Di dalam `make check`

- Penyimpan atas pelaksana memori **dan** PostgreSQL, tersambung sebagai
  perannya sendiri (TK-64).
- Penolakan peladen Bagian 2.2, tiap baris dengan sebabnya
  `permission denied`.
- **C-06 dari ujung ke ujung lewat HTTP:** kandidat tidak tampil pada beranda;
  sesudah disetujui kurator, tampil bagi pengguna berprioritas sesuai, dan
  tidak bagi yang tidak.
- **C-07:** status `dicabut` lewat perkakas → persetujuan ditolak TL-04, butir
  tayang tertarik dan lenyap dari beranda.
- Pagu: empat butir tersedia, tiga tampil; muat ulang menjawab tiga yang sama;
  hari WIB berikutnya tidak mengulang butir lama.
- **C-14:** pemilihan tidak berubah oleh butir yang dibuka; jalur penjawab
  tidak menerima prioritas maupun butir.
- **C-02:** butir berlisensi tertutup tanpa teks penuh pada tanggapan maupun
  layar.
- Peran: pengguna 403 pada rute kurasi; kurator 403 pada rute penemuan.
- **C-15** diperiksa sebagai ketiadaan pada skema dan layar baru.
- Layar: Vitest untuk tujuh keadaan S-05, S-06, keadaan S-15, dan cangkang
  kurator.

### 10.2 Di luar `make check`

Playwright terhadap `make jalan`: perkakas mengisi antrean dari berkas uji,
kurator masuk dan menyetujui, pengguna masuk dan melihat butir pada beranda,
membuka S-06, menyatakan belum relevan; kurator menarik; beranda tanpa butir
itu. Tangkapan layar ke `bukti/`.

### 10.3 Uji mutasi

| Kode | Mutasi | Uji yang wajib merah |
|---|---|---|
| M-1 | Beranda membaca `kandidat`, bukan `butir_tayang` | C-06 ujung ke ujung |
| M-2 | `GRANT SELECT ON kurasi.kandidat` kepada `peran_penayangan` | penolakan peladen |
| M-3 | `GRANT INSERT ON kurasi.kandidat` kepada `peran_kurasi` | penolakan peladen |
| M-4 | `GRANT INSERT ON kurasi.butir_tayang` kepada `peran_penayangan` | penolakan peladen |
| M-5 | Rute putusan memakai status salinan lama, bukan terkini | C-07 TL-04 |
| M-6 | Butir hari ini dihitung ulang tiap pemanggilan | pagu muat ulang |
| M-7 | Batas hari pada UTC, bukan WIB | pagu pukul 06.00 WIB |
| M-8 | Butir tertolak tetap terpilih | R-07 |
| M-9 | `boleh_teks_penuh` dibaca layar dari untai lisensi | C-02 |
| M-10 | `pseudonim_kurator` diisi `pengguna.id` | K-5 |
| M-11 | Suntingan dapat mengganti lisensi | Bagian 6.2 |
| M-12 | `GET /butir/{id}` menjawab butir yang belum tayang bagi pemanggil | Bagian 6.1 |
| M-13 | Butir ditarik tetap pada beranda hari itu | R-02, K-4 |

## 11. Urutan tugas

| Tugas | Isi |
|---|---|
| T-1 | Kontrak lebih dulu: D-14 4.6, 4.7, 5.1; D-04 7.3 (K-5); D-05 S-05, S-15, S-16 |
| T-2 | Peladen: `09-kurasi.sql`, tiga peran; M-2 s.d. M-4 |
| T-3 | `src/penyimpanan/kurasi.py` dan `penemuan.py`, dua pelaksana; M-6, M-7, M-13 sisi penyimpan |
| T-4 | Perkakas `perkakas/kurasi.py`: `isi` dan `status`; M-5 sisi perkakas |
| T-5 | Rute kurasi; M-5, M-10, M-11 |
| T-6 | Rute penemuan; M-1, M-8, M-9, M-12, M-13 |
| T-7 | Layar S-05, S-06, simpanan luring, navigasi |
| T-8 | Layar S-15, S-16, cangkang kurator |
| T-9 | Putaran mutasi, Playwright, penutupan: D-00, L8, HKI, L4 |

## 12. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Rute selain enam rute di atas tampak perlu | Berhenti; AG-02 |
| Skor relevansi atau ambang tampak perlu ditampilkan | Berhenti; C-16, BT-24 |
| Pemilihan butir tampak perlu membaca perilaku | Berhenti; C-14 |
| Perubahan `src/rag/`, `src/llm/`, atau `src/telemetri/` tampak perlu | Berhenti |
| Kandidat tampak perlu ditambahkan dari layar | Berhenti; FR-I07 |
| Paket baru tampak perlu | Berhenti; C-12 |
