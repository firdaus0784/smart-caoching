# Tasks: 023-lapisan-http

| | |
|---|---|
| Plan | `specs/023-lapisan-http/plan.md` |
| Status | Gerbang 3 lolos — KB-070 |

Satu tugas satu commit. Uji ditulis sebelum implementasi.

## Fase A — kerangka aplikasi dan kendali peran

**A-1 · Penentu identitas dan penyusun aplikasi**

- [x] Uji: aplikasi tanpa `identitas` gagal disusun (`TypeError`)
- [x] Uji: `docs_url`, `redoc_url`, `openapi_url` seluruhnya mati
- [x] Uji: daftar rute aplikasi seluruhnya ada pada peta rute `peran.py`
- [x] `PenentuIdentitas` sebagai `Protocol`; `susun_aplikasi()` menuntutnya

**A-2 · Gerbang peran pada setiap penangan**

- [x] Uji: peran tidak berhak ditolak 403
- [x] Uji: jalur penjawaban **tidak tersentuh** ketika peran ditolak
- [x] Uji: pola jalur yang dipakai `boleh()` dibaca dari rute FastAPI
- [x] Penjaga peran sebagai satu tempat, dipakai seluruh penangan

## Fase B — penangan rute D-14 Bagian 3.2

**B-1 · `POST /api/v1/tanya`**

- [x] Uji: jawaban sah dikembalikan utuh tanpa bidang berubah
- [x] Uji: jalur berhenti tanpa jawaban tetap **200** beserta bentuk D-14
- [x] Uji: `menunggu_model` terbawa apa adanya
- [x] Uji: pertanyaan kosong ditolak 400, pesan ≤ 20 kata tanpa istilah teknis
- [x] Uji: pesan galat tidak memuat kembali nilai yang ditolak

**B-2 · `GET /api/v1/percakapan` dan `/api/v1/percakapan/{id}`**

- [x] Uji: giliran dikembalikan tanpa bidang tanggapan
- [x] Uji: percakapan tak dikenal ditolak 404 dengan pesan ≤ 20 kata

## Fase C — penutup

**C-1 · Uji mutasi dan Gerbang 4**

- [x] Delapan mutasi `plan.md` Bagian 7 dijalankan, seluruhnya menyala
- [x] `make check` lulus enam gerbang; `make lint` hijau
- [x] Cakupan tidak turun
- [x] Catatan keputusan pada `logbook/L4`
