# Plan: 014-pemeriksa-konsistensi-dokumen

Disusun agen. Ditinjau manusia bersama `spec.md` dan `tasks.md` pada gerbang
gabungan.

## Pendekatan

Satu modul `perkakas/pemeriksa/konsistensi_dokumen.py`, disambungkan ke V-03
pada `make check`. V-03 sudah bernama "ketertelusuran dan keselarasan dokumen"
dan sudah memuat pemeriksa placeholder serta keselarasan perintah; pemeriksa
ini melengkapi kelompok yang sama alih-alih membuat gerbang baru.

Pekerjaannya dua tahap. Pertama, membaca register `docs/D00.md` Bagian 2
menjadi pemetaan kode dokumen ke versi. Kedua, membandingkannya dengan kepala
dan riwayat revisi tiap dokumen, lalu dengan isi direktori `docs/`.

**Tanpa ketergantungan baru.** Seluruhnya penguraian teks dengan `re` pustaka
baku, sama seperti pemeriksa placeholder dan keselarasan perintah pada fitur
001. Sikap yang Gerbang 2 minta dipertahankan.

### Satu keputusan yang menentukan pemeriksa ini berguna atau dimatikan

Kepala dokumen tidak seragam. D-01 memakai `| Versi dokumen |`, sisanya
memakai `| Versi |`, dan nilainya sering diikuti keterangan — `0.5 — Penambahan
ADR-12 dan ADR-13`. Pengurai wajib menerima keragaman itu dan mengambil hanya
angka versinya.

Bila pengurai terlalu ketat, ia akan melaporkan kegagalan pada dokumen yang
sebenarnya benar, dan pemeriksa yang menyalak pada keadaan sah akan dimatikan
orang — pelajaran V-05 pada fitur 001. Karena itu keragaman bentuk kepala
diuji sebagai kasus tersendiri, bukan diasumsikan.

## Berkas yang disentuh

| Berkas | Baru/ubah | Alasan |
|---|---|---|
| `perkakas/pemeriksa/konsistensi_dokumen.py` | baru | R-01 s.d. R-08 |
| `perkakas/pemeriksa/jalankan.py` | ubah | Sambungkan ke V-03 |
| `tests/pemeriksa/test_konsistensi_dokumen.py` | baru | Uji |
| `docs/D12.md` | ubah | Baris fitur pada Bagian 7; naikkan versi |
| `docs/D00.md` | ubah | Register D-12; riwayat revisi |
| `logbook/L4-keputusan.md` | ubah | Entri bila ada keputusan berjalan |

## Kontrak

**Tidak ada rute baru.** Fitur ini tidak menyentuh `docs/D14.md` Bagian 3.

## Skema data

**Tidak ada tabel basis data.** Satu bentuk internal:

| Tipe | Bidang |
|---|---|
| `Dokumen` | `kode`, `berkas`, `versi_kepala`, `versi_register`, `versi_riwayat` |

## Pasal konstitusi

| Pasal | Bagaimana dipenuhi | Cara diuji |
|---|---|---|
| **C-11** | Uji menyertai setiap pemeriksa; cakupan tidak turun dari 98,9% | `make check` V-01 |
| **C-12** | Tanpa ketergantungan baru; `re` pustaka baku | `make check` V-04 |

Fitur ini perkakas, bukan sistem. Pasal yang mengatur perilaku sistem — C-01
s.d. C-07, C-17 s.d. C-20 — tidak tersentuh, dan `make compliance` tetap
melaporkan keadaan yang sama.

## Risiko

| Kode | Risiko | Bila terjadi |
|---|---|---|
| RQ-01 | Pengurai kepala terlalu ketat, menyalak pada dokumen yang benar | Keragaman bentuk diuji sebagai kasus tersendiri. Bila tetap muncul, pengurai dilonggarkan — **bukan** dokumennya yang diseragamkan; menyeragamkan dokumen demi perkakas adalah ekor menggoyang anjing |
| RQ-02 | Pemeriksa R-05 menyalak pada kutipan sejarah yang sah, misalnya "TK-07" yang dirujuk sebagai pelajaran | Definisi dicari di seluruh `docs/`; kode yang pernah didefinisikan di mana pun dianggap ada. Kutipan sejarah selalu merujuk kode yang ada |
| RQ-03 | Pemeriksa menjadi alasan menunda audit manusia | Dinyatakan pada docstring: ia memeriksa **bentuk**, bukan makna. Uji tujuh pertanyaan D-00 Bagian 5 tetap pekerjaan manusia, dan lima dari tujuhnya di luar jangkauan mesin |

## Yang tidak dikerjakan

- Perbaikan otomatis atas penyimpangan yang ditemukan
- Pemeriksaan klaim jumlah dalam prosa
- Pemeriksaan kepemilikan fakta tunggal atau kecocokan isi antardokumen
- Penyeragaman bentuk kepala dokumen
- Penyelesaian TK-40, TK-41, TK-42, TK-44 — keempatnya menunggu keputusan
  pemilik dokumen, bukan pekerjaan teknis
