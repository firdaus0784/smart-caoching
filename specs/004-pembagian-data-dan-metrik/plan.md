# Plan: 004-pembagian-data-dan-metrik

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 — 10 Agustus 2026, keputusan KB-028 |
| Ketergantungan baru | **Nol paket Python** |
| Keputusan Gerbang 1 | **Pilihan C** — Bagian 5 |

---

## 1 · Letak modul

`AGENTS.md` menyebut `src/nlp/` sebagai "NER, klasifikasi, praproses,
anonimisasi". Pembagian data dan metrik adalah bahan keduanya. Tanpa perubahan
daftar arsitektur.

```
src/nlp/pelatihan/
  pembagian.py       PembagianData beku, tingkat dokumen    R-01 s.d. R-06
  metrik.py          metrik per kelas                       R-07 s.d. R-09
  jejak_percobaan.py catatan L1 keempat belas bidang        R-10, R-11
```

**Tidak menulis berkas.** Pelajaran B-1 fitur 016: `src/nlp` berada pada jalur
penjawaban dan C-17 melarang akses tulis dari sana. Pencatatan ke `logbook/`
tetap lewat `src/logbook/penulis.py`, satu-satunya jalur yang diizinkan.

---

## 2 · Yang paling mudah keliru, dan bentuk yang mencegahnya

### Segmen dari satu dokumen tersebar ke dua himpunan

Kekeliruan yang D-08 sebut "mudah terjadi dan sulit terdeteksi setelahnya",
dan akibatnya model tampak lebih baik daripada kenyataannya.

Bentuk yang mencegahnya: `PembagianData` **hanya menerima id dokumen**, tidak
pernah segmen. Pembagian pada tingkat segmen karena itu tidak dapat dilakukan
tanpa mengubah tipenya — dan tipe yang berubah menuntut penjelasan. Bentuk
yang sama dengan `PutusanKategori` yang menjaga Kappa pada fitur 003.

### Himpunan uji yang "sekadar dilihat"

PU-01. Pelanggarannya tidak pernah disengaja: seseorang melihat hasil uji
untuk memilih konfigurasi berikutnya, dan sesudah itu angka pada naskah bukan
lagi hasil pada data tersembunyi.

Bentuknya: himpunan uji **tidak dapat dibaca lewat atribut biasa**. Ia di
balik satu metode yang mencatat pembukaannya, dan hitungan pembukaan ikut pada
catatan percobaan (R-06, pilihan C).

### Kelas tanpa contoh yang dilaporkan nol

R-08, dan ini bentuk yang sudah tiga kali terbukti pada proyek ini. Kelas
tanpa contoh yang dilaporkan F1 = 0,0 terbaca sebagai kelas yang modelnya
gagal total; tindak lanjutnya menjadi melatih ulang, padahal yang diperlukan
menambah data.

`HasilKelas` karena itu membawa `nilai: float | None` beserta `alasan`,
mengikuti `HasilKesepakatan` fitur 003 persis.

### Rerata yang tidak dinyatakan jenisnya

R-09. Makro dan mikro berbeda tajam pada kelas tidak seimbang — dan korpus
manajerial hampir pasti tidak seimbang, sebab K5 dan K7 mendominasi menurut
D-03. Rerata tanpa nama jenisnya adalah angka yang dua pembaca tafsirkan
berbeda, dan keduanya merasa benar.

---

## 3 · Cara metrik diuji

**Terhadap contoh yang dihitung tangan**, sama dengan Kappa dan F1 fitur 003.
Uji regresi hanya membuktikan hasilnya tidak berubah, termasuk ketika ia salah
sejak awal.

| Contoh | Yang diuji |
|---|---|
| Prediksi sempurna | batas atas, seluruh kelas 1,0 |
| Satu kelas kacau, dua kelas baik | **rerata makro turun, mikro hampir tidak** |
| Kelas tanpa contoh pada acuan | belum terhitung, bukan 0,0 |
| Kelas hanya pada prediksi | dilaporkan sebagai halusinasi kelas |

Baris kedua yang membuat R-09 berarti.

---

## 4 · Rencana uji mutasi

| Yang dimutasi | Yang wajib gagal |
|---|---|
| `PembagianData` menerima id segmen | Uji sifat tanda tangan |
| Pemeriksaan irisan dilepas | Uji dokumen pada dua himpunan |
| Sidik pembagian tidak dibandingkan | Uji pembagian ulang yang berbeda |
| Himpunan uji dapat dibaca tanpa mencatat | Uji pembukaan tercatat |
| Kelas tanpa contoh mengembalikan 0,0 | Uji belum terhitung |
| Rerata makro diganti mikro | Uji contoh dihitung tangan |

---

## 5 · Keputusan Gerbang 1

**Pilihan C** — diputus 10 Agustus 2026, KB-028.

Pembukaan himpunan uji dicatat, tetap diizinkan, dan **hitungannya ikut pada
catatan percobaan** yang menjadi bahan naskah.

B ditolak: penjagaan yang menghalangi pekerjaan sah — mengulang evaluasi
karena galat perkakas — adalah penjagaan yang akan dilucuti, dan cara
melucutinya adalah membuat pembagian baru, yang justru menghapus jejaknya.
A ditolak: catatan yang tidak pernah sampai ke laporan tidak ada yang membaca.

---

## 6 · Ketergantungan

**Nol.** Pembagian memakai `random.Random` dengan seed tercatat; metrik
memakai aritmetika pustaka baku. Bila implementasi menemukan satu pun
diperlukan, pekerjaan berhenti dan diajukan.
