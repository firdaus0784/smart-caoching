# Plan: 023-lapisan-http

| | |
|---|---|
| Spec | `specs/023-lapisan-http/spec.md` |
| Status | Gerbang 2 lolos — KB-070 |
| Ketergantungan baru | **Nol.** `fastapi` sudah masuk titik nol pada KB-067 |

## 1. Letak modul

`src/api/aplikasi.py`, satu berkas. `src/api/` sudah memuat ketiga bahannya —
`peran.py`, `tanya.py`, `percakapan.py` — dan aturan arah `AGENTS.md` sudah
mengizinkan `api` memanggil seluruh lapisan yang diperlukannya. **Tidak ada
tepi arsitektur baru**, dan itu tanda bahwa fitur ini memang lapisan tipis:
lapisan tipis yang menuntut tepi baru bukan lapisan tipis.

## 2. Bentuk yang menegakkan R-04

```python
def susun_aplikasi(*, jalur: Jalur, identitas: PenentuIdentitas, ...) -> FastAPI
```

`identitas` adalah parameter **kata kunci wajib tanpa nilai baku**. Aplikasi
tanpa penentu identitas tidak dapat disusun — bukan disusun lalu ditolak saat
jalan. Bentuk yang sama dengan `susun_komitmen` fitur 011, dan alasannya
sejajar: nilai baku pada bidang yang menentukan siapa pemanggil adalah nilai
baku yang akan terpakai di lingkungan sungguhan.

`PenentuIdentitas` adalah `Protocol`, bukan kelas. Yang dituntut hanya satu
kemampuan — mengubah permintaan menjadi `Peran` — sehingga fitur autentikasi
kelak mengisinya tanpa menyentuh berkas ini.

## 3. Bentuk yang menegakkan R-07

Rute didaftarkan **dari `src/api/peran.py`**, bukan ditulis ulang sebagai untai
pada dekorator. Modul itu sudah memuat peta rute D-14 beserta penjaganya, dan
menuliskan jalurnya kedua kali menghasilkan dua daftar yang berselisih pada
hari salah satunya disunting — bentuk kekeliruan yang sama dengan
`PAGU_TAYANG_PER_PENGGUNA` pada fitur 011 dan daftar gamifikasi pada C-14.

Tiga penyetelan `FastAPI` yang wajib, dan seluruhnya mematikan rute bawaan:

| Setelan | Nilai | Sebab |
|---|---|---|
| `docs_url` | `None` | `/docs` bukan rute D-14 |
| `redoc_url` | `None` | `/redoc` bukan rute D-14 |
| `openapi_url` | `None` | `/openapi.json` bukan rute D-14 |

Ketiganya menyala secara baku pada FastAPI. Rute yang menyala tanpa seorang pun
mendaftarkannya adalah bentuk pelanggaran AG-02 yang paling mungkin luput,
sebab tidak ada baris kode yang dapat dibaca sebagai penyebabnya.

## 4. Pemetaan jalur permintaan ke pola D-14

`boleh()` menuntut **pola** D-14 (`/api/v1/percakapan/{id}`), bukan jalur
permintaan (`/api/v1/percakapan/abc`). Pemetaannya diambil dari atribut rute
FastAPI itu sendiri, bukan disusun ulang — FastAPI sudah menyimpan pola yang
dipakainya mendaftarkan penangan, dan membacanya dari sana menutup selisih
antara apa yang didaftarkan dan apa yang diperiksa.

## 5. Bentuk galat

Satu penerjemah galat, satu tempat. `GalatPercakapan` dan `GalatFeed` sudah
membawa pesan yang memenuhi R-06 pada lapisan di bawahnya; penangan **tidak
menyusun pesannya sendiri** melainkan meneruskannya. Yang disusun di sini hanya
pemetaan jenis galat ke status HTTP, dan itu penerjemahan, bukan keputusan.

| Keadaan | Status | Isi |
|---|---|---|
| Peran tidak berhak | 403 | Pesan tetap, ≤ 20 kata |
| Permintaan tidak lengkap | 400 | Pesan dari galat lapisan bawah |
| Percakapan tidak ada | 404 | Pesan tetap, ≤ 20 kata |
| Jalur berhenti tanpa jawaban | **200** | Bentuk D-14 utuh — R-03 |

Baris terakhir yang paling mudah keliru, dan karena itu diuji tersendiri.

## 6. Rencana uji

Uji memakai `TestClient` bawaan `starlette`, yang tidak menuntut peladen
berjalan maupun porta terbuka. Prinsip fitur 021 tetap berlaku: uji yang
menuntut peladen berjalan adalah uji yang dilewati orang ketika sedang
buru-buru.

Kolaborator dipalsukan pada tingkat `Jalur`, bukan pada tingkat HTTP — yang
diuji di sini penerjemahannya, dan jalur penjawabannya sudah diuji fitur 021.

## 7. Rencana uji mutasi

Delapan mutasi, masing-masing menuntut satu uji menyala:

| | Mutasi | Uji yang wajib gagal |
|---|---|---|
| M-1 | Panggilan `boleh()` dihapus dari penangan `/tanya` | peran tak berhak tetap ditolak |
| M-2 | `boleh()` dipanggil **sesudah** `Jalur.jawab()` | jalur tidak tersentuh saat ditolak |
| M-3 | `docs_url=None` dihapus | tidak ada rute di luar D-14 |
| M-4 | `openapi_url=None` dihapus | tidak ada rute di luar D-14 |
| M-5 | `identitas` diberi nilai baku | aplikasi tanpa penentu identitas gagal disusun |
| M-6 | Jawaban tertahan dikembalikan sebagai 503 | jalur berhenti tetap 200 |
| M-7 | Pola jalur ditulis ulang sebagai untai pada dekorator | pola dibaca dari `peran.py` |
| M-8 | Pesan galat memuat kembali nilai yang ditolak | pesan tidak memuat masukan |

## 8. Yang sengaja tidak dibangun

**Pemeriksa mesin bagi R-07.** Ia akan memeriksa daftar rute aplikasi terhadap
D-14 — pekerjaan yang berguna, tetapi cakupannya melampaui fitur ini: rute
D-14 di luar Bagian 3.2 belum ada penangannya sama sekali, sehingga pemeriksa
yang menuntut kecocokan penuh akan menyalak pada keadaan yang sah. Ia dicatat
sebagai calon pekerjaan, bukan dikerjakan setengah.
