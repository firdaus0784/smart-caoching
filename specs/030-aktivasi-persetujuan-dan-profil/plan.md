# Plan: 030-aktivasi-persetujuan-dan-profil

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 4 Oktober 2026 (KB-165); P-1 s.d. P-7 sesuai anjuran |
| Status | **Menunggu Gerbang 2.** Delapan keputusan rancangan (K-1 s.d. K-8) dan draf S-03 |
| Kebutuhan | R-01 s.d. R-10 `spec.md`; FR-A02 s.d. FR-A06; C-04, C-05, C-13, C-14, C-20 |

## 1. Letak dan batas

```
perkakas/basis_data/
  01-peran-dan-basis-data.sql   + peran_pengguna
  08-pengguna.sql               baru — skema pengguna: profil_sekolah,
                                prioritas_manajerial, persetujuan
src/penyimpanan/pengguna.py     baru — PenyimpanPengguna, memori dan PostgreSQL
src/api/saya.py                 baru — penerjemah empat rute D-14 3.1
src/api/aplikasi.py             pemasangan rute /saya/* bila penyimpannya diberikan
src/api/peran.py                POLA_* bagi empat rute, diambil dari PETA_RUTE
web/public/naskah/              tempat berkas naskah persetujuan yang diisi tim (P-1)
web/src/aktivasi/               S-02, S-03, S-04; cangkang memperoleh tahap aktivasi
docs/                           D-14 4.5 dan 5.1; D-04 7.1 (TK-50); D-05 S-02 s.d. S-04
AGENTS.md                       tepi api → pengguna (K-1)
```

**Model fitur 022 dipakai, tidak ditulis ulang.** `ProfilSekolah`,
`PrioritasManajerial`, dan `CatatanPersetujuan` sudah menegakkan batas enam
isian, tiga sampai lima prioritas tanpa kembar, penolakan data pribadi pada
`wilayah`, dan versi naskah wajib. Rute hanya menerjemahkan.

**`src/rag/`, `src/llm/`, dan `src/telemetri/` tidak disentuh.** Gerbang
perekaman fitur 012 sudah membaca `KeadaanPersetujuan`; fitur ini menyediakan
sumber keadaan itu, tidak mengubah gerbangnya.

## 2. K-1 · Tepi `api → pengguna`

AGENTS.md menulis `api` boleh memanggil `nlp`, `rag`, `ingest`, `llm`,
`penyimpanan` — **tidak `pengguna`**, dan pemeriksa arah V-03 membaca daftar
itu. Rute `/saya/*` menerima badan yang wajib divalidasi `ProfilSekolah`,
`PrioritasManajerial`, dan `CatatanPersetujuan`, ketiganya tinggal di
`src/pengguna/`.

| Pilihan | Arti |
|---|---|
| A | **Tepi `api → pengguna`, satu jurusan**, ditulis ke AGENTS.md dengan alasan umum: `api` satu-satunya titik masuk, sehingga setiap lapisan yang modelnya **diterima lewat rute** wajib terjangkau darinya — bentuk yang sama dengan tepi `telemetri → pengguna`. Arah sebaliknya terlarang: `pengguna` yang memanggil `api` membuat model profil bergantung pada bentuk HTTP |
| B | Validasi ditulis ulang di `src/api/` — dua tempat yang menegakkan batas enam isian dan tiga sampai lima prioritas akan berselisih, kekeliruan yang sama dengan `IndeksTujuan` yang ditulis dua kali |

**Anjuran: A.** Ini perubahan AGENTS.md, dan karena itu diajukan di sini,
bukan dilakukan diam-diam saat menulis kode.

## 3. Penyimpanan — K-2, K-3

### 3.1 Skema `pengguna` pada basis data perilaku

```sql
pengguna.profil_sekolah (
  id_pengguna text PRIMARY KEY,   -- pseudonim akun (P-7, R-02)
  jabatan text, masa_kerja int, jumlah_rombel int, jumlah_ptk int,
  jalur_akreditasi text,          -- visitasi | automasi (P-3)
  wilayah text, tanggal_perbarui timestamptz
)
pengguna.prioritas_manajerial (
  nomor bigint identity, id_pengguna text, kategori text[], ditetapkan_pada timestamptz
)                                 -- tambah-saja; yang berlaku baris terbaru (K-3)
pengguna.persetujuan (
  nomor bigint identity, id_pengguna text, jenis text, versi_naskah text,
  disetujui boolean, tanggal timestamptz, dicabut_pada timestamptz
)                                 -- tambah-saja kecuali dicabut_pada
```

### 3.2 K-2 · Peran tersendiri `peran_pengguna`

| Hak | Yang ditolak peladen |
|---|---|
| `profil_sekolah`: `SELECT`, `INSERT`, `UPDATE` atas tujuh kolom selain `id_pengguna` | memindahkan profil ke pengguna lain; `DELETE` |
| `prioritas_manajerial`: `SELECT`, `INSERT` | mengubah atau menghapus riwayat prioritas |
| `persetujuan`: `SELECT`, `INSERT`, `UPDATE (dicabut_pada)` | mengubah apa yang disetujui, versi naskah, maupun waktunya; `DELETE` |
| `CONNECT` basis data perilaku saja | basis data pseudonim (C-05); skema `akun`, `riwayat`, korpus, karantina |

**Anjuran:** peran tersendiri, bukan perluasan `peran_autentikasi`. Layanan
yang menulis profil tidak membutuhkan turunan sandi, dan sebaliknya.

### 3.3 K-3 · Prioritas tambah-saja

`PUT /saya/prioritas` menambah baris baru; yang berlaku baris terbaru.
**Anjuran: tambah-saja**, bukan timpa. Perubahan prioritas adalah data
penelitian tentang bagaimana kepala sekolah menata ulang perhatiannya, dan
penimpaan menghapusnya tanpa jejak. Penarikan data (NFR-09) tetap jalur
tersendiri.

Persetujuan tambah-saja dengan alasan yang lebih keras: catatan persetujuan
yang dapat disunting tidak membuktikan apa pun. Berubah pikiran sesudah
menolak menambah baris baru; mencabut sesudah setuju mengisi `dicabut_pada`
pada baris yang berlaku — satu-satunya kolom yang dapat diubah.

## 4. Naskah persetujuan — K-4 (P-1)

Naskah ET-02 tinggal pada **satu berkas** `web/public/naskah/persetujuan.json`:

```json
{ "versi": "et02-v1", "judul": "…", "paragraf": ["…", "…"] }
```

- Layar S-02 memuatnya dan menampilkannya **apa adanya**. Berkas ini tidak
  diperiksa pemeriksa C-13: kalimatnya milik komite etik, bukan mikrokopi
  aplikasi, dan menyuntingnya agar ≤ 20 kata mengubah naskah yang disetujui.
- Peladen menerima `versi_naskah` **hanya bila sama** dengan versi pada berkas
  yang sama, dibaca saat aplikasi disusun. Klien yang mengirim versi karangan
  ditolak 400.
- **Selama berkas itu belum ada**, S-02 menyatakan naskah belum tersedia dan
  tidak menampilkan tombol setuju; peladen menolak setiap persetujuan.
  Telemetri tetap mati bagi semua orang — C-04 terjaga tanpa kode tambahan.
- Agen **tidak membuat berkas naskah**, juga tidak naskah contoh di luar uji.

## 5. Bentuk rute — K-5, R-01

Ditulis ke D-14 Bagian 4.5 sebelum kodenya.

| Rute | Permintaan | Berhasil |
|---|---|---|
| `GET /api/v1/saya/profil` | — | 200 `{"profil": {…} \| null, "prioritas": ["K1", …], "persetujuan": "belum_diminta" \| "diberikan" \| "ditolak" \| "dicabut"}` |
| `PUT /api/v1/saya/profil` | enam bidang FR-A02 | 200, bentuk yang sama dengan `GET` |
| `PUT /api/v1/saya/prioritas` | `{"kategori": ["K5", "K1", "K7"]}` | 200, bentuk yang sama |
| `POST /api/v1/saya/persetujuan` | `{"versi_naskah": "…", "disetujui": true}` atau `{"cabut": true}` | 200, bentuk yang sama |

**K-5 · `GET /saya/profil` membawa ringkasan aktivasi.** Layar perlu tahu tiga
hal untuk memilih langkah — persetujuan sudah ditanya, profil sudah ada,
prioritas sudah ada — dan D-14 Bagian 3 tidak memuat rute lain yang dapat
menjawabnya. **Anjuran:** ketiganya pada `GET /saya/profil`; menambah rute
"status aktivasi" dilarang AG-02. Ketiga rute penulis mengembalikan bentuk
yang sama, sehingga layar tidak membaca dua kali.

`id_pengguna` dan `tanggal_perbarui` **tidak** dikirim maupun diterima:
pemiliknya ditentukan sesi (R-02), waktunya oleh peladen. Penolakan memakai
D-14 Bagian 4.2: 400 `VALIDASI_GAGAL` dengan kalimat yang tidak mengutip
masukan; 401 tanpa sesi; 403 bagi peran selain `pengguna`. Ketiganya
menuntut `application/json` (K-4 fitur 029).

## 6. Alur layar — K-6, R-07

```
S-01 Masuk ─► GET /saya/profil
   persetujuan = belum_diminta  ─► S-02
   profil = null                ─► S-03 (empat layar) ─► S-04
   selainnya                    ─► S-09 Tanya
```

- S-03 tampil **hanya menjelang S-04 pertama**: ia penjelasan sebelum mulai,
  bukan gerbang yang diulang.
- Menolak di S-02 tetap melanjutkan ke S-03 (R-03, FR-A05).
- S-09 memperoleh tautan **"Persetujuan penelitian"** yang membuka S-02 lagi
  dengan keadaannya sekarang: setuju sesudah menolak, atau mencabut sesudah
  setuju (P-5).
- S-04: enam isian, lalu pilihan prioritas berurutan dengan **label D-03
  Bagian 5 apa adanya** (K-7): "Kurikulum dan pembelajaran", "Kepegawaian dan
  tenaga kependidikan", dan seterusnya. Kode K1 s.d. K8 tidak tampil.

**K-6 · Bila rute `/saya/profil` gagal karena luring,** cangkang membuka S-09
seperti fitur 029 — aktivasi ditanyakan lagi pada pembukaan berikutnya.

## 7. Draf S-03 — P-2, diputus di Gerbang 2

Empat layar, satu gagasan per layar (AI-02), tiap kalimat ≤ 20 kata.

| Layar | Judul | Isi |
|---|---|---|
| 1 | Yang dapat dibantu | Aplikasi ini menjawab pertanyaan pengelolaan sekolah dasar. Setiap jawaban menyebut dokumen yang menjadi dasarnya. |
| 2 | Alat bantu, bukan penentu | Keputusan tetap berada pada Anda sebagai kepala sekolah. Jawaban membantu menimbang, tidak menggantikan pertimbangan Anda. |
| 3 | Bila dasarnya tidak ada | Bila tidak ada dokumen yang memuat jawabannya, aplikasi mengatakannya terus terang. Itu bukan kesalahan Anda. |
| 4 | Menjaga data | Akun Anda tidak memuat nama Anda. Jangan tulis nama orang atau nomor pribadi pada pertanyaan. |

Tombol: "Lanjut" pada layar 1 sampai 3, "Mulai mengisi profil" pada layar 4.
Tidak ada tombol "lewati" yang menyembunyikan layar 2: pernyataan bahwa sistem
alat bantu adalah satu-satunya isi yang FR-A04 wajibkan.

## 8. Keputusan rancangan Gerbang 2

| Kode | Pertanyaan | Anjuran |
|---|---|---|
| K-1 | Tepi `api → pengguna` pada AGENTS.md | **Ya**, satu jurusan — Bagian 2 |
| K-2 | Peran basis data tersendiri | **`peran_pengguna`** — Bagian 3.2 |
| K-3 | Prioritas ditimpa atau ditambah | **Tambah-saja** — Bagian 3.3 |
| K-4 | Letak dan perlakuan naskah persetujuan | **Satu berkas JSON berversi**, tanpa pemeriksa C-13, versi dicocokkan peladen — Bagian 4 |
| K-5 | Ringkasan aktivasi pada `GET /saya/profil` | **Ya** — Bagian 5 |
| K-6 | Luring saat memeriksa aktivasi | **Buka S-09**, tanyakan lagi lain kali — Bagian 6 |
| K-7 | Label prioritas pada S-04 | **Nama kategori D-03 apa adanya** |
| K-8 | Draf S-03 | Empat layar Bagian 7, atau kalimat pengganti dari tim |

## 9. Uji

### 9.1 Di dalam `make check`

- Perilaku penyimpan atas pelaksana memori **dan** PostgreSQL, tersambung
  sebagai `peran_pengguna` sendiri (TK-64).
- Penolakan peladen Bagian 3.2, tiap baris dengan sebabnya `permission denied`.
- Rute lewat `TestClient` dengan `PenentuSesi`: pemilik adalah pseudonim;
  pengguna B tidak membaca maupun menulis profil A; tujuh isian ditolak;
  dua atau enam prioritas ditolak; versi naskah karangan ditolak; tanpa berkas
  naskah setiap persetujuan ditolak; penolakan persetujuan tidak menghalangi
  `/tanya`.
- **C-14**: jalur penjawab tidak menerima profil maupun prioritas — diuji pada
  argumen `jawab`, sama dengan R-07 fitur 028.
- Layar: Vitest untuk tiap tahap alur, naskah yang belum ada, label D-03, dan
  tautan persetujuan dari S-09.

### 9.2 Di luar `make check`

Playwright terhadap `make jalan`: akun baru, masuk, S-02 dengan naskah uji
pada direktori sementara, S-03, S-04, Tanya; muat ulang tidak mengulang
aktivasi; tautan persetujuan mencabut.

### 9.3 Uji mutasi

| Kode | Mutasi | Uji yang wajib merah |
|---|---|---|
| M-1 | Pemilik profil dari badan permintaan, bukan sesi | dua pengguna |
| M-2 | Versi naskah tidak dicocokkan | versi karangan |
| M-3 | Persetujuan diterima tanpa berkas naskah | naskah belum ada |
| M-4 | `GRANT UPDATE (id_pengguna)` pada profil | penolakan peladen |
| M-5 | `GRANT UPDATE (disetujui)` pada persetujuan | penolakan peladen |
| M-6 | `GRANT CONNECT` basis data pseudonim kepada `peran_pengguna` | penolakan peladen |
| M-7 | Prioritas ditimpa, riwayat hilang | tambah-saja |
| M-8 | Penolakan persetujuan menghalangi `/tanya` | R-03 |
| M-9 | Profil diteruskan ke `jalur.jawab` | C-14 |
| M-10 | S-03 dapat dilewati langsung ke S-04 tanpa layar 2 | Vitest FR-A04 |
| M-11 | Kode K1 s.d. K8 tampil pada S-04 | Vitest K-7 |

## 10. Urutan tugas

| Tugas | Isi |
|---|---|
| T-1 | Kontrak lebih dulu: D-14 4.5 dan 5.1, D-04 7.1 (TK-50), D-05 S-02 s.d. S-04; AGENTS.md K-1 |
| T-2 | Peladen: `08-pengguna.sql`, `peran_pengguna`; M-4 s.d. M-6 |
| T-3 | `src/penyimpanan/pengguna.py`, dua pelaksana; M-7 |
| T-4 | Rute `/saya/*` dan naskah; M-1 s.d. M-3, M-8, M-9 |
| T-5 | Layar S-02, S-03, S-04, cangkang, tautan dari S-09; M-10, M-11 |
| T-6 | Putaran mutasi, Playwright, penutupan: D-00, L8, HKI, L4 |

## 11. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Naskah persetujuan tampak perlu ditulis agen | Berhenti; ET-02 |
| Perubahan `src/rag/`, `src/llm/`, atau `src/telemetri/` tampak perlu | Berhenti |
| Rute selain empat rute D-14 3.1 tampak perlu | Berhenti; AG-02 |
| Profil tampak perlu memengaruhi jawaban | Berhenti; C-14 |
| Paket baru tampak perlu | Berhenti; C-12 |
