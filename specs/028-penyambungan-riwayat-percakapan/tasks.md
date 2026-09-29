# Tasks: 028-penyambungan-riwayat-percakapan

| | |
|---|---|
| Spec | Gerbang 1 lolos 28 September 2026 (KB-138) |
| Plan | Gerbang 2 lolos 28 September 2026 (KB-139); K-1, K-2, K-3 sesuai anjuran |
| Status | **Gerbang 3 lolos** — 29 September 2026 (KB-140). T-1 selesai; delapan tugas tersisa |
| Kebutuhan | R-01 s.d. R-17; C-05, C-13, C-14, C-17, C-20 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sebelum tiap tugas dinyatakan selesai —
dijalankan sebagai perintah berdiri sendiri, tanpa pipa (KB-080), dengan
PostgreSQL menyala. **Tidak satu baris pun berubah di `src/rag/` maupun
`src/llm/`** (R-11).

---

## T-1 · Kontrak lebih dulu: D-14 Bagian 5 dan 4.3

**Kebutuhan:** R-04, R-12; K-1.

- [x] D-14 Bagian 5: tabel `riwayat.percakapan` dan `riwayat.giliran` beserta
      aturan bidangnya — pemilik berupa pseudonim (C-05), waktu UTC (KM-01),
      tambah-saja (KM-02)
- [x] D-14 Bagian 4.3: "terurut" diperjelas menjadi **terbaru lebih dulu
      menurut waktu dibuat** (K-1); bentuk tanggapan tidak berubah
- [x] D-14 naik ke 0.8; register D-00
- [x] Pemeriksa C-20 tetap lulus — blok JSON pertama Bagian 4.1 tetap bentuk
      tanggapan

---

## T-2 · Peladen menegakkan tambah-saja

**Kebutuhan:** R-05, R-08, R-12.

- [ ] Uji lebih dulu pada `tests/penyimpanan/test_persiapan_basis_data.py`:
      `peran_riwayat` **ditolak** `UPDATE`, `DELETE`, `TRUNCATE` atas kedua
      tabel; `peran_penjawaban` **ditolak** membaca maupun menulis skema
      `riwayat` — setiap penolakan menuntut `permission denied` pada stderr
- [ ] Uji `peran_riwayat` **berjalan**: menambah percakapan dan giliran, lalu
      membacanya, tersambung sebagai peran itu sendiri (TK-64)
- [ ] `01-peran-dan-basis-data.sql`: `peran_riwayat`, `CONNECT` ke basis data
      perilaku saja — tidak ke basis data pseudonim
- [ ] `06-riwayat.sql` baru: skema, dua tabel, hak `SELECT` dan `INSERT` saja;
      `README.md` memuat urutan jalannya
- [ ] Mutasi M-6 dan M-7 pada berkas SQL, dengan basis data dibangun ulang
      — bukan `REVOKE` pada basis data yang disiapkan ulang (pelajaran TK-64)

---

## T-3 · Penyimpan riwayat

**Kebutuhan:** R-02, R-08, R-12, R-13.

- [ ] Satu himpunan uji perilaku, dijalankan atas `RiwayatMemori` **dan**
      `RiwayatPostgres`: mencatat, membaca, daftar terbaru lebih dulu,
      pemilik ditetapkan sekali, `BukanPemilik` bagi pemilik lain tanpa
      menulis giliran
- [ ] Uji R-13: dua `RiwayatPostgres` dengan sambungan berbeda — yang kedua
      membaca giliran yang ditulis yang pertama
- [ ] `src/penyimpanan/riwayat.py`: `PenyimpanRiwayat`, kedua pelaksana,
      `KredensialRiwayat`; tanpa impor `src/api/` maupun `src/nlp/`
- [ ] Permukaan tanpa metode ubah maupun hapus — diuji atas atribut kelasnya

---

## T-4 · Identitas dan pemilik

**Kebutuhan:** R-06, R-17; P-1.

- [ ] Uji: `Identitas(peran, pemilik)` beku; pemilik kosong ditolak
- [ ] `src/api/identitas.py`; `PenentuIdentitas.identitas()` menggantikan
      `.peran()` — seluruh pemanggil dan uji `tests/api/` dimutakhirkan tanpa
      melonggarkan satu pernyataan pun
- [ ] `perkakas/jalankan_lokal.py`: pemilik tetap `pengembangan-pemilik-tunggal`;
      uji bahwa ia tetap tidak terjangkau dari `src/`

---

## T-5 · Bentuk galat D-14 Bagian 4.2 dan log operasional

**Kebutuhan:** R-14; TK-66.

- [ ] Uji lebih dulu: setiap galat ketiga rute berbentuk
      `{"galat": {"kode", "pesan_pengguna", "id_jejak"}}` dengan kode dan
      status tabel `plan.md` Bagian 5; galat tak tertangani menjadi
      `GALAT_INTERNAL`; `GalatLayananModel` menjadi `LAYANAN_MODEL_GAGAL`
- [ ] Uji: `id_jejak` yang sama muncul pada tanggapan dan pada log operasional;
      log tidak memuat pertanyaan maupun pesan pengecualian — hanya nama
      kelasnya
- [ ] `src/api/galat.py`: `KodeGalat` tujuh nilai D-14; penyusun badan galat
- [ ] Pemeriksa C-13 Aturan 2 mengenal jalan keluar baru; uji bahwa untai
      harfiah pada jalan keluar baru **ditolak** — tanpanya pesan baru lolos
      C-13 tanpa dibaca (KB-133)
- [ ] Mutasi M-8 dan M-9

---

## T-6 · `/tanya` mencatat giliran — inti fitur

**Kebutuhan:** R-01, R-02, R-03, R-07, R-15, R-16; TK-65, TK-67, TK-68.

- [ ] Uji dua identitas: B tidak dapat membaca daftar A, membaca percakapan A,
      menulis ke percakapan A, maupun membedakan percakapan A dari yang tidak
      ada — ketiga tanggapan penolakan **sama persis** kecuali `id_jejak`
- [ ] Uji: pertanyaan berdata pribadi → 400 `VALIDASI_GAGAL`, **nol** panggilan
      jalur, nol giliran, dan tidak ada pada log; pesannya tidak mengutip nomor
- [ ] Uji: `id_percakapan` bukan UUID v4 → 400; bidang tambahan → 400
- [ ] Uji: jawaban tercatat sebagai giliran dengan `id_pesan` tanggapannya;
      `jalur.jawab` dipanggil hanya dengan pertanyaan — tanpa giliran
      sebelumnya (R-07, C-14)
- [ ] `PermintaanTanya` memperoleh `id_percakapan`; `susun_aplikasi` menerima
      `PenyimpanRiwayat`; rute riwayat tersaring pemilik
- [ ] Docstring `src/api/percakapan.py` "di memori … menunggu penggerak
      PostgreSQL" dimutakhirkan — kalimat yang tertinggal sesudah utangnya
      lunas adalah kalimat yang dipercaya orang berikutnya
- [ ] Mutasi M-1 s.d. M-5, M-10, M-11, M-14

---

## T-7 · Layar: melanjutkan percakapan

**Kebutuhan:** R-09, R-10; K-2, K-3; D-05 S-09 blok 9 dan 10.

- [ ] Uji lebih dulu: permintaan membawa `id_percakapan` yang sama sepanjang
      percakapan dan sesudah muat ulang; "Percakapan baru" membangkitkan yang
      baru
- [ ] Uji: blok 9 memuat pertanyaan percakapan aktif **tanpa jawaban**; blok 10
      memuat pertanyaan pertama paling banyak sepuluh percakapan terbaru,
      dimuat saat blok dibuka (K-2)
- [ ] Uji: mengetuk pertanyaan lama mengisi isian dan **tidak** mengirim
- [ ] Uji: kalimat `pertanyaan_ditolak` baru (K-3); layar tetap tidak membaca
      badan galat
- [ ] `kontrak.ts` memperoleh `Giliran` dan bentuk kedua rute riwayat;
      `kontrak_web.py` membandingkannya dengan model Python
- [ ] `percakapan.ts`, komponen blok 9 dan 10, `mikrokopi.ts`; uji
      `halaman.test.ts` tentang simpanan lokal diperluas ke kunci kedua
      secara tegas
- [ ] Anggaran muat tetap ≤ 150 KB
- [ ] Mutasi M-12 dan M-13

---

## T-8 · Putaran mutasi dan bukti ujung ke ujung

**Kebutuhan:** `plan.md` Bagian 8.

- [ ] M-1 s.d. M-14 sebagai satu putaran; yang tidak menyala **dilaporkan
      beserta sebabnya**
- [ ] Playwright global terhadap `make jalan` dengan riwayat PostgreSQL: dua
      pertanyaan, muat ulang, percakapan berlanjut; percakapan baru; blok 10
      memuat yang lama. Tangkapan layar disimpan
- [ ] `git diff --stat` atas `src/rag/` dan `src/llm/` sejak Gerbang 3: **kosong**

---

## T-9 · Penutupan

- [ ] D-00: TK-65, TK-66, TK-67, TK-68 ditutup dengan bukti mutasinya
- [ ] D-14 Bagian 4.3: catatan "belum ditegakkan kode" dimutakhirkan
- [ ] `logbook/L8` catatan akhir fitur — juga bila tagihan pasal tidak menyusut
- [ ] `docs/hki/dokumentasi-teknis.md`: baris "Layanan API" dan "Basis data"
- [ ] Catatan keputusan pada `logbook/L4`

---

## Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Perubahan `src/rag/` atau `src/llm/` tampak perlu | Berhenti; R-11 |
| Bentuk tanggapan `/tanya` tampak perlu berubah | Berhenti; C-20 |
| Basis data pseudonim tampak perlu terjangkau layanan aplikasi | Berhenti; C-05 |
| Paket baru tampak perlu | Berhenti; C-12 |
| Uji `tests/api/` hanya dapat lulus bila pernyataannya dilonggarkan | Berhenti; tanyakan |
