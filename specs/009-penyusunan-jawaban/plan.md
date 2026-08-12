# Plan: 009-penyusunan-jawaban

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 — 12 Agustus 2026, KB-039 |
| Status | **Lolos Gerbang 4** — 12 Agustus 2026 (KB-040) |
| Ketergantungan baru | **Nol paket Python** |
| Pertanyaan terbuka | **Nol** — ketiganya dijawab pada KB-039 |

---

## 1 · Jawaban atas ketiga pertanyaan

| | Pertanyaan | Putusan |
|---|---|---|
| 1 | C-20 berpindah tanpa rute? | **A** — ya; separuh rute menuntut sesuatu **tidak ada**, dan itu benar atas nol rute |
| 2 | Cakupan domain tanpa K1–K8 | **B** — daftar hitam ranah terlarang, arah konservatif berlawanan dengan fitur 006 |
| 3 | Rujukan pengubah | **A** — bidang pada `SegmenRujukan`, diisi pemanggil |

---

## 2 · Letak modul

```
src/rag/jawaban/
  domain.py       pemeriksaan cakupan domain, tahap 1        R-02, R-03
  tanggapan.py    Tanggapan, Sitasi, BacaanLanjutan           R-01, R-04 s.d. R-09
  susun.py        penyusun dari JawabanTervalidasi            R-10, R-11, R-12
perkakas/pemeriksa/
  bentuk_tanggapan.py  pemeriksa C-20                          R-01, R-13
```

`src/api/` **tidak dibuat**. Direktori kosong yang menunggu FastAPI adalah
kerangka kosong, dan C-14 melarangnya untuk fitur ruang lingkup — semangat yang
sama berlaku di sini meski pasalnya tidak. Fitur 021 membuatnya bersama
rutenya.

---

## 3 · Pemeriksa C-20 membaca kontraknya dari D-14

**Bentuk tanggapan tidak disalin ke pemeriksa maupun ke uji.** Ia dibaca dari
blok JSON pada `docs/D14.md` Bagian 4.1.

Alasannya bukan kerapian melainkan bahwa uji yang menyalin bidangnya hanya
membuktikan dua salinan sama — **termasuk ketika keduanya sudah menyimpang
dari D-14**. Bentuk yang sama dengan `test_ambang_kesepakatan.py` fitur 003,
yang membaca angkanya dari `docs/D03.md` sungguhan:

> Uji yang menyalin angkanya hanya membuktikan dua salinan sama, termasuk
> ketika keduanya sudah menyimpang dari pemiliknya.

Dua aturan:

1. **Bidang `Tanggapan` sama persis dengan kunci blok JSON D-14 Bagian 4.1.**
   Kurang maupun lebih keduanya temuan — AG-03 melarang penambahan, dan
   pengurangan menghapus tempat C-02, C-07, atau C-19 diwujudkan.
2. **Tidak ada rute di luar `docs/D14.md` Bagian 3.** Hari ini nol rute,
   sehingga nol pelanggaran — dan itu **pernyataan yang benar**, bukan
   pemeriksaan yang hampa. Ia menyala pada rute pertama yang lahir salah.

### Bedanya dengan kekeliruan C-01 pada fitur 008

Perlu dinyatakan tegas, sebab bentuknya mirip dan kesimpulannya berlawanan.

C-01 menuntut sesuatu **ada dan benar**: sitasi terverifikasi terhadap segmen.
Menandainya lulus tanpa VS-03 adalah melaporkan pemeriksaan yang tidak
berjalan — dan MK-07 akan berarti "100% klaim menyebut id yang ada".

C-20 separuh rute menuntut sesuatu **tidak ada**: rute di luar D-14. "Nol
rute, karena itu nol rute terlarang" benar tanpa syarat. Preseden yang sudah
berjalan: C-15 lulus atas basis data yang belum memiliki satu tabel pun.

Separuh bentuk tanggapan menjadi nyata pada fitur ini, sehingga C-20 tidak
berpindah atas kekosongan saja.

---

## 4 · Bentuk yang menentukan

### 4.1 `Tanggapan` hanya dibentuk dari `JawabanTervalidasi`

`susun()` menerima `JawabanTervalidasi`, bukan `KeluaranModel`. Tipe itu hanya
dapat dibentuk validator (fitur 008, R-09), sehingga jalur dari keluaran model
ke tanggapan **melewati validator karena tidak ada jalan lain** — bukan karena
pemanggilnya ingat.

Ketiga lapisan bertingkat, dan masing-masing menutup yang di bawahnya:

| Lapisan | Menutup |
|---|---|
| `JawabanTervalidasi` hanya dibentuk validator | jalur pintas dari keluaran model |
| `susun()` hanya menerima `JawabanTervalidasi` | jalur pintas dari `KeluaranModel` |
| Pemeriksa C-19 aturan 1 | pembentukan `JawabanTervalidasi` di luar validator |

### 4.2 Penolakan berbentuk jawaban, bukan galat

D-14 Bagian 4.1: keadaan `tidak_ditemukan` dan `di_luar_domain` memakai bentuk
yang **sama** dengan ringkasan dan klaim kosong — *"bentuk yang seragam inilah
yang membuat layar D-05 dapat menampilkannya sebagai jawaban sah, bukan pesan
galat."*

`Tanggapan.tolak_domain()` dan `Tanggapan.tidak_ditemukan()` karena itu
menghasilkan `Tanggapan` yang sah, bukan menaikkan galat. D-02 titik kritis T3:
sistem yang mengaku tidak tahu justru memperkuat kepercayaan.

### 4.3 Cakupan domain: daftar hitam, dan arahnya berlawanan dengan fitur 006

Fitur 006 memilih **daftar putih** bagi lisensi. Di sini dipilih **daftar
hitam**, dan pembedaannya bukan ketidakkonsistenan melainkan arah kerugian:

| | Kekeliruan ke arah longgar | Kekeliruan ke arah ketat |
|---|---|---|
| Lisensi (006) | **Menggugurkan publikasi** | Mengurangi jumlah butir |
| Cakupan domain (009) | Biaya satu panggilan LLM yang berakhir tidak-ditemukan | **Menolak kepala sekolah yang bertanya wajar** |

D-02 titik kritis T1: jawaban pertama menentukan retensi. Kepala sekolah yang
pertanyaan sahnya ditolak tidak bertanya kedua kalinya.

Batasnya wajib tertulis pada uraian modul: daftar hitam meloloskan yang belum
pernah terlihat, dan penutupnya **kecukupan bukti** — pertanyaan di luar domain
tidak memiliki segmen pendukung sehingga berakhir `tidak_ditemukan`. FR-F13
memangkas biaya dan mempercepat; ia bukan lapisan tunggal.

### 4.4 `dicabut` menolak pembentukan, `diubah` menuntut catatan

D-07 Bagian 4.5 memisahkan keduanya tegas, dan `Tanggapan` menegakkannya
sebagai bentuk:

- **`dicabut`** → tanggapan tidak dapat dibentuk. Validator sudah menolaknya
  (VS-06), dan ini lapisan kedua: yang lolos validator karena jalur lain tetap
  tidak dapat tayang.
- **`diubah`** → `catatan_keberlakuan` wajib terisi beserta rujukan
  pengubahnya. Kosong dengan sitasi `diubah` adalah temuan.

---

## 5 · Rencana uji mutasi

| | Mutasi | Uji yang harus menyala |
|---|---|---|
| M-1 | `Tanggapan` menerima bidang tambahan | R-01, pemeriksa C-20 aturan 1 |
| M-2 | Satu bidang D-14 dihapus dari `Tanggapan` | pemeriksa C-20 aturan 1 |
| M-3 | `susun()` menerima `KeluaranModel` | R-10 |
| M-4 | `di_luar_domain` tetap memuat klaim | R-04 |
| M-5 | Daftar hitam domain menolak kata manajerial yang wajar | uji pertanyaan sah diterima |
| M-6 | Segmen `indeks_metadata` masuk `sitasi` | R-09 |
| M-7 | Sitasi `diubah` tanpa `catatan_keberlakuan` diterima | R-07 |
| M-8 | Sitasi `dicabut` dapat dibentuk | R-08 |
| M-9 | Kalimat 21 kata diterima | R-11 |

---

## 6 · Ketergantungan

**Nol paket baru.** Seluruh bagian 1 adalah model pydantic dan pembacaan
bentuk.

Yang **akan** menuntut ketergantungan adalah fitur 021 — `fastapi`, `uvicorn`,
dan `httpx` bagi ujinya — dan itu sebabnya ia dipisah, bukan sebabnya ia
ditunda.

---

## 7 · Yang berpindah ke fitur 021

| | Menunggu |
|---|---|
| Rute `/api/v1/tanya` dan kendali peran | **FastAPI** — C-12 |
| Jawaban terkurasi 20 pertanyaan (FR-F12) | Kurator; isinya pekerjaan orang |
| Riwayat percakapan (FR-F09) | Penyimpanan percakapan |

**Yang ditunggu fitur 021 adalah satu keputusan rapat**, bukan orang yang
bekerja berbulan-bulan. Ia yang paling murah dibuka dari seluruh yang menunggu
— dan bersama keputusan model sematan, keduanya membuka empat fitur: 019, 020,
021, dan bagian kedua 009.
