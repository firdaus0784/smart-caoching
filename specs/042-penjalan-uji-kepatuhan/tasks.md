# Tasks: 042-penjalan-uji-kepatuhan

| | |
|---|---|
| Spec | Gerbang 1 lolos 14 Oktober 2026 (KB-313); P-1 s.d. P-6 sesuai anjuran |
| Plan | Gerbang 2 lolos 14 Oktober 2026 atas pendelegasian KB-168 (KB-314); K-1 s.d. K-6 |
| Status | **Menunggu Gerbang 4** — 14 Oktober 2026 (KB-320). Enam dari enam tugas selesai |
| Kebutuhan | R-01 s.d. R-07; D-08 Bagian 8; D-13 Bagian 8; D-09 PS-01, PS-14; NFR-21, NFR-22; C-02 s.d. C-06, C-09, C-17, C-18, C-20 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sesudah entri L4 ditulis, tepat sebelum
commit. **`src/`, `web/`, `perkakas/basis_data/`, dan
`perkakas/jalankan_lokal.py` tidak berubah.** Tanpa
rute, peran, hak, atau paket baru (R-07). Uji tidak meninggalkan baris pada
peladen selain akun uji yang dibuatnya sendiri.

---

## T-1 · Kontrak lebih dulu

**Kebutuhan:** R-01 s.d. R-06; K-6.

- [x] D-08 Bagian 8: aturan pelaksanaan penjalan
- [x] D-13 Bagian 8; D-09 Bagian 2.1 dan 4.1; D-10 Bagian 3
- [x] Register D-00

## T-2 · Kerangka

**Kebutuhan:** R-01, R-02, R-05, R-06; K-1, K-5; P-1 A, P-4 A, P-6 A.

- [x] Uji lebih dulu: daftar UK dibaca dari D-08 dan D-13; empat UK belum
      dapat diperiksa beserta sebabnya; keadaan keseluruhan; kode keluar;
      masukan tidak sah; L1 lulus pemeriksa catatan versi; tanpa kuki
- [x] `perkakas/kepatuhan/` — `hasil.py`, `daftar.py`, `__main__.py`
- [x] Mutasi M-3, M-4, M-6, M-7

## T-3 · Pemeriksaan basis data

**Kebutuhan:** R-03, R-04; K-2; P-2 A.

- [x] Uji lebih dulu atas PostgreSQL sebagai peran sungguhan: UK-02, UK-04,
      UK-08, UK-09 lulus; percobaan yang semestinya berhasil dilaporkan
      gagal; sisip yang berhasil tidak meninggalkan baris; sambungan gagal
      dilaporkan gagal
- [x] `perkakas/kepatuhan/basis_data.py`
- [x] Mutasi M-1, M-2

## T-4 · Pemeriksaan dalam proses

**Kebutuhan:** K-3; P-5 A; NFR-22.

- [x] Uji lebih dulu: UK-10, UK-12, UK-13 lulus; pemeriksa atau validator
      yang dilonggarkan dilaporkan gagal
- [x] `perkakas/kepatuhan/proses.py`

## T-5 · Pemeriksaan API

**Kebutuhan:** R-03, R-04, R-05; K-4; P-3 A.

- [x] Uji lebih dulu atas aplikasi bersesi yang berjalan: UK-05, UK-07,
      UK-14, UK-15 lulus; aplikasi tiruan dilaporkan gagal; kewarasan;
      masukan API tidak lengkap; akun berpersetujuan; peran aplikasi
      tercakup UK-04
- [x] `perkakas/kepatuhan/api.py`
- [x] Mutasi M-5, M-8

## T-6 · Bukti, penutupan

- [x] Bagian 9.2 plan; keluaran ke `bukti/`
- [x] Putaran mutasi dilaporkan apa adanya; L8, dokumen HKI, L4; status
      menunggu Gerbang 4
