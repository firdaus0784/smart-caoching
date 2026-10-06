# Tasks: 034-penyimpanan-dan-penyambungan-telemetri

| | |
|---|---|
| Spec | Gerbang 1 lolos 6 Oktober 2026 (KB-192); P-1 s.d. P-6 sesuai anjuran |
| Plan | Gerbang 2 lolos 6 Oktober 2026 atas pendelegasian KB-168 (KB-193); K-1 s.d. K-6 |
| Status | **Gerbang 4 lolos** — 6 Oktober 2026 (KB-202). Tujuh dari tujuh tugas selesai |
| Kebutuhan | R-01 s.d. R-10; FR-J01, FR-J02, FR-J05, FR-A05; C-04, C-05, C-09, C-14 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sesudah entri L4 ditulis, tepat sebelum
commit. **`src/telemetri/`, `src/rag/`, `src/llm/`, dan `web/` tidak berubah** — kecuali
T-7: satu tajuk pada pengambilan latar beranda (K-7, KB-199).
Agen **tidak** menulis naskah persetujuan (ET-02).

---

## T-1 · Kontrak lebih dulu

**Kebutuhan:** R-04, R-05; K-1.

- [x] D-14 Bagian 5.1: tabel `peristiwa` — tambah-saja, pseudonim, `tanpa_model`;
      catatan bahwa peristiwa direkam di rute yang ada (TK-73)
- [x] AGENTS.md: tepi `api → telemetri` satu jurusan beserta alasannya;
      pemeriksa arah tetap lulus
- [x] Register D-00

## T-2 · Peladen menegakkan tambah-saja

**Kebutuhan:** R-04, R-05; K-3.

- [x] Uji lebih dulu: penolakan `UPDATE`, `DELETE`, `TRUNCATE`, skema lain,
      basis data pseudonim — sebab `permission denied`; katalog hak persis;
      batasan pola pseudonim dan dua puluh kode
- [x] `01-peran-dan-basis-data.sql` + `peran_telemetri`; `10-telemetri.sql`
- [x] Mutasi M-4, M-5

## T-3 · Penyimpan telemetri

**Kebutuhan:** R-05, R-10; K-3.

- [x] Uji lebih dulu atas memori **dan** PostgreSQL sebagai `peran_telemetri`
- [x] `src/penyimpanan/telemetri.py`: `tambah`, `terakhir`
- [x] `PenyimpanPenemuan.kapan_tayang`

## T-4 · Perekam dan peristiwa sesi

**Kebutuhan:** R-01 s.d. R-04, R-07, R-08; K-2, K-4, K-5.

- [x] Uji lebih dulu lewat `TestClient`: C-04 ujung ke ujung pada masuk dan
      keluar, cabut seketika, galat penyimpan tidak mengubah tanggapan
- [x] `src/api/rekaman.py`; `PenjagaMasuk.pemilik_sesi`; `susun_aplikasi`
- [x] Mutasi M-1, M-2, M-3, M-7, M-8

## T-5 · Peristiwa Tanya dan penemuan

**Kebutuhan:** R-03, R-06, R-08, R-09; K-6.

- [x] Uji lebih dulu: tujuh kode, properti tanpa teks pengguna, tanggapan sama
      dengan dan tanpa persetujuan
- [x] Rute Tanya; `src/api/penemuan.py`
- [x] Mutasi M-6, M-9, M-10

## T-7 · Penanda pengambilan salinan (K-7, KB-199)

Ditambahkan sesudah Gerbang 3 atas putusan pemegang gerbang; dikerjakan
sebelum T-6, karena bukti T-6 yang menemukannya.

**Kebutuhan:** R-03, R-09; FR-J01; TK-74.

- [x] D-14 0.14 Bagian 4.6; D-00 TK-74
- [x] Uji lebih dulu: peladen tidak merekam `discovery_opened` bagi tajuk
      `X-Tujuan: salinan`, tanggapan sama; layar beranda mengirimnya, S-06 tidak
- [x] `src/api/aplikasi.py`; `web/src/klien.ts`, `LayarBeranda.tsx`
- [x] Mutasi M-11, M-12, M-13

## T-6 · Titik jalan, bukti, penutupan

- [x] `perkakas/jalankan_lokal.py`: penyimpan telemetri sebagai `peran_telemetri`
- [x] Playwright Bagian 9.2 plan; keluaran ke `bukti/`
- [x] Putaran mutasi dilaporkan apa adanya; L8, dokumen HKI, L4; status
      menunggu Gerbang 4
