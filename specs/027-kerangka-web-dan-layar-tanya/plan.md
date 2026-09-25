# Plan: 027-kerangka-web-dan-layar-tanya

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 25 September 2026 (KB-124); cakupan disempitkan atas TK-65 (KB-125) |
| Status | **Menunggu Gerbang 2** |
| Kebutuhan | R-01 s.d. R-20 `spec.md` kecuali R-11; C-12, C-13, C-20 |

## 1. Letak dan batas

```
web/                         (baru)  seluruh kode antarmuka
  package.json, package-lock.json   versi dipatok persis (--save-exact)
  index.html                        CSP 'self'; tanpa URL pihak ketiga
  public/manifest.webmanifest, public/sw.js
  src/kontrak.ts                    tipe tanggapan D-14 Bagian 4.1 dan 4.2
  src/klien.ts                      pemanggil POST /api/v1/tanya
  src/mikrokopi.ts                  SATU-SATUNYA tempat teks antarmuka
  src/draf.ts                       draf pertanyaan pada simpanan lokal
  src/tanya/…                       komponen layar S-09
  src/gaya.css                      token warna, huruf, dan ukuran ketuk
perkakas/pemeriksa/          (ubah)  V-01, V-04, C-13, dan dua pemeriksa baru
ketergantungan-disetujui.toml (ubah) bagian [npm]
Makefile                     (ubah)  `setup` memasang `web/` juga
src/                                 TIDAK DISENTUH SATU BARIS PUN (R-16)
```

**Tanpa perubahan backend, dan itu diperiksa, bukan dijanjikan.** Pada
pengembangan, peladen Vite meneruskan `/api` ke `127.0.0.1:8000` (`make
jalan`). Asal yang sama membuat CORS tidak dibutuhkan — dan CORS adalah
perubahan backend. Gerbang 4 menuntut `git diff --stat` atas `src/` sejak
Gerbang 3 kosong.

## 2. Blast radius, diukur di muka

`plan.md` fitur 019 dua kali menyatakannya di bawah kenyataan (KB-094,
KB-100), sehingga angka ini dihitung sekarang, bukan diperkirakan.

| Kelompok | Berkas |
|---|---|
| Baru di `web/` | ± 15 berkas sumber dan uji |
| Pemeriksa baru | `perkakas/pemeriksa/ketergantungan_npm.py`, `kontrak_web.py` |
| Pemeriksa diubah | `jalankan.py` (V-01, V-04), `bahasa_antarmuka.py` (C-13), `rute_terdaftar.py` |
| Lain-lain | `ketergantungan-disetujui.toml`, `Makefile`, `.gitignore` |
| `src/` | **0** |

## 3. `make check` membaca `web/` — R-19

Tanpa bagian ini keenam gerbang melaporkan lulus tanpa pernah melihat
frontend: bentuk TA-01, dan bentuk TK-64.

| Gerbang | Yang ditambahkan | Bila Node tidak ada |
|---|---|---|
| **V-01** | `npm --prefix web run periksa` — `tsc --noEmit` mode ketat, lalu `vitest run` | **Gagal**, bukan dilewati — sejajar keputusan 12 September atas PostgreSQL |
| **V-02** | Pemeriksa C-13 membaca `web/src/mikrokopi.ts`; aturan bentuk menolak teks harfiah pada berkas `.tsx` | — |
| **V-03** | `kontrak_web.py`: nama bidang `kontrak.ts` wajib sama dengan `Tanggapan` pada `src/rag/jawaban/tanggapan.py`. `rute_terdaftar.py`: setiap jalur `/api/v1/…` pada `web/src` wajib rute yang **terpasang** | — |
| **V-04** | `ketergantungan_npm.py`: ketergantungan langsung ⊆ `[npm].langsung`; seluruh isi `package-lock.json` = `[npm.terkunci]` | **Gagal** |

**Kontrak ditulis dua kali, dan itu disengaja, tetapi dijaga.** TypeScript
tidak dapat mengimpor model pydantic. Dua daftar yang menggambarkan hal yang
sama akan hanyut; `kontrak_web.py` yang membuat hanyutnya menjatuhkan V-03
alih-alih muncul sebagai layar kosong di lapangan.

**Cakupan uji `web/` tidak diukur.** Pengukurnya (`@vitest/coverage-v8`) paket
yang tidak termasuk persetujuan KB-123. Dinyatakan terbuka, bukan disiasati.

## 4. Bentuk layar S-09

Susunan blok mengikuti D-05 S-09 dan D-07 Bagian 4 tahap 10. Keadaan
`tidak_ditemukan` dan `di_luar_domain` memakai **komponen yang sama** dengan
jawaban normal — hanya isinya berbeda (R-04). Dua komponen berbeda akan
berbeda susunannya pada hari salah satunya disunting.

| Blok | Sumber data | Catatan |
|---|---|---|
| Pertanyaan | masukan pengguna | Dapat disunting ulang |
| Penanda dasar rujukan | `status_dasar` | **Teks**, dengan warna sebagai penguat saja (AK-04) |
| Ringkasan tindakan | `ringkasan_tindakan` | Paling banyak tiga; lebihnya dipotong **dan dicatat pada uji**, bukan disembunyikan diam-diam |
| Penjelasan | `penjelasan` | `tidak_ditemukan` dengan penjelasan kosong memakai kalimat pertama D-05 Bagian 10 (K-2) |
| Dasar rujukan | `sitasi[]` | Judul, tahun, bagian; penanda keberlakuan bila bukan `berlaku`; `catatan_keberlakuan` bila terisi |
| Bacaan lanjutan | `bacaan_lanjutan[]` | Blok terpisah, dengan keterangan bahwa isinya tidak dipakai menyusun jawaban |
| Tindakan | — | "Salin ringkasan" saja |
| Penafian | `penafian` | Selalu tampak, pada ketiga keadaan |

`klaim[]` dan `versi` diterima tetapi tidak ditampilkan: D-05 S-09 tidak
memintanya, dan arti `peringkat_kepercayaan` belum diputus (TK-40).

## 5. Keputusan yang diambil di sini

**Draf disimpan pada simpanan lokal peramban, dibungkus penjagaan.** Simpanan
lokal dapat menolak ditulis (mode pribadi, kuota penuh). Kegagalannya tidak
boleh menjatuhkan layar — tetapi juga tidak boleh diam: KL-E menyatakan "catatan
Anda tersimpan" **hanya bila memang tersimpan**. Pernyataan aman yang tidak
benar lebih buruk daripada tidak ada pernyataan.

**Anggaran muat awal 150 KB terkompresi** sebagai ukuran pengganti NFR-02.
**Penetapan tim tanpa dasar literatur** (SI-01 pilihan kedua), diturunkan dari
anggapan laju 3G sekitar 0,75 Mbit/s — anggapan yang **wajib diverifikasi**
terhadap sinyal di lokus pilot sebelum dipakai sebagai klaim kinerja. Diperiksa
V-01 atas hasil `vite build`.

**Kontras dihitung, bukan dilihat.** Warna tinggal sebagai token pada
`gaya.css`; uji menghitung rasio kontras WCAG setiap pasangan huruf-latar yang
dipakai dan menuntut ≥ 4,5 (AK-02). Ukuran huruf dasar ≥ 16px dan sasaran
ketuk ≥ 44px dibaca dari token yang sama (AK-01, AK-03).

**Service worker ditulis tangan, dan logikanya fungsi murni.** Keputusan
"tembolok atau jaringan" untuk setiap permintaan diuji tanpa peramban.
Permintaan `/api/…` **tidak pernah** ditembolok: jawaban lama yang tersaji dari
tembolok melanggar C-07 dengan cara yang sama persis dengan riwayat yang
menyimpan tanggapan (D-14 Bagian 4.3).

## 6. Uji

### 6.1 Di dalam `make check`

Komponen dengan `@testing-library/react` di atas `jsdom`; fungsi murni dengan
`vitest`. Seluruhnya berjalan tanpa peladen backend — `klien.ts` menerima
pemanggil `fetch` yang disuntikkan, bentuk yang sama dengan `Penyemat` dan
`sekarang` pada fitur 026.

### 6.2 Di luar `make check`: bukti ujung ke ujung

Playwright tersedia pada lingkungan ini sebagai alat **global**, bukan
ketergantungan proyek. Ia dipakai sekali pada Gerbang 4: layar dibuka terhadap
`make jalan`, dan tangkapan layar ketiga keadaan (`kuat`/`terbatas`,
`tidak_ditemukan`, luring) dilampirkan. Ia **tidak** masuk `make check`:
gerbang yang bergantung pada alat di luar daftar persetujuan adalah
ketergantungan tersembunyi.

### 6.3 Uji mutasi

| | Mutasi | Yang wajib menangkapnya |
|---|---|---|
| M-1 | Penanda dasar dipindah ke sesudah ringkasan | R-02 |
| M-2 | Penanda hanya warna, tanpa teks | R-03, AK-04 |
| M-3 | `tidak_ditemukan` ditampilkan sebagai galat | R-04 |
| M-4 | Penafian disembunyikan pada keadaan tidak-ditemukan | R-02 |
| M-5 | Bacaan lanjutan digabung ke dasar rujukan | R-07 |
| M-6 | Draf tidak disimpan saat kiriman gagal | R-09 |
| M-7 | Status HTTP ditampilkan kepada pengguna | R-10 |
| M-8 | Teks harfiah pada `.tsx` di luar `mikrokopi.ts` | R-12 |
| M-9 | URL pihak ketiga pada `index.html` | R-18 |
| M-10 | Satu uji `web/` dibuat gagal | R-19 — **V-01 wajib merah** |
| M-11 | Paket npm di luar persetujuan ditambahkan | R-19 — **V-04 wajib merah** |
| M-12 | Satu bidang `kontrak.ts` diganti nama | R-19 — **V-03 wajib merah** |
| M-13 | Permintaan `/api/…` ditembolok service worker | R-15, C-07 |
| M-14 | KL-E menyatakan "tersimpan" saat simpanan lokal menolak | R-09, Bagian 5 |

M-10 s.d. M-12 yang membuktikan R-19: gerbang yang tidak pernah merah atas
kerusakan di `web/` tidak terbukti membacanya.

## 7. Urutan tugas

| | Tugas | Mengapa di sini |
|---|---|---|
| T-1 | Pemasangan paket, bagian `[npm]`, V-04 membaca `package-lock.json` | Tidak ada yang boleh dipasang sebelum pemeriksanya ada — pelajaran KB-079 dan KB-083 |
| T-2 | V-01 membaca `web/`, dengan satu uji asap | Gerbang berdiri sebelum isinya; M-10 dapat dipasang sejak hari itu |
| T-3 | `kontrak.ts`, `klien.ts`, pemeriksa kontrak dan rute | Bentuk data sebelum layar yang memakainya |
| T-4 | `mikrokopi.ts` dan perluasan pemeriksa C-13 | Teks sebelum layar yang menampilkannya |
| T-5 | Layar S-09 beserta KL-A, KL-B, KL-D, KL-E, KL-G dan draf | Inti fitur |
| T-6 | Gaya, aksesibilitas, cangkang luring, CSP, anggaran muat | Sifat seluruh halaman, bukan satu komponen |
| T-7 | Uji mutasi M-1 s.d. M-14 dan bukti ujung ke ujung | |
| T-8 | Penutupan: L8, D-00, catatan keputusan | |

## 8. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Kedelapan paket tidak dapat dipasang bersama tanpa paket tambahan | **Berhenti.** Paket tambahan menuntut persetujuan C-12 baru, bukan dipasang diam-diam |
| Layar ternyata membutuhkan perubahan backend | **Berhenti.** R-16; ajukan sebagai temuan |
| Bentuk tanggapan ternyata berbeda dari D-14 Bagian 4.1 | **Berhenti.** Itu cacat kontrak (C-20), bukan hal yang disesuaikan di sisi layar |
| Godaan menambah pustaka komponen agar lebih cepat | **Berhenti.** KB-123 sengaja tidak memintanya |
