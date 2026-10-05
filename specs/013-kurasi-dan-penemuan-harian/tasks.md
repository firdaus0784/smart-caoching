# Tasks: 013-kurasi-dan-penemuan-harian

| | |
|---|---|
| Spec | Gerbang 1 lolos 5 Oktober 2026 (KB-178); P-1 s.d. P-7 sesuai anjuran |
| Plan | Gerbang 2 lolos 5 Oktober 2026 atas pendelegasian KB-168 (KB-179); K-1 s.d. K-8 sesuai anjuran |
| Status | **Lolos Gerbang 2–3** atas pendelegasian KB-168 (KB-179). Tujuh dari sembilan tugas selesai; Gerbang 4 menunggu pemegang gerbang |
| Kebutuhan | R-01 s.d. R-13; FR-G01 s.d. G05, G07, G08; FR-I01 s.d. I03, I05 s.d. I07; C-02, C-03, C-05, C-06, C-07, C-13, C-14, C-15, C-20 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sesudah entri L4 ditulis, tepat sebelum
commit. **`src/rag/`, `src/llm/`, dan `src/telemetri/` tidak berubah.**
Agen **tidak** mengisi antrean dengan butir karangan di luar uji dan bukti.

---

## T-1 · Kontrak lebih dulu

**Kebutuhan:** R-01; K-5, K-6.

- [x] D-14 Bagian 4.6: bentuk tiga rute penemuan — keadaan beranda, ringkas,
      lengkap, penolakan; syarat `application/json` pada `tolak`
- [x] D-14 Bagian 4.7: bentuk tiga rute kurasi — antrean dua daftar, empat
      badan putusan, badan penarikan
- [x] D-14 Bagian 5.1: `kandidat`, `butir_tayang`, `putusan`, `penarikan`,
      `tayang_harian`, `belum_relevan`
- [x] D-04 Bagian 7.3: `jejak_kurasi.id_kurator` diselaraskan menjadi
      `peran, pseudonim_kurator`; tabel penarikan
- [x] D-05: blok S-05, S-15, S-16; navigasi dua tujuan (K-7)
- [x] Register D-00

## T-2 · Peladen menegakkan hak kurasi dan penayangan

**Kebutuhan:** R-02, R-03; K-1.

- [x] Uji lebih dulu: tiap baris "yang ditolak" plan Bagian 2.2 dengan sebab
      `permission denied`; ketiga peran tanpa `CONNECT` basis data pseudonim,
      tanpa karantina dan korpus, tanpa `DELETE`
- [x] Uji peran **berjalan** pada haknya; himpunan hak dari katalog
- [x] `01-peran-dan-basis-data.sql` tiga peran; `09-kurasi.sql`
- [x] Mutasi M-2, M-3, M-4

## T-3 · Penyimpan kurasi dan penemuan

**Kebutuhan:** R-02, R-05, R-07; K-2.

- [x] Uji lebih dulu atas memori **dan** PostgreSQL tersambung sebagai perannya
- [x] `src/penyimpanan/kurasi.py`: kandidat menunggu (tunda WIB), putusan dan
      butir tayang satu transaksi, penarikan, status salinan
- [x] `src/penyimpanan/penemuan.py`: butir hari ini tercatat, satu butir tayang
      sekali, belum relevan
- [x] Permukaan tanpa ubah dan hapus
- [x] Mutasi M-6, M-7, M-13 sisi penyimpan

## T-4 · Perkakas tim

**Kebutuhan:** R-04; K-3, K-4; FR-I07.

- [x] Uji lebih dulu: `isi` menolak berkas yang tidak lolos `ButirPengetahuan`
      dan L1–L3; `status dicabut` memperbarui kandidat dan menarik butir tayang
- [x] `perkakas/kurasi.py` tersambung sebagai `peran_pengisi_antrean`
- [x] Mutasi M-5 sisi perkakas

## T-5 · Rute kurasi

**Kebutuhan:** R-04, R-09, R-10; K-5, K-6.

- [x] Uji lebih dulu lewat `TestClient` dengan `PenentuSesi`
- [x] `src/api/kurasi.py`, pemasangan di `aplikasi.py`, `POLA_*`
- [x] Mutasi M-5, M-10, M-11

## T-6 · Rute penemuan

**Kebutuhan:** R-02, R-05 s.d. R-08; K-2.

- [x] Uji lebih dulu, termasuk C-06 ujung ke ujung dan C-14
- [x] `src/api/penemuan.py`, pemasangan di `aplikasi.py`, `POLA_*`
- [x] Mutasi M-1, M-8, M-9, M-12, M-13

## T-7 · Layar S-05 dan S-06

**Kebutuhan:** R-06, R-11, R-12, R-13; K-7; P-7.

- [x] Vitest lebih dulu: tujuh keadaan, label D-03, tanpa teks penuh bagi
      lisensi tertutup, salinan luring, navigasi
- [x] `web/src/penemuan/`, klien, kontrak, mikrokopi

## T-8 · Layar S-15, S-16, cangkang kurator

**Kebutuhan:** R-09, R-11, R-12; K-8.

- [ ] Vitest lebih dulu: cangkang 403 → 200, empat putusan setara, label TL
      tanpa singkatan, penarikan
- [ ] `web/src/kurasi/`, klien, kontrak, mikrokopi

## T-9 · Putaran mutasi, bukti, penutupan

- [ ] Tiga belas mutasi dijalankan dan dilaporkan apa adanya
- [ ] Playwright Bagian 10.2 plan; tangkapan layar ke `bukti/`
- [ ] D-00, L8, dokumen HKI, L4; status menunggu Gerbang 4
