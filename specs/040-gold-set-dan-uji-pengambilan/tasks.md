# Tasks: 040-gold-set-dan-uji-pengambilan

| | |
|---|---|
| Spec | Gerbang 1 lolos 13 Oktober 2026 (KB-291); P-1 s.d. P-6 sesuai anjuran |
| Plan | Gerbang 2 lolos 13 Oktober 2026 atas pendelegasian KB-168 (KB-292); K-1 s.d. K-8 |
| Status | **Gerbang 4 lolos** — 13 Oktober 2026 (KB-301). Delapan dari delapan tugas selesai |
| Kebutuhan | R-01 s.d. R-08; D-08 Bagian 5 dan 6 (U3); BT-35; KL-01; AP-01 s.d. AP-07; C-09, C-16, C-17, C-20 |

Satu tugas = satu commit. Uji ditulis lebih dulu dan dijalankan merah sebelum
implementasinya. `make check` lulus sesudah entri L4 ditulis, tepat sebelum
commit. **`src/api/`, `src/penyimpanan/`, `src/ingest/`, `src/llm/`,
`src/logbook/`, `src/pengguna/`, `src/telemetri/`, `web/`, dan
`perkakas/basis_data/` tidak berubah.** Tanpa rute, peran, hak, atau paket
baru (R-08, C-12, C-20). Isi *gold set* sungguhan dan ambang tidak dibuat di
mana pun (D-08 Bagian 5.2, C-16). Uji dan bukti tidak menulis ke `logbook/` repositori selain entri L4.

---

## T-1 · Kontrak lebih dulu

**Kebutuhan:** R-01 s.d. R-04, R-06; K-8; P-1 A, P-2 A, P-5 A, P-6 A.

- [x] D-08 Bagian 5.3 baru: bentuk berkas, satuan dan pencocokan kunci, batas
      dokumen tanpa pasal, sidik, pembekuan, penyimpanan di luar repositori
- [x] D-08 Bagian 6: aturan pelaksanaan metrik; konfigurasi dinyatakan;
      putaran satu sumber tidak menyatakan U3 lulus
- [x] D-10 Bagian 3 `tugas` dan Bagian 4 baris *gold set*
- [x] Register D-00

## T-2 · Bentuk *gold set* dan sidik

**Kebutuhan:** R-02, R-03, R-07; K-1, K-3; P-1 A, P-6 A.

- [x] Uji lebih dulu: aturan jenis dan kunci; kategori; `bernomor_regulasi`
      wajib; pesan galat tanpa teks; enam jenis dan komposisi dibaca dari
      tabel D-08 Bagian 5.1; sidik tetap terhadap urutan dan berubah terhadap
      isi
- [x] `src/rag/evaluasi/gold_set.py`
- [x] Mutasi M-4, M-5

## T-3 · Kunci dan pemeriksaan korpus

**Kebutuhan:** R-02; K-2; P-2 A.

- [x] Uji lebih dulu: satuan penanda fitur 038; sama persis, bukan awalan;
      kunci di bawah pasal ditolak; dokumen di luar korpus dan bagian tanpa
      segmen
- [x] `src/rag/evaluasi/kunci.py`
- [x] Mutasi M-3

## T-4 · Metrik

**Kebutuhan:** R-04; K-4; P-5 A, AP-03, AP-06.

- [x] Uji lebih dulu: contoh yang dihitung tangan bagi setiap metrik; k dan
      kebocoran nol dibaca dari tabel D-08 Bagian 6; setiap kunci; penyebut
      nol; pemangkasan satu desimal; per jenis dan per kategori
- [x] `src/rag/evaluasi/metrik.py`
- [x] Mutasi M-7, M-8

## T-5 · Pengukur

**Kebutuhan:** R-05; K-5; P-4 A.

- [x] Uji lebih dulu: tiga sebab luput; kunci hilang tetap di penyebut;
      kebocoran dari sumber atas indeks metadata; pertanyaan C dan D ikut
      dicari; konfigurasi dinyatakan; dua putusan
- [x] `src/rag/evaluasi/pengukur.py`
- [x] Mutasi M-6, M-9

## T-6 · Logbook

**Kebutuhan:** R-03, R-06, R-07; K-6; AP-05.

- [x] Uji lebih dulu: `VersiGoldSet` menjumlah, berzona, sidik berbentuk;
      pembaca atas berkas ada dan tidak ada; L1 berbidang versi lengkap dan
      lulus pemeriksa catatan versi; pembukaan dihitung; pembekuan dicari
      menurut sidik
- [x] `src/rag/evaluasi/jejak.py` — `src/logbook/` tidak disentuh (KB-298)

## T-7 · Perkakas

**Kebutuhan:** R-01 s.d. R-08; K-7.

- [x] Uji lebih dulu atas PostgreSQL sebagai peran sungguhan: `periksa`,
      `bekukan`, `ukur`; komposisi menyimpang ditolak; belum beku ditolak tanpa
      baris L1; ditolak peladen tercatat gagal; kebocoran berkode 3; keluaran
      dan L1 tanpa teks; berkas di dalam repositori ditolak
- [x] `perkakas/evaluasi.py`
- [x] Mutasi M-1, M-2, M-10, M-11, M-12

## T-8 · Bukti, penutupan

- [x] Bagian 11.2 plan; keluaran ke `bukti/`
- [x] Putaran mutasi dilaporkan apa adanya; L8, dokumen HKI, L4; status
      menunggu Gerbang 4
