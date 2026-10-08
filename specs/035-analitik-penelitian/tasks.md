# Tasks: 035-analitik-penelitian

| | |
|---|---|
| Spec | Gerbang 1 lolos 6 Oktober 2026 (KB-215); P-1 s.d. P-5 sesuai anjuran |
| Plan | Gerbang 2 lolos 6 Oktober 2026 atas pendelegasian KB-168 (KB-216); K-1 s.d. K-5 |
| Status | **Gerbang 4 lolos** — 8 Oktober 2026 (KB-224). Tujuh dari tujuh tugas selesai |
| Kebutuhan | R-01 s.d. R-08; FR-J03, FR-J04; C-04, C-05, C-09, C-12, C-14, C-17, C-20 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sesudah entri L4 ditulis, tepat sebelum
commit. **`src/rag/`, `src/llm/`, `src/ingest/`, dan `src/pengguna/` tidak
berubah.** Tanpa paket baru (C-12).

---

## T-1 · Kontrak lebih dulu

**Kebutuhan:** R-01, R-06, R-08; K-3.

- [x] D-14 Bagian 4.8: bentuk `GET /analitik/ringkas` dan `POST /analitik/ekspor`
- [x] D-14 Bagian 5.1: tabel `ekspor`; definisi retensi
- [x] Register D-00

## T-2 · Peladen

**Kebutuhan:** R-02; K-1.

- [x] Uji lebih dulu: penolakan `peran_analitik` dengan sebab
      `permission denied`; katalog hak persis; batasan tabel ekspor
- [x] `01-peran-dan-basis-data.sql` + `peran_analitik`; `12-analitik.sql`
- [x] Mutasi M-1

## T-3 · Penyimpan analitik

**Kebutuhan:** R-02, R-05, R-06; K-1.

- [x] Uji lebih dulu atas memori **dan** PostgreSQL sebagai `peran_analitik`
- [x] `src/penyimpanan/analitik.py`; `ke_csv` atas baris berbidang sama
- [x] Mutasi M-7

## T-4 · Metrik dan rute

**Kebutuhan:** R-01, R-03, R-04, R-05, R-07; K-2, K-3.

- [x] Uji lebih dulu: metrik atas peristiwa buatan yang dihitung tangan;
      lewat HTTP 403, ekspor tercatat, CSV, `pengembangan` terpisah
- [x] `src/api/analitik.py`; rute pada `src/api/aplikasi.py`
- [x] Mutasi M-2, M-3, M-4, M-5, M-6, M-9

## T-5 · Perkakas penarikan menyebut ekspor

**Kebutuhan:** P-4 B; K-4.

- [x] Uji lebih dulu terhadap PostgreSQL: ekspor yang rentangnya memuat
      peristiwa permintaan tertunda disebut, yang lain tidak; tanpa pseudonim
- [x] `PenarikanPostgres.ekspor_terkait`; `perkakas/penarikan.py`
- [x] Mutasi M-8

## T-6 · S-18 Analitik

**Kebutuhan:** R-04, R-05; K-5; C-13.

- [x] Uji lebih dulu: peneliti dikenali, tabel, `null` bukan nol, belum
      terukur bersebab, unduhan CSV, galat dan luring
- [x] `web/src/analitik/`; cangkang; mikrokopi
- [x] Mutasi M-10

## T-7 · Titik jalan, bukti, penutupan

- [x] `perkakas/jalankan_lokal.py`: penyimpan analitik sebagai `peran_analitik`
- [x] Playwright Bagian 8.2 plan; keluaran ke `bukti/`
- [x] Putaran mutasi dilaporkan apa adanya; L8, dokumen HKI, L4; status
      menunggu Gerbang 4
