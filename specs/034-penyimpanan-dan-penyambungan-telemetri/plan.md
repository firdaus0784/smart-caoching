# Plan: 034-penyimpanan-dan-penyambungan-telemetri

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 6 Oktober 2026 (KB-192); P-1 s.d. P-6 sesuai anjuran |
| Status | **Lolos Gerbang 2–3** atas pendelegasian KB-168 — 6 Oktober 2026 (KB-193). Enam tugas pada `tasks.md` |
| Kebutuhan | R-01 s.d. R-10 `spec.md`; FR-J01, FR-J02, FR-J05, FR-A05; C-04, C-05, C-09, C-14 |

## 1. Letak dan batas

```
perkakas/basis_data/
  01-peran-dan-basis-data.sql   + peran_telemetri
  10-telemetri.sql              baru — skema telemetri, tabel peristiwa, hak
src/penyimpanan/telemetri.py    baru — PenyimpanTelemetri, memori dan PostgreSQL
src/penyimpanan/penemuan.py     + kapan_tayang (menit sejak ditayangkan)
src/api/rekaman.py              baru — Perekam: persetujuan → rekam() → simpan
src/api/autentikasi.py          + PenjagaMasuk.pemilik_sesi
src/api/aplikasi.py             perekam disuntikkan; peristiwa pada rute masuk,
                                keluar, tanya
src/api/penemuan.py             peristiwa beranda, detail, belum relevan
perkakas/jalankan_lokal.py      penyimpan telemetri pada titik jalan bersesi
AGENTS.md                       tepi api → telemetri (K-1)
docs/                           D-14 5.1; D-00
```

**Model dan gerbang fitur 012 dipakai, tidak diubah.** `Peristiwa` tetap hanya
dibentuk `rekam()`; pemeriksa C-04 tetap menjaganya. `src/telemetri/` tidak
disentuh — yang dibangun di sini pemanggilnya dan tempat simpannya.

**`src/rag/` dan `src/llm/` tidak disentuh.** Peristiwa jawaban dibaca dari
`HasilTanya` yang sudah dikembalikan jalur.

**Tanpa perubahan `web/`.** Seluruh peristiwa teramati peladen (P-1 C).

## 2. K-1 · Tepi `api → telemetri`

AGENTS.md: `api` boleh memanggil `telemetri`, satu jurusan, dengan alasan umum
— `api` satu-satunya titik masuk, sehingga setiap peristiwa yang teramati pada
sebuah rute wajib direkam dari sana. Arah sebaliknya terlarang: telemetri yang
memanggil `api` membuat perekaman bergantung pada bentuk HTTP. Diputus pada
Gerbang 1 (P-3).

## 3. K-2 · Perekam: satu jalan, persetujuan setiap kali

```python
class Perekam:
    async def rekam(self, pemilik, jenis, properti, *, sekarang, versi_model=TANPA_MODEL)
```

1. Baca `KeadaanPersetujuan` dari penyimpan pengguna **pada pemanggilan ini**
   — lewat `keadaan_persetujuan()` fitur 030, satu jalur penafsiran. Perekam
   tidak memiliki tempat menyimpan keadaan (R-02).
2. `rekam()` fitur 012. `DILEWATI_TANPA_PERSETUJUAN` dan `DITOLAK_PROPERTI`
   berhenti di sini tanpa menulis apa pun.
3. Simpan lewat `PenyimpanTelemetri.tambah`.
4. **Galat apa pun** pada langkah 1 sampai 3 ditangkap, dicatat ke log
   operasional dengan jenis peristiwa dan kelas galatnya saja — tanpa
   pseudonim, tanpa properti — dan **tidak diteruskan** (R-07). Telemetri yang
   menjatuhkan rute adalah telemetri yang membuat pengguna menolak persetujuan.

`Perekam` boleh kosong: tanpa penyimpan telemetri, rute berjalan seperti
sebelum fitur ini, dan tidak satu baris pun tersimpan.

## 4. K-3 · Penyimpanan

```sql
telemetri.peristiwa (
  nomor bigint identity, pseudonim text, jenis text, waktu timestamptz,
  properti jsonb, versi_aplikasi text, versi_model text
)
```

- `jenis` dibatasi dua puluh kode taksonomi D-01 Bagian 9 — dibaca dari
  `JenisPeristiwa` oleh uji, bukan disalin tangan tanpa penjaga.
- `pseudonim` berpola `^psd_[a-z]{16}$`, dipasang ulang tiap kali berkas
  dijalankan (KB-158).
- `peran_telemetri`: `INSERT`, `SELECT` atas `peristiwa` saja. Tanpa `UPDATE`,
  `DELETE`, `TRUNCATE`; tanpa skema lain; tanpa `CONNECT` basis data pseudonim.

`PenyimpanTelemetri`: `tambah(baris)` dan `terakhir(pemilik, jenis)` — yang
kedua bagi `return_visit` dan durasi `session_end`. Lapisan penyimpanan tidak
mengimpor `src/telemetri/`; ia menerima baris sederhana.

## 5. K-4 · Versi

`susun_aplikasi(..., versi_aplikasi=...)` wajib diisi bila penyimpan telemetri
diberikan. Peristiwa jawaban membawa `tanggapan.versi.model`; selebihnya
`TANPA_MODEL = "tanpa_model"`, tetapan bernama pada `src/api/rekaman.py`.
`make jalan` mengisi `versi_aplikasi` dengan `pengembangan`, sama dengan
penanda versinya.

## 6. K-5 · Pemilik pada saat masuk

Rute masuk menerbitkan sesi sebelum identitas dapat dibaca dari kuki.
`PenjagaMasuk.pemilik_sesi(pengenal)` membaca pseudonim dari sesi yang baru
diterbitkan, lewat penyimpan akun yang sama. Tidak ada yang berubah pada
penolakan masuk: keempat penolakan tidak merekam apa pun, sebab tidak ada
pemilik.

## 7. K-6 · Letak tiap peristiwa

| Kode | Di mana | Properti |
|---|---|---|
| `return_visit` | rute masuk, **sebelum** `session_start` baru, bila `session_start` terakhir > 24 jam | `jeda_jam` |
| `session_start` | rute masuk | `{}` |
| `session_end` | rute keluar | `durasi_menit` sejak `session_start` terakhir; kosong bila tidak ada |
| `question_asked` | `POST /tanya` sesudah lolos validasi | `panjang_pertanyaan` |
| `answer_served` | `POST /tanya` sesudah tercatat | `status_dasar`, `jumlah_sitasi`, `waktu_tanggap_ms` |
| `answer_rejected_validator` | bila `alasan_berhenti` = `ditahan_validator` | `alasan_berhenti` |
| `discovery_served` | beranda, bagi butir yang **baru** tercatat hari itu | `id_butir`, `jenis_sumber`, `kategori` |
| `discovery_opened` | `GET /butir/{id}` berhasil | `id_butir`, `menit_sejak_tayang` |
| `discovery_dismissed` | "belum relevan" tercatat | `id_butir`, `panjang_alasan` |

Teks pertanyaan dan alasan **tidak pernah** menjadi properti (R-06). Ambang 24
jam pada `return_visit` berasal dari D-01 Bagian 9 apa adanya.

## 8. Keputusan rancangan Gerbang 2

| Kode | Pertanyaan | Putusan |
|---|---|---|
| K-1 | Tepi arsitektur | `api → telemetri` — Bagian 2 (P-3) |
| K-2 | Bentuk pemanggil | **Perekam tunggal** yang membaca persetujuan tiap kali dan menelan galatnya — Bagian 3 |
| K-3 | Penyimpanan | Skema `telemetri`, `peran_telemetri` — Bagian 4 (P-6) |
| K-4 | Versi | `versi_aplikasi` dari titik jalan, `tanpa_model` — Bagian 5 (P-4) |
| K-5 | Pemilik saat masuk | `PenjagaMasuk.pemilik_sesi` — Bagian 6 |
| K-6 | Letak peristiwa | Tabel Bagian 7 (P-2) |

## 9. Uji

### 9.1 Di dalam `make check`

- Penolakan peladen atas `peran_telemetri`, tiap baris dengan sebab
  `permission denied`; katalog hak persis; batasan pola dan jenis.
- Penyimpan atas memori **dan** PostgreSQL sebagai `peran_telemetri`.
- **C-04 ujung ke ujung lewat HTTP:** tanpa persetujuan, alur masuk → tanya →
  beranda → butir → belum relevan → keluar menyimpan **nol** peristiwa; dengan
  persetujuan, sembilan kode tercatat sesuai Bagian 7; sesudah mencabut,
  permintaan berikutnya tidak menambah satu pun.
- **R-03:** tanggapan setiap rute sama persis dengan dan tanpa persetujuan.
- **R-07:** penyimpan yang melempar tidak mengubah tanggapan; log tidak memuat
  pseudonim maupun properti.
- **R-06:** teks pertanyaan dan alasan tidak muncul pada tabel peristiwa.
- **C-05:** pseudonim, tidak pernah `pengguna.id`.

### 9.2 Di luar `make check`

Playwright terhadap `make jalan`: pengguna menyetujui naskah uji sementara
(tidak di-commit, sama dengan bukti fitur 030), bertanya, membuka beranda dan
butir; peristiwa dibaca dari basis data dan dicocokkan. Lalu mencabut; jumlah
peristiwa tidak bertambah.

### 9.3 Uji mutasi

| Kode | Mutasi | Uji yang wajib merah |
|---|---|---|
| M-1 | Keadaan persetujuan disimpan pada `Perekam` sekali | cabut seketika |
| M-2 | Perekam melewati pemeriksaan persetujuan | nol peristiwa tanpa persetujuan |
| M-3 | Pemilik peristiwa diisi `pengguna.id` | C-05 |
| M-4 | `GRANT UPDATE` atau `DELETE` atas `peristiwa` | penolakan peladen |
| M-5 | `GRANT CONNECT` basis data pseudonim kepada `peran_telemetri` | penolakan peladen |
| M-6 | Teks pertanyaan masuk properti | R-06 |
| M-7 | Galat penyimpan diteruskan | R-07 |
| M-8 | `return_visit` tanpa ambang 24 jam | `return_visit` |
| M-9 | `answer_served` membawa `tanpa_model` | versi model jawaban |
| M-10 | `discovery_served` direkam ulang pada muat ulang | satu kali per butir |

## 10. Urutan tugas

| Tugas | Isi |
|---|---|
| T-1 | Kontrak: D-14 5.1 `peristiwa`; AGENTS.md K-1; D-00 |
| T-2 | Peladen: `10-telemetri.sql`, `peran_telemetri`; M-4, M-5 |
| T-3 | `src/penyimpanan/telemetri.py`, `kapan_tayang` |
| T-4 | `src/api/rekaman.py`, peristiwa sesi pada masuk dan keluar; M-1, M-2, M-3, M-7, M-8 |
| T-5 | Peristiwa Tanya dan penemuan; M-6, M-9, M-10 |
| T-6 | Titik jalan, bukti Playwright, penutupan: L8, HKI, L4 |

## 11. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Rute baru tampak perlu | Berhenti; AG-02, TK-73 |
| Perubahan `src/telemetri/`, `src/rag/`, `src/llm/` tampak perlu | Berhenti |
| Peristiwa tampak perlu dibaca untuk menyesuaikan beranda atau jawaban | Berhenti; C-14 |
| Naskah persetujuan tampak perlu ditulis agen | Berhenti; ET-02 |
| Paket baru tampak perlu | Berhenti; C-12 |
