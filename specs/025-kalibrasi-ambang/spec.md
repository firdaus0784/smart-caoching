# Spec: 025-kalibrasi-ambang

| | |
|---|---|
| Kebutuhan | BT-29, C-16, C-09; D-07 Bagian 4.6, D-08 Bagian 5 |
| Dokumen terkait | D-07 Bagian 4.4 dan 4.6, D-08 Bagian 5 dan 6, D-06 ambang relevansi L4 |
| Status | **Menunggu Gerbang 1** |
| Asal | Dipecah dari fitur 019 pada 20 September 2026 (KB-091) |

## Tujuan

Seluruh ambang pada sistem ini **belum ada satu pun**, dan itu keadaan yang
benar. `AmbangKecukupan` tidak dapat dibentuk tanpa `CatatanKalibrasi` yang
menyebut gold set, jumlah pertanyaan, pemutus, dan prosedurnya — dan kalibrasi
itu belum pernah dijalankan.

Akibatnya sistem hari ini **selalu menjawab "tidak ditemukan"**. Itu bukan
kerusakan: ia sistem yang menolak menebak. Fitur ini yang mengubahnya menjadi
sistem yang menjawab — dan karena itu ia fitur paling berbahaya pada seluruh
siklus.

## Mengapa fitur ini dipisahkan dari 019

Keduanya tertahan hal yang berbeda, dengan tenggat berbeda berbulan-bulan:
019 menunggu bobot model yang diunduh di mesin penelitian, 025 menunggu **gold
set D-08 yang belum disusun**. Satu baris yang separuhnya menunggu akan
tercatat "belum selesai" sepanjang itu sampai ketidakselesaiannya berhenti
bermakna.

## Yang menghalangi, dinyatakan di muka

| Bahan | Keadaan | Pemilik |
|---|---|---|
| *Gold set* 200 pertanyaan, **dibekukan sebelum kalibrasi** | **belum disusun** | D-08 Bagian 5; tim substansi |
| Enam puluh pertanyaan jenis C, D, E yang jawaban benarnya **penolakan** | belum disusun | D-08 Bagian 5 |
| Sumber vektor berjalan | menunggu fitur 019 | — |
| Penyemat sungguhan terpasang | menunggu unduhan di mesin penelitian | ketua peneliti |

Tidak satu pun dapat disiapkan agen. Fitur ini **tidak dapat dimulai** sampai
gold set dibekukan.

## Di luar cakupan

- **Menyusun gold set.** Ia milik D-08, disusun tim substansi dari survei 50
  kepala sekolah, pertanyaan nyata uji internal, dan penyusunan tim. **Agen
  yang menyusunnya menguji dirinya sendiri**, dan angka yang lahir dari itu
  tidak berarti apa-apa.
- **Menyetel ambang di luar prosedur BT-29.** C-16, tanpa pengecualian.
- **Melonggarkan validator** bila tingkat penolakan tinggi. C-16 kalimat
  kedua: perbaiki pengambilannya, jangan longgarkan validatornya.

## Kebutuhan (EARS)

**R-01.** Kalibrasi WAJIB dijalankan terhadap gold set yang **sudah dibekukan**,
dan penanda bekunya WAJIB tercatat pada `CatatanKalibrasi`.

**R-02.** JIKA gold set belum dibekukan, MAKA prosedur kalibrasi WAJIB menolak
berjalan — bukan berjalan dengan peringatan.

**R-03.** Ambang yang dihasilkan WAJIB dibentuk hanya lewat `AmbangKecukupan`
beserta `CatatanKalibrasi`-nya; tidak ada jalur lain yang menghasilkan nilai
ambang.

**R-04.** Ambang tinggi dan menengah WAJIB selaras dengan ambang relevansi L4
pada D-06 — tidak boleh ada butir yang lolos ke feed tetapi tak pernah cukup
sebagai dasar jawaban (D-07 Bagian 4.6).

**R-05.** Hasil kalibrasi WAJIB dilaporkan **apa adanya**, termasuk tingkat
penolakan yang dihasilkannya dan pertanyaan gold set mana yang gagal.

**R-06.** Setiap percobaan kalibrasi WAJIB tercatat ke `logbook/` mengikuti
C-09, termasuk percobaan yang **gagal** — rangkaian percobaan yang gagal adalah
bukti bahwa ambang akhir dipilih berdasarkan pengujian, bukan kebetulan.

**R-07.** Penguatan kategori (D-07 Bagian 4.4) WAJIB dikalibrasi pada prosedur
yang sama, bukan disetel terpisah.

## Pertanyaan yang wajib dijawab Gerbang 1

1. **Berapa besar gold set minimum bagi kalibrasi pertama?** D-08 menetapkan
   200 pertanyaan. Prototipe mungkin cukup dengan lebih sedikit — tetapi
   **D-08 pemilik tunggal komposisi gold set**, dan angka yang diturunkan agen
   akan menjadi angka yang tidak dapat dipertahankan di hadapan penilai.

2. **Siapa pemutus yang namanya masuk `CatatanKalibrasi`?** Bidang itu wajib
   dan tidak boleh diisi "tim" — ia ada supaya ada yang dapat ditanya.

3. **Kalibrasi diulang berapa lama sekali, dan apa yang memicunya?** Ambang
   yang dikalibrasi sekali lalu dibiarkan akan menua bersama korpusnya, dan
   penuaan itu tidak menghasilkan satu galat pun.

## Ketertelusuran

| Kebutuhan | Diwujudkan |
|---|---|
| BT-29 | R-01, R-07 |
| C-16 | R-02, R-03 |
| D-07 Bagian 4.6, D-06 | R-04 |
| C-09, D-10 L1 | R-06 |
| PU-05, AP-07 | R-05 |
