# Tasks: 027-kerangka-web-dan-layar-tanya

| | |
|---|---|
| Spec | Gerbang 1 lolos 25 September 2026 (KB-124); cakupan disempitkan (KB-125) |
| Plan | Gerbang 2 lolos 27 September 2026 (KB-126) |
| Status | **Gerbang 3 lolos** — 27 September 2026 (KB-127). T-1 s.d. T-7 selesai (KB-134); satu tugas tersisa |
| Kebutuhan | R-01 s.d. R-20 kecuali R-11; C-12, C-13, C-20 |

Satu tugas = satu commit. Uji ditulis lebih dulu. `make check` lulus sebelum
tiap tugas dinyatakan selesai — dijalankan sebagai perintah berdiri sendiri,
tanpa pipa (KB-080). **Tidak satu baris pun berubah di `src/`** pada tugas
mana pun (R-16).

---

## T-1 · Pemeriksa paket npm lebih dulu, baru paketnya

**Kebutuhan:** R-19; C-12; KB-123.

Tidak ada yang dipasang sebelum pemeriksanya ada — pelajaran KB-079 dan KB-083.

- [x] Uji: `ketergantungan_npm.py` menolak ketergantungan langsung di luar
      `[npm].langsung`, dan menolak `package-lock.json` yang berbeda dari
      `[npm.terkunci]` — paket masuk, paket hilang, versi bergeser, termasuk
      **versi bersarang** (kunci berupa jalur di dalam lock, bukan nama)
- [x] Uji: tanpa `web/package.json` sama sekali, pemeriksa **melapor**, bukan
      lulus diam-diam
- [x] `web/package.json` dengan kedelapan paket, versi dipatok persis —
      **`vitest` 5.0.2, bukan 5.0.1** (lihat KB-127)
- [x] `npm install` sekali; **tidak ada paket langsung tambahan**.
      `@testing-library/dom` masuk sebagai peer wajib yang dipasang otomatis —
      transitif, dan dilaporkan terbuka
- [x] `ketergantungan-disetujui.toml` bertambah `[npm]` dan `[npm.terkunci]`
      (136 jalur), dibangkitkan dari lock yang sebenarnya
- [x] V-04 memanggil pemeriksa baru; `make setup` memasang `web/` dengan
      `npm ci`; `web/node_modules/` dan `web/dist/` masuk `.gitignore`
- [x] Mutasi M-11: paket di luar persetujuan ditambahkan → **V-04 merah**;
      ditambah mutasi versi bergeser di dalam lock → **V-04 merah**

---

## T-2 · V-01 membaca `web/`

**Kebutuhan:** R-19.

Gerbang berdiri sebelum isinya ada, sehingga M-10 dapat dipasang sejak hari ini.

- [x] `tsconfig.json` mode ketat; skrip `periksa` = `tsc --noEmit` lalu
      `vitest run`
- [x] Satu uji asap `web/`
- [x] V-01 menjalankan `npm --prefix web run periksa`; tanpa Node, V-01
      **gagal** dengan pesan yang menyebut cara memperbaikinya
- [x] Uji atas V-01 sendiri: galat tipe di `web/` dan uji `web/` yang gagal
      keduanya menjatuhkan V-01
- [x] Mutasi M-10: satu uji `web/` dibuat gagal → **V-01 merah**

---

## T-3 · Kontrak, klien, dan dua penjaga keselarasan

**Kebutuhan:** R-16, R-19; C-20; D-14 Bagian 4.1 dan 4.2.

- [x] Uji: `kontrak_web.py` menolak `kontrak.ts` yang nama bidangnya berbeda
      dari model `Tanggapan` — bidang hilang, bidang lebih, bidang berganti nama
- [x] Uji: `rute_terdaftar.py` menolak jalur `/api/v1/…` pada `web/src` yang
      bukan rute terpasang — **terpasang**, bukan sekadar tercantum D-14
- [x] `web/src/kontrak.ts` — tipe tanggapan dan bentuk galat
- [x] `web/src/klien.ts` — `fetch` disuntikkan; galat HTTP dan jaringan
      dipetakan ke keadaan layar, **tidak pernah** ke teks yang menyebut status
- [x] Mutasi M-12: satu bidang `kontrak.ts` diganti nama → **V-03 merah**

---

## T-4 · Mikrokopi dan C-13 atas teks layar

**Kebutuhan:** R-12; C-13; NFR-19; D-05 Bagian 10; K-2.

- [x] Uji: pemeriksa C-13 membaca tetapan `web/src/mikrokopi.ts` dan menolak
      kalimat > 20 kata, tanda seru, kata terlarang, kode galat
- [x] Uji: aturan bentuk menolak teks harfiah pada berkas `.tsx` di luar
      `mikrokopi.ts`
- [x] `web/src/mikrokopi.ts` — tidak-ditemukan memakai **kalimat pertama saja**
      (K-2, BT-71)
- [x] Mutasi M-8: teks harfiah disisipkan ke `.tsx` → **V-02 merah**

---

## T-5 · Layar S-09

**Kebutuhan:** R-01 s.d. R-10.

- [x] Uji: penanda dasar rujukan tampil **sebelum** ringkasan, berupa teks
- [x] Uji: ringkasan paling banyak tiga butir
- [x] Uji: `tidak_ditemukan` dan `di_luar_domain` memakai **komponen yang sama**
      dengan jawaban normal; penafian tampak pada ketiga keadaan
- [x] Uji: sitasi memuat judul, tahun, bagian; penanda keberlakuan bila bukan
      `berlaku`; `catatan_keberlakuan` bila terisi
- [x] Uji: bacaan lanjutan pada blok terpisah beserta keterangannya
- [x] Uji: KL-A kerangka, KL-B kosong pertama, KL-D galat tanpa kode, KL-E
      luring
- [x] Uji: draf pertanyaan bertahan sesudah kiriman gagal dan sesudah muat
      ulang; KL-E menyatakan tersimpan **hanya bila simpanan lokal menerimanya**
- [x] Komponen layar dan `web/src/draf.ts`
- [x] Mutasi M-1 s.d. M-7 dan M-14

---

## T-6 · Sifat seluruh halaman

**Kebutuhan:** R-13, R-14, R-15, R-17, R-18, R-20.

- [x] Uji: rasio kontras WCAG setiap pasangan token huruf-latar ≥ 4,5;
      huruf dasar ≥ 16px; sasaran ketuk ≥ 44px
- [x] Uji: keputusan tembolok service worker — cangkang ditembolok,
      `/api/…` **tidak pernah**
- [x] Uji: `index.html` memuat CSP `'self'` dan tanpa URL pihak ketiga;
      sumber `web/src` tanpa URL mutlak
- [x] Uji: tanpa artefak autentikasi — tidak ada token maupun sandi disimpan
- [x] V-01 memeriksa anggaran muat 150 KB terkompresi atas hasil `vite build`
- [x] `gaya.css`, `manifest.webmanifest`, `sw.js`
- [x] Mutasi M-9 dan M-13

---

## T-7 · Uji mutasi lengkap dan bukti ujung ke ujung

**Kebutuhan:** `plan.md` Bagian 6.

- [x] M-1 s.d. M-14 dijalankan sebagai satu putaran; yang tidak menyala
      **dilaporkan beserta sebabnya**
- [x] Layar dibuka dengan Playwright global terhadap `make jalan`;
      tangkapan layar keadaan normal, tidak-ditemukan, dan luring disimpan
- [x] `git diff --stat` atas `src/` sejak Gerbang 3: **kosong**

---

## T-8 · Penutupan

- [ ] `logbook/L8` catatan akhir fitur — juga bila tagihan pasal tidak menyusut
- [ ] `docs/hki/dokumentasi-teknis.md`: wadah "Aplikasi web" berpindah dari
      *Dirancang* ke keadaan yang sebenarnya
- [ ] Catatan keputusan pada `logbook/L4`

---

## Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Kedelapan paket menuntut paket tambahan | Berhenti; persetujuan C-12 baru |
| Layar ternyata butuh perubahan backend | Berhenti; R-16, ajukan sebagai temuan |
| Bentuk tanggapan berbeda dari D-14 Bagian 4.1 | Berhenti; cacat kontrak C-20 |
| Godaan menambah pustaka komponen | Berhenti; KB-123 |
