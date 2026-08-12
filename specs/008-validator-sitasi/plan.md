# Plan: 008-validator-sitasi

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 — 12 Agustus 2026, KB-036 |
| Status | Menunggu Gerbang 2 |
| Ketergantungan baru | **Nol paket Python** |
| Pertanyaan terbuka | **Nol** — ketiganya dijawab pada KB-036 |

---

## 1 · Jawaban atas ketiga pertanyaan

| | Pertanyaan | Putusan |
|---|---|---|
| 1 | `IndeksTujuan` kembar | **A** — modul kamus `src/kamus/`; tepi `ingest → llm` sekaligus ditulis |
| 2 | `StatusKeberlakuan` | **Ditambahkan sekarang** — pengendali sebelum yang dikendalikannya |
| 3 | Pemeriksaan belum-dapat-diperiksa | **A** — jawaban tidak dinyatakan tervalidasi |

---

## 2 · Letak modul

```
src/kamus/
  segmen.py       IndeksTujuan, Peringkat, StatusKeberlakuan   D-14 Bagian 5
src/rag/validator/
  keluaran.py     Klaim, KeluaranModel, SegmenRujukan          kontrak D-14 4.1
  pemeriksaan.py  KodePemeriksaan, Status, HasilPemeriksaan     R-08, R-10
  sitasi.py       VS-01, VS-02, VS-04, VS-06, VS-08             R-01 s.d. R-05
  penyimpangan.py VS-09                                         R-07
  validator.py    penyusun; JawabanTervalidasi                  R-06, R-09, R-10
perkakas/pemeriksa/
  peringkat_klaim.py  pemeriksa C-19                            R-05, R-09
```

### `src/kamus/` — satu direktori baru, dan alasannya

`IndeksTujuan` didefinisikan dua kali: `src/llm/tipe.py` (fitur 001) dan
`src/penyimpanan/indeks.py` (fitur 006). **Kekeliruan saya pada fitur 006.**

Yang membuatnya lebih dari kerapian: enum itu tempat C-02 terbaca. Dua
definisi berarti perubahan D-14 kelak dapat memperbarui satu dan melewatkan
yang lain, dan tidak satu uji pun gagal karenanya. Kalimat proyek ini sendiri,
diulang pada enam berkas: *yang berbeda adalah yang tidak diperbarui.*

`src/kamus/` **tidak mengimpor apa pun dari `src/`**. Ia lapisan di bawah
`src/penyimpanan/`, dan sifat itu ditegakkan uji — modul kamus yang mengimpor
lapisan lain akan menjadi tempat ketergantungan melingkar bersembunyi.

`AGENTS.md` bertambah dua baris: `src/kamus/` pada daftar arsitektur, dan tepi
`ingest → llm` yang **sudah ada sejak fitur 002 tanpa pernah dituliskan** —
`src/ingest/dokumen.py`, `gerbang.py`, dan `peringkat.py` ketiganya mengimpor
`Peringkat` dari `src/llm/tipe.py`. Menemukannya sekarang dan tidak
menuliskannya berarti membiarkannya tetap kebiasaan tak berdokumen.

**`Peringkat` pindah ke `src/kamus/`; `src/llm/tipe.py` mengimpornya.** Dengan
itu tepi `ingest → llm` yang lahir hanya demi `Peringkat` menjadi tidak perlu —
tetapi ia tetap dituliskan, sebab `src/ingest/gerbang.py` memakainya untuk hal
lain, dan tepi yang dihapus dari dokumen sementara impornya masih ada lebih
buruk daripada tepi yang tidak pernah ditulis.

---

## 3 · Bentuk yang menentukan

### 3.1 Tiga keadaan, dan mengapa keenam kalinya masih perlu ditulis

`Status` bernilai `LULUS`, `GAGAL`, `BELUM_DAPAT_DIPERIKSA`.

Tiga dari sembilan pemeriksaan tidak dapat dibangun hari ini. Validator yang
mengembalikan `True` atas kesembilannya tidak dapat dibedakan dari validator
yang benar — dan tempat kekeliruan itu berdiam adalah komponen yang D-04
ADR-04 sebut "terpenting dalam sistem".

`HasilValidasi.tervalidasi` adalah **sifat terhitung, bukan bidang**. Bidang
dapat diisi `True` oleh pemanggil yang lelah; sifat terhitung menuntut
kesembilan pemeriksaan berstatus `LULUS`.

Bentuknya sengaja sama dengan `make compliance`. Perkakas yang menegakkan
pelajaran TA-01 pada proyek kini menegakkannya pada sistem.

### 3.2 `JawabanTervalidasi` hanya dibentuk validator

Mengikuti ADR-13, yang membatasi pembentukan `Instruksi` pada satu modul dan
sudah punya pemeriksa. Fitur 009 kemudian tidak **memiliki cara** menayangkan
jawaban yang belum lewat validator — bukan dilarang, melainkan tidak bisa.

C-01 tetap tidak berpindah karena ini; lihat Bagian 5.

### 3.3 VS-08 tidak bergantung pada BT-64

D-14 Bagian 4.1 menyatakan arti `klaim[].peringkat_kepercayaan` pada klaim
campuran adalah **keputusan BT-64, bukan keputusan pelaksana**.

Pemeriksaan VS-08 dirumuskan agar tidak menyentuhnya: sebuah klaim melanggar
bila **seluruh** penopangnya T3 atau T4. Pernyataan itu benar pada ketiga
pilihan BT-64 — peringkat terbaik, terburuk, maupun larik sejajar.

Uji yang menjaganya bukan "T3 saja ditolak" melainkan **"T1 dan T3 sekaligus
diterima"**. D-13 Bagian 6 mewajibkan bentuk campuran itu: T3 *"boleh menopang,
tetapi klaim memerlukan segmen T1 atau T2"*. Validator yang menolaknya akan
membuang jawaban yang sah, lalu dilonggarkan orang — dan yang longgar bersamanya
adalah VS-08.

### 3.4 Dua tingkat pembuangan, dan bedanya disengaja

D-07 Bagian 6.2 membedakan keduanya, dan pembedaannya bukan gradasi keparahan:

- **VS-01, VS-02, VS-03 gagal sebagian** → klaimnya dibuang, jawaban lanjut.
  Ini kekeliruan **penyusunan**; model menyusun klaim yang tidak tertopang.
- **VS-04, VS-06 gagal** → seluruh jawaban dibuang, **dicatat sebagai insiden
  kepatuhan**. Ini bukan kekeliruan penyusunan melainkan **gerbang yang
  bocor**: segmen yang tidak boleh terjangkau ternyata terjangkau.

Membuang klaimnya saja pada kasus kedua akan menghasilkan jawaban yang tampak
sehat di atas gerbang yang rusak.

### 3.5 VS-09 tanpa daftar hitam kata

Yang diperiksa **bentuk**, bukan kosakata: kontrak D-14 Bagian 4.1 dipenuhi,
tautan yang muncul berasal dari metadata sumber yang benar-benar diambil, dan
keluaran tidak memuat bentuk instruksi.

Daftar hitam kata ditolak: ia meloloskan setiap ungkapan yang belum pernah
terlihat, dan yang belum pernah terlihat justru yang dipakai penyerang. Sama
alasannya dengan daftar putih lisensi pada fitur 006, dari arah sebaliknya.

**Tautan diperiksa terhadap tautan segmen yang diambil**, bukan terhadap daftar
ranah tepercaya. Ranah tepercaya adalah daftar yang bertambah, dan yang
bertambah akan ditambahi.

---

## 4 · Pemeriksa C-19

C-19 kini `fitur_pengunci="008 validator sitasi"`. Sesudah fitur ini ia menjadi
`pemeriksa=periksa_peringkat_klaim`, dengan tiga aturan:

1. **`JawabanTervalidasi` hanya dibentuk pada `src/rag/validator/`.** Bentuk
   yang sama dengan aturan `Instruksi` ADR-13, yang sudah terbukti.
2. **Daftar pemeriksaan meliputi setiap anggota `KodePemeriksaan`.** Menjatuhkan
   VS-08 dari daftar jalannya adalah cara termudah melanggar C-19 tanpa
   menyentuh satu baris logika pun.
3. **`KodePemeriksaan` memuat persis kesembilan kode D-07 Bagian 6.1.** Tanpa
   aturan ini, aturan 2 dapat dipuaskan dengan menghapus VS-08 dari enumnya.

Aturan 3 menutup aturan 2, dan tanpa keduanya aturan 1 menjaga bentuk yang
isinya boleh kosong. **Diuji terhadap pohon yang sengaja dirusak.**

---

## 5 · C-01 tidak berpindah, dan daftar pasal dikoreksi

`daftar_pasal.py` mencatat C-01 dengan `fitur_pengunci="008 validator sitasi"`.
Itu keliru: verifikasi yang C-01 tuntut mencakup VS-03 — dukungan isi, bukan
sekadar keberadaan id — dan VS-03 menunggu model sematan serta ambang BT-29.

Tanpa VS-03, klaim yang mengutip segmen yang sama sekali tidak membahasnya
tetap lolos. Menandai C-01 lulus akan membuat MK-07 berarti *"100% klaim
menyebut id yang ada"*, dan angka itu masuk naskah.

`fitur_pengunci` C-01 karena itu **dikoreksi** menjadi menyebut fitur 020 dan
VS-03. Mengoreksi alasan tunggu bukan menambah utang — ia membuat utang yang
sudah ada terbaca benar.

---

## 6 · Rencana uji mutasi

| | Mutasi | Uji yang harus menyala |
|---|---|---|
| M-1 | `tervalidasi` menjadi bidang, bukan sifat terhitung | R-10 |
| M-2 | `BELUM_DAPAT_DIPERIKSA` diperlakukan sebagai lulus | R-10 |
| M-3 | VS-08 menolak klaim yang memuat **satu** segmen T3 | uji T1+T3 diterima |
| M-4 | VS-08 dijatuhkan dari daftar pemeriksaan | pemeriksa C-19 aturan 2 |
| M-5 | VS-04 membuang klaimnya saja, bukan seluruh jawaban | R-03 |
| M-6 | Ringkasan kosong tetap ditayangkan | R-06 |
| M-7 | VS-02 memeriksa keberadaan id pada klaim, bukan pada segmen terambil | R-02 |
| M-8 | Tautan diperiksa terhadap daftar ranah, bukan metadata segmen | R-07 |
| M-9 | Kode pemeriksaan yang gagal tidak ikut dilaporkan | R-08 |

---

## 7 · Ketergantungan

**Nol paket baru.** Seluruh pemeriksaan pada bagian 1 adalah perbandingan
himpunan dan pembacaan bentuk.

Yang **akan** menuntut ketergantungan adalah fitur 020 — VS-03 dan VS-05
menuntut model sematan, VS-07 menuntut model NER — dan itu sebabnya ia dipisah.

---

## 8 · Yang berpindah ke fitur 020

| | Menunggu |
|---|---|
| VS-03 dukungan isi klaim | Model sematan (fitur 019) **dan** ambang BT-29 |
| VS-05 batas penyalinan | Ambang BT-29 |
| VS-07 nama perorangan | Model NER (fitur 017) → korpus teranotasi bulan 2–4 |
| **Pemindahan C-01** | VS-03 |

Dua ketergantungan berbeda, bukan satu. VS-07 tertahan paling jauh: fitur 017
menunggu pekerjaan dua mahasiswa yang belum lulus uji kualifikasi.
