# Tasks: 032-koleksi-dan-pembaca-sumber

| | |
|---|---|
| Spec | Gerbang 1 lolos 9 Oktober 2026 (KB-241); TK-81 A (KB-242), TK-82 A (KB-243) |
| Plan | Gerbang 2 lolos 9 Oktober 2026 atas pendelegasian KB-168 (KB-243); K-1 s.d. K-8 |
| Status | **Gerbang 3 lolos** — 9 Oktober 2026 atas pendelegasian KB-168 (KB-243). Lima dari delapan tugas selesai |
| Kebutuhan | R-01 s.d. R-10; FR-F11, FR-G06, FR-G10, FR-B06, NFR-09; C-02, C-03, C-04, C-05, C-07, C-13, C-14, C-17, C-20 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sesudah entri L4 ditulis, tepat sebelum
commit. **`src/rag/`, `src/llm/`, `src/pengguna/`, dan `src/nlp/` tidak
berubah; `src/ingest/` hanya pada `setujui()`.** Tanpa paket baru (C-12).
Empat rute saja — dua yang sudah ada pada D-14 dan dua yang disetujui P-1 A.

---

## T-1 · Kontrak lebih dulu

**Kebutuhan:** R-09, R-10; K-3 s.d. K-7; P-1 A, P-3 A, TK-81 A, TK-82 A.

- [x] D-14 Bagian 3.3: baris `GET /api/v1/koleksi` dan `DELETE /api/v1/butir/{id}/simpan`
- [x] D-14 Bagian 4.10: bentuk pembaca sumber dan koleksi, termasuk nama kunci
      properti `citation_opened` dan `discovery_saved`; 4.8: bagian
      `penelusuran_sumber`; 5.1: ketiga tabel, letak bidang `dokumen_sumber`
- [x] D-04 Bagian 7.2 dan 7.4: catatan metadata, catatan status, koleksi
- [x] D-05: navigasi "Milik saya"; S-06 blok 8; S-09 blok 5; S-10; S-11
- [x] D-01 Bagian 9 **tidak berubah**: properti apa adanya (P-3 A)
- [x] D-12 baris 032 menyebut TK-81 dan TK-82; register D-00
- [x] Peta rute peran: kedua rute baru

## T-2 · Peladen

**Kebutuhan:** R-03, R-04, R-05, R-06; K-1.

- [x] Uji lebih dulu: katalog hak persis kelima peran; penolakan berpenyebab;
      batasan ketiga tabel dibandingkan dengan enumnya
- [x] `01-peran-dan-basis-data.sql` + dua peran; `14-sumber-dan-koleksi.sql`
- [x] Mutasi M-1, M-2, M-3

## T-3 · Metadata dan status dicatat

**Kebutuhan:** R-04, R-07; K-2, K-8; TK-81 A, TK-82 A.

- [x] Uji lebih dulu atas tiruan **dan** PostgreSQL: metadata bersama
      pemindahan, pembatalan bersama, penarikan tanpa metadata; gerbang
      ingesti menyerahkan metadata; status bersama salinan kurasi; `--pengganti`
- [x] `src/penyimpanan/dasar.py`, `tiruan.py`, `postgres.py`, `kurasi.py`;
      `src/ingest/gerbang.py`; `perkakas/kurasi.py`
- [x] Mutasi M-4, M-5
- [x] TK-83 diajukan: pemindahan sebagai `peran_verifikasi` ditolak peladen (pra-ada, fitur 024)

## T-4 · Pembaca sumber dan `citation_opened`

**Kebutuhan:** R-04 s.d. R-07; K-3, K-5.

- [x] Uji lebih dulu atas memori **dan** PostgreSQL sebagai
      `peran_pembaca_sumber`, lewat HTTP, dan atas perekam
- [x] `src/penyimpanan/sumber.py`; `src/api/sumber.py`; rute; `rekam_sumber_dibuka`
- [x] Mutasi M-6, M-7, M-8, M-9

## T-5 · Koleksi dan `discovery_saved`

**Kebutuhan:** R-01, R-02, R-03; K-4, K-5; P-1 A, P-4 A.

- [x] Uji lebih dulu atas memori **dan** PostgreSQL sebagai `peran_koleksi`,
      lewat HTTP, dan atas perekam
- [x] `src/penyimpanan/koleksi.py`; `src/api/koleksi.py`; tiga rute; `rekam_simpan`
- [x] Mutasi M-10, M-11, M-12, M-14

## T-6 · Penarikan dan analitik

**Kebutuhan:** R-08; K-5, K-6; P-3 A.

- [ ] Uji lebih dulu terhadap PostgreSQL (penarikan) dan atas peristiwa buatan
      (analitik)
- [ ] `TABEL_DATA_PENGGUNA`, `_HAPUS`; `src/api/analitik.py`
- [ ] Mutasi M-13, M-15

## T-7 · Layar S-06, S-09, S-10, S-11, navigasi, S-14, S-18

**Kebutuhan:** R-07, R-08, R-10; K-7; C-13.

- [ ] Uji lebih dulu: Simpan dan catatan; sitasi dapat diketuk; S-10 status
      sebelum teks dan keempat alasan; S-11 penyaring, penanda sebelum isi,
      keluarkan; navigasi; galat dan luring
- [ ] `web/src/sumber/`, `web/src/koleksi/`, `web/src/penemuan/`,
      `web/src/tanya/`, `web/src/Aplikasi.tsx`; mikrokopi
- [ ] Mutasi M-16, M-17

## T-8 · Titik jalan, bukti, penutupan

- [ ] `perkakas/jalankan_lokal.py`: pembaca sumber dan koleksi berperan
      masing-masing
- [ ] Playwright Bagian 10.2 plan; keluaran ke `bukti/`
- [ ] Putaran mutasi dilaporkan apa adanya; L8, dokumen HKI, L4; status
      menunggu Gerbang 4
