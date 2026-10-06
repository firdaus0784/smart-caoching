# Plan: 033-pengaturan-dan-penarikan-data

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 6 Oktober 2026 (KB-204); P-1 s.d. P-5 sesuai anjuran |
| Status | **Gerbang 4 lolos** — 6 Oktober 2026 (KB-213). Tujuh dari tujuh tugas selesai |
| Kebutuhan | R-01 s.d. R-09 `spec.md`; FR-A06, NFR-09, RE-04, KM-02; C-04, C-05, C-13, C-17, C-20 |

## 1. Letak dan batas

```
perkakas/basis_data/
  01-peran-dan-basis-data.sql   + peran_penarikan, peran_penarikan_pseudonim
  11-penarikan.sql              baru — akun.permintaan_penarikan; hak kedua peran
src/penyimpanan/akun.py         + catat_penarikan; akun berpermintaan tidak dapat masuk
src/penyimpanan/penarikan.py    baru — daftar dan jalankan; HANYA dipakai perkakas
src/api/aplikasi.py             + DELETE /saya/data
perkakas/penarikan.py           baru — `daftar`, `jalankan`
web/src/pengaturan/             baru — S-14
web/src/Aplikasi.tsx            tombol Pengaturan di samping Keluar
docs/                           D-14 4.5 dan 5.1; D-00
```

**`src/rag/`, `src/llm/`, `src/telemetri/`, `src/ingest/` tidak disentuh.**
Rute `/saya/profil`, `/saya/prioritas`, `/saya/persetujuan` dipakai apa
adanya; S-14 tidak menambah rute selain `DELETE /saya/data` yang sudah ada
pada D-14 Bagian 3.1.

## 2. K-1 · Dua langkah: rute mencatat, perkakas menghapus

```
DELETE /saya/data ──► akun.permintaan_penarikan (pseudonim, diminta_pada)
                  └─► seluruh sesi akun dicabut           — satu pernyataan
                      akun berpermintaan tertunda tidak dapat masuk

perkakas.penarikan jalankan
   1. peran_penarikan_pseudonim: hapus pemetaan pada basis data pseudonim
   2. peran_penarikan: satu pernyataan CTE menghapus seluruh data milik
      pseudonim itu, lalu mengosongkan pseudonim pada baris permintaan dan
      mengisi dipenuhi_pada serta jumlah baris per tabel
```

**R-01 dipenuhi oleh pencabutan sesi**, bukan oleh pencabutan persetujuan:
tanpa sesi tidak ada pemilik, dan perekam fitur 034 tidak merekam apa pun
tanpa pemilik. Persetujuan tidak disentuh rute — ia terhapus bersama data
lain pada langkah 2.

**Urutan langkah perkakas disengaja.** Pemetaan dihapus lebih dulu: bila
langkah 2 gagal, perkakas dijalankan ulang dan langkah 1 tidak menemukan apa
pun. Urutan sebaliknya meninggalkan pemetaan tanpa pseudonim untuk
mencarinya, sebab langkah 2 mengosongkannya.

**Satu pernyataan.** `SambunganAktif` tanpa transaksi (fitur 024);
penghapusan majemuk ditulis sebagai satu pernyataan CTE, sehingga separuh
penghapusan tidak dapat terjadi.

## 3. K-2 · Peran

| Peran | Hak | Tidak memegang |
|---|---|---|
| `peran_autentikasi` (ada) | + `INSERT` atas `akun.permintaan_penarikan`; `SELECT (pseudonim, dipenuhi_pada)` | `DELETE` apa pun |
| `peran_penarikan` (baru) | `USAGE` skema `akun`, `pengguna`, `riwayat`, `penemuan`, `telemetri`; `SELECT` kolom pemilik dan `DELETE` atas sepuluh tabel data pengguna; `SELECT` dan `UPDATE (pseudonim, dipenuhi_pada, jumlah_baris)` atas permintaan | `CONNECT` basis data pseudonim; skema `korpus`, `karantina`, `indeks_*`, `kurasi` |
| `peran_penarikan_pseudonim` (baru) | `CONNECT` basis data pseudonim; `SELECT (pseudonim)`, `DELETE` atas `peta_pseudonim` | `CONNECT` basis data utama |

**Kedua peran baru tidak dipegang layanan aplikasi.** `src/api/` dan
`perkakas/jalankan_lokal.py` tidak mengimpor `src/penyimpanan/penarikan.py`;
uji arah menjaganya. Sifat tambah-saja tabel data tetap berlaku bagi setiap
peran yang dipakai aplikasi — katalog hak pada uji peladen fitur 028, 030,
013, dan 034 diperbarui menjadi "tidak satu peran **aplikasi** pun", dengan
`peran_penarikan` disebut tegas sebagai satu-satunya pemegang `DELETE`.

## 4. K-3 · Tabel permintaan

```sql
akun.permintaan_penarikan (
  nomor bigint identity, pseudonim text NULL, diminta_pada timestamptz,
  dipenuhi_pada timestamptz NULL, jumlah_baris jsonb NULL
)
```

- `pseudonim` berpola pseudonim selama tertunda; **kosong sesudah dipenuhi**
  — batasan: `(dipenuhi_pada IS NULL) = (pseudonim IS NOT NULL)`
- Satu permintaan tertunda per pseudonim — indeks unik bersyarat
- Tanpa kunci asing ke `akun.pengguna`: baris permintaan bertahan sesudah
  akunnya dihapus, dan itulah buktinya (P-3)

## 5. K-4 · Akun berpermintaan tertunda tidak dapat masuk

`AkunPostgres.baca_akun` membaca `status_aktif` **dan** ketiadaan permintaan
tertunda. Akun berpermintaan tertunda terbaca nonaktif, sehingga penolakan
masuknya **sama persis** dengan keempat penolakan lain (R-04 fitur 029) —
tanpa kalimat baru yang memberi tahu orang lain bahwa akun itu sedang menarik
datanya.

## 6. K-5 · Bentuk rute (D-14 Bagian 4.5)

| Rute | Permintaan | Tanggapan |
|---|---|---|
| `DELETE /api/v1/saya/data` | `{"konfirmasi": true}`, `application/json` | **202** tanpa badan; kuki sesi dihapus |

- Tanpa `konfirmasi: true` tepat, 400 — rute yang menghapus tidak dipicu
  permintaan kosong yang terkirim tidak sengaja
- Permintaan kedua dari akun yang sama tidak terjadi: sesinya sudah dicabut
- 202, bukan 204: yang terjadi adalah penerimaan, penghapusannya menyusul
  ≤ 14 hari (NFR-09)

## 7. K-6 · S-14 Pengaturan

| Bagian | Isi |
|---|---|
| Profil dan prioritas | Formulir S-04 fitur 030 dalam mode sunting, terisi dari `GET /saya/profil`; menyimpan lewat dua rute yang sama |
| Persetujuan penelitian | Keadaan dan tindakan yang sama dengan panel pada Tanya (fitur 030) |
| Penarikan data | Daftar data yang dihapus — dibangkitkan dari tabel `spec.md`, ditulis sebagai bahasa pengguna; kalimat penjelasan dari `web/public/naskah/penarikan.json` milik tim bila ada (P-4 B); dua tombol setara: "Tarik data saya" dan "Batal" |

Sesudah 202: layar Masuk dengan kalimat bahwa permintaan diterima dan
dipenuhi paling lambat 14 hari. Tidak ada pemberitahuan yang memakai rasa
bersalah atau kehilangan (D-05 Bagian 10).

Keadaan D-05 Bagian 7: KL-A memuat, KL-D galat dengan satu tindakan, KL-E
luring — penarikan **tidak diantrekan** saat luring; KL-F terkirim.

## 8. K-7 · Perkakas

```
python -m perkakas.penarikan daftar     # nomor, umur dalam hari, tertunda > 14 hari ditandai
python -m perkakas.penarikan jalankan   # seluruh yang tertunda, satu per satu
```

Keluaran tidak memuat pseudonim (R-09): nomor permintaan dan jumlah baris per
tabel saja. Kredensial dibaca dari lingkungan, tidak pernah dari berkas
repositori.

## 9. Keputusan rancangan Gerbang 2

| Kode | Pertanyaan | Putusan |
|---|---|---|
| K-1 | Alur | Rute mencatat dan mencabut sesi; perkakas menghapus — Bagian 2 (P-1 B) |
| K-2 | Peran | Dua peran baru di luar aplikasi — Bagian 3 |
| K-3 | Bukti | Baris permintaan tanpa pseudonim sesudah dipenuhi — Bagian 4 (P-3) |
| K-4 | Masuk sesudah meminta | Ditolak sama dengan penolakan lain — Bagian 5 |
| K-5 | Bentuk rute | 202 dengan konfirmasi tegas — Bagian 6 |
| K-6 | Layar | S-14 memakai ulang formulir dan panel fitur 030 — Bagian 7 (P-4 B, P-5) |

## 10. Uji

### 10.1 Di dalam `make check`

- Penolakan peladen atas kedua peran baru, dengan sebab `permission denied`;
  katalog hak persis; kedua peran berjalan dengan haknya
- **Penghapusan terhadap PostgreSQL:** dua pengguna berdata pada setiap
  tabel; sesudah `jalankan` bagi yang satu, setiap tabel kosong darinya dan
  utuh bagi yang lain; baris permintaan tanpa pseudonim, berjumlah baris
- Lewat HTTP: 202, kuki dihapus, sesi lain akun itu ditolak, masuk ditolak
  dengan tanggapan yang sama dengan sandi salah
- Arah: `src/api/` dan titik jalan tidak mengimpor penyimpan penarikan
- Layar: dua tombol setara, tanpa permintaan sebelum konfirmasi, luring tidak
  mengirim

### 10.2 Di luar `make check`

Playwright terhadap `make jalan`: pengguna bertanya, membuka beranda,
menyetujui telemetri, lalu menarik data dari S-14; perkakas dijalankan; setiap
tabel dibaca langsung dan kosong dari pseudonim itu.

### 10.3 Uji mutasi

| Kode | Mutasi | Uji yang wajib merah |
|---|---|---|
| M-1 | Rute tidak mencabut sesi | sesi lain ditolak |
| M-2 | Akun berpermintaan tertunda dapat masuk | masuk ditolak |
| M-3 | Satu tabel terlewat dari penghapusan (`telemetri.peristiwa`) | setiap tabel kosong |
| M-4 | Penghapusan tanpa saringan pemilik | pengguna lain utuh |
| M-5 | Pseudonim tidak dikosongkan sesudah dipenuhi | baris permintaan tanpa pseudonim |
| M-6 | `GRANT CONNECT` basis data pseudonim kepada `peran_penarikan` | penolakan peladen |
| M-7 | Layanan aplikasi memakai penyimpan penarikan | uji arah |
| M-8 | Rute menerima tanpa `konfirmasi` | 400 |
| M-9 | Layar mengirim sebelum konfirmasi | uji layar |

## 11. Urutan tugas

| Tugas | Isi |
|---|---|
| T-1 | Kontrak: D-14 4.5 dan 5.1; D-00 |
| T-2 | Peladen: `11-penarikan.sql`, dua peran; katalog hak fitur lain; M-6 |
| T-3 | Penyimpan akun: `catat_penarikan`, akun tertunda tidak masuk; M-2 |
| T-4 | Rute `DELETE /saya/data`; M-1, M-8 |
| T-5 | `src/penyimpanan/penarikan.py`, `perkakas/penarikan.py`; M-3, M-4, M-5, M-7 |
| T-6 | S-14; M-9 |
| T-7 | Titik jalan, bukti Playwright, penutupan: L8, HKI, L4 |

## 12. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Rute baru tampak perlu | Berhenti; AG-02 |
| Peran yang dipakai aplikasi tampak perlu memegang `DELETE` | Berhenti; P-1 |
| Kalimat penjelasan penarikan tampak perlu ditulis agen | Berhenti; P-4 |
| Catatan persetujuan tampak perlu disimpan | Berhenti; TK-75 |
| Paket baru tampak perlu | Berhenti; C-12 |
