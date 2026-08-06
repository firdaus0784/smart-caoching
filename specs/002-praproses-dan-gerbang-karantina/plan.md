# Plan: 002-gerbang-karantina

Disusun agen. Ditinjau manusia sebelum `tasks.md`.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 pada 5 Agustus 2026 |
| Status | **Lolos Gerbang 2** — 5 Agustus 2026. Menunggu `tasks.md` dan Gerbang 3 |

## Keputusan Gerbang 1 yang mengikat rencana ini

1. FR-B01 s.d. FR-B04 dibangun pada fitur 015. Rencana ini tidak menyentuhnya.
2. **Tiga** peran kredensial: jalur penjawaban, jalur verifikasi, pemanggil LLM.
3. Peringkat ditetapkan saat masuk; **T3 sah hanya setelah verifikasi**, dan
   peringkat dokumen di karantina tidak terbaca jalur penjawaban.

## Tiga hal yang ditemukan saat menyusun rencana — diputus di Gerbang 2

### G2-A · Tidak ada peran `verifikator` pada D-14

`docs/D14.md` Bagian 3 semula menetapkan lima peran: `pengguna`, `kurator`,
`anotator`, `peneliti`, `admin`. **Tidak ada `verifikator`**, sementara FR-B05
mewajibkan verifikasi manusia dan R-04 menjadikannya gerbang. AG-04 melarang
agen mengubah daftar nilai enum, sehingga penambahannya bukan keputusan agen.

**Diputus: peran baru.** ADR-06 sudah menuntut kredensial berbeda untuk area
karantina; memberi pekerjaannya kepada peran yang kredensialnya dirancang untuk
hal lain melemahkan justru pemisahan yang sedang dibangun. Menyerahkannya ke
`kurator` ditolak karena D-06 Bagian 8 merancang beban kurator di bawah 4 jam
per minggu, dan menambahnya menyentuh langsung BT-62. D-14 ke 0.4.

### G2-B · Letak modul penyimpanan

Menaruhnya di dalam `src/ingest/` tidak berhasil: `src/rag/` perlu membaca
korpus, sehingga `rag` harus memanggil `ingest` — melanggar aturan arah.

**Diputus: `src/penyimpanan/` sebagai lapisan bersama di bawah keempatnya,
persis bentuk `src/llm/`.** Alasannya sama dengan alasan `src/llm/` ada: C-03
menuntut satu titik sempit yang tidak dapat dilewati, dan aturan yang penting
ditegakkan pada satu tempat, bukan pada setiap pemanggil (AP-01). `AGENTS.md`
bagian Arsitektur dan aturan arah diperbarui.

### G2-C · Catatan perpindahan antar area

`docs/D04.md` Bagian 7 memuat `jejak_kurasi` untuk kurasi, tanpa padanan bagi
perpindahan area yang dituntut R-11.

**Diputus: tabel `jejak_area`** pada `docs/D04.md` Bagian 7.2 dengan bidang
`id`, `id_dokumen`, `id_pelaku`, `dari_area`, `ke_area`, `alasan`, `waktu`;
D-04 ke 0.6. Terpisah dari `jejak_kurasi` karena keduanya alur berbeda dengan
pemilik berbeda. Aturan bidang `alasan` masuk `docs/D14.md` Bagian 5.1 —
tidak pernah memuat kutipan isi dokumen, sehingga **R-12 punya tempat tertulis
di dokumen pemiliknya**, bukan hanya di dalam spec fitur.

## Pendekatan

Pemisahan diwujudkan sebagai **ketidakmampuan**, mengikuti ADR-06 yang menolak
penandaan status. Bentuknya: sebuah `Kredensial` membawa himpunan area yang
boleh dibacanya, dan penyimpan menolak permintaan di luar himpunan itu sebelum
menyentuh data. Kredensial dibentuk hanya di satu modul, cara yang sama dengan
`Instruksi` pada ADR-13.

Penyimpan dibangun terhadap antarmuka abstrak dengan pelaksana tiruan
deterministik dalam memori, mengikuti ADR-12. PostgreSQL adalah pekerjaan
penyebaran D-09.

### Tiga keputusan teknis pokok

**1 · Kredensial sebagai kemampuan, bukan identitas.** Bukan "siapa" melainkan
"boleh membaca area apa, boleh menulis area apa". Pemeriksaannya menjadi
perbandingan himpunan, bukan penafsiran peran — dan yang dapat diuji adalah
yang tidak menafsirkan.

**2 · Peringkat disimpan sejak masuk, disahkan oleh verifikasi.** Yang menahan
peringkat T3 bukan bidang kedua melainkan `dokumen_sumber.area_simpan`: selama
bernilai `karantina`, segmennya tidak terjangkau kredensial jalur penjawaban.
R-07a dipenuhi pemisahan yang sudah ada, tanpa bidang tambahan.

**3 · Pemeriksa pola adversarial menahan, tidak menilai.** Ia mengembalikan
temuan; yang memindahkan dokumen ke tinjauan manusia adalah gerbang. Pemeriksa
yang juga memutuskan akan menggoda siapa pun melonggarkan ambangnya ketika
antrean menumpuk — persis yang C-16 larang.

## Berkas yang disentuh

| Berkas | Baru/ubah | Alasan |
|---|---|---|
| `src/penyimpanan/area.py` | baru | Enum `Area`, mengikuti `dokumen_sumber.area_simpan` D-14 Bagian 5.1 |
| `src/penyimpanan/kredensial.py` | baru | Satu-satunya tempat `Kredensial` dibentuk — R-01 |
| `src/penyimpanan/kredensial_baku.py` | baru | Tiga kredensial baku — R-01a, R-01b |
| `src/penyimpanan/galat.py` | baru | `GalatAksesDitolak`; bentuknya D-14 Bagian 4.2 |
| `src/penyimpanan/dasar.py` | baru | Antarmuka abstrak; ADR-12 |
| `src/penyimpanan/tiruan.py` | baru | Pelaksana dalam memori, deterministik |
| `src/penyimpanan/catatan_akses.py` | baru | R-02, R-12 |
| `src/ingest/peringkat.py` | baru | R-07: jenis sumber ke T1–T4 |
| `src/ingest/dokumen.py` | baru | R-06: metadata asal |
| `src/ingest/gerbang.py` | baru | R-03, R-04, R-05 |
| `src/ingest/adversarial.py` | baru | R-09, R-10 |
| `src/ingest/jejak.py` | baru | R-11, R-12 |
| `perkakas/pemeriksa/pemisahan_penyimpanan.py` | baru | Pemeriksa C-03 |
| `perkakas/kepatuhan/daftar_pasal.py` | ubah | C-03 dari `fitur_pengunci` ke `pemeriksa` |
| `AGENTS.md` | **sudah diubah** | Arsitektur dan aturan arah; disetujui G2-B |

## Kontrak

**Tidak ada rute baru.** `docs/D14.md` Bagian 3 tidak memuat rute unggah
dokumen maupun rute verifikasi, dan AG-02 melarang agen menambahnya. Fitur ini
membangun lapisan layanan yang kelak dipanggil rute itu.

Ini bukan kelalaian melainkan urutan yang benar: rute tanpa lapisan layanan
menghasilkan kendali peran di antarmuka saja, yang KT-05 tolak tegas.

## Skema data

Seluruhnya sudah ditetapkan `docs/D14.md` Bagian 5.1 dan `docs/D04.md`
Bagian 7.2. **Tidak ada bidang baru pada tabel yang ada.**

| Bidang | Dipakai untuk |
|---|---|
| `dokumen_sumber.area_simpan` | `karantina` atau `korpus`; kredensial berbeda |
| `dokumen_sumber.status_anonimisasi` | `menunggu`, `terverifikasi`, `ditolak` |
| `segmen_teks.peringkat_kepercayaan` | T1 s.d. T4 |
| `jejak_area` | tujuh bidang, ditambahkan pada G2-C |

## Pasal konstitusi

| Pasal | Bagaimana dipenuhi | Cara diuji |
|---|---|---|
| **C-03** | Kredensial jalur penjawaban tidak memuat `Area.KARANTINA` pada himpunan bacanya; penyimpan menolak sebelum menyentuh data | Penanda dijalankan: kredensial penjawaban meminta dokumen karantina → wajib galat. Ditambah pemeriksa AST bahwa `src/rag/` tidak membentuk kredensial |
| C-05 | Kredensial pemanggil LLM tidak menjangkau kunci pseudonim | Uji: himpunan bacanya tidak memuat area kunci |
| C-11 | Cakupan tidak turun | `periksa_cakupan` |
| C-12 | Nol ketergantungan baru | `periksa_ketergantungan` |
| C-16 | Ambang pemeriksa adversarial dinyatakan nilai awal | Ditulis pada uraian modul; kalibrasinya BT-29 |

**C-03 berpindah dari `fitur_pengunci` menjadi `pemeriksa`**, dan tagihan
`make compliance` menyusut dari 13 menjadi 12 — pertama kalinya sejak fitur 001.

## Ketergantungan — C-12

**Nol.** Seluruhnya pustaka baku dan pydantic yang sudah disetujui. Bila
ternyata ada yang diperlukan, pekerjaan berhenti dan persetujuan diminta.

## Risiko

| Risiko | Bila terjadi |
|---|---|
| Pemisahan dapat dilewati lewat pemanggilan dinamis | Diakui terbuka, sama dengan RP-01. Yang dirancang pembatasan kerugian, bukan pencegahan sempurna (PT-01) |
| Pemeriksa C-03 lulus karena tidak memeriksa apa pun | Uji mutasi wajib pada tugas terakhir |
| Penyimpan tiruan menyembunyikan persoalan basis data sungguhan | Diakui. Yang diuji aturan aksesnya, bukan ketahanan penyimpanannya |
| Peringkat T3 bocor lewat jalur tak terpikirkan | Uji tersendiri pada R-07a, bukan disandarkan pada uji R-01 |

## Yang tidak dikerjakan

- Rute apa pun (AG-02)
- Bidang baru pada tabel yang ada (D-14 Bagian 5)
- FR-B01 s.d. FR-B04 — fitur 015
- Antarmuka verifikator — menunggu D-05
- Penyetelan ambang pemeriksa adversarial — BT-29, C-16
- PostgreSQL dan peran basis datanya — D-09
