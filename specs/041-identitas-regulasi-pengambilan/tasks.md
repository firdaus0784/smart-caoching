# Tasks: 041-identitas-regulasi-pengambilan

| | |
|---|---|
| Spec | Gerbang 1 lolos 13 Oktober 2026 (KB-304); P-1 s.d. P-5 sesuai anjuran |
| Plan | Gerbang 2 lolos 13 Oktober 2026 atas pendelegasian KB-168 (KB-305); K-1 s.d. K-4 |
| Status | **Gerbang 3 lolos** — 13 Oktober 2026 atas pendelegasian KB-168 (KB-305). Nol dari empat tugas selesai |
| Kebutuhan | R-01 s.d. R-06; TK-88; FR-F02, FR-F11; ADR-03; D-08 Bagian 6; C-02, C-16, C-18, C-20 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sesudah entri L4 ditulis, tepat sebelum
commit. **`src/penyimpanan/`, `src/llm/`, `src/nlp/`, `src/pengguna/`,
`src/telemetri/`, penyematan, segmentasi, pengindeksan, `web/`, dan
`perkakas/basis_data/` tidak berubah.** Tanpa rute, skema, peran, atau paket
baru (R-06). Tanpa bobot, faktor pengali, maupun ambang (R-03, C-16).

---

## T-1 · Kontrak lebih dulu

**Kebutuhan:** R-02, R-04; K-4; P-1 A, P-3 A.

- [x] D-07 Bagian 3.3: teks pencarian dan penanda versinya
- [x] D-06 K-A: pola judul regulasi beserta contoh diterima dan ditolak
- [x] Register D-00

## T-2 · Teks pencarian dan versi

**Kebutuhan:** R-01, R-03, R-04, R-05; K-1, K-2; P-1 A, P-2 A, P-4 A, P-5 A.

- [x] Uji lebih dulu: aturan dibaca dari D-07; pasal regulasi berjudul serupa
      terbedakan oleh judulnya, dengan uji pembanding tanpa judul; teks
      bahan, sitasi, dan `layak_utama` tidak berubah; indeks metadata; versi
      memuat penanda; uji fitur 039 yang menyatakan bentuk versi disesuaikan
- [x] `src/rag/pengambilan/teks_pencarian.py`, `src/api/penjawab_korpus.py`,
      `perkakas/pengambilan.py`
- [x] Mutasi M-1, M-2, M-3, M-4

## T-3 · Judul regulasi

**Kebutuhan:** R-06; K-3; P-3 A.

- [ ] Uji lebih dulu: contoh D-06; hanya `regulasi_resmi`; `Gerbang.terima`
      menolak sebelum menulis; perkakas berkode 2 tanpa mengutip judul; uji
      fitur 037 dan lainnya yang memakai judul regulasi tanpa pola
      disesuaikan
- [ ] `src/ingest/judul_regulasi.py`, `src/ingest/gerbang.py`
- [ ] Mutasi M-5, M-6, M-7

## T-4 · Bukti, penutupan

- [ ] Bagian 7.2 plan; keluaran ke `bukti/`
- [ ] Putaran mutasi dilaporkan apa adanya; L8, dokumen HKI, L4; status
      menunggu Gerbang 4
