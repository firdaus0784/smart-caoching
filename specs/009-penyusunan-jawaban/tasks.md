# Tasks: 009-penyusunan-jawaban

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 (KB-039) |
| Plan | `plan.md`, lolos Gerbang 2 (KB-039) |
| Status | **Lolos Gerbang 4** — 12 Agustus 2026 (KB-040). Lima tugas selesai |
| Jumlah tugas | **5** |
| Ketergantungan baru | **Nol** |

## Fase A · Cakupan domain

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `domain.py` — tahap 1 D-07 Bagian 4.1 | **Uji: pertanyaan manajerial yang memuat kata berdekatan dengan ranah terlarang TETAP DITERIMA.** Uji: keempat ranah FR-F13 ditolak. Uji: penolakan menyebut cakupan sistem, bukan galat | R-02, R-03 | [x] — pola menuntut kata ranah **dan** penanda subjek pribadi |

**Uji yang paling mudah keliru ada di sini.** "Pertanyaan medis ditolak"
dipenuhi juga oleh penyaring yang menolak setiap pertanyaan yang menyebut
"kesehatan" — dan "bagaimana mengelola program kesehatan sekolah" adalah
pertanyaan manajerial yang sah. D-02 titik kritis T1: kepala sekolah yang
pertanyaan sahnya ditolak tidak bertanya kedua kalinya.

## Fase B · Bentuk tanggapan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | `tanggapan.py` — `Tanggapan`, `Sitasi`, `BacaanLanjutan` | **Uji: bidang dibaca dari `docs/D14.md` Bagian 4.1, bukan disalin ke uji.** Uji: bidang tambahan ditolak. Uji: `tidak_ditemukan` menuntut ringkasan dan klaim kosong | R-01, R-04, R-05, R-06 | [x] — sepuluh bidang dibaca dari blok JSON D-14 sungguhan |
| B-2 | Keberlakuan dan bacaan lanjutan | **Uji: sitasi `dicabut` tidak dapat dibentuk.** Uji: sitasi `diubah` menuntut catatan beserta pengubahnya. Uji: segmen `indeks_metadata` tidak pernah pada `sitasi` | R-07, R-08, R-09 | [x] — `BacaanLanjutan` bertipe berbeda, bukan `Sitasi` yang lebih lemah |

**B-1 adalah C-20 itu sendiri.** D-14 menyatakan alasannya: bentuk tanggapan
"adalah tempat C-02, C-07, dan C-19 diwujudkan". Bidang tambahan yang tampak
tidak berbahaya memindahkan penilaian dari sistem ke klien, dan klien tidak
terikat konstitusi.

## Fase C · Penyusun dan pemeriksanya

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | `susun.py` — dari `JawabanTervalidasi` | **Uji: `susun()` tidak menerima `KeluaranModel`.** Uji: kalimat > 20 kata ditolak. Uji: tidak menulis apa pun | R-10, R-11, R-12 | [x] — lapisan kedua dari tiga; menghapus satu meninggalkan dua |
| C-2 | Pemeriksa C-20 dan pemindahannya pada `daftar_pasal.py` | **Uji: `make compliance` menyusut satu — 12 lulus, 8 belum.** Uji: kedua aturan menyala pada pohon yang sengaja dirusak. Uji: rute di luar D-14 ditemukan | R-01, R-13 | [x] — aturan 2 diuji dengan rute yang benar-benar dideklarasikan |

**C-1 adalah lapisan kedua, bukan lapisan pertama.** Yang menjaga jalur dari
keluaran model ke tanggapan sudah tiga: `JawabanTervalidasi` hanya dibentuk
validator, `susun()` hanya menerima tipe itu, dan pemeriksa C-19 aturan 1.
Ketiganya bertingkat; menghapus salah satunya meninggalkan dua.

## Verifikasi akhir

- [x] `make check` lulus 6 gerbang
- [x] `make compliance` **menyusut satu** — 12 lulus, 0 gagal, **8** belum
- [x] Kesembilan uji mutasi `plan.md` Bagian 5 dijalankan; **seluruhnya menyala**
- [x] Cakupan uji tidak turun — 99,81% atas 2.229 pernyataan; penanda naik ke 99,81
- [x] **Nol ketergantungan baru**
- [x] `src/api/` **tidak** dibuat

## Hasil kesembilan uji mutasi

| | Mutasi | Uji yang menyala |
|---|---|---|
| M-1 | `Tanggapan` menerima bidang tambahan | 3 |
| M-2 | Satu bidang D-14 dihapus | 6 |
| M-3 | `susun()` menerima `KeluaranModel` | 2 |
| M-4 | `di_luar_domain` tetap memuat klaim | 2 |
| M-5 | Daftar hitam domain berkata tunggal | 2 |
| M-6 | Segmen `indeks_metadata` masuk `sitasi` | 1 |
| M-7 | Sitasi `diubah` tanpa catatan diterima | 1 |
| M-8 | Sitasi `dicabut` dapat dibentuk | 1 |
| M-9 | Kalimat 21 kata diterima | 2 |

Seluruh sembilan menyala. **Satu kekeliruan saya pada perkakas mutasinya
sendiri**: `\n` harfiah masuk ke berkas sumber dan merusaknya, sehingga M-2
s.d. M-9 sempat melaporkan "0 uji menyala" — bukan karena ujinya lemah
melainkan karena pengumpulan uji gagal seluruhnya. Angka nol yang terbaca
seperti kelulusan adalah bentuk TA-01 pada perkakas saya sendiri. Perkakasnya
ditulis ulang agar membedakan galat pengumpulan dari nol kegagalan, lalu
kesembilan mutasi dijalankan ulang.

## Yang tidak dikerjakan di sini

Rute `/api/v1/tanya`, kendali peran, jawaban terkurasi FR-F12, dan riwayat
percakapan — seluruhnya **fitur 021**, tertahan pada **FastAPI** yang belum
ada pada `ketergantungan-disetujui.toml`.

Itu pemisahan ketujuh, dan yang pertama tertahan **satu keputusan rapat** —
bukan orang yang bekerja berbulan-bulan, bukan korpus, bukan model yang harus
dilatih.
