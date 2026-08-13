# Tasks: 022-profil-dan-persetujuan

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 (KB-046) |
| Plan | `plan.md`, lolos Gerbang 2 (KB-046) |
| Status | **Lolos Gerbang 4** (KB-047) |
| Jumlah tugas | **5** |
| Ketergantungan baru | **Nol** |

## Fase A · Profil dan prioritas

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `profil.py` — enam bidang D-04 Bagian 7.1 | **Uji: bidang dibaca dari `docs/D04.md`, bukan disalin ke uji.** Uji: bidang ketujuh ditolak. Uji: pembaruan mencatat waktunya | R-02, R-10, R-12 | [x] — enam isian dari D-04; nama bidang mengikuti D-14; pendeteksi FR-B04 dipakai ulang, dan salinan ketiganya dihapus |
| A-2 | `prioritas.py` — 3–5 kategori K1–K8 berurutan | **Uji: 2 ditolak DAN 6 ditolak — kedua arah.** Uji: kategori kembar ditolak. Uji: `KategoriMasalah` dipakai ulang, tidak ditulis ulang | R-03, R-04 | [x] — kedua batas diuji; kembar dijaga tersendiri; urutan dihitung dari posisi; `KategoriMasalah` pemakaian ketiga |

**A-2 diuji dari kedua arah.** "Menerima 3 sampai 5" lulus juga pada
implementasi yang menerima berapa pun di atas 2, dan prioritas yang boleh
berjumlah sembilan membuat penyaringan feed FR-G01 tidak menyaring apa pun.

## Fase B · Persetujuan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | `persetujuan.py` — empat keadaan, sifat terhitung | **Uji: `DICABUT` tidak mengizinkan perekaman.** Uji: `BELUM_DIMINTA` dan `DITOLAK` tidak sama meski keduanya menghentikan. Uji: gabungan mustahil ditolak; `dicabut_pada` mendahului `tanggal` ditolak | R-05, R-06, R-08 | [x] — empat keadaan, dua pembedaan dijaga uji tersendiri; gabungan mustahil ditolak; M-1, M-2, M-4, M-10 menyala |
| B-2 | Ketiadaan pemetaan persetujuan ke akses | **Uji: permukaan modul tidak menyediakan cara menurunkan akses berdasarkan persetujuan** | R-07 | [x] — ketiadaan diuji tiga arah: permukaan tipe, daftar sifat, dan naskah modul |

**B-1 adalah prasyarat C-04.** `boleh_merekam` adalah satu-satunya sifat yang
fitur 012 kelak tanyakan, dan ia terhitung — bukan bidang yang dapat diisi.

**B-2 menegakkan sebuah ketiadaan**, dan itu satu-satunya cara R-07 dapat
diuji: larangan tidak terlihat dengan menjalankan apa pun.

## Fase C · Pemisahan pseudonim

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | `pseudonim.py` + pemeriksa C-05; pemindahannya pada `daftar_pasal.py` | **Uji: `make compliance` menyusut satu — 15 lulus, 5 belum.** Uji: ketiga aturan menyala terpisah pada pohon yang dirusak. Uji: `Area` tetap dua nilai | R-09 | [x] — kredensial bertipe tersendiri; ketiga aturan diuji terpisah pada pohon yang dirusak; tagihan 14 → 15 |

**Aturan 3 menutup dua aturan pertama.** Memindahkan peta pseudonim menjadi
nilai ketiga pada `Area` memuaskan keduanya sambil membatalkan C-05 — bentuk
yang sama dengan aturan VS-08 pada pemeriksa C-19.

## Verifikasi akhir

- [x] `make check` lulus 6 gerbang
- [x] `make compliance` **menyusut satu** — 15 lulus, 0 gagal, **5** belum
- [x] Kesepuluh uji mutasi `plan.md` Bagian 4 dijalankan; hasilnya dilaporkan apa adanya — M-1 s.d. M-10 seluruhnya menyala, dua sesudah uji ditambahkan; sembilan mutasi tambahan
- [x] Cakupan uji tidak turun — 99,83 → 99,84 atas 2.758 pernyataan
- [x] **Nol ketergantungan baru**
- [x] `AGENTS.md` bertambah satu baris arah bagi `src/pengguna/`
- [x] `KategoriMasalah` dipakai ulang — pemakaian ketiga, bukan definisi kedua

## Yang tidak dikerjakan di sini

Layar, rute, dan perekaman telemetri. FR-A04 menunggu `web/`; C-04 menunggu
fitur 012, yang kini memiliki sesuatu untuk diperiksa.
