# Tasks: 009-penyusunan-jawaban

Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 (KB-039) |
| Plan | `plan.md`, lolos Gerbang 2 (KB-039) |
| Status | Menunggu Gerbang 3 |
| Jumlah tugas | **5** |
| Ketergantungan baru | **Nol** |

## Fase A · Cakupan domain

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | `domain.py` — tahap 1 D-07 Bagian 4.1 | **Uji: pertanyaan manajerial yang memuat kata berdekatan dengan ranah terlarang TETAP DITERIMA.** Uji: keempat ranah FR-F13 ditolak. Uji: penolakan menyebut cakupan sistem, bukan galat | R-02, R-03 | [ ] |

**Uji yang paling mudah keliru ada di sini.** "Pertanyaan medis ditolak"
dipenuhi juga oleh penyaring yang menolak setiap pertanyaan yang menyebut
"kesehatan" — dan "bagaimana mengelola program kesehatan sekolah" adalah
pertanyaan manajerial yang sah. D-02 titik kritis T1: kepala sekolah yang
pertanyaan sahnya ditolak tidak bertanya kedua kalinya.

## Fase B · Bentuk tanggapan

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | `tanggapan.py` — `Tanggapan`, `Sitasi`, `BacaanLanjutan` | **Uji: bidang dibaca dari `docs/D14.md` Bagian 4.1, bukan disalin ke uji.** Uji: bidang tambahan ditolak. Uji: `tidak_ditemukan` menuntut ringkasan dan klaim kosong | R-01, R-04, R-05, R-06 | [ ] |
| B-2 | Keberlakuan dan bacaan lanjutan | **Uji: sitasi `dicabut` tidak dapat dibentuk.** Uji: sitasi `diubah` menuntut catatan beserta pengubahnya. Uji: segmen `indeks_metadata` tidak pernah pada `sitasi` | R-07, R-08, R-09 | [ ] |

**B-1 adalah C-20 itu sendiri.** D-14 menyatakan alasannya: bentuk tanggapan
"adalah tempat C-02, C-07, dan C-19 diwujudkan". Bidang tambahan yang tampak
tidak berbahaya memindahkan penilaian dari sistem ke klien, dan klien tidak
terikat konstitusi.

## Fase C · Penyusun dan pemeriksanya

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | `susun.py` — dari `JawabanTervalidasi` | **Uji: `susun()` tidak menerima `KeluaranModel`.** Uji: kalimat > 20 kata ditolak. Uji: tidak menulis apa pun | R-10, R-11, R-12 | [ ] |
| C-2 | Pemeriksa C-20 dan pemindahannya pada `daftar_pasal.py` | **Uji: `make compliance` menyusut satu — 12 lulus, 8 belum.** Uji: kedua aturan menyala pada pohon yang sengaja dirusak. Uji: rute di luar D-14 ditemukan | R-01, R-13 | [ ] |

**C-1 adalah lapisan kedua, bukan lapisan pertama.** Yang menjaga jalur dari
keluaran model ke tanggapan sudah tiga: `JawabanTervalidasi` hanya dibentuk
validator, `susun()` hanya menerima tipe itu, dan pemeriksa C-19 aturan 1.
Ketiganya bertingkat; menghapus salah satunya meninggalkan dua.

## Verifikasi akhir

- [ ] `make check` lulus 6 gerbang
- [ ] `make compliance` **menyusut satu** — 12 lulus, 0 gagal, **8** belum
- [ ] Kesembilan uji mutasi `plan.md` Bagian 5 dijalankan; hasilnya dilaporkan apa adanya
- [ ] Cakupan uji tidak turun
- [ ] **Nol ketergantungan baru**
- [ ] `src/api/` **tidak** dibuat — kerangka kosong yang menunggu FastAPI

## Yang tidak dikerjakan di sini

Rute `/api/v1/tanya`, kendali peran, jawaban terkurasi FR-F12, dan riwayat
percakapan — seluruhnya **fitur 021**, tertahan pada **FastAPI** yang belum
ada pada `ketergantungan-disetujui.toml`.

Itu pemisahan ketujuh, dan yang pertama tertahan **satu keputusan rapat** —
bukan orang yang bekerja berbulan-bulan, bukan korpus, bukan model yang harus
dilatih.
