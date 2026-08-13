# Plan: 012-telemetri

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 (KB-048) |
| Ketergantungan baru | **Nol** |
| Status | **Lolos Gerbang 1–3** (KB-048) |

## 1 · Letak modul

```
src/telemetri/
    peristiwa.py     taksonomi D-01 Bagian 9 + bentuk D-04 Bagian 7.4
    gerbang.py       C-04 — satu-satunya tempat Peristiwa dibentuk
    ekspor.py        CSV (FR-J03 separuh)
perkakas/pemeriksa/
    perekaman_telemetri.py   pemeriksa C-04
```

**`src/telemetri/` lapisan baru**, dan `AGENTS.md` bertambah satu baris —
kedua kalinya dalam satu hari sesudah `src/pengguna/`. Ia tidak masuk
`src/pengguna/` karena telemetri bukan profil, dan tidak masuk
`src/penyimpanan/` karena ia bukan soal akses.

Arahnya: **`telemetri` boleh memanggil `pengguna` dan `nlp`**, satu jurusan.
Yang pertama bagi `KeadaanPersetujuan` — C-04 dibaca dari sana. Yang kedua
bagi pendeteksi data pribadi FR-B04. `pengguna` tidak memanggil `telemetri`:
profil yang bergantung pada rekaman perilaku membalik arah C-04.

## 2 · Bentuk yang menentukan

### 2.1 `rekam()` mengembalikan `Peristiwa | None`, bukan melempar galat

Pengguna yang tidak menyetujui **bukan keadaan galat**. Ia keadaan yang sah
dan diharapkan — FR-A05 menjamin menolak tidak mengurangi akses fitur inti.

Gerbang yang melempar galat akan mengundang pemanggil membungkusnya dengan
`try` yang juga menelan kekeliruan lain, dan pada akhirnya seseorang akan
menuliskan `except: pass` di sekeliling seluruh pemanggilan telemetri.

Bentuknya karena itu mengikuti `terapkan()` fitur 010 dan `validasi()` fitur
008: kembalian dua nilai, dan yang kedua **hanya ada bila boleh**.

```
rekam(...) -> tuple[HasilPerekaman, Peristiwa | None]
```

`HasilPerekaman` bernilai **tiga**: `DIREKAM`, `DILEWATI_TANPA_PERSETUJUAN`,
`DITOLAK_PROPERTI`. Pengulangan ketujuh pola "tiga keadaan, bukan dua" — dan
di sini ia memisahkan **tidak merekam karena tidak boleh** dari **tidak
merekam karena isinya cacat**. Menyamakannya membuat pelanggaran KM-03
terhitung sebagai pengguna yang menolak, lalu laporan partisipasi keliru.

### 2.2 Keadaan persetujuan adalah argumen, bukan bidang

`rekam()` menerima `KeadaanPersetujuan` setiap kali dipanggil. Tidak ada
tempat menyimpannya, dan itu yang membuat R-05 bekerja — lihat `spec.md`
Bagian 4.2.

### 2.3 `Peristiwa` tanpa bidang `id_pengguna`

Bukan memilikinya lalu mengosongkannya. Yang tidak ada tidak dapat terisi.

## 3 · Pemeriksa C-04

| # | Aturan |
|---|---|
| 1 | `Peristiwa` hanya dibentuk pada `src/telemetri/gerbang.py` |
| 2 | `Peristiwa` tidak memiliki bidang bernama identitas — `id_pengguna`, `nama`, `surel` |
| 3 | `rekam()` menerima parameter bertipe `KeadaanPersetujuan`, dan **tanpa nilai bawaan** |

Aturan 3 menutup dua yang pertama: gerbang yang parameternya berbawaan
`DIBERIKAN` memuaskan keduanya sambil membatalkan C-04 pada setiap pemanggilan
yang lupa mengisinya. Bentuk yang sama dengan aturan `AmbangKecukupan` pada
pemeriksa C-16.

Diuji terhadap pohon yang sengaja dirusak, masing-masing aturan terpisah.

## 4 · Uji mutasi

| | Mutasi | Uji yang harus menyala |
|---|---|---|
| M-1 | `DICABUT` diperlakukan boleh merekam | R-04, R-05 |
| M-2 | `BELUM_DIMINTA` diperlakukan boleh merekam | R-04 |
| M-3 | Keadaan persetujuan disimpan, bukan diterima tiap panggilan | R-05 |
| M-4 | `DITOLAK_PROPERTI` disamakan dengan `DILEWATI_TANPA_PERSETUJUAN` | R-06 |
| M-5 | Penjagaan nilai `properti` dilepas | R-06 |
| M-6 | Penjagaan kunci `properti` dilepas | R-06 |
| M-7 | `Peristiwa` dibentuk di luar gerbang | pemeriksa aturan 1 |
| M-8 | Parameter keadaan diberi nilai bawaan | pemeriksa aturan 3 |
| M-9 | Kode peristiwa di luar taksonomi diterima | R-01 |
| M-10 | Ekspor memuat kolom identitas | R-03 |

## 5 · Ketergantungan

**Nol.** CSV memakai `csv` pada pustaka baku. Parquet menuntut `pyarrow` dan
**tidak dibangun**.
