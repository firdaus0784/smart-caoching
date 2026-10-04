# Tasks: 030-aktivasi-persetujuan-dan-profil

| | |
|---|---|
| Spec | Gerbang 1 lolos 4 Oktober 2026 (KB-165); P-1 s.d. P-7 sesuai anjuran |
| Plan | Gerbang 2 lolos 4 Oktober 2026 (KB-168); K-1 s.d. K-8 dan draf S-03 sesuai anjuran |
| Status | **Gerbang 3 lolos (didelegasikan)** — 4 Oktober 2026 (KB-168). Pelaksanaan berjalan |
| Kebutuhan | R-01 s.d. R-10; FR-A02 s.d. FR-A06; C-04, C-05, C-13, C-14, C-20; TK-50 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sesudah entri L4 ditulis, tepat sebelum
commit. **`src/rag/`, `src/llm/`, dan `src/telemetri/` tidak berubah.**
Agen **tidak** membuat berkas naskah persetujuan (ET-02).

---

## T-1 · Kontrak lebih dulu

**Kebutuhan:** R-01; K-1, K-5; P-3.

- [x] D-14 Bagian 4.5: bentuk empat rute `/saya/*` — ringkasan aktivasi,
      permintaan, penolakan; syarat `application/json`
- [x] D-14 Bagian 5.1: `prioritas_manajerial` tambah-saja, `persetujuan`
      tambah-saja kecuali `dicabut_pada`; `id_pengguna` berisi pseudonim
- [x] D-04 Bagian 7.1: `akreditasi` diselaraskan menjadi `jalur_akreditasi`
      (TK-50 ditutup)
- [x] D-05: blok S-02, S-03 (draf Bagian 7 plan), S-04; tautan persetujuan pada S-09
- [x] AGENTS.md: tepi `api → pengguna` satu jurusan beserta alasannya;
      pemeriksa arah tetap lulus
- [x] Register D-00

## T-2 · Peladen menegakkan hak profil

**Kebutuhan:** R-02; K-2, K-3.

- [x] Uji lebih dulu: `peran_pengguna` ditolak `UPDATE (id_pengguna)` profil,
      `UPDATE`/`DELETE` prioritas, `UPDATE` selain `dicabut_pada` pada
      persetujuan, `DELETE` di mana pun, skema `akun`/`riwayat`/karantina, dan
      basis data pseudonim — sebab `permission denied`
- [x] Uji peran **berjalan** pada haknya; himpunan hak dari katalog
- [x] `08-pengguna.sql`; `peran_pengguna` pada `01`; `tests/peladen.py`; README
- [x] Mutasi M-4 s.d. M-6

## T-3 · Penyimpan pengguna

**Kebutuhan:** R-02, R-03, R-04; K-3.

- [x] Satu himpunan uji atas pelaksana memori **dan** PostgreSQL (sebagai
      `peran_pengguna`): profil simpan-baca-perbarui; prioritas tambah-saja
      dengan yang terbaru berlaku; persetujuan tambah-saja, keadaan dari baris
      terbaru, pencabutan hanya mengisi `dicabut_pada`
- [x] `src/penyimpanan/pengguna.py`; permukaan tanpa hapus
- [x] Mutasi M-7

## T-4 · Rute `/saya/*` dan naskah

**Kebutuhan:** R-01 s.d. R-05, R-08, R-10; K-4, K-5.

- [x] Uji lebih dulu: pemilik dari sesi; B tidak membaca maupun menulis milik A;
      tujuh isian ditolak; dua atau enam prioritas ditolak; versi naskah
      karangan ditolak; tanpa berkas naskah setiap persetujuan ditolak;
      penolakan persetujuan tidak menghalangi `/tanya`; `jalur.jawab` tidak
      menerima profil (C-14); kalimat lolos C-13
- [x] `src/api/saya.py`; pemasangan pada `susun_aplikasi`; titik jalan memuatnya
- [x] Mutasi M-1 s.d. M-3, M-8, M-9

## T-5 · Layar aktivasi

**Kebutuhan:** R-06, R-07, R-09; K-6, K-7, K-8.

- [ ] Uji lebih dulu: alur menurut ringkasan aktivasi; S-02 tanpa naskah;
      setuju, tolak, cabut; S-03 empat layar tanpa jalan pintas melewati layar 2;
      S-04 enam isian dan tiga sampai lima prioritas berlabel D-03; tautan
      persetujuan dari S-09; luring membuka S-09
- [ ] `web/src/aktivasi/`; cangkang; mikrokopi; `kontrak.ts` dan pemeriksa kontrak
- [ ] Anggaran muat ≤ 150 KB; mutasi M-10 dan M-11

## T-6 · Putaran mutasi, bukti, penutupan

- [ ] M-1 s.d. M-11 sebagai satu putaran
- [ ] Playwright terhadap `make jalan` dengan naskah uji pada direktori sementara
- [ ] `git diff --stat` atas `src/rag/`, `src/llm/`, `src/telemetri/` sejak Gerbang 3: kosong
- [ ] D-00, L8, dokumen HKI, L4; **menunggu Gerbang 4 manusia**

## Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Naskah persetujuan tampak perlu ditulis agen | Berhenti; ET-02 |
| Perubahan `src/rag/`, `src/llm/`, atau `src/telemetri/` tampak perlu | Berhenti |
| Rute selain empat rute D-14 3.1 tampak perlu | Berhenti; AG-02 |
| Profil tampak perlu memengaruhi jawaban | Berhenti; C-14 |
| Paket baru tampak perlu | Berhenti; C-12 |
