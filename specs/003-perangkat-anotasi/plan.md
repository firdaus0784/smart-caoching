# Plan: 003-perangkat-anotasi

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 — 6 Agustus 2026 |
| Status | **Lolos Gerbang 2** — 6 Agustus 2026, keputusan KB-022. Menunggu `tasks.md` |
| Ketergantungan baru | **Nol paket Python** — KB-020 |
| Pertanyaan yang menuntut putusan Anda | **Satu, sudah diputus** — Bagian 5; putusannya Bagian 8 |

---

## 1 · Letak modul

`AGENTS.md` tidak menyebut anotasi pada daftar arsitekturnya, dan itu keadaan
yang sudah dua kali muncul: `src/penyimpanan/` pada fitur 002, tepi
`ingest → nlp` pada fitur 015. Kali ini jawabannya **tidak** menuntut baris
baru.

Anotasi adalah pekerjaan `src/nlp/` menurut `AGENTS.md` sendiri — "NER,
klasifikasi, praproses, anonimisasi". Skema label dan kategori adalah bahan
NER dan klasifikasi; perhitungan kesepakatan menilai bahan itu. Keduanya
tinggal di `src/nlp/anotasi/`.

```
src/nlp/anotasi/
  skema.py        label, kategori, versi skema        R-01 s.d. R-04
  rentang.py      anotasi entitas berindeks karakter   R-05, R-06
  kesepakatan.py  Kappa, F1 berpasangan                R-07 s.d. R-09
  kualifikasi.py  uji kualifikasi anotator             R-14
  batch.py        catatan batch, pra-anotasi           R-12, R-13, R-15
  ekspor.py       JSONL dan CoNLL                      R-10, R-11
  impor_ls.py     pembacaan ekspor Label Studio        BAGIAN 2
```

Tanpa perubahan `AGENTS.md`.

---

## 2 · Yang paling mudah keliru, dan bentuk yang mencegahnya

### Kappa dipakai pada tempat yang salah

Ini kekeliruan yang D-03 Bagian 11 tolak dengan dua rujukan literatur, dan ia
kekeliruan yang **tampak seperti kerapian**: dua jenis tugas, satu ukuran,
kode lebih pendek. Siapa pun yang merapikan modul ini kelak akan
menggodanya.

Bentuk yang mencegahnya: **fungsi Kappa tidak menerima anotasi rentang sama
sekali.** Ia menerima tipe `PutusanKategori`, dan anotasi rentang bertipe
`RentangEntitas`. Penyeragaman karena itu tidak dapat dilakukan tanpa
mengubah tanda tangan — dan tanda tangan yang berubah menuntut penjelasan.

Ditambah uji sifat yang menyatakannya, dan R-09 yang menuntut alasannya
tertulis pada uraiannya.

### Angka kesepakatan yang lahir dari ketiadaan

`spec.md` menuntut batch tanpa anotasi ganda dilaporkan **belum dapat
dihitung**. Bentuknya mengikuti `HasilSistem` fitur 015: hasil membawa
`terhitung: bool` di samping angkanya, bukan angka yang dapat berarti dua
hal.

Nilainya `None` ketika belum terhitung — bukan 0,0, bukan 1,0. Angka yang
dapat dibaca sebagai hasil adalah angka yang akan disalin ke naskah.

### Rentang yang tidak cocok

R-06. Bentuknya sudah terbukti pada fitur 015: `TeksKanonik` yang menolak isi
kosong, dan `Token` yang menuntut panjang rentang sama dengan panjang
permukaannya. `RentangEntitas` mengikuti keduanya — ia menuntut teks kanonik
saat dibentuk, dan memeriksa potongannya cocok.

---

## 3 · Cara Kappa dan F1 diuji

**Terhadap contoh yang dihitung tangan, bukan terhadap keluaran dirinya
sendiri.** Ini yang membedakan uji perhitungan dari uji regresi: yang kedua
hanya membuktikan hasilnya tidak berubah, termasuk ketika ia salah sejak
awal.

Tiga jenis contoh:

| Contoh | Nilai yang diharapkan | Mengapa |
|---|---|---|
| Kesepakatan sempurna | Kappa = 1,0 | Batas atas |
| Kesepakatan setara kebetulan | Kappa = 0,0 | Batas yang membedakan Kappa dari persentase kesetujuan |
| Tabel 2×2 dengan angka dihitung tangan | nilai tertulis pada uji | Yang benar-benar menguji rumusnya |

Contoh kedua yang terpenting: persentase kesetujuan yang tinggi dengan Kappa
nol adalah keadaan yang justru dicari D-03 Bagian 11, dan modul yang keliru
akan melaporkan angka tinggi di sana.

F1 berpasangan diuji pada empat keadaan: rentang identik, rentang bertumpang
tindih dengan label sama, rentang identik dengan label berbeda, dan rentang
yang tidak bertemu sama sekali. Keempatnya membedakan pencocokan tepat dari
longgar, dan ketiga terakhir yang membuat pembedaannya berarti.

---

## 4 · Bagian 2, dan mengapa ia menunggu

`impor_ls.py` **tidak ditulis** sebelum satu berkas ekspor sungguhan ada pada
`tests/bahan/`. Bukan karena tidak dapat ditulis, melainkan karena yang
ditulis tanpa bahan akan berbentuk seperti dugaan penulisnya.

Dua kali pada fitur 015 dugaan itu terbukti keliru — `paragraph.text`
python-docx bukan teks final, dan XLSX tidak menyimpan hasil hitungan
rumusnya — dan keduanya baru ketahuan ketika bahan uji sungguhan dibuat.
Keduanya juga akan lolos seluruh uji yang disusun dari dugaan yang sama.

Yang dikerjakan sekarang sebagai gantinya: **bentuk sasarannya**. Tipe milik
kita — `AnotasiDokumen`, `RentangEntitas`, `PutusanKategori` — ditetapkan dari
D-03 dan D-04 Bagian 7.2, bukan dari bentuk ekspor. Pemetaan dari satu ke yang
lain menjadi pekerjaan yang kecil dan terpusat ketika bahannya ada.

---

## 5 · Pertanyaan yang menuntut putusan Anda

**Siapa yang menyediakan contoh ekspor Label Studio, dan kapan.**

Ia bukan pekerjaan kode. Seseorang memasang Label Studio 1.23 di lingkungan
tim, membuat satu proyek berskema D-03, menganotasi dua atau tiga dokumen
contoh dengan dua akun berbeda, lalu mengekspornya. Berkas itu disimpan pada
`tests/bahan/` beserta versinya.

| | Pilihan | Akibat |
|---|---|---|
| **A** | Ditugaskan sekarang, bagian 2 menyusul dalam fitur ini | Fitur 003 selesai utuh. Menuntut satu orang dan beberapa jam |
| **B** | Bagian 1 diselesaikan dan lolos Gerbang 4; bagian 2 menjadi fitur tersendiri | Fitur 003 selesai sebagian, dan sisanya bernomor sendiri pada `docs/D12.md` |
| **C** | Menunggu — tidak ada yang dikerjakan sampai contohnya ada | Menunda pekerjaan yang tidak menunggu apa pun |

**Saran saya: B.** Alasannya bukan kemudahan melainkan kejujuran penomoran:
bagian 2 menuntut orang di luar agen, dan fitur yang setengahnya menunggu
orang lain akan tercatat "berjalan" selama berminggu-minggu tanpa ada yang
berjalan. Memisahkannya membuat keadaan itu terbaca dari daftar urutan
pembangunan — pola yang sama dengan pemisahan fitur 002 dan 015 pada KB-010.

C ditolak dengan alasan yang sama seperti KB-021: bagian 1 tidak menyentuh
bentuk data Label Studio sama sekali.

---

## 6 · Rencana uji mutasi

| Yang dimutasi | Yang wajib gagal |
|---|---|
| Kappa dipakai menghitung kesepakatan rentang | Uji sifat tanda tangan (Bagian 2) |
| `terhitung` dihapus; batch kosong mengembalikan 1,0 | Uji batch tanpa anotasi ganda |
| `RentangEntitas` berhenti memeriksa potongan teksnya | Uji R-06 |
| Ambang D-03 diubah pada kode | Uji ambang terhadap nilai D-03 |

---

## 7 · Ketergantungan

**Nol.** Kappa dan F1 memakai aritmetika pustaka baku. Bila implementasi
menemukan satu pun diperlukan, pekerjaan berhenti dan diajukan — bukan
dipasang lalu dilaporkan.

`[sistem.label_studio]` ditambahkan pada bagian 2, bersama contoh ekspornya:
mencatat versi perangkat yang belum dipasang siapa pun akan menghasilkan
patokan yang tidak pernah dipakai, kekeliruan yang sudah dihindari pada
`[sistem.tesseract]` fitur 015.

---

## 8 · Keputusan Gerbang 2

**Pilihan B** — diputus 6 Agustus 2026, tercatat KB-022.

Fitur 003 memuat **bagian 1 saja**: perhitungan, skema berversi, uji
kualifikasi, ekspor, dan penandaan pra-anotasi. Ia diselesaikan sampai
Gerbang 4 tanpa menunggu siapa pun.

Pembacaan ekspor Label Studio menjadi **fitur 016**, ditempatkan pada
`docs/D12.md` Bagian 7 sesudah 003, dengan catatan bahwa ia tertahan sampai
satu contoh ekspor sungguhan tersedia pada `tests/bahan/`.

Alasannya kejujuran penomoran, bukan kemudahan: bagian 2 menuntut orang di
luar agen — memasang Label Studio, menganotasi dengan dua akun, mengekspor —
dan fitur yang setengahnya menunggu orang lain akan tercatat "berjalan"
selama berminggu-minggu tanpa ada yang berjalan. Memisahkannya membuat keadaan
itu terbaca dari daftar urutan pembangunan.

Pola yang sama dengan pemisahan fitur 002 dan 015 pada KB-010, dan alasan yang
sama pula.

Sesudah ini `tasks.md` bagian 1 disusun dan diajukan ke Gerbang 3.
