# Tasks: 005-ontologi-skema-dan-ekspor

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 |
| Plan | `plan.md`, lolos Gerbang 2 |
| Status | **Lolos Gerbang 3** — 10 Agustus 2026 (KB-032) |
| Cakupan | **Bagian 1 saja** — pengisian ontologi menjadi fitur 018 |
| Jumlah tugas | **4** |
| Ketergantungan baru | **Nol** |

## Fase A · Skema

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `JenisRelasi`, `Konsep`, `Relasi` | Uji: tujuh jenis persis FR-E02. **Uji: konsep tanpa dokumen sumber tidak dapat dibentuk.** Uji: relasi tanpa dokumen rujukan sendiri tidak dapat dibentuk | R-01, R-02, R-04 | [ ] |
| A-2 | `Ontologi` — relasi menunjuk konsep yang ada | **Uji: relasi ke konsep yang tidak ada ditolak** | R-05 | [ ] |

## Fase B · Hitung dan ekspor

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | **Jumlah sah dan mentah, dilaporkan terpisah** | **Uji: konsep tanpa definisi tidak terhitung sah tetapi terhitung mentah.** Uji: konsep dari karantina tidak terhitung sah | R-03, R-06, R-07 | [ ] |
| B-2 | Ekspor JSON-LD beserta pencatatannya | Uji: hasil dapat diurai dan memuat konteks bernama. **Uji: konsep tak sah tidak masuk ekspor.** Uji: ontologi kosong ditolak | R-08, R-09, R-10 | [ ] |

**B-1 adalah tugas terpenting fitur ini, dan ia tentang cara melapor bukan cara
menghitung.** Laporan yang hanya menyebut "512 konsep" tidak dapat dibedakan
antara 512 konsep berdefinisi dan 512 baris tabel. MK-06 adalah syarat
Definisi Selesai dengan tenggat bulan 8, dan menambah baris jauh lebih cepat
daripada menyusun definisi.

## Verifikasi akhir

- [ ] `make check` lulus 6 gerbang
- [ ] `make compliance` tidak berubah — 9 lulus, 0 gagal, 11 belum
- [ ] Keenam uji mutasi `plan.md` Bagian 4 dijalankan dan dilaporkan
- [ ] Cakupan uji tidak turun
- [ ] **Nol ketergantungan baru**
