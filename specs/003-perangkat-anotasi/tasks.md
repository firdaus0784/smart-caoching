# Tasks: 003-perangkat-anotasi

Ditinjau manusia sebelum kode ditulis. Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 |
| Plan | `plan.md`, lolos Gerbang 2 |
| Status | **Lolos Gerbang 3** — 6 Agustus 2026. Implementasi berjalan |
| Cakupan | **Bagian 1 saja** — pembacaan ekspor Label Studio menjadi fitur 016 (KB-022) |
| Jumlah tugas | **15** — di bawah ambang ±30. Kepala ini sempat tertulis 14; jumlah barisnya selalu 15 (A: 5, B: 6, C: 4), dan angkanya yang keliru, bukan daftarnya |
| Ketergantungan baru | **Nol** |

## Fase A · Skema dan tipe

Dibangun lebih dulu karena seluruh fase lain bekerja atasnya, dan karena
tipenya ditetapkan **dari D-03**, bukan dari bentuk ekspor perangkat mana pun
(KB-021).

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `LabelEntitas` — delapan label FR-C04 sebagai enum | Uji: kedelapan ada; **uji: label di luar daftar ditolak** | R-01 | [x] |
| A-2 | `KategoriMasalah` — K1 s.d. K8 sesuai D-03 Bagian 5 | Uji: kedelapan ada dengan kode persis D-03 | R-02 | [x] |
| A-3 | `VersiSkema` dan penyertaannya pada setiap anotasi | Uji: anotasi tanpa versi skema tidak dapat dibentuk | R-03 | [x] |
| A-4 | `RentangEntitas` — indeks karakter, memeriksa potongan teksnya | **Uji: rentang yang tidak cocok ditolak, bukan diperbaiki.** Uji: `teks[mulai:akhir]` sama dengan `teks_rentang` | R-05, R-06 | [x] |
| A-5 | `PutusanKategori` sebagai tipe tersendiri dari `RentangEntitas` | **Uji: keduanya tidak dapat saling menggantikan** — dinyatakan pada tanda tangan, bukan pada nilai | R-07, R-08 | [x] |

**A-5 adalah tugas terpenting fase ini, dan alasannya tidak terlihat dari
namanya.** Dua tipe terpisah itulah yang membuat Kappa **tidak dapat**
dipanggil atas anotasi rentang. Tanpa pemisahan itu, penyeragaman dua ukuran
menjadi satu adalah perubahan satu baris yang tampak seperti kerapian — dan
itu persis kekeliruan yang D-03 Bagian 11 tolak dengan dua rujukan literatur.

**A-4 mengikuti bentuk yang sudah terbukti dua kali:** `TeksKanonik` yang
menolak isi kosong dan `Token` yang menuntut panjang rentang sama dengan
panjang permukaan. Rentang yang diperbaiki diam-diam menunjuk kata lain tanpa
satu galat pun.

## Fase B · Perhitungan kesepakatan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | `HasilKesepakatan` — nilai boleh `None`, dengan `terhitung` terpisah | **Uji: batch tanpa anotasi ganda menghasilkan `terhitung=False` dan nilai `None`** — bukan 0,0, bukan 1,0 | R-07, R-08 | [x] |
| B-2 | Cohen's Kappa bagi klasifikasi | **Uji terhadap tiga contoh yang dihitung tangan**: kesepakatan sempurna, kesepakatan setara kebetulan, tabel 2×2 bernilai tertulis | R-07 | [x] |
| B-3 | Kappa per kategori, satu lawan sisanya | Uji: kategori yang batasnya kabur menghasilkan Kappa lebih rendah daripada keseluruhan | R-07 | [x] |
| B-4 | F1 berpasangan, pencocokan tepat dan longgar | Uji: empat keadaan — rentang identik, bertumpang tindih label sama, identik label berbeda, tidak bertemu | R-08 | [x] |
| B-5 | Uraian modul menyatakan mengapa Kappa tidak dipakai bagi rentang | Uji: uraian menyebut alasannya dan merujuk D-03 Bagian 11 serta D-11 Bagian 3.2 | R-09 | [x] — uraiannya sudah ada sejak B-2; buktinya **uji mutasi**, bukan uji yang gagal lebih dulu |
| B-6 | Ambang D-03 sebagai tetapan, bukan angka tertanam | Uji: ambang sama persis dengan D-03 Bagian 11. **Uji: tidak ada angka ambang tertulis di luar satu tempat** | C-16 | [x] — ujinya membaca `docs/D03.md` sungguhan, bukan menyalin angkanya |

**B-2 contoh kedua yang terpenting**, dan ia mudah luput: persentase
kesetujuan tinggi dengan Kappa nol. Itu justru keadaan yang D-03 Bagian 11
cari — dua anotator yang sepakat karena satu kategori mendominasi, bukan
karena mereka sungguh sepaham — dan modul yang keliru akan melaporkan angka
tinggi di sana.

**B-6 memisahkan ambang dari perhitungannya.** C-16 melarang menyetel ambang
di luar prosedur kalibrasi; ambang yang tersebar di beberapa tempat adalah
ambang yang akan disetel di salah satunya tanpa ada yang tahu.

## Fase C · Kualifikasi dan batch

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | Uji kualifikasi anotator terhadap kunci jawaban | Uji: ambang D-03 Bagian 12 — F1 longgar ≥ 0,80 dan Kappa kategori ≥ 0,70; **uji: lulus salah satu saja tidak cukup** | R-14 | [x] — ambangnya ada pada **Bagian 13**, bukan 12; pembetulan rujukan diajukan terpisah |
| C-2 | `StatusPraAnotasi` pada setiap dokumen | Uji: dokumen tanpa status pra-anotasi tidak dapat dibentuk | R-12 | [x] — **tiga** status, bukan dua; pembanding dibedakan dari tanpa-pra-anotasi |
| C-3 | Penyisihan batch pembanding ketika pra-anotasi dipakai | **Uji: batch berpra-anotasi tanpa pembanding ditolak** | R-13 | [ ] |
| C-4 | Catatan batch ke `logbook/`, seluruh bidang D-03 Bagian 11 | Uji: satu baris per batch memuat kedelapan bidang; uji: bidang yang belum terhitung tercatat sebagai belum terhitung | R-15, C-09 | [ ] |

**C-3 membangun pengendalian sebelum yang dikendalikannya ada.** Pra-anotasi
menunggu fitur 004, tetapi *automation bias* muncul pada hari pertama ia
dipakai. Menambahkan pengendalinya belakangan berarti batch pertama berjalan
tanpa pembanding — dan batch pertama justru yang paling menentukan kebiasaan
anotator.

## Urutan

Fase A mendahului seluruhnya. Fase B dan C dapat berjalan sejajar setelah A-5;
C-1 menuntut B-2 dan B-4 karena ia memakai keduanya.

**Ekspor JSONL/CoNLL (R-10, R-11) tidak ada pada daftar ini.** Ia menuntut
bentuk anotasi yang lengkap, dan kelengkapannya baru pasti sesudah fitur 016
memetakan ekspor Label Studio ke tipe kita. Menulisnya sekarang berarti
menebak bidang mana yang akan terisi — diajukan sebagai tugas tambahan pada
fitur 016, bukan dikerjakan di sini dari dugaan.

## Verifikasi akhir

- [ ] `make check` lulus 6 gerbang
- [ ] `make compliance` **tidak berubah** — 8 lulus, 0 gagal, 12 belum
- [ ] R-01 s.d. R-09 dan R-12 s.d. R-15 punya uji yang gagal sebelum implementasi
- [ ] Uji mutasi: Kappa dipanggil atas anotasi rentang → gagal saat memeriksa tipe
- [ ] Uji mutasi: `terhitung` dihapus → uji batch tanpa anotasi ganda gagal
- [ ] Cakupan uji tidak turun
- [ ] **Nol ketergantungan baru**
- [ ] Angka Kappa dan F1 diuji terhadap contoh yang dihitung tangan
