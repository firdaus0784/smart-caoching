# Tasks: 014-pemeriksa-konsistensi-dokumen

Ditinjau manusia sebelum kode ditulis. Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md` |
| Plan | `plan.md` |
| Status | Selesai — menunggu Gerbang 4 |
| Jumlah tugas | **7** — jauh di bawah ambang ±30 |

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| T-1 | Pengurai register `docs/D00.md` Bagian 2 menjadi pemetaan kode ke versi | Uji: register contoh terurai benar. **Uji: register tak terbaca → gagal, bukan bersih** | R-08 | [x] |
| T-2 | Pengurai versi pada kepala dokumen, menerima `Versi` maupun `Versi dokumen` dan keterangan di belakang angka | Uji: enam bentuk kepala yang benar-benar dipakai `docs/` terurai; bentuk tanpa versi → gagal | R-01 | [x] |
| T-3 | Bandingkan versi kepala dengan register | Uji: satu dokumen diberi versi berbeda → tertangkap | R-01 | [x] |
| T-4 | Bandingkan versi kepala dengan baris teratas riwayat revisi | Uji: riwayat tertinggal satu versi → tertangkap | R-02 | [x] |
| T-5 | Bandingkan daftar dokumen pada register dengan isi `docs/` | Uji: berkas dihapus → tertangkap; berkas asing ditambah → tertangkap | R-03, R-04 | [x] |
| T-6 | Kode `TK-xx` dan `ADR-xx` yang dirujuk tanpa definisi | Uji: rujukan ke `TK-99` → tertangkap; rujukan ke `TK-07` yang ada → lolos | R-05 | [x] |
| T-7 | Sambungkan ke V-03; perbarui `docs/D12.md` Bagian 7 dan register `docs/D00.md` | Uji: `make check` menjalankan pemeriksa. **Uji mutasi:** versi diubah buatan pada satu dokumen → `make check` gagal | R-06, R-07 | [x] |

## Urutan

T-1 dan T-2 adalah pengurai yang dipakai T-3 s.d. T-6, sehingga keduanya
mendahului. T-7 terakhir karena ia menyambungkan seluruhnya ke gerbang, dan
menyambungkan pemeriksa yang belum lengkap akan menghasilkan gerbang yang
lulus karena tidak memeriksa apa pun.

## Verifikasi akhir

- [x] `make check` lulus
- [x] `make compliance` lulus — keadaan pasal tidak berubah; fitur ini perkakas
- [x] R-01 s.d. R-08 punya uji yang lulus
- [x] Cakupan tidak turun dari 98,9%
- [x] Uji mutasi dijalankan dan dilaporkan pada uraian commit
- [x] Dijalankan terhadap `docs/` sebenarnya → bersih
