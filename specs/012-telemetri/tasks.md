# Tasks: 012-telemetri

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 (KB-048) |
| Plan | `plan.md`, lolos Gerbang 2 (KB-048) |
| Status | **Lolos Gerbang 4** (KB-049) |
| Jumlah tugas | **5** |
| Ketergantungan baru | **Nol** |

## Fase A · Peristiwa

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `peristiwa.py` — taksonomi + enam bidang FR-J02 | **Uji: kode peristiwa dibaca dari `docs/D01.md` Bagian 9, bukan disalin.** Uji: tidak ada bidang `id_pengguna`. Uji: kode di luar taksonomi ditolak | R-01, R-02, R-03, R-09 | [x] — dua puluh kode dibaca dari D-01; tanpa bidang `id_pengguna` |
| A-2 | Penjagaan `properti` dua arah | **Uji: nilai bermuatan nomor ditolak DAN kunci beridentitas ditolak** — keduanya, sebab kunci beridentitas lolos pendeteksi pola | R-06 | [x] — nilai, kunci, sarang, dan daftar; galat berhenti membocorkan masukan lewat `hide_input_in_errors` |

## Fase B · Gerbang C-04

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | `gerbang.py` — perekaman menuntut persetujuan aktif | **Uji: hanya `DIBERIKAN` yang merekam; ketiga keadaan lain tidak.** Uji: pencabutan di tengah rangkaian menghentikan seketika. Uji: `DITOLAK_PROPERTI` bukan `DILEWATI_TANPA_PERSETUJUAN` | R-04, R-05, R-07 | [x] — keadaan diterima tiap panggilan dan tidak punya tempat disimpan; urutan pemeriksaan dinyatakan; M-1 s.d. M-4 menyala |

**B-1 adalah C-04 itu sendiri.** Keadaan persetujuan diterima **tiap
panggilan**, bukan disimpan — salinan yang diambil saat sesi dibuka membuat
"seketika" berubah menjadi "pada sesi berikutnya" tanpa seorang pun mengubah
satu baris.

## Fase C · Ekspor dan pemeriksa

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | `ekspor.py` — CSV; Parquet dinyatakan tertahan | **Uji: kolom ekspor tidak memuat identitas.** Uji: ketiadaan Parquet dinyatakan, bukan diam | R-08, R-03 | [x] — kolom diturunkan dari model; Parquet dinyatakan tertahan lewat fungsi yang dapat dipanggil |
| C-2 | Pemeriksa C-04; pemindahannya pada `daftar_pasal.py` | **Uji: `make compliance` menyusut satu — 16 lulus, 4 belum.** Uji: ketiga aturan menyala terpisah pada pohon yang dirusak | R-04 | [x] — tiga aturan diuji terpisah pada pohon yang dirusak; tagihan 15 → 16 |

**Aturan 3 pemeriksa menutup dua yang pertama**: gerbang yang parameter
keadaannya berbawaan `DIBERIKAN` memuaskan keduanya sambil membatalkan C-04
pada setiap pemanggilan yang lupa mengisinya.

## Verifikasi akhir

- [x] `make check` lulus 6 gerbang
- [x] `make compliance` **menyusut satu** — 16 lulus, 0 gagal, **4** belum
- [x] Kesepuluh uji mutasi `plan.md` Bagian 4 dijalankan; hasilnya dilaporkan apa adanya — M-1 s.d. M-10 seluruhnya menyala; empat mutasi tambahan
- [x] Cakupan uji tidak turun — 99,84 → 99,85 atas 2.875 pernyataan
- [x] **Nol ketergantungan baru**
- [x] `AGENTS.md` bertambah satu baris arah bagi `src/telemetri/`

## Yang tidak dikerjakan di sini

Panel analitik FR-J04, metrik turunan D-01 Bagian 9.1, dan ekspor Parquet.
Sesudah fitur ini, **empat pasal tersisa dan tiga di antaranya menunggu
`web/`** — C-01 (fitur 020), C-13 (013), C-14 (010 s.d. 013). Yang keempat,
C-10, sudah dibangun sejak fitur 003.
