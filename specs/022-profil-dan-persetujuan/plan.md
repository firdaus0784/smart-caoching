# Plan: 022-profil-dan-persetujuan

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 (KB-046) |
| Ketergantungan baru | **Nol** |
| Status | **Lolos Gerbang 1–3** (KB-046) |

## 1 · Letak modul

```
src/pengguna/                 baru
    profil.py                 enam bidang D-04 Bagian 7.1
    prioritas.py              3–5 kategori K1–K8, berurutan
    persetujuan.py            empat keadaan; pencabutan menghentikan seketika
src/penyimpanan/
    pseudonim.py              antarmuka terpisah, di luar jangkauan Area
perkakas/pemeriksa/
    peta_pseudonim.py         pemeriksa C-05
```

**`src/pengguna/` adalah lapisan baru, dan `AGENTS.md` bertambah satu baris.**
Ia tidak masuk `src/api/` karena bukan titik masuk, tidak masuk `src/nlp/`
karena tidak mengolah bahasa, dan tidak masuk `src/ingest/` karena tidak
menerima dokumen. Menaruhnya di salah satu dari ketiganya akan menjadi
kebiasaan tak berdokumen — persis yang pemeriksa arah fitur 009 ada untuk
mencegah.

Arahnya: **`src/pengguna/` boleh memanggil `src/kamus/` dan `src/nlp/`**
(bagi `KategoriMasalah`), satu jurusan. Tidak ada yang memanggilnya balik pada
fitur ini; fitur 011 dan 012 kelak memanggilnya dari `api`.

`pseudonim.py` tinggal di `src/penyimpanan/` karena ia soal **akses**, bukan
soal pengguna — dan `src/penyimpanan/` yang menegakkan C-03 dengan cara yang
sama.

## 2 · Bentuk yang menentukan

### 2.1 `KeadaanPersetujuan` — empat, dan dua pembedaan yang mudah hilang

```
BELUM_DIMINTA   pekerjaan yang belum dilakukan
DITOLAK         keputusan partisipan
DIBERIKAN       satu-satunya yang mengizinkan perekaman
DICABUT         keputusan partisipan, sesudah pernah memberi
```

Ketiga selain `DIBERIKAN` menghentikan perekaman — tetapi ketiganya **tidak
boleh disatukan**, sebab laporan partisipasi wajib membedakan orang yang
menolak dari orang yang belum ditanya, dan data yang sudah terekam sebelum
pencabutan kehilangan penjelasannya bila `DICABUT` dicatat sebagai `DITOLAK`.

**Sifat `boleh_merekam` berupa properti terhitung**, dan hanya `DIBERIKAN` yang
menghasilkan benar. Bidang boolean di sini akan diisi `True` oleh pemanggil
yang lelah — dan yang dilewati bersamanya adalah C-04.

### 2.2 Gabungan mustahil ditolak saat pembentukan

| `disetujui` | `dicabut_pada` | Keadaan |
|---|---|---|
| — (tanpa catatan) | — | `BELUM_DIMINTA` |
| salah | kosong | `DITOLAK` |
| benar | kosong | `DIBERIKAN` |
| benar | terisi | `DICABUT` |
| **salah** | **terisi** | **ditolak saat pembentukan** |

Baris terakhir yang menjadi uji. Penolakan yang membawa waktu pencabutan tidak
berarti apa pun, dan yang tidak berarti apa pun akan ditafsirkan berbeda oleh
dua pembaca.

### 2.3 Pencabutan menuntut waktu, dan waktunya tidak boleh mendahului persetujuan

`dicabut_pada` lebih awal daripada `tanggal` berarti perekaman berhenti sebelum
ia diizinkan — keadaan yang tidak dapat terjadi dan karena itu ditolak.

### 2.4 Menolak tidak mengurangi apa pun — R-07 ditegakkan bentuk

Tidak ada bidang, sifat, maupun fungsi pada modul ini yang memetakan keadaan
persetujuan ke tingkat akses. Ketiadaan itu **diuji**: uji menegakkan bahwa
permukaan modul tidak menyediakan cara menurunkan akses berdasarkan
persetujuan.

Uji yang menegakkan ketiadaan diperlukan karena R-07 tidak dapat dibuktikan
dengan menjalankan apa pun — ia larangan, dan larangan hanya terlihat pada
bentuk. Bentuk yang sama dengan C-17 pada fitur 001.

### 2.5 Peta pseudonim — kredensial yang tidak dimiliki siapa pun di `src/`

`peta_pseudonim` diakses lewat antarmuka tersendiri yang menuntut
`KredensialPseudonim` — tipe **berbeda** dari `Kredensial`, bukan nilai lain
padanya. Tipe berbeda berarti kredensial layanan aplikasi tidak dapat
dipakaikan ke sana **oleh kekeliruan pengetikan mana pun**, sedangkan nilai
lain pada tipe yang sama hanya dijaga pemeriksaan saat jalan.

`src/` tidak memuat satu pun pembentukan `KredensialPseudonim`. Ia dibentuk
hanya pada uji dan kelak pada lingkungan penelitian yang terpisah — itulah
wujud "tidak terjangkau layanan aplikasi" pada C-05.

## 3 · Pemeriksa C-05

| # | Aturan |
|---|---|
| 1 | `KredensialPseudonim` **tidak dibentuk di mana pun pada `src/`** |
| 2 | Modul di luar `src/penyimpanan/pseudonim.py` **tidak mengimpor** peta pseudonim |
| 3 | `Area` tetap bernilai persis dua — `karantina` dan `korpus` (AG-04, D-14 Bagian 5.1) |

Aturan 3 menutup lubang dua aturan pertama: memindahkan peta pseudonim menjadi
nilai ketiga pada `Area` akan memuaskan keduanya sambil membatalkan C-05.
Bentuk yang sama dengan aturan VS-08 pada pemeriksa C-19 (fitur 008).

Diuji terhadap pohon yang sengaja dirusak, masing-masing aturan terpisah.

## 4 · Uji mutasi

| | Mutasi | Uji yang harus menyala |
|---|---|---|
| M-1 | `DICABUT` diperlakukan sebagai `DIBERIKAN` | R-06 |
| M-2 | `BELUM_DIMINTA` disamakan dengan `DITOLAK` | R-05 |
| M-3 | `boleh_merekam` menjadi bidang, bukan sifat | R-06 |
| M-4 | Gabungan mustahil (salah + tercabut) diterima | R-05 |
| M-5 | Prioritas menerima 2 atau 6 kategori | R-03 |
| M-6 | Prioritas menerima kategori kembar | R-04 |
| M-7 | Profil menerima bidang ketujuh | R-02 |
| M-8 | `KredensialPseudonim` dibentuk pada `src/` | pemeriksa C-05 aturan 1 |
| M-9 | `Area` bertambah nilai ketiga | pemeriksa C-05 aturan 3 |
| M-10 | `versi_naskah` boleh kosong | R-08 |

## 5 · Ketergantungan

**Nol.** Seluruhnya pydantic dan pustaka baku, keduanya sudah disetujui.
