# Tasks: 016-pembacaan-ekspor-label-studio

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 |
| Plan | `plan.md`, lolos Gerbang 2 |
| Status | **Lolos Gerbang 3** — 10 Agustus 2026 (KB-025) |
| Jumlah tugas | **9** — di bawah ambang ±30 |
| Ketergantungan baru | **Nol** |

## Fase A · Pembacaan ekspor

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `GalatBentukEkspor` dan penguraian tugas; bentuk yang dirusak gagal tegas | **Uji: salinan bahan sungguhan yang satu kuncinya dihapus → galat menyebut kunci itu.** Uji: penguraian sebagian tidak terjadi | R-02 | [x] |
| A-2 | Rentang dan putusan menjadi tipe fitur 003 | Uji terhadap `tests/bahan/ekspor-label-studio-1.23.json`; **uji: rentang diperiksa terhadap teks dokumennya** | R-01, R-03 | [x] — dua uji A-6 datang lebih awal; jalurnya sudah dilalui A-2 |
| A-3 | `versi_skema` dari pemanggil; **uji: tidak ditebak dari berkas** | Uji: impor tanpa versi skema tidak dapat dipanggil | R-04 | [x] — tugas beruji saja; tanda tangannya sudah menuntutnya sejak A-2 |
| A-4 | `status_pra_anotasi` diturunkan dari `predictions` | Uji: tugas ber-`predictions` → `DENGAN_PRA_ANOTASI`; tanpa → `TANPA_PRA_ANOTASI` | R-05 | [x] |
| A-5 | **`bendera` dan `bendera_terkumpul`** | **Uji: proyek tanpa kendali bendera tidak menghasilkan korpus yang terbaca bersih** | R-06 | [x] — `None` berarti tidak terkumpul; himpunan kosong berarti diperiksa dan bersih |
| A-6 | Kode anotator anonim dari tabel pemanggil; `anotasi_ganda` | **Uji: id Label Studio tidak muncul pada korpus.** Uji: id di luar tabel menggagalkan impor. Uji: dua anotator → `anotasi_ganda` | R-07, R-08 | [x] |

**A-5 adalah tugas terpenting fitur ini.** `bocor_pii` menyatakan data pribadi
lolos anonimisasi dan KM-05 memeriksanya harian. Korpus tanpa bendera karena
proyeknya tidak dapat mengumpulkannya terbaca persis seperti korpus bersih.

## Fase B · Ekspor

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | Ekspor JSONL sesuai D-03 Bagian 15 | Uji: setiap bidang D-03 ada dengan nama persis; **uji: bendera tak terkumpul ditulis `null`, bukan `[]`**; uji: tanpa versi skema tidak dihasilkan | R-09, R-12 | [x] — modul tidak menulis berkas; C-17 melarangnya dari `src/nlp` |
| B-2 | Ekspor CoNLL beserta pedoman anotasi | **Uji: rentang tak sejajar batas token dilaporkan, dokumennya dilewati** — bukan digeser. Uji: berkas pedoman ikut dihasilkan | R-10, R-11 | [ ] |

## Fase C · Catatan dan patokan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | Catatan impor ke `logbook/` L2; `[sistem.label_studio]` dan perluasan pemeriksa R-18 | Uji: baris memuat versi Label Studio, versi skema, jumlah dokumen, dan keadaan bendera. **Uji: versi tercatat berbeda dari yang dipakai → pemeriksa menyala** | R-13, R-14, C-09 | [ ] |

## Verifikasi akhir

- [ ] `make check` lulus 6 gerbang
- [ ] `make compliance` tidak berubah — 8 lulus, 0 gagal, 12 belum
- [ ] Seluruh uji impor berjalan atas **berkas sungguhan**, bukan bentuk susunan uji
- [ ] Kelima uji mutasi `plan.md` Bagian 6 dijalankan dan hasilnya dilaporkan
- [ ] Cakupan uji tidak turun
- [ ] **Nol ketergantungan baru**
