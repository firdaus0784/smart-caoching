# Tasks: 037-perkakas-ingesti

| | |
|---|---|
| Spec | Gerbang 1 lolos 9 Oktober 2026 (KB-255); TK-84 A (KB-255), TK-85 A (KB-256) |
| Plan | Gerbang 2 lolos 10 Oktober 2026 atas pendelegasian KB-168 (KB-256); K-1 s.d. K-6 |
| Status | **Gerbang 4 lolos** — 10 Oktober 2026 (KB-264). Tujuh dari tujuh tugas selesai |
| Kebutuhan | R-01 s.d. R-11; FR-B01, FR-B04, FR-B05, FR-B06, FR-B07, FR-B08; C-02, C-03, C-05, C-17, C-20 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sesudah entri L4 ditulis, tepat sebelum
commit. **`src/api/`, `src/rag/`, `src/llm/`, `src/pengguna/`,
`src/telemetri/`, dan `web/` tidak berubah.** Tanpa rute baru dan tanpa paket
baru (C-12, C-20). Uji fitur 002 lulus tanpa diubah (R-02).

---

## T-1 · Kontrak lebih dulu

**Kebutuhan:** R-06, R-10; K-1, K-5; P-1 A, P-6 A.

- [x] D-14 Bagian 5.1: `penerimaan`, `temuan_pola`, `tinjauan_temuan`,
      `jejak_area` (`nomor_penerimaan`, `putusan`); bidang `dokumen_sumber`
      yang diturunkan; kamus enum `PutusanGerbang`
- [x] D-04 Bagian 7.2 dan KA-04: catatan karantina dan ketiga peran dokumen
- [x] `src/kamus/`: `PutusanGerbang`, dengan uji nilai terhadap D-14
- [x] Register D-00

## T-2 · Peladen

**Kebutuhan:** R-04, R-05; K-1; P-2 A.

- [x] Uji lebih dulu: katalog hak persis ketiga peran dokumen di seluruh
      skema; penolakan berpenyebab; peran aplikasi lain tanpa karantina;
      batasan pola pelaku dan `putusan` dibandingkan dengan enumnya
- [x] `01-peran-dan-basis-data.sql` + dua peran; `15-ingesti.sql`; hak bawaan
      karantina bagi verifikator dicabut; `tests/peladen.py` dan README
- [x] Mutasi M-1, M-2, M-3, M-4, M-11

## T-3 · Penyamaran FR-B04

**Kebutuhan:** R-07; K-2; P-5 A.

- [x] Uji lebih dulu: keenam jenis, bertindih, berurutan, nol temuan, indeks
      karakter, jumlah tanpa nilai
- [x] `src/nlp/anonimisasi/samaran.py`
- [x] Mutasi M-8 sisi penyamar

## T-4 · Catatan gerbang

**Kebutuhan:** R-03, R-06, R-09; K-1, K-3; P-1 A, P-3 A.

- [x] Uji kontrak lebih dulu atas memori **dan** PostgreSQL, tiap perintah
      dengan perannya: keadaan diturunkan; tinjauan hanya bagi penerimaan
      terbaru; pemindahan, metadata, dan jejak bersama atau tidak sama sekali;
      keluar dari korpus menghapus segmen kedua indeks
- [x] `src/penyimpanan/karantina.py`; `dasar.py`, `tiruan.py`, `postgres.py`
      (`pindahkan(..., jejak=)`)
- [x] Mutasi M-5, M-6, M-12

## T-5 · Gerbang memakai catatan

**Kebutuhan:** R-01, R-02, R-03, R-11; K-2, K-3, K-6; TK-85 A.

- [x] Uji lebih dulu: keadaan bertahan antarobjek `Gerbang` atas PostgreSQL;
      penyamaran sebelum pemeriksa pola; unggahan ulang atas dokumen korpus
      ditolak pada kedua pelaksana; seluruh uji fitur 002 tetap lulus
- [x] `src/ingest/gerbang.py`, `src/ingest/jejak.py`
- [x] Mutasi M-7, M-8, M-9, M-10

## T-6 · Perkakas ingesti

**Kebutuhan:** R-04, R-07, R-08; K-4; P-6 A.

- [x] Uji lebih dulu: tiap perintah memakai perannya; pelaku tidak berpola
      ditolak sebelum menyambung; `daftar` tanpa teks; `baca` ke keluaran baku
      saja dengan pernyataan BT-70; galat tanpa kutipan; tanpa log
- [x] `perkakas/ingesti.py`
- [x] Mutasi M-13

## T-7 · Bukti, penutupan

- [x] Perkakas terhadap PostgreSQL, Bagian 8.2 plan; keluaran ke `bukti/`
- [x] Putaran mutasi dilaporkan apa adanya; L8, dokumen HKI, L4; status
      menunggu Gerbang 4
