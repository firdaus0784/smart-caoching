# Plan: 011-penemuan-dan-penerapan

| | |
|---|---|
| Spec | `spec.md` |
| Ketergantungan baru | **Nol** |
| Lapisan | `src/pengguna/` diperluas — bukan lapisan baru |

## 1 · Di mana modulnya tinggal

Bukan `src/api/`. Rantai penemuan-penerapan adalah **milik pengguna** —
komitmennya, jurnalnya, umpan baliknya — dan `src/pengguna/` sudah menjadi
rumah profil, prioritas, dan persetujuan sejak fitur 022. `src/api/` menjadi
tempat rutenya kelak, bukan tempat isinya.

Tepi yang dibutuhkan sudah tertulis pada `AGENTS.md`: `pengguna → nlp`
(pendeteksi data pribadi bagi bidang bebas, KM-03) dan `pengguna → kamus`.
Feed membaca `ButirTayang` milik `src/ingest/kurasi/` — dan tepi
`pengguna → ingest` **belum ada**. Lihat Bagian 6.

## 2 · Bentuk yang menegakkan TK-51

`Komitmen` memiliki `isyarat` dan `tindakan` sebagai dua bidang wajib, dan
**tidak memiliki bidang teks bebas tunggal**. Diuji sebagai ketiadaan bidang,
bukan sebagai penolakan nilai: bidang yang ada akan terisi.

Ini bentuk keenam sesudah `Instruksi` (ADR-13), `JawabanTervalidasi` (008),
`ButirTayang` (010), `Peristiwa` (012), dan `HasilTanya` (021). Perbedaannya:
kelima yang lain menjaga pasal konstitusi; yang ini menjaga **kesahihan
bukti**. Bila bentuknya longgar, sistemnya tetap patuh dan penelitiannya yang
kehilangan dasar.

## 3 · Tiga keadaan, bukan dua — kali kesembilan

`StatusPenerapan` bernilai empat, bukan tiga, dan itu D-01 FR-H04 sendiri:
`SUDAH_DITERAPKAN`, `SEDANG_BERJALAN`, `BELUM`, `TIDAK_JADI`. Yang keempat
menuntut alasan; ketiga lainnya tidak.

Yang membedakannya dari pola "tiga keadaan" sebelumnya: di sini pemisahannya
sudah ada pada dokumen, dan tugas kode hanya **tidak menggabungkannya**.
Menyatukan `BELUM` dengan `TIDAK_JADI` menghapus perbedaan antara komitmen
yang tertunda dan komitmen yang dibatalkan — dan rasio penerapan, yang menjadi
variabel hasil utama siklus ini, dihitung dari perbedaan itu.

## 4 · Pagu tayang memakai tetapan yang sudah ada

`PAGU_TAYANG_PER_PENGGUNA` sudah bernama pada `src/ingest/kurasi/tetapan.py`
sejak fitur 010, bernilai 3, dan terdaftar pada pemeriksa C-16. Feed
**mengimpornya**, tidak menuliskan angka kedua. Angka kedua akan benar hari ini
lalu berselisih pada hari salah satunya disetel — dan yang disetel bukan yang
diperiksa.

## 5 · Yang tidak dibangun, beserta cara menyatakannya

FR-H07 ekspor PDF menuntut ketergantungan yang belum disetujui. Dinyatakan
lewat fungsi yang **dapat dipanggil** dan mengembalikan alasannya, mengikuti
`parquet_tertahan()` fitur 012: fungsi yang tidak ada terbaca sebagai fitur
yang tidak pernah diminta, sedangkan alasan yang dapat dipanggil terbaca
sebagai utang yang dapat ditagih.

## 6 · Tepi arsitektur yang perlu diputus

`pengguna → ingest` belum tertulis. Feed menyaring `ButirTayang`, dan tipe itu
tinggal di `src/ingest/kurasi/putusan.py`.

**Usul: tepi dituliskan.** Alasannya dapat dinyatakan umum, dan itu yang
membuatnya bukan perkecualian — C-06 menuntut butir tayang hanya lahir dari
gerbang kurasi, sehingga setiap lapisan yang **menayangkan** butir wajib
memiliki tepi ke tempat butir itu disahkan. Arah sebaliknya tetap terlarang:
`ingest` yang memanggil `pengguna` membuat kurasi bergantung pada profil orang
yang akan membacanya, dan itu membalik arah C-06.

## 7 · Rencana uji mutasi

| | Mutasi | Wajib menyalakan |
|---|---|---|
| M-1 | `Komitmen` diberi bidang `catatan_bebas` | Uji ketiadaan bidang (R-12) |
| M-2 | `isyarat` diberi nilai bawaan `""` | Uji bidang wajib — pydantic tidak memvalidasi bawaan |
| M-3 | Feed menayangkan butir di luar prioritas | Uji penyaringan R-01 |
| M-4 | Pagu tayang ditulis sebagai angka, bukan diimpor | Uji sumber tetapan R-06 |
| M-5 | Pagu dinaikkan menjadi 4 | Uji batas R-05 |
| M-6 | `TIDAK_JADI` diterima tanpa alasan | Uji R-14 |
| M-7 | `BELUM` dan `TIDAK_JADI` disatukan | Uji empat nilai R-13 |
| M-8 | Butir berlisensi tertutup membawa teks penuh | Uji R-08 |
| M-9 | Bidang bebas menerima nomor telepon | Uji KM-03 |

## 8 · Cakupan uji

Tidak turun. Patokan berjalan: 99,86% atas 3.059 pernyataan.
