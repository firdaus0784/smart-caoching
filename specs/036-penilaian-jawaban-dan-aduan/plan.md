# Plan: 036-penilaian-jawaban-dan-aduan

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 8 Oktober 2026 (KB-227, KB-228); P-1 A, P-2 B, P-3 B, P-4 B disusuli `id_pesan` |
| Status | **Gerbang 3 lolos** — 8 Oktober 2026 atas pendelegasian KB-168 (KB-229). Enam dari delapan tugas selesai |
| Kebutuhan | R-01 s.d. R-10 `spec.md`; FR-F07, FR-I04, NFR-09; C-04, C-05, C-06, C-07, C-13, C-14, C-16, C-17, C-20 |

## 1. Letak dan batas

```
perkakas/basis_data/
  01-peran-dan-basis-data.sql   + peran_penilaian
  13-penilaian.sql              baru — riwayat.pesan, riwayat.penilaian,
                                kurasi.aduan, kurasi.aduan_digantikan,
                                kurasi.tindak_lanjut_aduan; hak keempat peran;
                                hak hapus peran_penarikan
src/kamus/penilaian.py          baru — NilaiPenilaian, TindakLanjutAduan
src/penyimpanan/riwayat.py      catat() menerima tanggapan; satu pernyataan
src/penyimpanan/penilaian.py    baru — penilaian, aduan, tindak lanjut
src/penyimpanan/penarikan.py    + lima tabel
src/api/penilaian.py            baru — model permintaan dan tanggapan, aturan
src/api/aplikasi.py             tiga rute; /tanya menyerahkan tanggapan ke riwayat
src/api/rekaman.py              + rekam_penilaian (answer_rated)
src/api/analitik.py             + penilaian per nilai; AKURASI_QA keluar dari MetrikTertunda
perkakas/jalankan_lokal.py      penyimpan penilaian sebagai peran_penilaian; aduan sebagai peran_kurasi
web/src/tanya/                  blok "Nilai jawaban" pada BlokJawaban
web/src/kurasi/                 S-17 LayarAduan; cangkang kurator berpindah antrean ↔ aduan
web/src/analitik/               tabel penilaian
docs/                           D-14 3.4, 4.8, 4.9, 5.1; D-01 9; D-04 7.4; D-05 S-09, S-17; D-00
```

**`src/rag/`, `src/llm/`, `src/ingest/`, `src/pengguna/` tidak disentuh.**
Tidak ada tepi impor baru: `api → penyimpanan`, `api → telemetri`, `api → nlp`
(pendeteksi FR-B04 bagi `alasan`) dan setiap lapisan → `kamus` sudah tertulis
pada AGENTS.md.

## 2. K-1 · Tabel dan peran

Lima tabel, semuanya tambah-saja bagi peran aplikasi.

| Tabel | Isi | Penulis |
|---|---|---|
| `riwayat.pesan` | `id_pesan` (kunci), `id_percakapan`, `tanggapan` jsonb (D-14 4.1 apa adanya), `waktu` | `peran_riwayat`, **dalam pernyataan yang sama** dengan giliran |
| `riwayat.penilaian` | `nomor`, `id_pesan`, `nilai`, `alasan` (boleh kosong), `kirim_ke_kurator`, `waktu` | `peran_penilaian` |
| `kurasi.aduan` | `nomor`, `nomor_penilaian`, `pertanyaan`, `tanggapan` jsonb **tanpa `id_pesan`**, `alasan`, `diadukan_pada` | `peran_penilaian`, saat `kirim_ke_kurator` |
| `kurasi.aduan_digantikan` | `nomor_aduan` (kunci), `waktu` | `peran_penilaian`, saat penilaian berikutnya atas pesan yang sama |
| `kurasi.tindak_lanjut_aduan` | `nomor_aduan` (kunci), `tindak_lanjut`, `catatan`, `peran`, `pseudonim_kurator`, `waktu` | `peran_kurasi` |

| Peran | Hak baru | Yang sengaja **tidak** dipegang |
|---|---|---|
| `peran_riwayat` | `INSERT` atas `riwayat.pesan` | `SELECT` atas `riwayat.pesan` — rute riwayat tidak dapat menayangkan ulang jawaban, ditegakkan peladen (C-07) |
| `peran_penilaian` (baru) | `USAGE` riwayat dan kurasi; `SELECT` berkolom atas percakapan (`id_percakapan`, `pemilik`), giliran (`id_pesan`, `pertanyaan`), pesan; `SELECT`, `INSERT` atas penilaian; `INSERT` atas aduan dan aduan_digantikan; `SELECT (nomor, nomor_penilaian)` atas aduan | `UPDATE`, `DELETE`; tindak lanjut; `CONNECT` basis data pseudonim |
| `peran_kurasi` | `SELECT` atas aduan dan aduan_digantikan; `SELECT`, `INSERT` atas tindak_lanjut_aduan | **`USAGE` atas skema `riwayat`** — kurator tidak dapat menjangkau pemilik, percakapan, maupun pesan yang tidak diadukan (R-06, P-2 B) |
| `peran_penarikan` | `SELECT`, `DELETE` atas kelima tabel | — |

**Mengapa salinan, bukan izin baca.** Aduan menyalin pertanyaan dan tanggapan
saat peserta mencentang. Kurator karena itu tidak memerlukan hak apa pun atas
skema `riwayat`, dan batas P-2 B — hanya yang dikirim peserta — menjadi batas
hak peladen, bukan saringan kueri. `id_pesan` dibuang dari salinan: pengenal
itu ikut pada peristiwa `answer_rated` (KB-228), dan pemegang aduan sekaligus
ekspor analitik dapat menautkan aduan ke pseudonim lewatnya.

**Penilaian berikutnya menggugurkan aduan sebelumnya** (R-05) lewat
`aduan_digantikan`, ditulis dalam pernyataan yang sama dengan penilaian baru.
Antrean = aduan yang tidak digugurkan dan belum bertindak lanjut.

## 3. K-2 · Penulisan atomik tanpa transaksi

`SambunganAktif` tidak menyediakan transaksi; setiap penulisan majemuk satu
pernyataan CTE, mengikuti `_CATAT` fitur 028.

- `/tanya`: giliran **dan** pesan dalam satu pernyataan. Tanggapan yang tidak
  tercatat tidak dikirim — sama dengan giliran kini.
- Penilaian: periksa pemilik (pesan → percakapan → `pemilik`), sisipkan
  penilaian, sisipkan aduan bila dikirim, gugurkan aduan terdahulu atas pesan
  yang sama. Pesan milik orang lain tidak menulis apa pun dan tidak
  mengembalikan baris — sama persis dengan pesan yang tidak dikenal (R-01).
- Tindak lanjut: kunci `nomor_aduan` menolak yang kedua; aduan yang digugurkan
  atau sudah bertindak lanjut 404, seperti putusan atas kandidat yang tidak
  menunggu (D-14 4.7).

## 4. K-3 · Bentuk rute (D-14 Bagian 4.9 baru; 3.4 + satu baris)

| Rute | Permintaan | Tanggapan |
|---|---|---|
| `POST /pesan/{id}/penilaian` | `{"nilai": "membantu \| tidak_membantu \| keliru", "alasan": "…", "kirim_ke_kurator": false}`; `alasan` dan `kirim_ke_kurator` boleh tidak ada | 200 `{"id_pesan", "nilai", "kirim_ke_kurator"}` |
| `GET /kurasi/aduan` | — | 200 `{"aduan": [ { "nomor", "diadukan_pada", "pertanyaan", "alasan", "tanggapan" } ]}`, terlama lebih dulu |
| `POST /kurasi/aduan/{id}/tindak-lanjut` | `{"tindak_lanjut": "…", "catatan": "…"}` | 200 bentuk yang sama dengan `GET /kurasi/aduan` — sejajar ketiga rute kurasi 4.7 |

Aturan:

- `kirim_ke_kurator: true` hanya bersama `keliru`; selainnya 400.
- `alasan` dengan data pribadi berpola 400, tanpa mengutip, tanpa log isi.
- Bidang lain ditolak; `application/json` wajib.
- `tanggapan` pada aduan = bentuk D-14 4.1 tanpa `id_pesan`.
- `TindakLanjutAduan`: `sumber_diajukan` (sumber diajukan lewat kanal D-06),
  `butir_ditarik` (FR-I06), `jawaban_sesuai_dasar`, `di_luar_cakupan` —
  keempat contoh P-3 B, tidak ditambah.
- `catatan` wajib, tanpa data pribadi berpola.

## 5. K-4 · Telemetri dan analitik

`answer_rated` lewat gerbang perekaman fitur 034 (C-04):
`{"nilai", "beralasan", "id_pesan"}`. Versi model diambil dari tanggapan
tersimpan yang dinilai, bukan `tanpa_model`. Penilaian yang ditolak tidak
direkam.

Analitik fitur 035 memperoleh bagian `penilaian`:
`{"per_nilai": {"membantu": n, "tidak_membantu": n, "keliru": n}}`, dihitung atas
peristiwa pilot `answer_rated` **terakhir** per (pseudonim, `id_pesan`).
Ketiga kunci selalu ada; nol di sini berarti diukur dan tidak ada.
`MetrikTertunda.AKURASI_QA` keluar dari daftar (P-4 B) — tanpa rasio
"ketepatan" baru.

## 6. K-5 · Penarikan data

`TABEL_DATA_PENGGUNA` bertambah lima (10 → 15); `_HAPUS` menghapusnya dalam
pernyataan yang sama. Aduan ditemukan lewat `nomor_penilaian` → penilaian →
pesan → percakapan milik pseudonim itu. Tindak lanjut kurator atas aduan itu
ikut terhapus: catatannya dapat mengutip isi pertanyaan peserta.

## 7. K-6 · Layar

**S-09.** `BlokJawaban` memperoleh blok "Nilai jawaban" pada **keempat** status
dasar (R-10): tiga pilihan, alasan opsional, centang kirim yang **hanya tampil
bila `keliru`**, tombol kirim. Keadaan tidak-ditemukan memperoleh tombol
"Laporkan bahwa ini seharusnya ada" yang membuka blok itu dengan `keliru`
terpilih. Penilaian dapat diganti; luring tidak diantrekan.

**S-17.** Cangkang kurator memperoleh dua tombol, antrean dan aduan. S-17
mendaftar aduan: waktu, pertanyaan, alasan, jawaban saat itu (blok jawaban
tanpa tindakan), dan isian tindak lanjut. Keterangan tetap menyatakan jawaban
itu **jawaban saat diadukan**, bukan jawaban kini.

**S-18.** Satu tabel "Penilaian jawaban" per nilai.

## 8. Keputusan rancangan Gerbang 2

| Kode | Pertanyaan | Putusan |
|---|---|---|
| K-1 | Tabel dan peran | Bagian 2 — salinan aduan; kurator tanpa hak atas `riwayat` |
| K-2 | Atomik | Bagian 3 — satu pernyataan per penulisan |
| K-3 | Bentuk rute | Bagian 4 |
| K-4 | Telemetri dan analitik | Bagian 5 |
| K-5 | Penarikan | Bagian 6 |
| K-6 | Layar | Bagian 7 |

## 9. Uji

### 9.1 Di dalam `make check`

- Peladen: katalog hak persis bagi keempat peran; penolakan berpenyebab
  `permission denied` — `peran_riwayat` membaca pesan, `peran_kurasi` membaca
  riwayat, `peran_penilaian` mengubah atau menghapus; batasan tabel
- `/tanya` mencatat pesan bersama giliran; gagal mencatat berarti tidak dikirim
- Penilaian atas memori **dan** PostgreSQL: pemilik, aduan hanya bila dikirim,
  penggantian menggugurkan, tanpa `id_pesan` maupun pseudonim pada aduan
- Lewat HTTP: 401/403/404/400; alasan berdata pribadi; tindak lanjut sekali
- Telemetri: properti tepat tiga; tanpa persetujuan tidak direkam
- Analitik: penilaian terakhir per pesan; pengembangan terpisah
- Penarikan: kelima tabel terhapus; tabel lain tidak tersentuh
- Layar: tiga pilihan, centang hanya pada keliru, tidak-ditemukan, luring,
  S-17, S-18

### 9.2 Di luar `make check`

Playwright terhadap `make jalan`: pengguna bertanya, menilai keliru dengan
centang; kurator membuka S-17, melihat aduan tanpa pseudonim, menindaklanjuti;
pengguna menilai ulang pesan lain tanpa centang dan aduan tidak lahir;
peneliti melihat tabel penilaian.

### 9.3 Uji mutasi

| Kode | Mutasi | Uji yang wajib merah |
|---|---|---|
| M-1 | `GRANT SELECT` atas `riwayat.pesan` kepada `peran_riwayat` | katalog hak |
| M-2 | `GRANT USAGE` atas skema `riwayat` kepada `peran_kurasi` | penolakan peladen |
| M-3 | Pesan dicatat terpisah dari giliran (dua pernyataan) | atomik `/tanya` |
| M-4 | Pemilik pesan tidak diperiksa | 404 milik orang lain |
| M-5 | `kirim_ke_kurator` diabaikan — setiap `keliru` menjadi aduan | P-2 B |
| M-6 | `id_pesan` tidak dibuang dari salinan aduan | R-06 |
| M-7 | Penilaian berikutnya tidak menggugurkan aduan | R-05 |
| M-8 | Alasan tidak diperiksa pendeteksi FR-B04 | R-03 |
| M-9 | `answer_rated` membawa teks alasan | P-4 B |
| M-10 | Analitik menghitung setiap penilaian, bukan yang terakhir | KB-228 |
| M-11 | Penarikan melewatkan `kurasi.aduan` | R-07 |
| M-12 | Tindak lanjut kedua diterima | antrean |
| M-13 | Centang kirim tampil pada nilai selain keliru | uji layar |

## 10. Urutan tugas

| Tugas | Isi |
|---|---|
| T-1 | Kontrak: D-14 3.4, 4.8, 4.9, 5.1; D-01 9; D-04 7.4; D-05 S-09, S-17; D-00 |
| T-2 | Peladen: `13-penilaian.sql`, `peran_penilaian`; M-1, M-2 |
| T-3 | Catatan tanggapan pada `/tanya`; TK-69; M-3 |
| T-4 | `src/kamus/penilaian.py`; `src/penyimpanan/penilaian.py`; M-5, M-6, M-7 |
| T-5 | Rute dan `answer_rated`; M-4, M-8, M-9, M-12 |
| T-6 | Penarikan dan analitik; M-10, M-11 |
| T-7 | Layar S-09, S-17, S-18; M-13 |
| T-8 | Titik jalan, bukti Playwright, penutupan: L8, HKI, L4 |

## 11. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Rute lain tampak perlu | Berhenti; AG-02 — hanya satu rute yang disetujui |
| Bidang `/tanya` tampak perlu | Berhenti; C-20 |
| Kurator tampak perlu membaca riwayat | Berhenti; R-06 |
| Penilaian tampak perlu mengubah pengambilan atau ambang | Berhenti; C-14, C-16 |
| Naskah ET-02 tampak perlu kalimat baru | Berhenti; tim etik |
