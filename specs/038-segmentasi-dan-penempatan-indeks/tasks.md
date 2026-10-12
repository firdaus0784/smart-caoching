# Tasks: 038-segmentasi-dan-penempatan-indeks

| | |
|---|---|
| Spec | Gerbang 1 lolos 11 Oktober 2026 (KB-266); TK-86 A (KB-266) |
| Plan | Gerbang 2 lolos 12 Oktober 2026 atas pendelegasian KB-168 (KB-267); K-1 s.d. K-6 |
| Status | **Gerbang 3 lolos** — 12 Oktober 2026 atas pendelegasian KB-168 (KB-267). Enam dari tujuh tugas selesai |
| Kebutuhan | R-01 s.d. R-08; FR-D06, FR-F11; C-02, C-03, C-16, C-17, C-19, C-20 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sesudah entri L4 ditulis, tepat sebelum
commit. **`src/api/`, `src/rag/`, `src/llm/`, `src/pengguna/`,
`src/telemetri/`, dan `web/` tidak berubah.** Tanpa rute baru dan tanpa paket
baru (C-12, C-20). Ukuran segmen milik D-07 (C-16).

---

## T-1 · Kontrak lebih dulu

**Kebutuhan:** R-02, R-03, R-08; K-6; P-3 A, P-4 A.

- [x] D-14 Bagian 5.1: lisensi pada penerimaan dan metadata korpus;
      `dokumen_sumber.lisensi`; peringkat dan indeks tujuan segmen sebagai
      bidang turunan; aturan `id_segmen`
- [x] D-04 Bagian 7.2 dan KA-04: `peran_pengindeks`, TK-86
- [x] Register D-00

## T-2 · Peladen

**Kebutuhan:** R-04; K-1; P-2 A; TK-86.

- [x] Uji lebih dulu: katalog `peran_pengindeks` persis; verifikator tanpa
      tulis indeks pada katalog dan hak bawaan; penolakan berpenyebab; tiap
      peran berjalan pada haknya; batasan lisensi
- [x] `01-peran-dan-basis-data.sql` + peran; `16-segmen-dan-lisensi.sql`;
      `tests/peladen.py` dan README
- [x] Mutasi M-1, M-2, M-3

## T-3 · Lisensi dicatat

**Kebutuhan:** R-03; K-4; P-3 A.

- [x] Uji lebih dulu: lisensi ikut penerimaan dan catatan metadata korpus atas
      memori dan PostgreSQL; bawaan kosong; uji fitur 002, 032, 037 tetap lulus
- [x] `Dokumen`, `CatatanPenerimaan`, `MetadataDokumen`; gerbang, catatan,
      pemindahan; `terima --lisensi`
- [x] Mutasi M-10

## T-4 · Pemotongan

**Kebutuhan:** R-01, R-02, R-06; K-2; P-1 A.

- [x] Uji lebih dulu atas teks berpasal dan tanpa pasal
- [x] `src/ingest/segmentasi.py`
- [x] Mutasi M-7, M-8. M-9 pindah ke T-5: pengenal segmen ditetapkan
      pengindeksan, bukan pemotongan (KB-271)

## T-5 · Pengindeksan

**Kebutuhan:** R-03, R-04, R-05; K-3; P-2 A, P-4 A.

- [x] Uji kontrak lebih dulu atas memori **dan** PostgreSQL sebagai
      `peran_pengindeks`: indeks tujuan menurut lisensi; ganti, bukan tambah;
      di luar korpus ditolak; pratinjau tidak menulis
- [x] `PENGINDEKSAN`; `src/penyimpanan/pengindeks.py`; `src/ingest/pengindeksan.py`
- [x] Mutasi M-4, M-5, M-6, M-9

## T-6 · Perkakas `indeks`

**Kebutuhan:** R-07; K-5.

- [x] Uji lebih dulu: peran, pratinjau, keluaran tanpa teks, tanpa log;
      pembaca sumber menampilkan teks bagian dokumen yang diindeks
- [x] `perkakas/ingesti.py`
- [x] Mutasi M-11

## T-7 · Bukti, penutupan

- [ ] Bagian 9.2 plan; keluaran ke `bukti/`
- [ ] Putaran mutasi dilaporkan apa adanya; L8, dokumen HKI, L4; status
      menunggu Gerbang 4
