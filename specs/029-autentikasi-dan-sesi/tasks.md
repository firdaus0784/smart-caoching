# Tasks: 029-autentikasi-dan-sesi

| | |
|---|---|
| Spec | Gerbang 1 lolos 1 Oktober 2026 (KB-151); P-1 s.d. P-7 sesuai anjuran |
| Plan | Gerbang 2 lolos 1 Oktober 2026 (KB-153); K-1 s.d. K-7 dan angka P-4 sesuai anjuran |
| Status | **Gerbang 3 lolos** — 1 Oktober 2026 (KB-154). Sembilan dari sembilan tugas selesai — **menunggu Gerbang 4** (KB-162) |
| Kebutuhan | R-01 s.d. R-10; FR-A01; NFR-05, NFR-06, NFR-08; KA-01, KA-03; C-05, C-13, C-17, C-20; TK-70 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sebelum tiap tugas dinyatakan selesai —
dijalankan sebagai perintah berdiri sendiri, tanpa pipa (KB-080), dengan
PostgreSQL menyala. **Tidak satu baris pun berubah di `src/rag/` maupun
`src/llm/`**, dan tidak ada paket baru (C-12).

---

## T-1 · Kontrak lebih dulu: D-14, D-04, D-05

**Kebutuhan:** R-02; K-1, K-2; P-6.

- [x] D-14 Bagian 4.4 baru: bentuk `POST /api/v1/auth/masuk` dan
      `/auth/keluar` — permintaan, 204 tanpa badan, kuki, 400 dan 401;
      syarat `Content-Type: application/json` pada rute pengubah keadaan (K-4)
- [x] D-14 Bagian 5.1: `pengguna.turunan_sandi`, `pengguna.gagal_beruntun`,
      `pengguna.ditahan_sampai`, `sesi.*`; `pengguna.id` berupa nama pengguna
      buatan tim yang tidak mengidentifikasi; `pseudonim` terpisah darinya (K-1)
- [x] D-04 Bagian 7.1: baris `pengguna` dan `sesi`; arti
      `peta_pseudonim.id_pengguna` di bawah P-1 A (K-2)
- [x] D-05: S-01 — bidang, keadaan galat dan luring, mikrokopi; tombol Keluar
      pada S-09
- [x] Register D-00; pemeriksa C-20 tetap lulus — blok JSON pertama Bagian 4.1
      tetap bentuk tanggapan `/tanya`

---

## T-2 · Peladen menegakkan hak akun

**Kebutuhan:** R-03, R-07; plan Bagian 3.2.

- [x] Uji lebih dulu pada `tests/penyimpanan/test_persiapan_basis_data.py`,
      tiap penolakan menuntut `permission denied`:
      `peran_autentikasi` ditolak `INSERT` akun, `UPDATE` atas `turunan_sandi`,
      `peran`, `status_aktif`, `pseudonim`, `DELETE`, dan `CONNECT` ke basis
      data pseudonim; `peran_pengelola_akun` ditolak `UPDATE` atas `peran`,
      `pseudonim`, dan `DELETE`; `peran_penjawaban` dan `peran_riwayat`
      ditolak seluruh skema `akun`
- [x] Uji kedua peran **berjalan** pada hak yang diberikan, tersambung sebagai
      peran itu sendiri (TK-64)
- [x] `01-peran-dan-basis-data.sql`: dua peran baru, `CONNECT` ke basis data
      perilaku saja
- [x] `07-akun.sql` baru; `README.md` dan `tests/peladen.py` menjalankannya
- [x] Mutasi M-7 dan M-8 pada berkas SQL, dengan basis data dibangun ulang

---

## T-3 · Sandi

**Kebutuhan:** R-03; P-3, P-4; plan Bagian 4.

- [x] Uji lebih dulu: turunan memuat parameter dan garamnya; dua akun dengan
      sandi sama berturunan berbeda; sandi benar cocok, salah tidak; tanda
      hubung pada sandi masukan diabaikan; sandi > 128 karakter ditolak
      **sebelum** diturunkan
- [x] Uji: turunan berparameter N=2^15, r=8, p=3 **berhasil** — tanpa `maxmem`
      tegas ia gagal pada OpenSSL 3 (KB-152)
- [x] Uji: sandi bangkitan 16 karakter dari 31 simbol, tanpa `0 O 1 l I`
- [x] `src/api/sandi.py`: turunan, pemeriksaan dengan `hmac.compare_digest`,
      pembangkit sandi; tanpa impor selain pustaka baku dan `src/kamus/`

---

## T-4 · Penyimpan akun dan sesi

**Kebutuhan:** R-04, R-06; P-2, P-4; plan Bagian 5 dan 6.

- [x] Satu himpunan uji perilaku atas `AkunMemori` **dan** `AkunPostgres`:
      baca akun; catat gagal sampai ditahan; penahanan berakhir; berhasil
      mengembalikan penghitung ke nol; percobaan selama ditahan tidak
      memperpanjang; buat, baca, sentuh, dan cabut sesi; sesi akun nonaktif
      tidak terbaca
- [x] Uji atomik: sepuluh `catat_gagal` bersamaan pada PostgreSQL menghasilkan
      tepat satu penahanan dan penghitung sepuluh
- [x] Uji: baris `sesi` memuat SHA-256 pengenal, **tidak** pengenalnya
- [x] `src/penyimpanan/akun.py`; permukaan tanpa metode hapus — diuji atas
      atribut kelasnya

---

## T-5 · Identitas dari sesi; 401

**Kebutuhan:** R-05, R-10; KA-01.

- [x] Uji lebih dulu: tanpa kuki, kuki tak dikenal, kuki dicabut, dan sesi
      kedaluwarsa (tanpa aktivitas 30 menit; mutlak 8 jam, jam disuntikkan) →
      401 `TIDAK_TERAUTENTIKASI` pada ketiga rute lama, **sebelum** badan
      permintaan dibaca
- [x] Uji: peran dibaca dari akun tiap permintaan — akun dinonaktifkan
      sesudah masuk ditolak pada permintaan berikutnya
- [x] `PenentuIdentitas.identitas` menjadi `async`, mengembalikan
      `Identitas | None`; `PenentuSesi` pada `src/api/autentikasi.py`
- [x] Sembilan tempat pada `tests/api/`, `IdentitasPengembangan`, dan tiruan
      pemeriksa `rute_terdaftar` dimutakhirkan **tanpa melonggarkan satu
      pernyataan pun**
- [x] Uji bahwa `IdentitasPengembangan` tetap tidak terjangkau dari `src/`
- [x] Mutasi M-9, M-10, M-11

---

## T-6 · Rute masuk dan keluar — inti fitur

**Kebutuhan:** R-01, R-03, R-04, R-06, R-09; K-3, K-4.

- [x] Uji lebih dulu: masuk berhasil → 204, kuki `__Host-sesi` dengan
      `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/`, tanpa `Domain`
- [x] Uji R-04: akun tidak ada, sandi salah, ditahan, dan nonaktif →
      tanggapan **sama persis** kecuali `id_jejak`, dan **tepat satu**
      turunan sandi dijalankan pada keempatnya
- [x] Uji: sesudah masuk, kuki sesi lama dicabut; sesudah keluar, kuki lama
      ditolak 401 (R-06)
- [x] Uji K-4: masuk, keluar, dan tanya dengan `Content-Type` selain JSON
      ditolak, tanpa turunan sandi dan tanpa panggilan jalur
- [x] Uji R-09: log tidak memuat sandi, pengenal sesi, turunannya, maupun nama
      pengguna yang diketik pada penolakan; penahanan akun yang ada tercatat
      dengan `id` akun dan `id_jejak`
- [x] Uji: badan berbidang tambahan → 400; pesan penolakan lolos C-13
- [x] Turunan pada utas, semafor dua; rute pada `src/api/aplikasi.py`;
      `POLA_MASUK`, `POLA_KELUAR` dari `PETA_RUTE`
- [x] Mutasi M-1 s.d. M-6, M-12, M-13

---

## T-7 · Perkakas tim dan titik jalan

**Kebutuhan:** P-5, P-7; K-5, K-7.

- [x] Uji lebih dulu: `--id` yang bukan pola `^[a-z]{2,8}-[0-9]{3}$` atau
      berpola data pribadi ditolak; sandi tercetak sekali dan tidak tertulis
      ke berkas mana pun; atur ulang sandi dan nonaktifkan mencabut seluruh
      sesi akun itu; pseudonim acak dan tidak dicetak
- [x] `perkakas/akun.py` dengan tiga perintah, tersambung sebagai
      `peran_pengelola_akun`
- [x] `perkakas/jalankan_lokal.py`: `--autentikasi sesi` bawaan;
      `pengembangan` hanya bila diminta, dengan peringatan yang sudah ada

---

## T-8 · Layar S-01, Keluar, peralihan 401

**Kebutuhan:** R-08; P-6; K-6.

- [x] Uji lebih dulu: saat dibuka, 401 dari `GET /api/v1/percakapan`
      menampilkan S-01 dan 200 menampilkan Tanya
- [x] Uji: isian sandi `type="password"`, `autocomplete` tepat; sandi tidak
      ada di simpanan lokal maupun keadaan sesudah dikirim
- [x] Uji: 401 di tengah pemakaian kembali ke S-01, draf tetap tersimpan;
      `belum_masuk` terpisah dari `tidak_berhak`
- [x] Uji K-6: Keluar menghapus draf dan percakapan aktif dari simpanan lokal
- [x] Mikrokopi lolos pemeriksa C-13; anggaran muat tetap ≤ 150 KB
- [x] Mutasi M-14 dan M-15

---

## T-9 · Putaran mutasi, bukti, penutupan

**Kebutuhan:** plan Bagian 12.

- [x] M-1 s.d. M-15 sebagai satu putaran; yang tidak menyala **dilaporkan
      beserta sebabnya**
- [x] Playwright global terhadap `make jalan`: buat akun lewat perkakas, masuk,
      bertanya, muat ulang, keluar, kuki lama ditolak. Kuki `__Host-` `Secure`
      pada `http://127.0.0.1` **diverifikasi**, tidak diandaikan
- [x] `git diff --stat` atas `src/rag/` dan `src/llm/` sejak Gerbang 3: **kosong**
- [x] D-00: TK-70 ditutup dengan buktinya; `logbook/L8`; dokumen HKI; L4

---

## Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Perubahan `src/rag/` atau `src/llm/` tampak perlu | Berhenti |
| Layanan aplikasi tampak perlu menjangkau basis data pseudonim | Berhenti; C-05 |
| Paket baru tampak perlu | Berhenti; C-12 |
| Peramban menolak kuki `__Host-` `Secure` pada pengembangan | Berhenti; tanyakan. `Secure` tidak dilepas |
| Rute selain dua rute D-14 3.1 tampak perlu | Berhenti; AG-02 |
| Uji `tests/api/` hanya lulus bila pernyataannya dilonggarkan | Berhenti; tanyakan |
