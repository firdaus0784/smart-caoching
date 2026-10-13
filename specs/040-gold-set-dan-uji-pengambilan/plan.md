# Plan: 040-gold-set-dan-uji-pengambilan

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 13 Oktober 2026 (KB-291); P-1 s.d. P-6 sesuai anjuran |
| Perubahan atas fitur yang lolos Gerbang 4 | Tidak ada. `src/logbook/artefak.py` (fitur 026) bertambah satu jenis artefak sebagaimana dijanjikan uraiannya: *"sisanya menyusul bersama fitur yang menghasilkannya"* |
| Status | **Gerbang 3 lolos** — 13 Oktober 2026 atas pendelegasian KB-168 (KB-292). Nol dari delapan tugas selesai |
| Kebutuhan | R-01 s.d. R-08 `spec.md`; D-08 Bagian 5 dan 6 (U3); BT-35; KL-01; AP-01 s.d. AP-07; C-09, C-16, C-17, C-20 |

## 1. Letak dan batas

```
src/rag/evaluasi/
  __init__.py
  gold_set.py        baru — bentuk berkas, jenis A s.d. F, kunci, sidik kanonik, komposisi
  kunci.py           baru — satuan penanda, pencocokan kunci, pemeriksaan terhadap korpus
  metrik.py          baru — Recall@8, MRR, Precision@5, recall bernomor regulasi; persen D-08
  pengukur.py        baru — satu putaran atas satu sumber kandidat; kebocoran; sebab luput
  jejak.py           baru — pembekuan ke L2, putaran ke L1, pembacaan keduanya
src/logbook/artefak.py   VersiGoldSet; KeteranganArtefak menjadi dua jenis
src/logbook/pembaca.py   baru — membaca baris L1 dan L2; tanpa cara menulis
perkakas/evaluasi.py     baru — periksa, bekukan, ukur
docs/                    D-08 Bagian 5.3 baru dan 6; D-10 Bagian 3 dan 4; D-00
```

**Tidak disentuh:** `src/api/`, `src/penyimpanan/`, `src/ingest/`, `src/llm/`,
`src/pengguna/`, `src/telemetri/`, `web/`, `perkakas/basis_data/`, dan
`perkakas/jalankan_lokal.py`. Tanpa rute, tanpa skema, tanpa peran, tanpa hak
peladen baru (R-08, C-17, C-20). Tanpa paket baru (C-12): `json`, `hashlib`,
`fractions`, dan `decimal` pustaka baku.

**Tepi impor.** `src/rag/evaluasi/` mengimpor `src/rag/pengambilan/` (kontrak
`SumberKandidat`), `src/nlp/anotasi/skema.py` (`KategoriMasalah`; tepi
`rag → nlp` sudah tertulis), dan `src/logbook/`. Ia **tidak** mengimpor `api`
maupun `penyimpanan`: baris korpus diserahkan perkakas sebagai pengenal dan
penanda. Perakitan — pemuat PostgreSQL, `bangun_muatan`, `SumberBM25` —
tinggal di `perkakas/evaluasi.py`, sama dengan `perkakas/pengambilan.py`
fitur 039. Tanpa tepi baru.

**Mengapa `rag`, bukan lapisan baru.** Yang diukur adalah pengambilan, dan
`rag` sudah memiliki tepi ke `nlp` dan `logbook` yang dibutuhkan. Lapisan
`src/evaluasi/` menuntut baris arsitektur baru pada `AGENTS.md` bagi tiga
modul murni.

## 2. K-1 · Bentuk berkas (P-1 A, R-01, R-02)

JSON Lines UTF-8, satu baris satu pertanyaan; baris hampa dilewati; kunci
kembar pada satu baris ditolak. Bentuknya tertulis pada D-08 Bagian 5.3 baru:

| Bidang | Wajib | Ketentuan |
|---|---|---|
| `id` | ya | Unik; huruf, angka, titik, garis bawah, tanda hubung; paling panjang 64. Satu-satunya pengenal yang muncul pada laporan dan logbook |
| `pertanyaan` | ya | Kata-kata asli kepala sekolah. **Tidak pernah** muncul pada laporan, pesan galat, maupun logbook (R-07) |
| `jenis` | ya | `A` s.d. `F`, D-08 Bagian 5.1 |
| `kategori` | ya, kecuali jenis D | `K1` s.d. `K8`, D-03 Bagian 5 (`KategoriMasalah`) |
| `kunci` | sesuai jenis | Daftar `{"dokumen": …, "bagian": …}`; C dan D kosong; A, B, E sedikitnya satu; F sedikitnya dua; tanpa kembar |
| `bernomor_regulasi` | ya, tanpa nilai baku | Ditandai tim (P-6 A). Tanpa nilai baku: nilai baku `false` diam-diam mengeluarkan pertanyaan dari himpunan berambang 95% |

`JenisPertanyaan` enum enam nilai milik D-08 Bagian 5.1; `KOMPOSISI_D08`
dicocokkan uji dengan tabel D-08 Bagian 5.1, bukan disalin dari ingatan.

**Pesan galat tanpa teks.** Galat bentuk dilaporkan sebagai nomor baris,
bidang, dan sebab. Galat pydantic diubah memakai `loc` dan `msg` saja —
`input` tidak pernah dibawa — sehingga pertanyaan yang salah bentuk tidak
bocor lewat pesannya.

**Berkas di dalam repositori ditolak perkakas** (R-01): jalur yang terurai ke
dalam pohon kerja repositori ditolak sebelum dibaca. Contoh rekaan pada uji
dibangun di `tmp_path`.

## 3. K-2 · Kunci dokumen dan pasal (P-2 A)

**Satuan sebuah penanda** adalah penanda fitur 038 tanpa akhiran pemotongan:
bagian sesudah `" ayat ("` atau `", "` pertama dibuang. Maka `Pasal 7 ayat
(1)–(3)`, `Pasal 7, potongan 2 dari 3`, dan `Pasal 7` bersatuan `Pasal 7`;
`Penjelasan Pasal 1` bersatuan dirinya; `Pasal 7A` dan `Pasal 71` bukan
`Pasal 7`.

**Kunci cocok dengan segmen** bila dokumennya sama dan satuan penanda segmen
**sama persis** dengan `bagian` kunci. Bukan awalan: awalan membuat `Pasal 2`
cocok dengan `Pasal 21`.

**`bagian` kunci wajib berupa satuan** — memuat `" ayat ("` atau `", "`
ditolak bentuk. Inilah yang membuat *gold set* beku tahan pengindeksan ulang
dan perubahan ukuran segmen D-07 Bagian 3.2, alasan P-2 A.

**Batas yang dinyatakan terbuka.** Dokumen tanpa pasal dipotong fitur 038
menjadi `Bagian k` menurut ukuran; nomor itu ikut berubah bila ukuran segmen
berubah. Kunci atas dokumen semacam itu tidak tahan perubahan D-07 Bagian 3.2,
dan D-08 Bagian 5.3 menyatakannya.

**Pemeriksaan terhadap korpus** (R-02) memakai seluruh segmen kedua indeks,
layak atau tidak: kunci yang dokumennya tidak bersegmen di korpus →
*dokumen di luar korpus*; dokumennya ada tetapi tidak satu segmen pun
bersatuan sama → *bagian tanpa segmen*. Laporannya menyebut pengenal
pertanyaan, urutan kunci, dokumen, dan bagian — tanpa teks.

## 4. K-3 · Sidik dan pembekuan (P-3 A, R-03)

**Sidik kanonik**: `sha256:` atas JSON padat bersusun kunci terurut dari
seluruh pertanyaan yang sudah tervalidasi, diurutkan menurut `id`, dengan
kunci tiap pertanyaan diurutkan menurut (dokumen, bagian). Urutan baris,
urutan bidang, dan spasi di luar nilai tidak mengubahnya; satu huruf pada
pertanyaan, satu kunci, satu jenis, atau satu tanda bernomor mengubahnya.

**`bekukan` menolak** bila: bentuk tidak sah; pemeriksaan korpus menemukan
masalah; komposisi per jenis tidak sama persis dengan D-08 Bagian 5.1 (P-3 A);
sidik sudah tercatat beku; atau label versi sudah dipakai bersidik lain.

**Baris L2** bertipe `VersiGoldSet` pada `src/logbook/artefak.py`:
`artefak = "gold-set"`, `versi`, `sidik`, `dibekukan_pada` (UTC), `jumlah`,
`komposisi_jenis`, `komposisi_kategori`, `jumlah_bernomor_regulasi`,
`pelaku`. Komposisi wajib menjumlah — pola `VersiIndeks`. `pelaku` wajib:
spec fitur 025 menuntut nama yang dapat ditanya, bukan "tim".

**`ukur` menolak** berkas yang sidiknya tidak tercatat pada baris L2
`gold-set`. Penolakan ini terjadi **sebelum** apa pun dibaca dari peladen dan
tidak dicatat ke L1: berkas yang belum beku belum menjadi bahan percobaan.

## 5. K-4 · Metrik (R-04, P-5 A)

Definisi milik D-08 Bagian 6. Yang tidak dinyatakan tabelnya dijelaskan pada
D-08 Bagian 6 sebagai **aturan pelaksanaan**, sebelum kode, dengan pilihan
yang menurunkan angka bila ragu:

| Metrik | Populasi | Pelaksanaan |
|---|---|---|
| Recall@8 | Jenis A | Pertanyaan terhitung bila **setiap** kuncinya memiliki sedikitnya satu segmen cocok pada 8 teratas |
| MRR | Jenis A | Kebalikan peringkat segmen cocok pertama pada daftar kandidat (20, D-07 Bagian 4.4); di luar daftar bernilai 0 |
| Precision@5 | Jenis A | Segmen cocok kunci pada 5 teratas dibagi 5, dirata-rata; **batas bawah** (P-5 A) |
| Recall bernomor regulasi | Jenis A bertanda `bernomor_regulasi` | Seperti Recall@8 |
| Kebocoran indeks | Seluruh pertanyaan, seluruh kandidat | Jumlah kandidat yang pengenalnya ada pada indeks metadata |

Alasan "setiap kunci": kunci disusun tim sebagai segmen pendukung yang benar;
pertanyaan yang separuh dasarnya terambil adalah pertanyaan yang jawabannya
dapat separuh benar. Pilihan "salah satu kunci" menaikkan angka tanpa
menaikkan mutu.

**Pertanyaan tidak pernah keluar dari penyebut.** Kunci yang tidak lagi
ditemukan di korpus — korpus berubah sesudah pembekuan — dihitung luput dan
disebut sebabnya. Mengeluarkannya menaikkan angka atas pertanyaan yang justru
gagal.

**Angka**: pecahan tepat (`Fraction`) beserta pembilang dan penyebut;
persen ditulis satu desimal **dipangkas ke bawah** (AP-06), sehingga 89,96%
tertulis 89,9%, bukan 90,0%. Penyebut nol → *tidak terhitung* beserta
sebabnya, bukan 0.

**Per kelas** (AP-03): ketiga metrik per jenis berkunci (A, B, E, F) dan per
kategori pada jenis A, tanpa ambang.

**Tanpa tetapan ambang.** `K_RECALL = 8` dan `K_PRESISI = 5` adalah definisi
metrik, diuji terhadap tabel D-08. Ambang 90% dan 95% **tidak** ditulis ke
kode: konfigurasi yang dapat berjalan hari ini hanya satu sumber, dan ambang
D-08 berlaku bagi pengambilan hibrida (P-4 A). Menuliskannya sekarang
membangun putusan yang tidak dapat dijalankan. Ambang kebocoran nol adalah
aturan kepatuhan, diuji terhadap baris D-08.

## 6. K-5 · Pengukur (P-4 A, R-05)

`ukur(gold, sumber, segmen, layak, id_metadata)` — fungsi asinkron murni:

- `sumber`: satu `SumberKandidat`; setiap pertanyaan, **termasuk C dan D**,
  dicari dengan `batas = JUMLAH_KANDIDAT_PER_SUMBER`. Kebocoran dapat muncul
  pada kueri apa pun.
- `segmen`: pengenal → (dokumen, penanda) bagi seluruh segmen kedua indeks.
- `layak`: pengenal segmen bahan indeks utama (`Muatan.layak_utama`).
- `id_metadata`: pengenal segmen indeks metadata.

Hasilnya per pertanyaan: peringkat cocok pertama, kunci yang luput beserta
sebabnya — **di luar korpus**, **di luar bahan** (ada di korpus, tidak layak
atau di indeks metadata), atau **di luar 8 teratas** — dan kandidat bocor.

**Konfigurasi dinyatakan** dari sumbernya: nama, indeks tujuan, kedalaman,
versi penyemat bila ada. Putaran satu sumber **tidak pernah** menyatakan U3
lulus; laporannya berbunyi: ambang D-08 Bagian 6 berlaku bagi pengambilan
hibrida dan tidak diterapkan pada putaran ini.

**Putusan** dua saja: *gagal kepatuhan KL-01* bila kebocoran lebih dari nol;
selain itu *diukur*. Putusan bagi pengambilan hibrida menyusul bersama ADR-12.

## 7. K-6 · Logbook (R-03, R-06, R-07, AP-05)

`src/logbook/pembaca.py`: `baca(akar, buku)` → baris terurai; berkas yang
belum ada → kosong. Modul itu tidak menyediakan cara menulis; `penulis.py`
tetap satu-satunya jalur menulis.

**Satu baris L1 per putaran** lewat `tambah_baris(…, Buku.L1, …)` dengan
kelima bidang `Versi` (pemeriksa V-0x tetap lulus) dan bidang D-10 Bagian 3:

| Bidang | Isi |
|---|---|
| `id_percobaan` | `EXP-2026-nnn`, dari tim; ditolak bila sudah ada pada L1 |
| `tujuan`, `tugas` | tetap; `tugas` = `pengambilan` (D-10 Bagian 3 bertambah) |
| `versi_kode` | penanda commit; berakhiran `+ubahan` bila pohon kerja di luar `logbook/` berubah |
| `versi_indeks` | `Muatan.versi_indeks`; `tidak-terbaca` bila peladen menolak |
| `versi_model`, `versi_skema_anotasi`, `pembagian_data`, `model_dasar`, `perangkat_keras` | `belum-berlaku` (R-12) |
| `versi_gold_set`, `sidik_gold_set` | dari baris L2 yang cocok |
| `pembukaan_gold_set` | putaran ke berapa atas sidik ini, dihitung dari L1 — AP-05 terbaca, tidak diingat |
| `konfigurasi` | sumber, indeks, kedalaman, k |
| `hasil` | angka beserta pembilang dan penyebut, per kelas, kebocoran, pertanyaan gagal — **pengenal saja** |
| `status`, `catatan` | `berhasil`; `gagal` beserta dugaan penyebab bila kebocoran atau peladen menolak |
| `durasi_detik` | — |

**Putaran yang gagal tercatat** (R-06): setiap `ukur` yang lolos pemeriksaan
beku, apa pun yang terjadi sesudahnya.

**Akar logbook bukan argumen baris perintah.** Perkakas menulis ke
`logbook/` repositori; uji dan naskah bukti memanggil `utama(…,
akar_logbook=…)` dengan akar sementara. Pembekuan *gold set* rekaan tidak
pernah sampai ke L2 repositori, yang tambah-saja dan tidak dapat dikoreksi.

## 8. K-7 · Perkakas (R-08)

```
python -m perkakas.evaluasi periksa --berkas <jalur>
python -m perkakas.evaluasi bekukan --berkas <jalur> --versi <label> --pelaku <nama>
python -m perkakas.evaluasi ukur    --berkas <jalur> --id-percobaan EXP-2026-nnn
```

Korpus dibaca dengan peran pemuat fitur 039 — indeks utama sebagai
`peran_pemanggil_llm`, indeks metadata sebagai `peran_penjawaban` — lewat
`PemuatKorpusPostgres`; muatan dirakit `bangun_muatan`; sumbernya
`SumberBM25` atas `Muatan.indeks_leksikal[UTAMA]`, persis yang dipakai jalur
penjawab. Kode keluar: 0 berhasil; 1 ditolak peladen; 2 masukan tidak sah,
termasuk belum beku dan komposisi menyimpang; 3 diukur dengan kebocoran.
Keluaran tanpa teks pertanyaan dan teks segmen; tanpa log.

## 9. K-8 · Kontrak

- **D-08 Bagian 5.3 baru**: bentuk berkas, satuan dan pencocokan kunci, batas
  dokumen tanpa pasal, sidik, pembekuan, berkas di luar repositori.
- **D-08 Bagian 6**: aturan pelaksanaan Bagian 5 di atas; konfigurasi
  dinyatakan; putaran satu sumber tidak menyatakan U3 lulus.
- **D-10 Bagian 3** `tugas` bertambah `pengambilan`; **Bagian 4** baris *gold
  set*: sidik, komposisi, jumlah bernomor regulasi, pelaku.
- **D-00** register.

## 10. Keputusan rancangan Gerbang 2

| Kode | Pertanyaan | Putusan |
|---|---|---|
| K-1 | Bentuk berkas | Bagian 2 — JSONL; `bernomor_regulasi` tanpa nilai baku; pesan tanpa teks; berkas di dalam repositori ditolak |
| K-2 | Kunci | Bagian 3 — satuan penanda, sama persis; kunci di bawah pasal ditolak |
| K-3 | Pembekuan | Bagian 4 — sidik kanonik; komposisi D-08 persis; ukur menolak sebelum menyentuh peladen |
| K-4 | Metrik | Bagian 5 — setiap kunci; tidak keluar dari penyebut; dipangkas ke bawah; tanpa tetapan ambang |
| K-5 | Pengukur | Bagian 6 — seluruh pertanyaan dicari; tiga sebab luput; dua putusan |
| K-6 | Logbook | Bagian 7 — pembaca terpisah; L1 tiap putaran; pembukaan dihitung; akar bukan argumen |
| K-7 | Perkakas | Bagian 8 — peran pemuat fitur 039; empat kode keluar |
| K-8 | Kontrak | Bagian 9 |

## 11. Uji

### 11.1 Di dalam `make check`

- Bentuk: setiap aturan jenis dan kunci; `bernomor_regulasi` wajib; pesan
  galat tidak memuat teks pertanyaan; komposisi dan enam jenis dibaca dari
  tabel D-08 Bagian 5.1
- Sidik: tetap terhadap urutan baris, bidang, dan kunci; berubah terhadap
  setiap bidang isi
- Kunci: satuan; `Pasal 2` tidak cocok `Pasal 21` maupun `Pasal 2A`; kunci di
  bawah pasal ditolak; dua masalah korpus
- Metrik: setiap definisi pada contoh kecil yang dihitung tangan; k dan
  kebocoran nol dibaca dari tabel D-08 Bagian 6; pemangkasan; penyebut nol
- Pengukur: sebab luput ketiganya; kebocoran dari sumber atas indeks metadata;
  pertanyaan C dan D ikut dicari
- Logbook: `VersiGoldSet` menjumlah dan berzona; pembaca; L1 berbidang versi
  lengkap; pembukaan dihitung
- Perkakas atas PostgreSQL **sebagai peran sungguhan**: periksa, bekukan,
  ukur; berkas belum beku ditolak tanpa baris L1; putaran yang ditolak peladen
  tercatat gagal; keluaran dan L1 tanpa teks; berkas di dalam repositori
  ditolak

### 11.2 Di luar `make check`

Korpus contoh fitur 039 diindeks lewat perkakas ingesti; *gold set* rekaan
berkomposisi D-08 **disusun naskah dan dinyatakan rekaan** pada setiap
pertanyaan; `periksa`, `bekukan`, dan `ukur` dijalankan atas PostgreSQL dengan
akar logbook sementara. Keluaran ke `bukti/`, beserta pernyataan bahwa
angkanya tidak bermakna sebagai hasil U3.

### 11.3 Uji mutasi

| Kode | Mutasi | Uji yang wajib merah |
|---|---|---|
| M-1 | Pembekuan tidak memeriksa komposisi | P-3 A |
| M-2 | Pengukur tidak memeriksa pembekuan | R-03 |
| M-3 | Pencocokan kunci memakai awalan | P-2 A |
| M-4 | Jenis F menerima satu kunci | R-02 |
| M-5 | Sidik bergantung pada urutan baris | R-03 |
| M-6 | Kebocoran tidak dihitung | R-05 |
| M-7 | Recall terhitung bila salah satu kunci masuk | K-4 |
| M-8 | Persen dibulatkan, bukan dipangkas | AP-06 |
| M-9 | Pertanyaan yang kuncinya hilang keluar dari penyebut | K-4 |
| M-10 | Laporan memuat teks pertanyaan | R-07 |
| M-11 | Putaran yang ditolak peladen tidak dicatat | R-06 |
| M-12 | Berkas di dalam repositori diterima | R-01 |

## 12. Urutan tugas

| Tugas | Isi |
|---|---|
| T-1 | Kontrak: D-08 Bagian 5.3 dan 6; D-10 Bagian 3 dan 4; D-00 |
| T-2 | Bentuk *gold set* dan sidik; M-4, M-5 |
| T-3 | Kunci dan pemeriksaan korpus; M-3 |
| T-4 | Metrik; M-7, M-8 |
| T-5 | Pengukur; M-6, M-9 |
| T-6 | Logbook: `VersiGoldSet`, pembaca, jejak |
| T-7 | Perkakas `periksa`, `bekukan`, `ukur`; M-1, M-2, M-10, M-11, M-12 |
| T-8 | Bukti, penutupan: L8, HKI, L4; status menunggu Gerbang 4 |

## 13. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Isi *gold set* sungguhan tampak perlu disusun agen | Berhenti; D-08 Bagian 5.2, spec fitur 025 |
| Ambang U3 atau kecukupan tampak perlu ditulis ke kode | Berhenti; C-16, P-4 A |
| Komposisi tampak perlu dilonggarkan agar dapat dibekukan | Berhenti; P-3 A |
| Peran, hak, skema, atau rute baru tampak perlu | Berhenti; R-08 |
| `rag` tampak perlu mengimpor `api` atau `penyimpanan` | Berhenti; `AGENTS.md` |
| Baris L1 atau L2 repositori tampak perlu ditulis oleh uji atau bukti | Berhenti; logbook tambah-saja |
