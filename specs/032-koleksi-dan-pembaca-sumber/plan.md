# Plan: 032-koleksi-dan-pembaca-sumber

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 9 Oktober 2026 (KB-241); P-1 s.d. P-4 sesuai anjuran |
| Temuan yang diputus sebelum plan | TK-81 A (KB-242): catatan status di korpus. TK-82 A (KB-243): metadata asal dicatat gerbang ingesti |
| Status | **Gerbang 3 lolos** — 9 Oktober 2026 atas pendelegasian KB-168 (KB-243). Tujuh dari delapan tugas selesai |
| Kebutuhan | R-01 s.d. R-10 `spec.md`; FR-F11, FR-G06, FR-G10, FR-B06, NFR-09; C-02, C-03, C-04, C-05, C-07, C-13, C-14, C-17, C-20 |

## 1. Letak dan batas

```
perkakas/basis_data/
  01-peran-dan-basis-data.sql   + peran_pembaca_sumber, peran_koleksi
  14-sumber-dan-koleksi.sql     baru — korpus.metadata_dokumen, korpus.status_dokumen,
                                penemuan.koleksi; hak kelima peran; hak hapus peran_penarikan
src/penyimpanan/dasar.py        MetadataDokumen; pindahkan(..., metadata=None)
src/penyimpanan/tiruan.py       metadata ikut pemindahan ke korpus
src/penyimpanan/postgres.py     metadata dalam pernyataan yang sama dengan pemindahan
src/penyimpanan/kurasi.py       perbarui_status(..., rujukan_pengganti=None); catatan korpus
                                dalam pernyataan yang sama dengan salinan kurasi
src/penyimpanan/sumber.py       baru — pembaca sumber, memori dan PostgreSQL
src/penyimpanan/koleksi.py      baru — koleksi, memori dan PostgreSQL
src/penyimpanan/penarikan.py    + penemuan.koleksi
src/ingest/gerbang.py           setujui() menyerahkan metadata asal ke pemindahan
perkakas/kurasi.py              status --pengganti
src/api/sumber.py               baru — bentuk dan aturan pembaca sumber
src/api/koleksi.py              baru — simpan, keluarkan, daftar
src/api/aplikasi.py             empat rute
src/api/peran.py                PETA_RUTE
src/api/rekaman.py              + rekam_sumber_dibuka, rekam_simpan
src/api/analitik.py             + penelusuran_sumber; RASIO_PENELUSURAN_SUMBER keluar
perkakas/jalankan_lokal.py      pembaca sumber dan koleksi berperan masing-masing
web/src/sumber/                 S-10 LayarSumber
web/src/koleksi/                S-11 LayarKoleksi
web/src/penemuan/LayarButir.tsx S-06 blok 8: Simpan
web/src/tanya/BlokJawaban.tsx   S-09 blok 5: baris sitasi membuka S-10
web/src/Aplikasi.tsx            navigasi "Milik saya"
web/src/pengaturan/             S-14 menyebut koleksi pada data yang ditarik
web/src/analitik/               tabel penelusuran sumber
docs/                           D-14 3.3, 4.8, 4.10, 5.1; D-04 7.2, 7.4; D-05 3.1, S-06,
                                S-09, S-10, S-11; D-12 baris 032; D-00. D-01 tidak berubah
```

**`src/rag/`, `src/llm/`, `src/pengguna/`, `src/nlp/` tidak disentuh.**
`src/ingest/` disentuh pada satu tempat saja — `setujui()` — atas putusan TK-82
A. Tidak ada tepi impor baru: `api → ingest` (enum jenis dan tingkat
kerahasiaan), `api → penyimpanan`, `api → telemetri`, `api → nlp` (pendeteksi
FR-B04 bagi catatan), dan `ingest → penyimpanan` sudah tertulis pada
AGENTS.md.

## 2. K-1 · Tabel dan peran

| Tabel | Isi | Penulis |
|---|---|---|
| `korpus.metadata_dokumen` | `nomor`, `id_dokumen`, `judul`, `jenis`, `penerbit`, `tahun`, `tingkat_kerahasiaan`, `dicatat_pada` — tambah-saja, yang terbaru berlaku | `peran_verifikasi`, **dalam pernyataan yang sama** dengan pemindahan dokumen ke korpus (TK-82 A) |
| `korpus.status_dokumen` | `nomor`, `id_dokumen`, `status` (KL-07), `rujukan_pengganti` (boleh kosong; hanya bersama `diubah` atau `dicabut`), `dicatat_pada` — tambah-saja, yang terbaru berlaku | `peran_pengisi_antrean`, **dalam pernyataan yang sama** dengan salinan status kurasi (TK-81 A) |
| `penemuan.koleksi` | `id_pengguna` (pseudonim), `id_butir`, `catatan` (boleh kosong), `disimpan_pada`; kunci (`id_pengguna`, `id_butir`) | `peran_koleksi` |

| Peran | Hak baru | Yang sengaja **tidak** dipegang |
|---|---|---|
| `peran_pembaca_sumber` (baru) | `USAGE` korpus dan indeks_utama; `SELECT (id)` atas `korpus.dokumen_sumber`; `SELECT` atas kedua tabel catatan korpus; `SELECT (id_segmen, id_dokumen, teks, lisensi, anonimisasi_terverifikasi, penanda_bagian)` atas `indeks_utama.segmen_teks` | Kolom `isi` dokumen korpus — teks dokumen utuh (P-2 B ditolak); kolom vektor; **`USAGE` atas karantina dan `indeks_metadata`** (C-03, C-02); tulis apa pun (R-05) |
| `peran_koleksi` (baru) | `USAGE` penemuan; `SELECT`, `INSERT`, `DELETE`, `UPDATE (catatan, disimpan_pada)` atas `penemuan.koleksi` | Kurasi, tayang harian, belum relevan — kelayakan butir dibaca penayang (Bagian 5) |
| `peran_penayangan` | — | **Hak apa pun atas `penemuan.koleksi`**: pemilihan beranda tidak dapat membaca koleksi, ditegakkan peladen (R-03, C-14) |
| `peran_pengisi_antrean` | `USAGE` korpus; `INSERT` atas `korpus.status_dokumen` | `SELECT` atas korpus — perkakas kurasi tetap tidak membaca dokumen |
| `peran_verifikasi` | `INSERT` atas `korpus.metadata_dokumen` (hak bawaan skema korpus) | `UPDATE` atas kedua tabel catatan, dan `INSERT` atas `status_dokumen` — dicabut dari hak bawaan skema |
| `peran_penarikan` | `SELECT (id_pengguna)`, `DELETE` atas `penemuan.koleksi` | — |

Hak bawaan skema korpus (`02-skema-dan-hak.sql`) memberi `SELECT` kepada
`peran_penjawaban` dan `peran_pemanggil_llm` atas kedua tabel catatan. Itu
dibiarkan: jalur penjawab kelak membaca status dan metadata dari sana (C-07,
penyusun sitasi fitur 021). Uji katalog menyebutnya, agar hak itu terbaca
sebagai rancangan.

`jenis`, `tingkat_kerahasiaan`, dan `status` dijaga batasan tabel atas daftar
nilai `JenisSumber`, `TingkatKerahasiaan`, dan `StatusKeberlakuan`; uji
membandingkan batasan dengan enumnya, sehingga nilai keenam pada enum
menjatuhkan uji, bukan penulisan di lapangan.

## 3. K-2 · Metadata dan status dicatat atomik

`SambunganAktif` tanpa transaksi; setiap penulisan majemuk satu pernyataan.

- **Pemindahan ke korpus** (TK-82 A). `pindahkan()` menerima `metadata` hanya
  bila tujuannya korpus. Pernyataannya: hapus dari karantina → sisipkan ke
  korpus → sisipkan metadata **dari baris yang berpindah**. Metadata yang
  ditolak batasan tabel membatalkan pemindahan; dokumen tetap di karantina.
  `MetadataDokumen` tinggal di `src/penyimpanan/` sebagai untai dan bilangan:
  penyimpanan berada di bawah ingesti dan tidak mengimpor enumnya
  (alasan yang sama dengan `anonimisasi_terverifikasi` pada `SegmenTerindeks`).
- **Penarikan dari korpus** tidak menulis metadata. Pembaca mensyaratkan
  dokumen ada di korpus, sehingga dokumen yang ditarik — persetujuan pemilik
  dicabut — berbentuk sama dengan yang tidak dikenal.
- **Status** (TK-81 A). `_PERBARUI_STATUS` memperoleh satu bagian CTE lagi:
  catatan korpus disisipkan bersama salinan kandidat dan butir tayang. Status
  yang tercatat di korpus tetapi tidak tersalin ke kurasi — atau sebaliknya —
  tidak dapat terjadi. Penarikan otomatis butir tetap sesudahnya, tidak
  berubah.
- Perkakas: `status --pengganti "<rujukan>"` opsional; ditolak bersama
  `berlaku`, ditolak bila berdata pribadi berpola, tanpa mengutipnya.

## 4. K-3 · Pembaca sumber (D-14 Bagian 4.10 baru)

`GET /api/v1/sumber/{id}?bagian=<penanda bagian>` — `{id}` adalah
`sitasi[].id_dokumen`, `bagian` adalah `sitasi[].bagian` dari tanggapan
`/tanya`. Bentuk `/tanya` tidak berubah (R-09, C-20).

```json
{
  "id_dokumen": "doc_…",
  "judul": "…", "jenis": "regulasi_resmi", "penerbit": "…", "tahun": 2026,
  "status_keberlakuan": "berlaku | diubah | dicabut | null",
  "rujukan_pengganti": "… | null",
  "bagian": "Pasal 7 ayat (2)",
  "teks_bagian": ["…"],
  "tanpa_teks": "dokumen_tidak_publik | status_belum_tercatat | dokumen_dicabut | bagian_tidak_tersedia | null"
}
```

Aturan, diperiksa berurutan; yang pertama berlaku menetapkan `tanpa_teks` dan
`teks_bagian` kosong:

| Urutan | Keadaan | `tanpa_teks` |
|---|---|---|
| — | Tidak ada di `korpus.dokumen_sumber`, atau tanpa catatan metadata | **404 `SUMBER_TIDAK_ADA`** — satu bentuk bagi karantina, tidak dikenal, dan ditarik (R-04) |
| 1 | `tingkat_kerahasiaan` bukan `publik`, **atau** `jenis` `dokumen_sekolah` pada tingkat mana pun | `dokumen_tidak_publik` (P-2 A; ET-04 milik tim etik) |
| 2 | `jenis` `regulasi_resmi` tanpa catatan status | `status_belum_tercatat` (TK-81 A) |
| 3 | Status terbaru `dicabut`, jenis apa pun | `dokumen_dicabut` (R-07, C-07) |
| 4 | Tidak ada segmen `indeks_utama` dengan `penanda_bagian` sama persis, `lisensi` terbuka, dan `anonimisasi_terverifikasi` | `bagian_tidak_tersedia` (R-06, R-04) |

- Segmen yang tidak terverifikasi disaring satu per satu, bukan menggugurkan
  dokumen. Urutannya `id_segmen` — korpus tidak menyimpan urutan lain.
- `jenis` di sini `JenisSumber` (asal dokumen, D-13 Bagian 6), **bukan**
  `jenis_sumber` butir: namanya dibedakan agar dua daftar tidak terbaca
  satu (uji audit 6 D-00).
- Tanggapan tidak membawa tautan: korpus tidak menyimpannya. S-10 menampilkan
  `sitasi[].tautan` yang sudah dipegangnya dari S-09.
- `bagian` wajib, tidak kosong; selainnya 400 `VALIDASI_GAGAL`. Ia tidak
  disimpan dan tidak masuk telemetri.
- **Mengapa `dicabut` tanpa teks**, padahal R-07 hanya menuntut penandanya:
  teks regulasi yang tidak berlaku, dibuka dari jawaban, terbaca sebagai dasar
  jawaban itu. C-07 melarang menjawab berdasarkannya; menayangkan teksnya
  sebagai dasar rujukan adalah jalan memutar ke tempat yang sama. `diubah`
  tetap berteks, dengan status dan rujukan pengganti **sebelum** teks (R-07,
  FR-F14).

## 5. K-4 · Koleksi (D-14 Bagian 3.3 + dua baris; 4.10)

| Rute | Permintaan | Tanggapan |
|---|---|---|
| `POST /butir/{id}/simpan` | `{"catatan": "…"}`; `catatan` boleh tidak ada, kosong, atau `null` | 200 satu butir koleksi |
| `DELETE /butir/{id}/simpan` | — | 204 tanpa badan |
| `GET /koleksi?kategori=K5&jenis_sumber=regulasi` | kedua penyaring opsional, satu nilai | 200 `{"koleksi": [ … ]}`, terbaru disimpan lebih dulu |

Satu butir koleksi = bentuk butir lengkap D-14 Bagian 4.6, ditambah:

```json
{ "catatan": "… | null", "disimpan_pada": "2026-10-09T03:00:00Z", "dasar_berubah": false }
```

- **Simpan** hanya bagi butir yang pernah tayang bagi pemanggil dan masih sah
  — pemeriksaan `detail()` fitur 013 apa adanya, lewat penyimpan penemuan
  (R-01). Selainnya 404 dengan bentuk detail butir. Menyimpan ulang mengganti
  catatan dan waktunya.
- **Keluarkan** hanya butir pada koleksi pemanggil; selainnya 404
  `SUMBER_TIDAK_ADA`. Butir yang sudah ditarik tetap dapat dikeluarkan.
- **Daftar** membaca butir tayang lewat penyimpan penemuan, bukan lewat hak
  `peran_koleksi`. Butir yang ditarik, atau yang status regulasinya `diubah`
  atau `dicabut`, **tetap tampil** dengan `dasar_berubah: true` (P-4 A, D-06
  Bagian 7.5). Baris yang isinya tidak lagi memenuhi model dilewati dan dicatat
  tanpa isi (pola TK-78).
- `catatan` berdata pribadi berpola 400 tanpa mengutip; isinya tidak sampai ke
  log (R-02, KM-03).
- Penyaring yang bukan nilai `KategoriMasalah` atau `JenisSumberButir` 400.
- Koleksi **tidak dibaca** pemilihan beranda maupun jalur penjawab (R-03):
  ditegakkan hak peladen pada Bagian 2, bukan kedisiplinan.

## 6. K-5 · Telemetri dan analitik

Lewat gerbang perekaman fitur 034 (C-04), `versi_model` `tanpa_model`:

| Peristiwa | Kapan | Properti |
|---|---|---|
| `citation_opened` | `GET /sumber/{id}` menjawab 200, termasuk tanpa teks | `{"id_sumber": "<id_dokumen>", "jenis_sumber": "<JenisSumber>"}` |
| `discovery_saved` | `POST /butir/{id}/simpan` menjawab 200 | `{"ada_catatan": true}` — tanpa teks catatan |

Penolakan tidak direkam. Properti persis D-01 Bagian 9, tanpa tambahan (P-3
A); nama kuncinya ditulis pada D-14 Bagian 4.10, dan D-01 tidak berubah.

Analitik fitur 035 memperoleh bagian
`"penelusuran_sumber": {"jawaban": n, "dibuka": n, "rasio": r}` —
`citation_opened` / `answer_served` atas peristiwa pilot (D-01 Bagian 9.1).
`rasio` `null` tanpa penyebut. `MetrikTertunda.RASIO_PENELUSURAN_SUMBER`
keluar dari daftar (P-3 A). TK-73 menyempit — `citation_opened` kini teramati
di peladen — tetapi tetap terbuka bagi peristiwa peramban lainnya.

## 7. K-6 · Penarikan data

`TABEL_DATA_PENGGUNA` bertambah satu (15 → 16): `penemuan.koleksi`, dihapus
menurut pseudonim dalam pernyataan `_HAPUS` yang sama. Catatan korpus tidak
tersentuh: ia bukan data peserta.

## 8. K-7 · Layar

**S-06 blok 8.** "Simpan" tampil di samping "Belum relevan". Mengetuknya
membuka isian catatan opsional berpetunjuk "Tanpa nama atau nomor pribadi" dan
tombol "Simpan ke koleksi". Sesudahnya: "Tersimpan di Koleksi saya." Luring
tidak diantrekan: "Belum tersimpan. Periksa sambungan, lalu simpan lagi."

**S-09 blok 5.** Setiap baris sitasi menjadi tombol yang membuka S-10 dengan
dokumen dan bagiannya (PK-03 "selalu dapat diketuk").

**S-10.** Urutan tetap: judul, jenis, penerbit, tahun, bagian → **status
keberlakuan dan rujukan pengganti** → teks bagian, atau keterangan mengapa
teks tidak tampil → tautan luar dari sitasi bila ada → "Kembali ke jawaban".
`dicabut`: "Dokumen ini sudah dicabut dan tidak berlaku." Keadaan memuat,
galat, luring, dan tidak-ditemukan.

**S-11.** Dua penyaring (kategori, jenis sumber), daftar butir tersimpan
terbaru lebih dulu: penanda "Dasar rujukan butir ini telah berubah"
**sebelum** isi bila `dasar_berubah`, judul, catatan, inti temuan, implikasi,
sumber, dan "Keluarkan dari koleksi". KL-B: belum ada butir tersimpan; KL-B
tersaring: tidak ada butir pada pilihan itu.

**Navigasi (R-10).** Navigasi bawah memperoleh tujuan ketiga, "Milik saya",
yang membuka S-11 saja. Komitmen dan jurnal tidak tampil sampai baris 031.

**S-14** menyebut koleksi dan catatannya pada daftar data yang ditarik.
**S-18** memperoleh baris penelusuran sumber.

## 9. Keputusan rancangan Gerbang 2

| Kode | Pertanyaan | Putusan |
|---|---|---|
| K-1 | Tabel dan peran | Bagian 2 — pembaca tanpa `isi`, karantina, `indeks_metadata`; penayang tanpa koleksi |
| K-2 | Atomik | Bagian 3 — metadata bersama pemindahan, status bersama salinan kurasi |
| K-3 | Pembaca sumber | Bagian 4 — empat alasan tanpa teks; `dicabut` tanpa teks |
| K-4 | Koleksi | Bagian 5 — kelayakan lewat penayang; butir ditarik tetap terbaca |
| K-5 | Telemetri dan analitik | Bagian 6 |
| K-6 | Penarikan | Bagian 7 |
| K-7 | Layar | Bagian 8 |
| K-8 | Batas sentuhan ingesti | Bagian 1 — `setujui()` saja; aturan gerbang tidak berubah |

## 10. Uji

### 10.1 Di dalam `make check`

- Peladen: katalog hak persis bagi kelima peran; penolakan berpenyebab
  `permission denied` — pembaca sumber atas `isi`, karantina, `indeks_metadata`,
  kolom vektor, dan tulis; penayang atas koleksi; pengisi antrean membaca
  korpus; batasan ketiga tabel sesuai enumnya
- Pemindahan atas tiruan **dan** PostgreSQL: metadata tercatat bersama
  pemindahan; metadata yang ditolak membatalkan pemindahan; penarikan tidak
  mencatatnya. Gerbang ingesti menyerahkan metadata `Dokumen` apa adanya
- Status atas memori **dan** PostgreSQL: catatan korpus bersama salinan;
  `--pengganti` ditolak bersama `berlaku` dan bila berdata pribadi
- Pembaca atas memori **dan** PostgreSQL: keempat alasan tanpa teks, urutannya,
  404 satu bentuk; segmen tidak terverifikasi tersaring
- Koleksi atas memori **dan** PostgreSQL; lewat HTTP: 401/403/404/400, simpan
  ulang, keluarkan, penyaring, butir ditarik tetap tampil berpenanda
- Telemetri: properti tepat; tanpa persetujuan tidak direkam; penolakan tidak
  direkam
- Analitik: rasio penelusuran; pengembangan terpisah
- Penarikan: koleksi terhapus; catatan korpus tidak tersentuh
- Layar: S-06 Simpan, S-09 sitasi dapat diketuk, S-10 urutan status sebelum
  teks dan keempat alasan, S-11 penanda sebelum isi, navigasi, luring

### 10.2 Di luar `make check`

Playwright terhadap `make jalan`: pengguna menyimpan butir dari S-06 dengan
catatan, membuka "Milik saya", menyaring, lalu mengeluarkannya; butir yang
ditarik perkakas kurasi tetap tampil berpenanda; pembaca sumber dibuka dari
baris sitasi bagi dokumen publik berteks dan dokumen tanpa status; peneliti
melihat rasio penelusuran. Jalur penjawab `make jalan` belum dirakit, sehingga
baris sitasi pada bukti berasal dari jawaban buatan naskah bukti — dinyatakan
pada keluarannya, bukan disamarkan.

### 10.3 Uji mutasi

| Kode | Mutasi | Uji yang wajib merah |
|---|---|---|
| M-1 | `GRANT SELECT (isi)` atas `korpus.dokumen_sumber` kepada `peran_pembaca_sumber` | katalog hak |
| M-2 | `GRANT USAGE` atas `indeks_metadata` kepada `peran_pembaca_sumber` | penolakan peladen |
| M-3 | `GRANT SELECT` atas `penemuan.koleksi` kepada `peran_penayangan` | katalog hak (R-03) |
| M-4 | Metadata disisipkan dalam pernyataan terpisah dari pemindahan | atomik pemindahan |
| M-5 | Perintah status tidak mencatat ke korpus | status atas PostgreSQL |
| M-6 | Syarat `dokumen_sekolah` dihapus — hanya tingkat yang diperiksa | pembaca |
| M-7 | Regulasi tanpa status berteks | pembaca |
| M-8 | `dicabut` berteks | pembaca |
| M-9 | Segmen tidak terverifikasi tidak disaring | pembaca |
| M-10 | Simpan tanpa pemeriksaan pernah tayang | 404 koleksi |
| M-11 | Catatan tanpa pendeteksi FR-B04 | 400 koleksi |
| M-12 | `discovery_saved` membawa teks catatan | telemetri |
| M-13 | Penarikan melewatkan `penemuan.koleksi` | penarikan |
| M-14 | Butir ditarik dikeluarkan dari daftar koleksi | koleksi (P-4 A) |
| M-15 | `RASIO_PENELUSURAN_SUMBER` tetap pada belum terukur | analitik |
| M-16 | S-10 menampilkan status sesudah teks | uji layar |
| M-17 | S-11 tanpa penanda dasar berubah | uji layar |

## 11. Urutan tugas

| Tugas | Isi |
|---|---|
| T-1 | Kontrak: D-14 3.3, 4.8, 4.10, 5.1; D-04 7.2, 7.4; D-05 3.1, S-06, S-09, S-10, S-11; D-12; D-00; peta rute peran |
| T-2 | Peladen: `14-sumber-dan-koleksi.sql`, dua peran; M-1, M-2, M-3 |
| T-3 | Metadata dan status dicatat: penyimpanan, `setujui()`, perkakas `status`; M-4, M-5 |
| T-4 | Pembaca sumber: penyimpan, aturan, rute, `citation_opened`; M-6 s.d. M-9 |
| T-5 | Koleksi: penyimpan, aturan, tiga rute, `discovery_saved`; M-10, M-11, M-12, M-14 |
| T-6 | Penarikan dan analitik; M-13, M-15 |
| T-7 | Layar S-06, S-09, S-10, S-11, navigasi, S-14, S-18; M-16, M-17 |
| T-8 | Titik jalan, bukti Playwright, penutupan: L8, HKI, L4 |

## 12. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Rute selain keempatnya tampak perlu | Berhenti; AG-02 |
| Bidang `/tanya` tampak perlu — misalnya tautan pembaca pada sitasi | Berhenti; C-20 |
| Teks dokumen sekolah tampak perlu tampil | Berhenti; ET-04 milik tim etik |
| Koleksi tampak perlu memengaruhi beranda atau jawaban | Berhenti; C-14 |
| Aturan gerbang ingesti tampak perlu berubah selain penyerahan metadata | Berhenti; K-8, fitur 002 lolos Gerbang 4 |
| Pembaca tampak perlu teks dokumen utuh | Berhenti; P-2 B ditolak |
