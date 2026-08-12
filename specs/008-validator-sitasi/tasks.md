# Tasks: 008-validator-sitasi

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 (KB-036) |
| Plan | `plan.md`, lolos Gerbang 2 (KB-036) |
| Status | Menunggu Gerbang 3 |
| Jumlah tugas | **7** |
| Ketergantungan baru | **Nol** |

## Fase A · Kamus dan kontrak

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `src/kamus/segmen.py` — `IndeksTujuan`, `Peringkat`, `StatusKeberlakuan`; kekembaran dihapus | **Uji: hanya satu definisi `IndeksTujuan` pada seluruh `src/`.** Uji: `src/kamus/` tidak mengimpor lapisan lain. Uji: nilai persis D-14 Bagian 5 | — | [ ] |
| A-2 | `keluaran.py` — `Klaim`, `SegmenRujukan`, `KeluaranModel` sesuai D-14 Bagian 4.1 | **Uji: klaim tanpa `id_segmen` tidak dapat dibentuk** (VS-01 sebagai bentuk). Uji: bidang persis D-14, tanpa tambahan (AG-03) | R-01 | [ ] |
| A-3 | `pemeriksaan.py` — `KodePemeriksaan` sembilan kode, `Status` tiga nilai, `HasilPemeriksaan` | **Uji: `Status` bertiga nilai, bukan dua.** Uji: kesembilan kode persis D-07 Bagian 6.1. Uji: kode yang gagal ikut terbawa | R-08, R-10 | [ ] |

**A-1 memperbaiki kekeliruan saya pada fitur 006.** `IndeksTujuan` ditulis dua
kali; enum itu tempat C-02 terbaca, dan dua definisi berarti perubahan D-14
dapat memperbarui satu dan melewatkan yang lain tanpa satu uji pun gagal.

## Fase B · Pemeriksaan sitasi

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | VS-01 dan VS-02 — klaim tanpa dasar dan rujukan mengada-ada | Uji: id yang tidak ada di antara segmen terambil ditolak. **Uji: pemeriksaan dilakukan terhadap segmen terambil, bukan terhadap daftar id pada klaimnya sendiri** | R-01, R-02 | [ ] |
| B-2 | VS-04 dan VS-06 — segmen metadata dan regulasi dicabut | **Uji: seluruh jawaban dibuang, bukan klaimnya saja.** Uji: dicatat sebagai insiden kepatuhan | R-03, R-04 | [ ] |
| B-3 | VS-08 — klaim bersandar tunggal T3 atau T4 | **Uji: klaim ditopang T1 dan T3 sekaligus DITERIMA.** Uji: T3 dan T4 saja diturunkan menjadi bacaan lanjutan. Uji: VS-08 tidak menyentuh arti bidang BT-64 | R-05 | [ ] |

**B-3 adalah tugas terpenting bagi C-19, dan ujinya yang paling mudah keliru.**
Uji "T3 saja ditolak" dipenuhi juga oleh validator yang menolak setiap klaim
yang menyentuh T3 — dan validator semacam itu membuang jawaban yang sah, lalu
dilonggarkan orang. D-13 Bagian 6 mewajibkan klaim campuran: T3 *"boleh
menopang, tetapi klaim memerlukan segmen T1 atau T2"*.

## Fase C · Penyimpangan, penyusun, dan pemeriksanya

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | VS-09 — kontrak keluaran, tautan, bentuk instruksi | **Uji: tautan diperiksa terhadap metadata segmen terambil, bukan daftar ranah.** Uji: keluaran memuat instruksi dibuang tanpa perbaikan | R-07 | [ ] |
| C-2 | `validator.py` — penyusun, tabel tindakan 6.2, `JawabanTervalidasi` | **Uji: satu pemeriksaan belum-dapat-diperiksa → jawaban tidak tervalidasi.** **Uji: `tervalidasi` sifat terhitung, bukan bidang.** Uji: ringkasan kosong membatalkan jawaban. Uji: tidak menulis, tidak memanggil model | R-06, R-09, R-10, R-11, R-12 | [ ] |
| C-3 | Pemeriksa C-19; koreksi `fitur_pengunci` C-01 | **Uji: `make compliance` menyusut satu — 11 lulus, 9 belum.** Uji: ketiga aturan menyala pada pohon yang sengaja dirusak. Uji: alasan tunggu C-01 menyebut fitur 020 | R-05, R-09 | [ ] |

**C-2 adalah tempat TA-01 diulang atau ditutup.** Tiga dari sembilan
pemeriksaan tidak dapat dijalankan hari ini. Validator yang mengembalikan
`True` atas kesembilannya tidak dapat dibedakan dari validator yang benar — di
komponen yang D-04 ADR-04 sebut terpenting dalam sistem.

## Verifikasi akhir

- [ ] `make check` lulus 6 gerbang
- [ ] `make compliance` **menyusut satu** — 11 lulus, 0 gagal, **9** belum
- [ ] Kesembilan uji mutasi `plan.md` Bagian 6 dijalankan; hasilnya dilaporkan apa adanya
- [ ] Cakupan uji tidak turun
- [ ] **Nol ketergantungan baru**
- [ ] `AGENTS.md` memuat `src/kamus/` dan tepi `ingest → llm`
- [ ] `fitur_pengunci` C-01 dikoreksi menyebut fitur 020 dan VS-03

## Yang tidak dikerjakan di sini

VS-03, VS-05, dan VS-07 — **fitur 020**, dan ketergantungannya dua berbeda:
VS-03 dan VS-05 menunggu model sematan (fitur 019) serta ambang BT-29; VS-07
menunggu model NER (fitur 017), yang menunggu korpus teranotasi.

Pemindahan C-01 menunggu VS-03. Itu koreksi terhadap `daftar_pasal.py`, bukan
utang baru.
