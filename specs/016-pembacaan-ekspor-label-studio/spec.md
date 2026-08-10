# Spec: 016-pembacaan-ekspor-label-studio

| | |
|---|---|
| Kebutuhan | FR-C06, FR-C08, FR-C10 bagian pemetaan · R-10, R-11, R-16 yang dipindahkan dari fitur 003 |
| Dokumen terkait | **D-03 Bagian 15** · D-04 ADR-08, Bagian 7.2 · D-01 Bagian 12.3 · D-12 Bagian 7 |
| Pasal konstitusi | **C-10**, C-09, C-11, C-12, C-16 |
| Urutan pembangunan | 016 pada `docs/D12.md` Bagian 7, sesudah 003 |
| Bahan | **Sudah ada** — `tests/bahan/ekspor-label-studio-1.23.json` (KB-023) |
| Status | **Lolos Gerbang 4** — 10 Agustus 2026 (KB-027) |

## Tujuan

Setelah fitur ini ada, hasil kerja anotator di Label Studio **menjadi korpus
milik kita**: dibaca dari berkas ekspornya, diubah menjadi tipe fitur 003, dan
diekspor ulang dalam bentuk D-03 Bagian 15 yang dapat dipakai melatih model
dan dilampirkan pada naskah.

Yang menentukan seluruh fitur ini: **Label Studio tidak membawa tiga bidang
yang D-03 tuntut.** KB-023 memeriksanya terhadap berkas sungguhan —
`versi_skema`, `bendera`, dan `status_pra_anotasi` tidak ada pada ekspornya
dalam bentuk apa pun. Ketiganya ditambahkan pada tahap ini, dan **cara
menambahkannya menentukan apakah korpusnya dapat dipercaya.**

## Yang sudah diketahui dari bahan sungguhan (KB-023)

| Hal | Temuan |
|---|---|
| `value.start` / `value.end` | **Indeks karakter** — dicocokkan terhadap potongan teks aslinya dan cocok. C-10 tidak menuntut penerjemahan |
| `completed_by` | Bilangan bulat id pengguna, **bukan surel**. Pemetaan id ke orang tinggal di dalam Label Studio |
| `predictions` | Ada pada tiap tugas; kosong bila tidak ada pra-anotasi |
| `versi_skema`, `bendera`, `status_pra_anotasi` | **Tidak ada** |
| Satu tugas, dua anotasi | Dua objek pada `annotations`, `completed_by` berbeda |

Batas yang KB-023 catat dan berlaku di sini: ekspor bahan uji dihasilkan lewat
API, bukan lewat peramban. `lead_time`, `draft_created_at`, dan `last_action`
**tidak boleh** menjadi dasar aturan apa pun pada fitur ini.

## Di luar cakupan

- **Memasang Label Studio.** Pekerjaan penyebaran (D-09). Fitur ini membaca
  berkasnya dan mencatat versinya.
- **Menyusun konfigurasi label pada Label Studio.** Ia pekerjaan tim anotasi.
  Fitur ini menyatakan apa yang wajib ada di sana agar impornya sah.
- **Adjudikasi.** Antarmukanya milik Label Studio (fitur 003 `spec.md`).
- **Mengubah bentuk JSONL.** Dimiliki D-03 Bagian 15.

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | Pembaca ekspor **HARUS** menghasilkan `RentangEntitas` dan `PutusanKategori` milik fitur 003, bukan bentuk Label Studio yang diteruskan |
| R-02 | **JIKA** bentuk berkas ekspor tidak sesuai yang dikenali, **MAKA** pembaca **HARUS** gagal tegas dan **TIDAK BOLEH** mengurai sebagian |
| R-03 | Rentang **HARUS** memakai `value.start` dan `value.end` sebagai indeks karakter, dan **HARUS** diperiksa terhadap teks dokumennya (C-10) |
| R-04 | `versi_skema` **HARUS** diberikan pemanggil saat impor; ia **TIDAK BOLEH** ditebak dari berkas ekspor (FR-C08) |
| R-05 | `status_pra_anotasi` **HARUS** diturunkan dari `predictions` tugas, bukan ditulis tangan |
| R-06 | `bendera` **HARUS** dibaca dari hasil anotasi; **JIKA** proyeknya tidak mengumpulkan bendera sama sekali, **MAKA** impor **HARUS** menyatakannya dan **TIDAK BOLEH** menghasilkan korpus yang terbaca "tanpa bendera" |
| R-07 | Anotator **HARUS** tercatat sebagai kode anonim; id pengguna Label Studio **TIDAK BOLEH** masuk korpus apa adanya |
| R-08 | **KETIKA** satu dokumen dianotasi lebih dari satu anotator, sistem **HARUS** menandainya `anotasi_ganda` |
| R-09 | Ekspor JSONL **HARUS** mengikuti D-03 Bagian 15, bidang demi bidang |
| R-10 | Ekspor CoNLL **HARUS** memetakan rentang karakter ke token memakai tokenisasi fitur 015, dan rentang yang tidak jatuh pada batas token **HARUS** dilaporkan, bukan digeser diam-diam |
| R-11 | Ekspor **HARUS** disertai berkas pedoman anotasi yang berlaku (FR-C06) |
| R-12 | Ekspor tanpa versi skema **TIDAK BOLEH** dihasilkan |
| R-13 | Versi Label Studio **HARUS** tercatat pada `ketergantungan-disetujui.toml` dan diperiksa pemeriksa R-18 |
| R-14 | Setiap impor **HARUS** tercatat ke `logbook/` beserta versi Label Studio, versi skema, dan jumlah dokumen (C-09) |

**R-06 adalah kebutuhan terpenting fitur ini, dan alasannya tidak terlihat dari
kalimatnya.** Salah satu bendera D-03 adalah `bocor_pii` — data pribadi yang
lolos anonimisasi, diperiksa harian pada KM-05. Korpus yang tercatat "tanpa
bendera" karena proyeknya **tidak dapat** mengumpulkan bendera terbaca persis
seperti korpus yang bersih. Itu bentuk laporan palsu yang sama dengan TA-01,
dan di sini akibatnya data pribadi masuk korpus tanpa seorang pun waspada.

**R-10 mengikuti pelajaran C-10 sampai ke ujungnya.** CoNLL berbaris per token
sedangkan anotasi kita berindeks karakter, sehingga pemetaannya tidak dapat
dihindari — dan di situlah rentang bergeser satu karakter tanpa satu galat pun.

## Keadaan yang wajib ditangani

| Keadaan | Perilaku yang dituntut |
|---|---|
| Berkas ekspor bentuknya berubah | Gagal tegas saat diurai |
| Anotasi merujuk tugas yang tidak ada | Ditolak |
| Rentang tidak cocok dengan teks dokumennya | Ditolak, tidak diperbaiki (R-06 fitur 003) |
| Tugas tanpa satu pun anotasi | Dilewati, dan jumlahnya dilaporkan — bukan diam |
| Anotasi `was_cancelled` | Tidak masuk korpus |
| Dua anotator pada satu dokumen | Keduanya masuk, ditandai `anotasi_ganda` |
| Proyek tanpa kendali bendera | Impor menyatakannya; korpus tidak terbaca bersih |
| Rentang tidak jatuh pada batas token saat ekspor CoNLL | Dilaporkan, tidak digeser |

## Kriteria penerimaan

- [ ] R-01 s.d. R-14 masing-masing punya uji yang gagal sebelum implementasi
- [ ] Uji dijalankan terhadap **berkas ekspor sungguhan** pada `tests/bahan/`, bukan terhadap bentuk yang disusun uji
- [ ] Uji bahwa bentuk yang berubah menggagalkan penguraian (R-02)
- [ ] Uji bahwa korpus dari proyek tanpa kendali bendera **tidak** terbaca bersih (R-06)
- [ ] Uji bahwa id pengguna Label Studio tidak muncul pada korpus (R-07)
- [ ] Uji bahwa rentang tak sejajar token dilaporkan saat ekspor CoNLL (R-10)
- [ ] Nol ketergantungan Python baru
- [ ] Cakupan uji tidak turun (C-11)
- [ ] `make compliance` tidak berubah

## Pertanyaan bagi Gerbang 1

**Satu, dan ia menentukan R-06.**

Bendera D-03 — `perlu_adjudikasi`, `ocr_rusak`, `anonimisasi_berlebih`,
`bocor_pii` — dikumpulkan Label Studio hanya bila konfigurasi labelnya memuat
kendali untuk itu. Konfigurasi tim belum disusun.

| | Pilihan | Akibat |
|---|---|---|
| **A** | Fitur ini menetapkan bentuk kendalinya — satu `Choices` bernama `bendera`, empat nilai D-03 — dan impor menolak proyek yang tidak memilikinya | Bentuk konfigurasi ditetapkan kode, tim mengikutinya. Menuntut satu baris pada dokumen penyebaran |
| **B** | Impor menerima parameter yang menyatakan apakah proyeknya mengumpulkan bendera; korpus menandai keadaan itu | Tidak menetapkan bentuk apa pun. Menuntut pemanggil jujur |
| **C** | Bendera diabaikan pada siklus ini, dicatat sebagai butir terbuka | `bocor_pii` tidak pernah masuk korpus — dan KM-05 memeriksanya harian |

**Saran saya: A, dengan B sebagai bentuk teknisnya.** Alasannya bukan
kelengkapan melainkan `bocor_pii`. Menetapkan nama kendali pada kode membuat
tim punya satu hal pasti untuk disalin; menerima parameter yang menyatakan
keadaannya membuat proyek yang belum memasangnya **tetap dapat diimpor** tanpa
korpusnya terbaca bersih. C ditolak: bendera yang ditunda adalah bendera yang
tidak ada ketika data pribadi lolos.
