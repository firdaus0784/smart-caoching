# Plan: 038-segmentasi-dan-penempatan-indeks

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 11 Oktober 2026 (KB-266); P-1 s.d. P-4 sesuai anjuran |
| Temuan yang diputus sebelum plan | TK-86 A (KB-266): hak tulis indeks `peran_verifikasi` dicabut |
| Status | **Gerbang 3 lolos** — 12 Oktober 2026 atas pendelegasian KB-168 (KB-267). Enam dari tujuh tugas selesai |
| Kebutuhan | R-01 s.d. R-08 `spec.md`; FR-D06, FR-F11; C-02, C-03, C-16, C-17, C-19, C-20 |

## 1. Letak dan batas

```
perkakas/basis_data/
  01-peran-dan-basis-data.sql   + peran_pengindeks
  16-segmen-dan-lisensi.sql     baru — kolom lisensi pada penerimaan dan metadata korpus;
                                hak peran_pengindeks; hak tulis indeks verifikator dicabut
src/ingest/dokumen.py           Dokumen.lisensi (boleh kosong)
src/ingest/gerbang.py           lisensi ikut penerimaan dan metadata korpus
src/ingest/segmentasi.py        baru — pemotongan D-07 Bagian 3.2, fungsi murni
src/ingest/pengindeksan.py      baru — dari dokumen korpus ke segmen terindeks
src/penyimpanan/dasar.py        MetadataDokumen.lisensi
src/penyimpanan/karantina.py    CatatanPenerimaan.lisensi
src/penyimpanan/postgres.py     lisensi ikut catatan metadata pemindahan
src/penyimpanan/kredensial_baku.py  PENGINDEKSAN
src/penyimpanan/pengindeks.py   baru — bahan dan penggantian segmen, memori dan PostgreSQL
perkakas/ingesti.py             terima --lisensi; indeks --id [--pratinjau]
docs/                           D-14 5.1; D-04 7.2 dan KA-04; D-00
```

**`src/api/`, `src/rag/`, `src/llm/`, `src/pengguna/`, `src/telemetri/`, dan
`web/` tidak disentuh.** Pembaca sumber fitur 032 tidak berubah: ia sudah
membaca segmen indeks utama menurut penanda bagian. Tidak ada tepi impor baru.

## 2. K-1 · Peladen

| Peran | Hak | Yang sengaja **tidak** dipegang |
|---|---|---|
| `peran_pengindeks` (baru) | `USAGE` korpus dan kedua indeks; `SELECT (id, isi)` atas `korpus.dokumen_sumber`; `SELECT` atas `korpus.metadata_dokumen`; `INSERT (id_segmen, id_dokumen, teks, lisensi, anonimisasi_terverifikasi, penanda_bagian)`, `SELECT (id_segmen, id_dokumen)`, dan `DELETE` atas kedua `segmen_teks` | Karantina sama sekali (C-03); kolom vektor (milik penyematan); mengubah segmen — pengindeksan ulang menghapus lalu menyisipkan |
| `peran_verifikasi` | — | **`INSERT` dan `UPDATE` atas kedua `segmen_teks`**, dicabut, juga pada hak bawaan kedua skema indeks (TK-86) |

Kolom `lisensi` (boleh kosong, tidak boleh hampa) pada `karantina.penerimaan`
dan `korpus.metadata_dokumen`. Kosong berarti tertutup, dibaca
`lisensi_dari_metadata` — tidak disimpulkan dari jenis (KL-01).

Uji katalog memeriksa `peran_pengindeks` **persis** di seluruh skema, hak
tulis indeks verifikator pada katalog dan hak bawaan, dan setiap peran
menjalankan pekerjaannya dengan haknya sendiri.

## 3. K-2 · Pemotongan (P-1 A)

`src/ingest/segmentasi.py`: `potong(teks) → list[Potongan(penanda, teks)]`,
fungsi murni tanpa basis data. Kata = rangkaian bukan-spasi.

1. **Satuan alami.** Baris `Pasal N` (nomor beserta huruf, mis. `7A`) memulai
   satuan berpenanda `Pasal N`. Baris `BAB`, `Bagian`, dan `Paragraf` adalah
   judul konteks: ikut ke awal satuan sesudahnya. Teks sebelum pasal pertama
   menjadi satuan `Pembukaan`. Dokumen tanpa pasal: paragraf (baris)
   dikumpulkan berurutan sampai sasaran, berpenanda `Bagian 1`, `Bagian 2`.
2. **Pasal pendek berdiri sendiri** — tidak digabung, berapa pun panjangnya
   (D-07 Bagian 3.2).
3. **Satuan di atas 500 kata** dipecah di batas ayat `(1)`, `(2)`, dikumpulkan
   tanpa melampaui 500 kata; penandanya `Pasal N ayat (a)` atau
   `Pasal N ayat (a)–(b)`. Batas alami tidak memotong ketentuan, sehingga
   **tumpang tindih tidak diberikan di sana**.
4. **Teks tanpa batas alami di atas 500 kata** — satu ayat, satu paragraf —
   dipecah menjadi jendela sama besar sebanyak yang diperlukan, masing-masing
   paling banyak 500 kata, dengan **tumpang tindih 60 kata** (dalam rentang
   50–80 D-07). Penandanya berakhiran `, potongan i dari n`, sehingga sitasi
   menunjuk satu jendela dan pembaca sumber tidak menampilkan tumpang tindih
   dua kali.

Angka 500, rentang 300–500, dan 50–80 milik D-07, dibaca dari tetapan yang
menyebut asalnya; tidak disetel di sini (C-16). Angka 60 adalah titik di dalam
rentang D-07, bukan angka baru. `id_segmen` = `<id_dokumen>:<urutan 4 digit>`
— deterministik (R-06).

## 4. K-3 · Pengindeksan (P-2 A, P-3 A, P-4 A)

`src/ingest/pengindeksan.py`: `indekskan(penulis, id_dokumen, *, tulis)`
membaca teks dan lisensi terbaru dokumen korpus, memotongnya, menetapkan
lisensi dan indeks tujuan lewat `lisensi_dari_metadata` dan `indeks_bagi`
fitur 006 apa adanya (R-03), membentuk `SegmenTerindeks` dengan
`anonimisasi_terverifikasi` benar — hanya dokumen korpus yang terjangkau, dan
korpus hanya terisi lewat gerbang — lalu, bila `tulis`, mengganti segmen
dokumen itu. Tanpa `tulis` ia pratinjau: penanda dan jumlah kata, tanpa teks.

`src/penyimpanan/pengindeks.py`, `PenulisIndeks`:

- `bahan(kredensial, id)`: teks dan lisensi terbaru; `GalatDokumenTidakAda`
  bila tidak di korpus;
- `ganti(kredensial, id, segmen)`: **satu pernyataan** — hapus segmen dokumen
  itu dari kedua indeks, sisipkan yang baru ke indeks tujuannya — hanya bila
  dokumennya di korpus (R-04, R-05). Penghapusan dan penyisipan kunci yang
  sama dalam satu pernyataan diverifikasi pada peladen sebelum plan ini. Verifikasi
  itu tidak mencakup urutan bagian `WITH`; sisip kini menunggu penghapusan
  selesai (KB-272).

Kredensial `PENGINDEKSAN` baru pada `kredensial_baku.py`: membaca korpus,
menulis kedua indeks, tanpa karantina.

Peringkat kepercayaan dan status keberlakuan **tidak disimpan** pada segmen
(P-4 A); D-14 menyatakannya bidang turunan dari catatan korpus.

## 5. K-4 · Lisensi dicatat (P-3 A)

`Dokumen.lisensi`, `CatatanPenerimaan.lisensi`, `MetadataDokumen.lisensi`,
ketiganya boleh kosong dengan bawaan kosong, sehingga uji fitur 002, 032, dan
037 tidak berubah. Gerbang meneruskannya ke penerimaan dan ke catatan metadata
korpus dalam pernyataan pemindahan yang sama. `terima --lisensi` opsional.

## 6. K-5 · Perkakas

`python -m perkakas.ingesti indeks --id <id> [--pratinjau]` sebagai
`peran_pengindeks`. Keluaran: indeks tujuan, jumlah segmen, dan daftar penanda
beserta jumlah kata — tanpa teks segmen (R-07).

## 7. K-6 · Kontrak

D-14 Bagian 5.1: `penerimaan.lisensi`, `metadata_dokumen.lisensi`,
`dokumen_sumber.lisensi` sebagai catatan; `segmen_teks.peringkat_kepercayaan`
dan `indeks_tujuan` sebagai bidang turunan; aturan `id_segmen`. D-04 Bagian 7.2
dan KA-04: `peran_pengindeks`, TK-86. Tanpa rute (R-08).

## 8. Keputusan rancangan Gerbang 2

| Kode | Pertanyaan | Putusan |
|---|---|---|
| K-1 | Peladen | Bagian 2 — peran pengindeks tanpa karantina dan vektor; verifikator tanpa tulis indeks |
| K-2 | Pemotongan | Bagian 3 — tumpang tindih hanya di dalam teks tanpa batas alami; jendela berpenanda sendiri |
| K-3 | Pengindeksan | Bagian 4 — ganti satu pernyataan; hanya dokumen korpus |
| K-4 | Lisensi | Bagian 5 — bawaan kosong berarti tertutup |
| K-5 | Perkakas | Bagian 6 — pratinjau tanpa teks |
| K-6 | Kontrak | Bagian 7 |

## 9. Uji

### 9.1 Di dalam `make check`

- Peladen: katalog `peran_pengindeks` persis; verifikator tanpa tulis indeks
  pada katalog dan hak bawaan; penolakan berpenyebab — pengindeks menjangkau
  karantina, menulis vektor, mengubah segmen; setiap peran berjalan pada haknya
- Pemotongan: pasal pendek berdiri sendiri; konteks BAB ikut pasal; pembukaan;
  dokumen tanpa pasal; pemecahan di batas ayat tanpa tumpang tindih; jendela
  bertumpang tindih 60 kata dan berpenanda sendiri; tidak satu segmen pun
  melampaui 500 kata; deterministik; penanda selalu berisi
- Pengindeksan atas memori **dan** PostgreSQL sebagai `peran_pengindeks`:
  lisensi terbuka ke indeks utama, kosong dan tak dikenal ke indeks metadata;
  pengindeksan ulang mengganti, bukan menambah; dokumen di luar korpus ditolak
  tanpa menulis apa pun; pratinjau tidak menulis
- Lisensi ikut penerimaan dan catatan metadata korpus
- Perkakas: perannya, keluaran tanpa teks, tanpa log
- Pembaca sumber fitur 032 menampilkan teks bagian dokumen yang diindeks

### 9.2 Di luar `make check`

Regulasi contoh berpasal dan berlisensi terbuka melewati perkakas: `terima
--lisensi` → `tinjau`/`setujui` → status lewat perkakas kurasi → `indeks
--pratinjau` → `indeks`; pembaca sumber `make jalan` menampilkan teks pasal yang
dirujuk. Dokumen tanpa lisensi masuk indeks metadata dan tidak tampil teksnya.
Keluaran ke `bukti/`.

### 9.3 Uji mutasi

| Kode | Mutasi | Uji yang wajib merah |
|---|---|---|
| M-1 | `GRANT INSERT` atas segmen kepada `peran_verifikasi` | katalog (TK-86) |
| M-2 | `GRANT USAGE ON SCHEMA karantina TO peran_pengindeks` | katalog skema |
| M-3 | `GRANT UPDATE (vektor_sematan)` kepada `peran_pengindeks` | katalog |
| M-4 | Lisensi kosong ke indeks utama | pengindeksan (C-02) |
| M-5 | Hapus dan sisip dalam pernyataan terpisah | penggantian atomik |
| M-6 | Syarat dokumen di korpus dihapus | R-04 |
| M-7 | Pasal pendek digabung | pemotongan |
| M-8 | Jendela tanpa tumpang tindih | pemotongan |
| M-9 | Pengenal segmen acak | deterministik |
| M-10 | Lisensi tidak ikut catatan metadata pemindahan | lisensi |
| M-11 | Perkakas mencetak teks segmen | perkakas |

## 10. Urutan tugas

| Tugas | Isi |
|---|---|
| T-1 | Kontrak: D-14 5.1; D-04 7.2 dan KA-04; D-00 |
| T-2 | Peladen: `16-segmen-dan-lisensi.sql`, `peran_pengindeks`, TK-86; M-1, M-2, M-3 |
| T-3 | Lisensi dicatat: `Dokumen`, catatan, pemindahan, `terima --lisensi`; M-10 |
| T-4 | Pemotongan D-07 Bagian 3.2; M-7, M-8 |
| T-5 | Penulis indeks dan pengindeksan; `PENGINDEKSAN`; M-4, M-5, M-6, M-9 (pindah dari T-4, KB-271) |
| T-6 | Perkakas `indeks`; pembaca sumber menampilkan teks; M-11 |
| T-7 | Bukti, penutupan: L8, HKI, L4; status menunggu Gerbang 4 |

## 11. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Ukuran segmen tampak perlu diubah | Berhenti; D-07 dan C-16 |
| Lisensi tampak perlu disimpulkan dari jenis | Berhenti; KL-01 |
| Pembaca sumber atau jalur penjawab tampak perlu berubah | Berhenti; fitur 032 dan 021 |
| Penyematan tampak perlu dijalankan | Berhenti; ADR-12 |
| Rute tampak perlu | Berhenti; R-08 |
