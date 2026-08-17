# Tasks: 011-penemuan-dan-penerapan

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 (KB-059) |
| Plan | `plan.md`, lolos Gerbang 2 (KB-059) |
| Status | Lolos Gerbang 3 (KB-059) |
| Jumlah tugas | **4** |
| Ketergantungan baru | **Nol** |

## Fase A · Komitmen dan penerapannya — TK-51

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `src/pengguna/komitmen.py` — niat pelaksanaan, status penerapan | **Uji: `Komitmen` tidak memiliki bidang teks bebas tunggal.** Uji: `isyarat` dan `tindakan` keduanya wajib, tanpa bawaan. Uji: `TIDAK_JADI` menuntut alasan; tiga lainnya tidak | R-11 s.d. R-14, R-16 | [x] — niat pelaksanaan dua bidang; bidang bebas ditolak dua lapis; M-1, M-2, M-6, M-7, M-9 menyala |
| A-2 | Jurnal belajar dan ekspor tertahan | **Uji: ketiga bagian FR-H06 ada.** Uji: ekspor PDF menyatakan alasan tertahannya, bukan tidak ada | R-15 | [ ] |

**A-1 adalah TK-51 itu sendiri.** Bila bentuknya longgar, sistemnya tetap
patuh konstitusi dan **penelitiannya yang kehilangan dasar** — rasio penerapan
diukur atas mekanisme yang tidak menanggung bukti yang dikutip untuk
membenarkannya.

## Fase B · Feed penemuan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | `src/pengguna/feed.py` — penyaringan prioritas, pagu tayang, label sumber | **Uji: butir di luar prioritas tidak tayang.** Uji: pagu memakai tetapan fitur 010, bukan angka kedua. Uji: butir berlisensi tertutup tidak pernah membawa teks penuh | R-01 s.d. R-08 | [ ] |
| B-2 | Tepi `pengguna → ingest` pada `AGENTS.md`; uji ketiadaan gamifikasi | **Uji: pemeriksa arah menerima tepi baru dan tetap menolak arah sebaliknya.** Uji: tidak ada poin, lencana, papan peringkat, pertemanan — C-15 | R-18 | [ ] |

**B-2 menguji C-15 sebagai ketiadaan.** Jurnal belajar dengan rekapitulasi
adalah tempat lencana terasa paling wajar, dan C-15 melarang membuatnya
"kosong pun tidak".

## Verifikasi akhir

- [ ] `make check` lulus 6 gerbang **dan dijalankan sesudah entri logbook ditulis** (KB-058)
- [ ] `make lint` hijau
- [ ] `make compliance` tetap 17 lulus / 0 gagal / 3 belum
- [ ] Kesembilan uji mutasi `plan.md` Bagian 7 dijalankan; hasilnya dilaporkan apa adanya
- [ ] Cakupan uji tidak turun
- [ ] **Nol ketergantungan baru**

## Yang tidak dikerjakan di sini

Seluruh layar (`web/`), isi *knowledge check* (kurator), FR-H05 lampiran bukti
(C-12), FR-H07 ekspor PDF (C-12), FR-G09 kalender manajerial (D-02 Bagian 5
belum terbaca mesin), penyimpanan tetap (C-12).
