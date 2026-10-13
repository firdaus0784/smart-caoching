# Tasks: 039-jalur-penjawab-postgresql

| | |
|---|---|
| Spec | Gerbang 1 lolos 13 Oktober 2026 (KB-278); P-1 s.d. P-6 sesuai anjuran |
| Plan | Gerbang 2 lolos 13 Oktober 2026 atas pendelegasian KB-168 (KB-279); K-1 s.d. K-8; perubahan fitur 021 atas putusan pemegang gerbang |
| Status | **Gerbang 3 lolos** — 13 Oktober 2026 atas pendelegasian KB-168 (KB-279). Tujuh dari delapan tugas selesai |
| Kebutuhan | R-01 s.d. R-08; FR-F02, FR-F03, FR-F11, FR-F14, FR-D06; KL-01, KL-04, KL-07; C-02, C-07, C-16, C-17, C-19, C-20 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sesudah entri L4 ditulis, tepat sebelum
commit. **`src/rag/`, `src/llm/`, `src/pengguna/`, `src/telemetri/`, `web/`,
dan `perkakas/jalankan_lokal.py` tidak berubah.** Tanpa rute baru dan tanpa
paket baru (C-12, C-20). Ambang, penyemat, dan model sungguhan tidak dibuat di
mana pun (C-16, ADR-12).

---

## T-1 · Kontrak lebih dulu

**Kebutuhan:** R-05; K-8; P-3 A, P-5 A, P-6 A.

- [x] D-14 Bagian 5.1: `tautan` pada penerimaan, catatan metadata, dan
      `dokumen_sumber`; keberlakuan dokumen bukan regulasi pada bahan
- [x] D-14 Bagian 4.1: aturan `sitasi` dan `bacaan_lanjutan`; Bagian 4.10:
      alasan tautan tidak dikirim
- [x] D-04 Bagian 7.2; D-06 aturan pelaksanaan KL-01: daftar lisensi terbuka
- [x] Register D-00

## T-2 · Peladen

**Kebutuhan:** R-01, R-04; K-1; P-5 A.

- [x] Uji lebih dulu: kolom dan batasan tautan; katalog hak tidak bertambah;
      kueri pemuat berjalan sebagai `peran_pemanggil_llm` dan
      `peran_penjawaban`; penolakan berpenyebab bagi pemanggil model atas
      indeks metadata
- [x] `17-tautan-sumber.sql`; `tests/peladen.py` dan README
- [x] Mutasi M-12

## T-3 · Lisensi dinormalisasi

**Kebutuhan:** R-01; K-2; P-6 A, TK-87.

- [x] Uji lebih dulu: kedua arah TK-87, normalisasi, daftar persis; uji fitur
      006 yang menyatakan varian terbuka disesuaikan
- [x] `src/penyimpanan/indeks.py`
- [x] Mutasi M-7

## T-4 · Tautan dicatat

**Kebutuhan:** K-3; P-5 A, KL-04.

- [x] Uji lebih dulu atas catatan gerbang (memori dan PostgreSQL), gerbang,
      dan perkakas
- [x] `Dokumen`, `CatatanPenerimaan`, `MetadataDokumen`; gerbang, catatan,
      pemindahan; `terima --tautan`
- [x] Mutasi M-11

## T-5 · Pemuat korpus

**Kebutuhan:** R-01, R-04, R-06; K-4.

- [x] Uji kontrak lebih dulu atas memori **dan** PostgreSQL sebagai peran
      sungguhan: hanya korpus; catatan terbaru; sidik deterministik dan
      berubah bersama isi, metadata, status; kredensial ditolak sebelum menyentuh
- [x] `src/penyimpanan/korpus_penjawab.py`
- [x] Mutasi M-1, M-2, M-9

## T-6 · Muatan dan penjawab korpus

**Kebutuhan:** R-01 s.d. R-08; K-5, K-6; P-2 A, P-3 A, P-4 A.

- [x] Uji lebih dulu: keenam alasan kelayakan berurutan; bahan, sitasi, dan
      bacaan lanjutan; sitasi dari klaim pada `Jalur`; `PenjawabKorpus` atas
      PostgreSQL — data ke model, versi indeks, muatan diganti saat sidik
      berubah; uji fitur 021 tetap lulus
- [x] `src/api/sumber.py` (fungsi bersama), `src/api/tanya.py`,
      `src/api/penjawab_korpus.py`
- [x] Mutasi M-3, M-4, M-5, M-6, M-8

## T-7 · Perkakas pencarian

**Kebutuhan:** R-08; K-7; P-1 A.

- [x] Uji lebih dulu: peran per indeks; satu sumber; keluaran tanpa teks;
      tanpa log; dokumen yang perlu diindeks ulang
- [x] `perkakas/pengambilan.py`
- [x] Mutasi M-10

## T-8 · Bukti, penutupan

- [ ] Bagian 11.2 plan; keluaran ke `bukti/`
- [ ] Putaran mutasi dilaporkan apa adanya; L8, dokumen HKI, L4; status
      menunggu Gerbang 4
