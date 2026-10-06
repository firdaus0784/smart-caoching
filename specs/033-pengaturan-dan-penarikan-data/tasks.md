# Tasks: 033-pengaturan-dan-penarikan-data

| | |
|---|---|
| Spec | Gerbang 1 lolos 6 Oktober 2026 (KB-204); P-1 s.d. P-5 sesuai anjuran |
| Plan | Gerbang 2 lolos 6 Oktober 2026 atas pendelegasian KB-168 (KB-205); K-1 s.d. K-6 |
| Status | **Lolos Gerbang 2–3** atas pendelegasian KB-168 (KB-205). Nol dari tujuh tugas selesai; Gerbang 4 menunggu pemegang gerbang |
| Kebutuhan | R-01 s.d. R-09; FR-A06, NFR-09, RE-04, KM-02; C-04, C-05, C-13, C-17, C-20 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sesudah entri L4 ditulis, tepat sebelum
commit. **`src/rag/`, `src/llm/`, `src/telemetri/`, dan `src/ingest/` tidak
berubah.** Agen **tidak** menulis kalimat penjelasan penarikan (P-4 B).

---

## T-1 · Kontrak lebih dulu

**Kebutuhan:** R-03, R-08; K-3, K-5.

- [ ] D-14 Bagian 4.5: bentuk `DELETE /saya/data` — konfirmasi, 202, kuki
- [ ] D-14 Bagian 5.1: `permintaan_penarikan`; KM-02 dirujuk; dua peran
- [ ] Register D-00

## T-2 · Peladen

**Kebutuhan:** R-02, R-04; K-2, K-3.

- [ ] Uji lebih dulu: penolakan kedua peran baru dengan sebab
      `permission denied`; katalog hak persis; batasan baris permintaan
- [ ] `01-peran-dan-basis-data.sql` + dua peran; `11-penarikan.sql`
- [ ] Katalog hak uji fitur 028, 030, 013, 034: `peran_penarikan` disebut
      tegas sebagai satu-satunya pemegang `DELETE`
- [ ] Mutasi M-6

## T-3 · Penyimpan akun

**Kebutuhan:** R-01, R-05; K-4.

- [ ] Uji lebih dulu atas memori **dan** PostgreSQL sebagai
      `peran_autentikasi`: mencatat sekaligus mencabut seluruh sesi; akun
      tertunda terbaca nonaktif
- [ ] `catat_penarikan`; `baca_akun`
- [ ] Mutasi M-2

## T-4 · Rute

**Kebutuhan:** R-01, R-05, R-08; K-5.

- [ ] Uji lebih dulu lewat `TestClient`: 202, kuki dihapus, sesi lain ditolak,
      masuk ditolak sama dengan sandi salah, tanpa konfirmasi 400
- [ ] `DELETE /saya/data` pada `src/api/aplikasi.py`
- [ ] Mutasi M-1, M-8

## T-5 · Penghapusan dan perkakas

**Kebutuhan:** R-02, R-03, R-04, R-09; K-1, K-7.

- [ ] Uji lebih dulu terhadap PostgreSQL: dua pengguna berdata pada sepuluh
      tabel dan pemetaan; sesudah `jalankan`, satu kosong dan satu utuh;
      baris permintaan tanpa pseudonim; keluaran dan log tanpa pseudonim
- [ ] `src/penyimpanan/penarikan.py`; `perkakas/penarikan.py`
- [ ] Uji arah: layanan aplikasi tidak mengimpor penyimpan penarikan
- [ ] Mutasi M-3, M-4, M-5, M-7

## T-6 · S-14 Pengaturan

**Kebutuhan:** R-05, R-06, R-07; K-6; C-13.

- [ ] Uji lebih dulu: formulir terisi dan tersimpan lewat rute fitur 030;
      persetujuan; daftar data; dua tombol setara; tanpa permintaan sebelum
      konfirmasi; luring tidak mengirim; naskah tim dibaca bila ada
- [ ] `web/src/pengaturan/`; tombol di samping Keluar; mikrokopi
- [ ] Mutasi M-9

## T-7 · Titik jalan, bukti, penutupan

- [ ] `make jalan` memasang rute penarikan bersama sesi
- [ ] Playwright Bagian 10.2 plan; keluaran ke `bukti/`
- [ ] Putaran mutasi dilaporkan apa adanya; L8, dokumen HKI, L4; status
      menunggu Gerbang 4
