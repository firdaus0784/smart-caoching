# Tasks: 005-ontologi-skema-dan-ekspor

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 |
| Plan | `plan.md`, lolos Gerbang 2 |
| Status | **Lolos Gerbang 4** — 10 Agustus 2026 (KB-033). Empat tugas selesai |
| Cakupan | **Bagian 1 saja** — pengisian ontologi menjadi fitur 018 |
| Jumlah tugas | **4** |
| Ketergantungan baru | **Nol** |

## Fase A · Skema

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `JenisRelasi`, `Konsep`, `Relasi` | Uji: tujuh jenis persis FR-E02. **Uji: konsep tanpa dokumen sumber tidak dapat dibentuk.** Uji: relasi tanpa dokumen rujukan sendiri tidak dapat dibentuk | R-01, R-02, R-04 | [x] |
| A-2 | `Ontologi` — relasi menunjuk konsep yang ada | **Uji: relasi ke konsep yang tidak ada ditolak** | R-05 | [x] — kedua ujung diperiksa, dan konsep berulang ditolak |

## Fase B · Hitung dan ekspor

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | **Jumlah sah dan mentah, dilaporkan terpisah** | **Uji: konsep tanpa definisi tidak terhitung sah tetapi terhitung mentah.** Uji: konsep dari karantina tidak terhitung sah | R-03, R-06, R-07 | [x] — dua angka selalu bersama; tidak ada bidang bernama `jumlah` saja |
| B-2 | Ekspor JSON-LD beserta pencatatannya | Uji: hasil dapat diurai dan memuat konteks bernama. **Uji: konsep tak sah tidak masuk ekspor.** Uji: ontologi kosong ditolak | R-08, R-09, R-10 | [x] |

**B-1 adalah tugas terpenting fitur ini, dan ia tentang cara melapor bukan cara
menghitung.** Laporan yang hanya menyebut "512 konsep" tidak dapat dibedakan
antara 512 konsep berdefinisi dan 512 baris tabel. MK-06 adalah syarat
Definisi Selesai dengan tenggat bulan 8, dan menambah baris jauh lebih cepat
daripada menyusun definisi.

## Verifikasi akhir

- [x] `make check` lulus 6 gerbang
- [x] `make compliance` tidak berubah — 9 lulus, 0 gagal, 11 belum
- [x] Keenam uji mutasi `plan.md` Bagian 4 dijalankan; seluruhnya menyala, ditambah tujuh mutasi lain
- [x] Cakupan uji tidak turun — 99% atas 1.668 pernyataan
- [x] **Nol ketergantungan baru** — tetap 10 langsung, 26 terkunci

## Yang menunggu fitur 018

FR-E01 (≥ 500 konsep, ≥ 1.000 relasi) dan FR-E04 (antarmuka graf). Keduanya
menunggu pakar domain dan bahan terkurasi — bukan kode.

Seluruh perkakas yang mereka butuhkan sudah berdiri: skema bertipe, aturan
hitung sah D-06 Bagian 11.2, dan ekspor JSON-LD berkonteks bernama. **Angka
MK-06 kini tidak dapat dipenuhi dengan konsep kosong**, dan selisih antara
jumlah sah dan mentah memberi tahu berapa banyak pekerjaan yang tersisa.
