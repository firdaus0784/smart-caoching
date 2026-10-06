# Plan: 035-analitik-penelitian

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 6 Oktober 2026 (KB-215); P-1 s.d. P-5 sesuai anjuran |
| Status | **Lolos Gerbang 2–3** atas pendelegasian KB-168 — 6 Oktober 2026 (KB-216). Tujuh tugas pada `tasks.md` |
| Kebutuhan | R-01 s.d. R-08 `spec.md`; FR-J03, FR-J04; C-04, C-05, C-09, C-12, C-14, C-17, C-20 |

## 1. Letak dan batas

```
perkakas/basis_data/
  01-peran-dan-basis-data.sql   + peran_analitik
  12-analitik.sql               baru — telemetri.ekspor; hak peran_analitik;
                                baca waktu peristiwa dan ekspor bagi peran_penarikan
src/penyimpanan/analitik.py     baru — peristiwa per rentang, catat ekspor
src/penyimpanan/penarikan.py    + ekspor_terkait
src/telemetri/ekspor.py         ke_csv menerima baris berbidang sama (Protocol)
src/api/analitik.py             baru — metrik D-01 9.1, model tanggapan bernama
src/api/aplikasi.py             GET /analitik/ringkas, POST /analitik/ekspor
perkakas/penarikan.py           daftar menyebut ekspor terkait (P-4 B)
perkakas/jalankan_lokal.py      penyimpan analitik sebagai peran_analitik
web/src/analitik/               baru — S-18
web/src/Aplikasi.tsx            peneliti dikenali seperti kurator (P-5)
docs/                           D-14 4.8 dan 5.1; D-00
```

**`src/rag/`, `src/llm/`, `src/ingest/`, `src/pengguna/` tidak disentuh.**
Metrik tinggal di `src/api/analitik.py`, bukan di `src/telemetri/`: tepi
`telemetri → penyimpanan` tidak ada pada AGENTS.md, dan menambahkannya bukan
keputusan fitur ini. `src/telemetri/ekspor.py` diubah hanya agar CSV fitur 012
dapat ditulis dari baris tersimpan tanpa membentuk `Peristiwa` di luar gerbang
`rekam()` (pemeriksa C-04).

## 2. K-1 · Peran dan tabel ekspor

| Peran | Hak | Tidak memegang |
|---|---|---|
| `peran_analitik` (baru) | `SELECT` atas `telemetri.peristiwa`; `SELECT`, `INSERT` atas `telemetri.ekspor` | skema lain; `UPDATE`/`DELETE`; `CONNECT` basis data pseudonim |
| `peran_penarikan` (ada) | + `SELECT (waktu)` atas peristiwa; `SELECT (nomor, diekspor_pada, dari, sampai)` atas ekspor | ubah atau hapus ekspor |

```sql
telemetri.ekspor (
  nomor bigint identity, peneliti text, diekspor_pada timestamptz,
  dari date, sampai date, termasuk_pengembangan boolean, jumlah_baris integer
)
```

Tambah-saja: catatan ekspor adalah jejak ke mana data pergi, dan jejak yang
dapat diubah tidak menjejak apa pun. `peneliti` berpola pseudonim (C-05).

## 3. K-2 · Metrik — dihitung saat diminta

Dari seluruh peristiwa **selain** `versi_aplikasi = pengembangan` (R-05),
dengan tanggal WIB.

| Metrik | Definisi |
|---|---|
| Aktif harian | Pseudonim berbeda yang berperistiwa pada tiap tanggal |
| Aktif mingguan | Sama, per pekan Senin–Minggu WIB |
| Retensi D-N, N ∈ {1, 7, 30} | Kohort = tanggal peristiwa pertama pseudonim. Penyebut: kohort dengan tanggal + N ≤ hari ini. Pembilang: yang berperistiwa **tepat** pada tanggal + N. Tanpa penyebut → rasio `null`, bukan 0 |
| Panjang sesi | Dari `durasi_menit` pada `session_end` yang membawanya: jumlah, median, rerata |
| Rasio penemuan | `discovery_opened` / `discovery_served`; `null` tanpa penyebut |
| Belum terukur | Rasio penuntasan, penelusuran sumber (TK-73); verifikasi, komitmen (031); akurasi QA (TK-77) — masing-masing dengan sebab bernama |
| Integritas | Jumlah per kode, per versi aplikasi, per versi model; waktu pertama dan terakhir; jumlah peristiwa `pengembangan` terpisah |

## 4. K-3 · Bentuk rute (D-14 Bagian 4.8)

| Rute | Permintaan | Tanggapan |
|---|---|---|
| `GET /analitik/ringkas` | — | 200 JSON bernama `RingkasanAnalitik` (Bagian 3) |
| `POST /analitik/ekspor` | `{"dari": "YYYY-MM-DD", "sampai": "YYYY-MM-DD", "termasuk_pengembangan": false}` | 200 `text/csv`, `Content-Disposition: attachment`; kolom `KOLOM` fitur 012 |

Rentang inklusif tanggal WIB; `dari` > `sampai` 400. Setiap ekspor tercatat
**sebelum** berkasnya dikirim — ekspor yang gagal tercatat lebih aman daripada
ekspor yang terkirim tanpa jejak. Peran selain `peneliti` 403 (R-01).

## 5. K-4 · Perkakas penarikan menyebut ekspor terkait (P-4 B)

`daftar` menambahkan pada tiap permintaan tertunda: nomor ekspor yang rentang
tanggalnya memuat satu atau lebih peristiwa pseudonim itu. Tanpa pseudonim
pada keluaran (R-09 fitur 033).

## 6. K-5 · S-18

Peneliti dikenali sesudah 403 pada ringkasan akun dan antrean kurasi: `GET
/analitik/ringkas` 200 membuka S-18. Satu halaman tabel, tanpa navigasi
pengguna; isian rentang tanggal dan tombol unduh CSV. Angka `null` tampil
sebagai "belum dapat dihitung", metrik belum terukur sebagai sebabnya —
tidak pernah nol.

## 7. Keputusan rancangan Gerbang 2

| Kode | Pertanyaan | Putusan |
|---|---|---|
| K-1 | Peran dan jejak | `peran_analitik` baca peristiwa saja; `telemetri.ekspor` tambah-saja — Bagian 2 |
| K-2 | Letak metrik | `src/api/analitik.py`, dihitung saat diminta — Bagian 3 |
| K-3 | Bentuk rute | Bagian 4 |
| K-4 | Ekspor dan penarikan | Bagian 5 (P-4 B) |
| K-5 | Layar | Bagian 6 (P-5) |

## 8. Uji

### 8.1 Di dalam `make check`

- Penolakan peladen atas `peran_analitik` dengan sebab `permission denied`;
  katalog hak persis; batasan tabel ekspor
- Metrik atas peristiwa buatan yang jawabannya dihitung tangan, termasuk
  kohort di batas hari ke-N dan kohort yang belum berumur
- Lewat HTTP: 403 bagi selain peneliti; ekspor tercatat; CSV berkolom model;
  `pengembangan` terpisah
- Perkakas penarikan menyebut ekspor terkait tanpa pseudonim
- Layar: tabel, `null` bukan nol, unduhan

### 8.2 Di luar `make check`

Playwright terhadap `make jalan`: pengguna beraktivitas dengan persetujuan;
peneliti membuka S-18, membaca angka, mengunduh CSV; perkakas penarikan
menyebut ekspor itu bagi permintaan tertunda.

### 8.3 Uji mutasi

| Kode | Mutasi | Uji yang wajib merah |
|---|---|---|
| M-1 | `GRANT SELECT` atas `akun.pengguna` kepada `peran_analitik` | penolakan peladen |
| M-2 | Retensi "pada atau sesudah" hari ke-N | retensi tepat |
| M-3 | Kohort yang belum berumur masuk penyebut | penyebut retensi |
| M-4 | Peristiwa `pengembangan` tercampur | metrik dan ekspor |
| M-5 | Metrik tanpa penyebut bernilai 0 | `null` |
| M-6 | Ekspor tidak tercatat | catatan ekspor |
| M-7 | Kolom ekspor ditulis tangan dan bertambah | kolom = model |
| M-8 | Perkakas tidak menyebut ekspor terkait | daftar |
| M-9 | Rute analitik terbuka bagi `pengguna` | 403 |
| M-10 | Layar menampilkan nol bagi angka `null` | uji layar |

## 9. Urutan tugas

| Tugas | Isi |
|---|---|
| T-1 | Kontrak: D-14 4.8 dan 5.1; D-00 |
| T-2 | Peladen: `12-analitik.sql`, `peran_analitik`; M-1 |
| T-3 | `src/penyimpanan/analitik.py`; `ke_csv` atas baris; M-7 |
| T-4 | Metrik dan rute; M-2, M-3, M-4, M-5, M-6, M-9 |
| T-5 | Perkakas penarikan menyebut ekspor; M-8 |
| T-6 | S-18; M-10 |
| T-7 | Titik jalan, bukti Playwright, penutupan: L8, HKI, L4 |

## 10. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Rute baru tampak perlu | Berhenti; AG-02 |
| Pustaka grafik atau Parquet tampak perlu | Berhenti; C-12 |
| Analitik tampak perlu membaca akun, profil, atau riwayat | Berhenti; C-05 |
| Hasil analitik tampak perlu dipakai menyesuaikan layanan | Berhenti; C-14 |
