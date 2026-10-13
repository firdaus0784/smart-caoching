# Plan: 039-jalur-penjawab-postgresql

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 13 Oktober 2026 (KB-278); P-1 s.d. P-6 sesuai anjuran |
| Perubahan atas fitur yang lolos Gerbang 4 | Fitur 006: daftar putih lisensi (TK-87, P-6 A). Fitur 021: `Jalur.jawab()` memilih sitasi dari segmen yang dirujuk klaim (putusan pemegang gerbang, KB-279) |
| Status | **Gerbang 3 lolos** — 13 Oktober 2026 atas pendelegasian KB-168 (KB-279). Tiga dari delapan tugas selesai |
| Kebutuhan | R-01 s.d. R-08 `spec.md`; FR-F02, FR-F03, FR-F11, FR-F14, FR-D06; KL-01, KL-04, KL-07; C-02, C-07, C-16, C-17, C-19, C-20 |

## 1. Letak dan batas

```
perkakas/basis_data/
  17-tautan-sumber.sql            baru — kolom tautan pada penerimaan dan metadata korpus
src/penyimpanan/indeks.py         lisensi dinormalisasi, daftar persis (TK-87)
src/penyimpanan/dasar.py          MetadataDokumen.tautan
src/penyimpanan/karantina.py      CatatanPenerimaan.tautan
src/penyimpanan/postgres.py       tautan ikut catatan metadata pemindahan
src/penyimpanan/korpus_penjawab.py  baru — pemuat segmen beserta catatan dokumennya; sidik
src/ingest/dokumen.py             Dokumen.tautan
src/ingest/gerbang.py             tautan ikut penerimaan dan catatan metadata korpus
src/api/sumber.py                 aturan tampil teks diangkat menjadi satu fungsi bersama (P-4 A)
src/api/tanya.py                  Jalur.jawab memilih sitasi dari klaim (021, KB-279)
src/api/penjawab_korpus.py        baru — kelayakan, muatan, bahan, sitasi, bacaan lanjutan, PenjawabKorpus
perkakas/ingesti.py               terima --tautan
perkakas/pengambilan.py           baru — cari --kueri [--indeks]
docs/                             D-14 4.1, 4.10, 5.1; D-04 7.2; D-06 KL-01; D-00
```

**Tidak disentuh:** `src/rag/`, `src/llm/`, `src/pengguna/`, `src/telemetri/`,
`web/`, dan `perkakas/jalankan_lokal.py`, yang tetap memasang
`PenjawabBelumSiap` (P-1 A). Tanpa rute baru; bentuk `/tanya` dan `/sumber`
tidak berubah (C-20). **Tanpa tepi impor baru**: perakitan tinggal di `api`,
yang sah memanggil `ingest` (`peringkat_bagi`, `JenisSumber`), `rag`, `llm`, dan
`penyimpanan`. `rag` tetap tidak memanggil `ingest`.

## 2. K-1 · Peladen

`17-tautan-sumber.sql`: kolom `tautan` boleh kosong pada `karantina.penerimaan`
dan `korpus.metadata_dokumen`, dengan batasan
`tautan IS NULL OR tautan ~ '^https?://[^[:space:]]+$'`. Hak sisip kedua tabel
diberikan per tabel (fitur 037, 032), sehingga kolom baru tidak menuntut hak
baru; uji katalog membuktikannya alih-alih menganggapnya.

Tanpa peran baru. Pemuat konteks tersambung sebagai `peran_pemanggil_llm`, yang
tidak memegang skema `indeks_metadata` sejak fitur 024; pemuat bacaan lanjutan
sebagai `peran_penjawaban`. Uji peladen: keduanya menjalankan kueri pemuatnya
dengan haknya sendiri, dan `peran_pemanggil_llm` ditolak peladen saat membaca
indeks metadata — penolakan berpenyebab, bukan sekadar galat.

## 3. K-2 · Lisensi (P-6 A, TK-87)

`lisensi_dari_metadata` menormalkan keterangan lebih dulu — huruf kecil;
spasi dan garis bawah menjadi tanda hubung; tanda hubung berulang dirapatkan;
nomor versi di ujung dibuang — lalu mencocokkannya **persis** dengan daftar:
`cc0`, `cc-zero`, `cc-by`, `public-domain`, `domain-publik`, `pddl`, `odc-by`.
Selebihnya tertutup, termasuk `cc-by-nc`, `cc-by-nd`, `cc-by-sa`, dan
gabungannya. `Creative Commons Attribution 4.0` tetap tertutup: normalisasi
tidak menerjemahkan nama panjang, dan arah kekeliruannya yang dikehendaki
KL-01. Daftar ini ditulis pada D-06 aturan pelaksanaan KL-01, pemiliknya.

Uji fitur 006 yang menyatakan varian sebagai terbuka diubah atas P-6 A, dan
perubahannya tercatat. Segmen yang sudah berada di indeks utama dipindah lewat
`indeks --id` fitur 038; sampai itu dilakukan, **lapis kedua** pada pemuat
(Bagian 5) membaca ulang lisensi dari catatan metadata terbaru dan tidak
memuat segmen yang dokumennya kini tertutup.

## 4. K-3 · Tautan sumber asli (P-5 A)

Bentuk yang sama dengan lisensi pada fitur 038: `Dokumen.tautan`,
`CatatanPenerimaan.tautan`, `MetadataDokumen.tautan`, ketiganya boleh kosong
dengan bawaan kosong; `Dokumen` menolak tautan yang bukan `http` atau `https`
atau yang memuat spasi. Gerbang meneruskannya ke penerimaan dan ke catatan
metadata korpus dalam pernyataan pemindahan yang sama. `terima --tautan`
opsional. Pembaca sumber tidak membacanya: `/sumber` tidak mengirim tautan, dan
bentuknya tidak berubah.

## 5. K-4 · Pemuat korpus

`src/penyimpanan/korpus_penjawab.py`:

- `BarisKorpus`: satu segmen — pengenal, dokumen, teks, penanda, lisensi dan
  anonimisasi yang tersimpan pada segmen — beserta catatan metadata terbaru
  dokumennya (boleh kosong) dan catatan status terbarunya (boleh kosong).
  Untai, bukan enum ingesti: penyimpanan tidak mengimpor `ingest`.
- `PemuatKorpus.muat(kredensial, indeks)` → `(sidik, baris)` dalam **satu
  pernyataan**, sehingga sidik dan isi berasal dari potret yang sama;
  `sidik(kredensial, indeks)` menghitung sidik saja.
- Hanya segmen yang dokumennya berada di `korpus.dokumen_sumber` (R-04).
- Kredensial diperiksa sebelum peladen disentuh: baca korpus **dan** baca
  indeks yang diminta. `PEMANGGIL_LLM` atas indeks metadata ditolak di kode,
  lalu di peladen.
- **Sidik** = ringkasan md5 atas pengenal, ringkasan teks, penanda, lisensi,
  dan nomor catatan metadata serta status terbaru tiap dokumen, berurutan
  pengenal. Perubahan status atau metadata mengubah sidik, sehingga regulasi
  yang baru dicabut tidak terus dilayani dari muatan lama.
- Pelaksana memori bagi uji dan PostgreSQL, satu himpunan uji kontrak.

## 6. K-5 · Kelayakan, muatan, bahan (P-2 A, P-3 A, P-4 A)

`src/api/penjawab_korpus.py`. **Kelayakan** satu baris diperiksa berurutan;
yang pertama berlaku menjadi alasannya, dan alasan dihitung, tidak dibuang:

1. tanpa catatan metadata, atau jenis dan tingkat kerahasiaan tidak terbaca;
2. dokumen tidak publik atau dokumen sekolah — **fungsi yang sama** dengan
   pembaca sumber, diangkat dari `src/api/sumber.py` (P-4 A);
3. indeks utama saja: lisensi dokumen kini tertutup menurut catatan metadata
   terbaru (lapis kedua TK-87);
4. anonimisasi belum terverifikasi;
5. regulasi tanpa catatan status (P-3 A, TK-81 A);
6. berstatus `dicabut` (D-07 Bagian 4.5, C-07).

Dokumen bukan regulasi tanpa catatan status bernilai `berlaku` (P-3 A).

**Muatan** — potret beku per sidik: indeks leksikal utama dan metadata yang
dibangun dari baris layak saja lewat `bangun_indeks` fitur 007 (praproses
FR-B03 apa adanya), bahan segmen (`SegmenRujukan` dengan peringkat dari
`peringkat_bagi`, keberlakuan, dan tautan), sitasi per segmen, himpunan segmen
resmi — peringkat T1, "regulasi dan panduan resmi" D-13 Bagian 6 sesuai
kriteria D-07 Bagian 4.6 — dan dokumen bacaan lanjutan per segmen metadata.
Karena hanya baris layak yang diindeks, segmen tak layak tidak pernah menjadi
kandidat dan tidak ikut dihitung penilai kecukupan: tahap 6 berjalan sebelum
tahap 7, sesuai urutan D-07 Bagian 4.

**`PenjawabKorpus`** memenuhi `JalurPenjawab` rute `/tanya`. Penyusunnya
menuntut kedua pemuat, penyemat, sambungan vektor, pemeringkat, ambang,
pembungkus, konfigurasi, dan versi model serta kode — tanpa nilai bawaan
(R-07). Pada setiap `jawab()`:

1. sidik dibaca; bila berubah, muatan baru dibangun **seluruhnya** lalu
   menggantikan yang lama dalam satu penugasan — yang lama melayani sampai
   saat itu (R-06);
2. bacaan lanjutan: pencarian leksikal atas muatan metadata, dokumen unik
   bertautan menurut peringkat, paling banyak `JUMLAH_SEGMEN_DITERUSKAN_MAKSIMUM`
   — tetapan D-07 Bagian 9 dipakai ulang, bukan angka baru;
3. `Jalur` fitur 021 dengan dua sumber atas indeks utama — BM25 muatan dan
   vektor fitur 019 yang kandidatnya dibatasi pada segmen layak — kredensial
   `PEMANGGIL_LLM`, bahan, segmen resmi, sitasi per segmen, bacaan lanjutan,
   pengenal pesan `msg_` acak, dan versi berindeks `utama:<sidik>`.

Teks segmen tidak ditulis ke log (R-08). Ambang dan penyemat sungguhan tidak
dibuat di mana pun pada fitur ini; uji memakai catatan kalibrasi dan penyemat
tiruan yang menyatakan dirinya.

## 7. K-6 · Sitasi dipilih dari klaim (fitur 021, KB-279)

`Jalur.jawab(..., sitasi: Mapping[str, Sitasi])` menggantikan daftar tetap.
Sesudah validasi lulus, sitasi dipilih dari `id_segmen` klaim tervalidasi
menurut urutan kemunculannya, **satu per pasangan dokumen dan bagian**. Segmen
yang dirujuk klaim tetapi tidak ada pada pemetaan adalah kekeliruan pemanggil:
`ValueError`, sebab jawaban yang tampil tanpa sitasi bagi salah satu klaimnya
adalah persis yang C-01 larang. Uji fitur 021 yang tidak pernah mengirim
sitasi tetap lulus; cabang sukses diuji dengan pola penggantian pemeriksaan
model yang sudah ada.

## 8. K-7 · Perkakas pencarian (P-1 A)

`python -m perkakas.pengambilan cari --kueri <teks> [--indeks utama|metadata]`
— utama tersambung sebagai `peran_pemanggil_llm`, metadata sebagai
`peran_penjawaban`. **Satu sumber leksikal**, tanpa penyemat, tanpa model,
tanpa jawaban; penggabungan hibrida tidak dipanggil (ADR-03 tetap utuh).
Keluaran: sidik, jumlah segmen layak dan tak layak per alasan, dokumen yang
perlu diindeks ulang karena lisensinya kini tertutup, lalu peringkat dengan
skor, dokumen, penanda, dan judul — **tanpa teks segmen** (R-08). Jumlah
kandidat `JUMLAH_KANDIDAT_PER_SUMBER`, tetapan D-07 yang sudah ada.

## 9. K-8 · Kontrak

D-14 Bagian 5.1: `penerimaan.tautan`, `metadata_dokumen.tautan`,
`dokumen_sumber.tautan`; keberlakuan dokumen bukan regulasi pada bahan (P-3 A).
Bagian 4.1: aturan `sitasi` — dipilih dari segmen yang dirujuk klaim, satu per
dokumen dan bagian — dan `bacaan_lanjutan` — dokumen indeks metadata yang
bertautan. Bagian 4.10: alasan tautan tidak dikirim diperbarui; bentuknya
tetap. D-04 Bagian 7.2: `metadata_dokumen.tautan`. D-06 aturan pelaksanaan
KL-01: daftar lisensi terbuka persis. Tanpa rute (R-05).

## 10. Keputusan rancangan Gerbang 2

| Kode | Pertanyaan | Putusan |
|---|---|---|
| K-1 | Peladen | Bagian 2 — kolom tautan; tanpa peran baru; pemuat berjalan sebagai peran sungguhan |
| K-2 | Lisensi | Bagian 3 — normalisasi lalu daftar persis; lapis kedua pada pemuat |
| K-3 | Tautan | Bagian 4 — bentuk lisensi fitur 038 |
| K-4 | Pemuat | Bagian 5 — satu pernyataan, sidik dari potret yang sama |
| K-5 | Muatan | Bagian 6 — kelayakan sebelum indeks leksikal; ganti muatan utuh |
| K-6 | Sitasi | Bagian 7 — dipilih dari klaim; kekeliruan pemanggil melempar |
| K-7 | Perkakas | Bagian 8 — satu sumber leksikal, tanpa teks |
| K-8 | Kontrak | Bagian 9 |

## 11. Uji

### 11.1 Di dalam `make check`

- Peladen: kolom dan batasan tautan; katalog hak tidak bertambah; kedua pemuat
  berjalan pada haknya; `peran_pemanggil_llm` ditolak membaca indeks metadata
- Lisensi: normalisasi dan daftar persis, kedua arah TK-87
- Tautan ikut penerimaan dan catatan metadata korpus; `terima --tautan`
- Pemuat atas memori **dan** PostgreSQL sebagai peran sungguhan: hanya korpus;
  catatan terbaru; sidik deterministik dan berubah bersama isi, metadata, dan
  status; kredensial tanpa indeks ditolak sebelum menyentuh
- Kelayakan: keenam alasan berurutan; bukan regulasi tanpa status berlaku
- `PenjawabKorpus` atas PostgreSQL: data yang sampai ke model hanya segmen
  utama yang layak; versi indeks pada tanggapan; muatan diganti saat sidik
  berubah; bacaan lanjutan bertautan; sitasi dari klaim
- Perkakas: perannya, keluaran tanpa teks, tanpa log

### 11.2 Di luar `make check`

Regulasi contoh berlisensi `CC BY 4.0` dan `CC-BY-NC 4.0` bertautan melewati
`terima --tautan`, `setujui`, status, dan `indeks`; yang pertama ke indeks
utama, yang kedua ke indeks metadata. `cari` menemukan pasal yang dirujuk;
dokumen yang lisensinya berubah tertangkap sebagai perlu diindeks ulang.
Keluaran ke `bukti/`.

### 11.3 Uji mutasi

| Kode | Mutasi | Uji yang wajib merah |
|---|---|---|
| M-1 | Pemuat konteks diberi kredensial yang menjangkau indeks metadata | C-02 |
| M-2 | Syarat dokumen di korpus dihapus dari pemuat | R-04 |
| M-3 | Regulasi tanpa status dianggap berlaku | P-3 |
| M-4 | Regulasi dicabut tidak dikeluarkan | C-07 |
| M-5 | Dokumen sekolah masuk bahan | P-4 |
| M-6 | Lisensi tidak dibaca ulang pada pemuat | TK-87 lapis kedua |
| M-7 | Pencocokan awalan dikembalikan | TK-87 |
| M-8 | Sitasi seluruh bahan, bukan yang dirujuk klaim | K-6 |
| M-9 | Sidik tanpa nomor catatan status | R-06 |
| M-10 | Perkakas mencetak teks segmen | R-08 |
| M-11 | Tautan tidak ikut catatan metadata pemindahan | P-5 |
| M-12 | Batasan bentuk tautan dihapus | K-1 |

## 12. Urutan tugas

| Tugas | Isi |
|---|---|
| T-1 | Kontrak: D-14 4.1, 4.10, 5.1; D-04 7.2; D-06 KL-01; D-00 |
| T-2 | Peladen: `17-tautan-sumber.sql`; pemuat berjalan sebagai perannya; M-12 |
| T-3 | Lisensi dinormalisasi (TK-87); uji fitur 006 disesuaikan; M-7 |
| T-4 | Tautan dicatat: `Dokumen`, catatan, pemindahan, `terima --tautan`; M-11 |
| T-5 | Pemuat korpus memori dan PostgreSQL; M-1, M-2, M-9 |
| T-6 | Kelayakan, muatan, sitasi dari klaim, `PenjawabKorpus`; M-3, M-4, M-5, M-6, M-8 |
| T-7 | Perkakas `cari`; M-10 |
| T-8 | Bukti, penutupan: L8, HKI, L4; status menunggu Gerbang 4 |

## 13. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Ambang, penyemat, atau model sungguhan tampak perlu dibuat | Berhenti; BT-29, ADR-12, C-16 |
| Validator tampak perlu dilonggarkan agar jawaban keluar | Berhenti; C-16 |
| Bentuk `/tanya` atau `/sumber` tampak perlu berubah | Berhenti; C-20 |
| `rag` tampak perlu memanggil `ingest` | Berhenti; `AGENTS.md` |
| Titik jalan tampak perlu memakai `PenjawabKorpus` | Berhenti; P-1 A |
