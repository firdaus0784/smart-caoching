# Tasks: 021-rute-tanya

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 (KB-052) |
| Plan | `plan.md`, lolos Gerbang 2 (KB-052) |
| Status | Lolos Gerbang 3 (KB-052) |
| Jumlah tugas | **5** |
| Ketergantungan baru | **Nol** |

## Fase A · Kendali peran

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `src/api/peran.py` — keenam peran D-14 Bagian 3 dan tabel rute | **Uji: tabel dibaca dari `docs/D14.md`, bukan disalin ke uji.** Uji: setiap rute D-14 punya peran. Uji: rute yang tidak ada di D-14 ditolak (AG-02) | R-01 s.d. R-04 | [x] — 29 rute D-14 Bagian 3 ditulis penuh; tabel dibaca dari dokumen dua arah; M-6 dan M-7 menyala |
| A-2 | Pemeriksa kendali peran pada `perkakas/` | **Uji: pemeriksa menyala ketika satu rute dihapus dari tabel DAN ketika satu rute dikarang** | R-02, R-03 | [x] — menyapu untai jalur API di seluruh `src/`, bukan mengulang uji `PETA_RUTE`; berjalan pada V-03 bersama pemeriksa arah |

**A-1 diuji dua arah, dan keduanya perlu.** Arah pertama menangkap rute yang
bertambah pada D-14; arah kedua menangkap rute yang dikarang pada kode. Satu
arah saja meninggalkan lubang yang bentuknya persis kebalikan dari yang dijaga.

## Fase B · Jalur penjawaban

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | `src/api/tanya.py` — `HasilTanya`, `AlasanBerhenti`, `jawab()` | **Uji: bukti tidak cukup TIDAK memanggil model** — dihitung adaptor tiruan, bukan disimpulkan dari kembalian. Uji: di luar domain berhenti sebelum pengambilan. Uji: keluaran yang ditahan validator tidak menjadi tanggapan | R-05 s.d. R-09, R-12 | [ ] |
| B-2 | Pemeriksa bentuk `HasilTanya` dan tepi `api → llm` pada `AGENTS.md` | **Uji: `HasilTanya` tidak dapat dibentuk di luar modulnya.** Uji: pemeriksa arah menerima tepi baru dan tetap menolak arah sebaliknya | R-06, R-10, R-11 | [ ] |

**B-1 adalah tempat C-17, C-18, dan C-19 bertemu satu urutan.** Ketiganya
dijaga lapisannya masing-masing hari ini; yang dibangun di sini adalah tempat
yang membuat melewatinya tidak mungkin, bukan sekadar salah.

**Uji "tidak memanggil model" tidak dapat digantikan uji nilai kembalian.**
Implementasi yang memanggil model lalu membuang hasilnya mengembalikan nilai
yang sama persis. Yang membedakan hanya apakah panggilannya terjadi — dan itu
biaya, jejak `logbook/`, serta satu kesempatan bagi C-18 untuk dilanggar.

## Fase C · Riwayat percakapan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | `src/api/percakapan.py` — FR-F09 | **Uji: riwayat menyimpan `id_pesan`, bukan salinan `Tanggapan`.** Uji: tambah-saja — permukaan tanpa cara menyunting maupun menghapus | R-13, R-14 | [ ] |

**C-1 melarang menyimpan salinan, dan itu bukan penghematan.** Tanggapan yang
tersimpan menua: status keberlakuan sitasinya berubah ketika regulasinya
dicabut, dan riwayat yang menayangkan salinan lama melanggar C-07 lewat pintu
yang tidak dijaga siapa pun.

## Verifikasi akhir

- [ ] `make check` lulus 6 gerbang
- [ ] `make compliance` **tetap 17 lulus / 0 gagal / 3 belum** — tidak satu pun
      pasal berpindah di sini, dan bila ia berpindah berarti ada yang keliru
- [ ] Kesembilan uji mutasi `plan.md` Bagian 7 dijalankan; hasilnya dilaporkan
      apa adanya
- [ ] Cakupan uji tidak turun
- [ ] **Nol ketergantungan baru**

## Yang tidak dikerjakan di sini

Adaptor HTTP (C-12), penyimpanan tetap riwayat (C-12), isi FR-F12 (kurator),
sisi semantik pengambilan (019), VS-03/05/07 (020), penyaringan prioritas dan
perekaman peristiwa (011).

**Sesudah fitur ini, jalur penjawaban berjalan ujung ke ujung tanpa peladen.**
Yang tersisa bagi rute yang sungguh melayani permintaan adalah satu berkas
adaptor dan satu baris pada berkas persetujuan ketergantungan.
