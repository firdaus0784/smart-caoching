# Tasks: 036-penilaian-jawaban-dan-aduan

| | |
|---|---|
| Spec | Gerbang 1 lolos 8 Oktober 2026 (KB-227, KB-228) |
| Plan | Gerbang 2 lolos 8 Oktober 2026 atas pendelegasian KB-168 (KB-229); K-1 s.d. K-6 |
| Status | **Gerbang 3 lolos** — 8 Oktober 2026 atas pendelegasian KB-168 (KB-229). Empat dari delapan tugas selesai |
| Kebutuhan | R-01 s.d. R-10; FR-F07, FR-I04, NFR-09; C-04, C-05, C-06, C-07, C-13, C-14, C-16, C-17, C-20 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sesudah entri L4 ditulis, tepat sebelum
commit. **`src/rag/`, `src/llm/`, `src/ingest/`, dan `src/pengguna/` tidak
berubah.** Tanpa paket baru (C-12). Satu rute baru saja — yang disetujui P-3 B.

---

## T-1 · Kontrak lebih dulu

**Kebutuhan:** R-02, R-06, R-08; K-3, K-4; P-1 A, P-3 B, P-4 B.

- [x] D-14 Bagian 3.4: baris `POST /api/v1/kurasi/aduan/{id}/tindak-lanjut`
- [x] D-14 Bagian 4.9: bentuk penilaian, aduan, tindak lanjut; 4.8: bagian
      `penilaian`; 5.1: kelima tabel, `NilaiPenilaian`, `TindakLanjutAduan`
- [x] D-01 Bagian 9: properti `answer_rated`
- [x] D-04 Bagian 7.4: baris `pesan` mengikuti P-1 A (TK-69)
- [x] D-05: S-09 blok "Nilai jawaban", S-17
- [x] Register D-00

## T-2 · Peladen

**Kebutuhan:** R-06, R-07; K-1.

- [x] Uji lebih dulu: katalog hak persis keempat peran; penolakan berpenyebab;
      batasan tabel
- [x] `01-peran-dan-basis-data.sql` + `peran_penilaian`; `13-penilaian.sql`
- [x] Mutasi M-1, M-2

## T-3 · Catatan tanggapan pada `/tanya`

**Kebutuhan:** P-1 A; K-2; C-07, C-17.

- [x] Uji lebih dulu atas memori **dan** PostgreSQL: pesan tercatat bersama
      giliran; tidak tercatat berarti tidak terkirim; rute riwayat tidak
      menayangkannya
- [x] `RiwayatMemori`, `RiwayatPostgres`; `/tanya` menyerahkan tanggapan
- [x] Mutasi M-3

## T-4 · Penyimpan penilaian dan aduan

**Kebutuhan:** R-01, R-02, R-05, R-06; K-1, K-2; P-2 B.

- [x] Uji lebih dulu atas memori **dan** PostgreSQL sebagai `peran_penilaian`
      dan `peran_kurasi`
- [x] `src/kamus/penilaian.py`; `src/penyimpanan/penilaian.py`
- [x] Mutasi M-5, M-6, M-7

## T-5 · Rute dan `answer_rated`

**Kebutuhan:** R-01, R-03, R-04, R-06, R-09; K-3, K-4.

- [ ] Uji lebih dulu lewat HTTP dan atas perekam
- [ ] `src/api/penilaian.py`; tiga rute pada `src/api/aplikasi.py`;
      `rekam_penilaian`
- [ ] Mutasi M-4, M-8, M-9, M-12

## T-6 · Penarikan dan analitik

**Kebutuhan:** R-07; K-4, K-5; P-4 B, KB-228.

- [ ] Uji lebih dulu terhadap PostgreSQL (penarikan) dan atas peristiwa buatan
      (analitik)
- [ ] `TABEL_DATA_PENGGUNA`, `_HAPUS`; `src/api/analitik.py`
- [ ] Mutasi M-10, M-11

## T-7 · Layar S-09, S-17, S-18

**Kebutuhan:** R-10; K-6; C-13.

- [ ] Uji lebih dulu: tiga pilihan, centang hanya pada keliru, tidak-ditemukan,
      penggantian, galat dan luring; S-17 daftar dan tindak lanjut; S-18 tabel
- [ ] `web/src/tanya/`, `web/src/kurasi/`, `web/src/analitik/`; mikrokopi
- [ ] Mutasi M-13

## T-8 · Titik jalan, bukti, penutupan

- [ ] `perkakas/jalankan_lokal.py`: penyimpan penilaian dan aduan berperan
      masing-masing
- [ ] Playwright Bagian 9.2 plan; keluaran ke `bukti/`
- [ ] Putaran mutasi dilaporkan apa adanya; L8, dokumen HKI, L4; status
      menunggu Gerbang 4
