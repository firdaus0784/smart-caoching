# Plan: 041-identitas-regulasi-pengambilan

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 13 Oktober 2026 (KB-304); P-1 s.d. P-5 sesuai anjuran |
| Perubahan atas fitur yang lolos Gerbang 4 | Atas putusan Gerbang 1 (KB-304): fitur 039 — `bangun_muatan` membangun indeks leksikal atas teks pencarian, dan perkakas pencarian mencetak versi yang memuat penanda aturan; fitur 002/037 — `Gerbang.terima` menolak regulasi resmi tanpa pola judul (P-3 A) |
| Status | **Menunggu Gerbang 4** — 13 Oktober 2026 (KB-309). Empat dari empat tugas selesai |
| Kebutuhan | R-01 s.d. R-06 `spec.md`; TK-88; FR-F02, FR-F11; ADR-03; D-08 Bagian 6; C-02, C-16, C-18, C-20 |

## 1. Letak dan batas

```
src/rag/pengambilan/teks_pencarian.py  baru — aturan teks pencarian dan penanda versinya
src/api/penjawab_korpus.py             bangun_muatan: indeks leksikal atas teks pencarian; versi memuat penanda
src/ingest/judul_regulasi.py           baru — pola judul regulasi D-06
src/ingest/gerbang.py                  terima menolak regulasi resmi tanpa pola, sebelum menulis apa pun
perkakas/pengambilan.py                versi yang dicetak diambil dari indeks leksikal
docs/                                  D-07 Bagian 3.3; D-06 K-A; D-00
```

**Tidak disentuh:** `src/penyimpanan/`, `src/llm/`, `src/nlp/`,
`src/pengguna/`, `src/telemetri/`, `src/ingest/penyematan.py` (P-4 A),
`src/ingest/segmentasi.py` dan `pengindeksan.py` (P-1 A), `web/`, dan
`perkakas/basis_data/`. Tanpa rute, skema, peran, atau paket baru (R-06).
**Tanpa tepi impor baru**: `api → rag` dan `perkakas → *` sudah ada; modul
baru di `ingest` tidak mengimpor lapisan lain.

## 2. K-1 · Teks pencarian (P-1 A, P-2 A, P-5 A)

`teks_pencarian(judul, teks) -> str` mengembalikan judul, baris baru, lalu
teks segmen. Ia tinggal di `src/rag/pengambilan/` sebab indeks leksikal
milik lapisan itu dan aturannya milik D-07 Bagian 3.3.

`bangun_muatan` membangun **dua** bentuk dari satu baris layak: `SegmenTerindeks`
bagi indeks leksikal, bertekskan teks pencarian, dan `BahanSegmen` bagi model,
bertekskan `baris.teks` seperti sebelumnya. Sitasi, bacaan lanjutan, dan
`layak_utama` tidak berubah. Berlaku bagi kedua indeks (P-5 A); sisi vektor
tidak disentuh (P-4 A).

Baris layak selalu bercatatan metadata — alasan tak layak yang pertama — sehingga
judul selalu ada; tidak ada cabang tanpa judul.

## 3. K-2 · Versi (R-04)

`ATURAN_PENCARIAN = "pencarian:judul-1"`. Versi indeks leksikal menjadi
`utama:<sidik>;pencarian:judul-1`, dan `Muatan.versi_indeks` menjadi
`utama:<sidik>;metadata:<sidik>;pencarian:judul-1`. Itulah yang tercatat pada
tanggapan `/tanya`, L1 perkakas evaluasi, dan keluaran perkakas pencarian.
Aturan yang berubah kelak menaikkan akhirannya; D-07 Bagian 3.3 menyatakannya.

Bentuk `/tanya` tidak berubah — `versi_indeks` tetap untai (C-20).

## 4. K-3 · Judul regulasi (P-3 A)

D-06 K-A sudah mewajibkan *nomor* dan *tahun* sebagai metadata regulasi,
tetapi sistem tidak memiliki bidangnya. Pola menjadikan judul tempatnya.

| Aspek | Ketentuan |
|---|---|
| Pola | `Nomor`, spasi, satu untai nomor tanpa spasi, spasi, `Tahun`, spasi, empat angka; huruf besar dan kecil sama; sebagai kata utuh |
| Berlaku bagi | `regulasi_resmi` saja; jenis lain tidak diperiksa |
| Tempat | `Gerbang.terima`, sebelum penyamaran dan sebelum penulisan apa pun, sehingga setiap jalur penerimaan melaluinya |
| Pesan | `GalatGerbang` tanpa mengutip judul; perkakas mencetak `Ditolak:` berkode 2 |
| Yang sudah di korpus | Tidak tersentuh |

Contoh diterima dan ditolak ditulis sebagai tabel pada D-06; uji membacanya
dari sana. `No. 6/2021` **ditolak**: bentuk singkat tidak cocok dengan
pertanyaan yang menulis "Nomor 6 Tahun 2021", dan judul yang seragam itulah
yang membuat identitas dapat dicari.

## 5. K-4 · Kontrak

- **D-07 Bagian 3.3**: baris *Teks pencarian*; baris *Versi indeks* menyebut
  penanda aturan. D-07 0.4.
- **D-06 K-A**: baris *Judul* dengan pola dan contoh. D-06 0.6.
- **D-00** register.

## 6. Keputusan rancangan Gerbang 2

| Kode | Pertanyaan | Putusan |
|---|---|---|
| K-1 | Teks pencarian | Bagian 2 — fungsi di `rag`; dua bentuk dari satu baris; kedua indeks |
| K-2 | Versi | Bagian 3 — penanda aturan pada versi indeks dan muatan |
| K-3 | Judul regulasi | Bagian 4 — pola pada `Gerbang.terima`; contoh pada D-06 |
| K-4 | Kontrak | Bagian 5 |

## 7. Uji

### 7.1 Di dalam `make check`

- Teks pencarian: judul mendahului teks; D-07 Bagian 3.3 menyebut aturan dan
  penandanya
- `bangun_muatan`: pasal regulasi yang ditanya dengan judulnya naik ke
  peringkat pertama di antara pasal berisi sama dari regulasi berjudul serupa
  — dan **tidak** demikian bila judul dibuang (uji pembanding); teks bahan,
  sitasi, dan `layak_utama` tidak berubah; indeks metadata juga; versi memuat
  penanda
- Pola judul: contoh D-06 diterima dan ditolak; hanya `regulasi_resmi`;
  `Gerbang.terima` menolak sebelum apa pun tertulis; perkakas berkode 2 tanpa
  mengutip judul
- Uji fitur 039 dan 037 yang menyatakan bentuk versi atau judul regulasi
  disesuaikan atas putusan KB-304

### 7.2 Di luar `make check`

Sepuluh regulasi rekaan berjudul serupa — nomor 7 sampai 16, tahun dan isi
pasal sama — diterima, disetujui, dan diindeks lewat baris perintah. *Gold
set* rekaan berkomposisi D-08 dengan dua puluh pertanyaan bernomor regulasi
dibekukan dan diukur dua kali atas **keadaan peladen yang sama**. Pertama
pada *worktree* git di commit sebelum T-2, lalu pada *worktree* di commit
sesudah T-3. Keduanya memakai perkakas evaluasi lewat baris perintah dengan
logbook *worktree* masing-masing, yang dibuang sesudahnya. Recall pertanyaan
bernomor dilaporkan berdampingan, beserta versi indeks keduanya. Keluaran ke
`bukti/`.

### 7.3 Uji mutasi

| Kode | Mutasi | Uji yang wajib merah |
|---|---|---|
| M-1 | Teks pencarian tanpa judul | R-01 |
| M-2 | Judul ikut teks bahan yang dikirim ke model | R-05, P-1 A |
| M-3 | Versi tanpa penanda aturan | R-04 |
| M-4 | Indeks metadata tanpa judul | P-5 A |
| M-5 | Pola judul tidak ditegakkan | P-3 A |
| M-6 | Pola menerima nomor tanpa tahun | P-3 A |
| M-7 | Pola ditegakkan bagi semua jenis | P-3 A |

## 8. Urutan tugas

| Tugas | Isi |
|---|---|
| T-1 | Kontrak: D-07 Bagian 3.3; D-06 K-A; D-00 |
| T-2 | Teks pencarian dan versi; `bangun_muatan`; perkakas pencarian; M-1, M-2, M-3, M-4 |
| T-3 | Pola judul regulasi; `Gerbang.terima`; M-5, M-6, M-7 |
| T-4 | Bukti sebelum dan sesudah; penutupan: L8, HKI, L4; status menunggu Gerbang 4 |

## 9. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Bobot, faktor pengali, atau ambang tampak perlu agar judul berpengaruh | Berhenti; R-03, C-16 |
| Teks segmen tersimpan atau teks bahan tampak perlu berubah | Berhenti; P-1 A |
| Penyematan tampak perlu berubah | Berhenti; P-4 A |
| Dokumen yang sudah di korpus tampak perlu disunting judulnya | Berhenti; P-3 A |
| Bukti sesudah tidak lebih baik daripada sebelum | Laporkan apa adanya; jangan setel |
