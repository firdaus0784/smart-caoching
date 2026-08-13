# Usulan ketergantungan — dua keputusan C-12

| | |
|---|---|
| Tanggal | 12 Agustus 2026 |
| Disusun oleh | Agen pembangun, atas temuan fitur 007, 008, dan 009 |
| Ditujukan kepada | Penanggung jawab teknis (C-12) |
| Status | **Usulan.** Berkas ini tidak mengubah apa pun; `ketergantungan-disetujui.toml` hanya berubah oleh keputusan tim |
| Keputusan | **Dua**, dan keduanya dapat diambil pada rapat yang sama |

---

## 1 · Mengapa berkas ini ada

Sesudah fitur 009, seluruh jalur dari pertanyaan sampai bentuk tanggapan
**ada dan diuji**. Yang memisahkan sistem ini dari jawaban pertamanya bukan
kode, bukan korpus, bukan anotasi, bukan pakar domain — melainkan **dua
keputusan C-12**.

| Penghalang | Fitur yang membukanya | Keputusan yang ditunggu |
|---|---|---|
| Sumber kandidat vektor (R-05 fitur 007) | 019 | **A — tumpukan sematan** |
| VS-03 dan VS-05 (R-10 fitur 008) | 020 | **A — tumpukan sematan** |
| Rute `/api/v1/tanya` | 021 | **B — kerangka web** |

Ketiganya menunggu, dan ketiganya sudah punya tempat yang siap menerimanya:
antarmuka `SumberKandidat` (fitur 007), sambungan
`pemeriksaan_menunggu_model` (fitur 008), dan pemeriksa rute yang berdiri
sebelum rute pertama ada (fitur 009).

**Yang tidak dibuka keputusan ini**: VS-07 menunggu model NER fitur 017, yang
menunggu korpus teranotasi bulan 2–4. Itu pekerjaan orang, bukan keputusan.

---

## 2 · Seluruh lisensi diperiksa langsung ke PyPI

Diambil **12 Agustus 2026** dari `pypi.org/pypi/<paket>/json`, bukan dikutip
dari ingatan. Bentuk yang sama dengan pemeriksaan KB-017 pada fitur 015.

Versi yang tercatat di bawah adalah yang terbaru pada tanggal itu. **Angka
versinya belum tentu yang dipasang**: C-12 menyetujui paketnya, dan pematokan
versi adalah keputusan terpisah pada `uv.lock`.

---

## 3 · Keputusan A — tumpukan sematan

Membuka **fitur 019 dan 020**.

| Paket | Versi | Lisensi | Keperluan |
|---|---|---|---|
| `sentence-transformers` | 5.7.0 | Apache-2.0 | Memuat model sematan multibahasa (D-07 Bagian 3.3) |
| `transformers` | 5.15.0 | Apache-2.0 | Ketergantungan `sentence-transformers` |
| `torch` | 2.13.0 | Apache-2.0 dan lainnya | Ketergantungan `transformers` |
| `pgvector` | 0.5.0 | MIT | Tipe vektor PostgreSQL (ADR-05) |
| Penggerak PostgreSQL | — | **lihat Bagian 5** | Sambungan basis data |

### 3.1 Dua hal yang wajib diketahui sebelum menyetujui

**`torch` berukuran ± 527 MB per *wheel*.** Itu bukan rincian teknis melainkan
angka yang menyentuh tiga hal: waktu pemasangan pada lingkungan penelitian,
ukuran citra penyebaran (D-09), dan **kemampuan bekerja luring**. Bila
lingkungan pilot di Kabupaten Sumedang memiliki sambungan yang terbatas,
mengunduhnya berulang bukan pilihan yang wajar.

**Menyetujui `sentence-transformers` berarti menyetujui `torch`.** Ia bukan
tambahan opsional; ia ketergantungan wajib yang datang bersamanya. Persetujuan
yang hanya menyebut paket teratas akan membuat `make check` V-04 menemukan
paket yang tidak disetujui pada pemasangan pertama.

### 3.2 Yang **bukan** urusan keputusan ini

**Model sematan mana yang dipakai.** D-07 Bagian 3.3 hanya menyatakan "model
multibahasa yang menangani Bahasa Indonesia; versi dicatat pada setiap segmen".
Memilih modelnya menyentuh mutu pengambilan, dan itu keputusan yang menuntut
pengujian terhadap *gold set* — bukan keputusan pemasangan paket.

Agen tidak mengusulkan model tertentu di sini, dan itu disengaja.

---

## 4 · Keputusan B — kerangka web

Membuka **fitur 021**.

| Paket | Versi | Lisensi | Keperluan |
|---|---|---|---|
| `fastapi` | 0.141.1 | MIT | `AGENTS.md`: `src/api/` "satu-satunya titik masuk" |
| `uvicorn` | 0.52.1 | BSD-3-Clause | Menjalankan aplikasi ASGI |
| `httpx` | 0.28.1 | BSD-3-Clause | **Menguji** rute tanpa menjalankan peladen |

Ketiganya berlisensi permisif, **sama kelasnya dengan sepuluh paket yang sudah
disetujui**. Tidak ada kewajiban baru yang timbul.

`httpx` dicantumkan meski ia hanya untuk pengujian: `pytest-cov` dan `ruff`
juga hanya untuk pembangunan, dan keduanya tercatat. Ketergantungan uji yang
tidak dicatat adalah ketergantungan yang V-04 temukan pada commit pertama.

---

## 5 · Satu hal yang menuntut keputusan tersendiri: lisensi penggerak PostgreSQL

**Ini temuan yang paling perlu perhatian pada berkas ini.**

Penggerak yang paling lazim untuk PostgreSQL pada Python adalah `psycopg`,
dan versinya **berlisensi LGPL-3.0-only**.

Seluruh sepuluh paket yang sudah disetujui berlisensi **MIT, BSD-3-Clause,
atau Apache-2.0** — ketiganya permisif. LGPL adalah **kelas lisensi yang belum
pernah disetujui proyek ini**, dan ia membawa kewajiban yang berbeda.

| Penggerak | Versi | Lisensi | Catatan |
|---|---|---|---|
| `psycopg` | 3.3.4 | **LGPL-3.0-only** | Paling lazim; kelas lisensi baru bagi proyek ini |
| `pg8000` | 1.31.5 | BSD-3-Clause | Murni Python; sama kelasnya dengan yang sudah disetujui |
| `asyncpg` | 0.31.0 | Apache-2.0 | Asinkron; sama kelasnya dengan yang sudah disetujui |

**Agen tidak memilih di antara ketiganya.** Yang diusulkan hanya bahwa
pilihannya diambil **sadar**, sebab menyetujui `psycopg` bersama paket lain
dalam satu baris akan membuat kelas lisensi baru masuk tanpa seorang pun
memutuskannya — dan proyek ini menerbitkan artefak penelitian serta mengejar
HKI (FR-E05).

Bila tim menilai LGPL dapat diterima, keputusan itu **wajib tercatat pada
`docs/D12.md`** sebagaimana perubahan konstitusi lain, sebab ia menetapkan
preseden bagi paket berikutnya.

---

## 6 · Yang diminta dari rapat

| | Keputusan | Akibat bila disetujui | Akibat bila ditunda |
|---|---|---|---|
| **A** | Tumpukan sematan | Fitur 019 dan 020 dapat dimulai | Sistem tetap tidak dapat menjawab; dua fitur menganggur |
| **B** | Kerangka web | Fitur 021 dapat dimulai | Rute tidak ada; sistem tidak dapat dicapai pengguna |
| **C** | Kelas lisensi penggerak PostgreSQL | Preseden tercatat | Keputusan A tertahan pada butir yang lebih kecil daripada dirinya |

**Ketiganya dapat diambil pada rapat yang sama.** C adalah bagian dari A dan
dipisahkan hanya karena ia menetapkan preseden yang berlaku melampaui A.

---

## 7 · Yang agen kerjakan sementara menunggu

Fitur **010** — pipeline pengetahuan dan gerbang kurasi — tidak tertahan
kedua keputusan ini, dan ia memindahkan C-06 serta C-07 menjadi terperiksa
mesin.

Menunggu keputusan bukan alasan berhenti; ia alasan mengerjakan yang tidak
menunggu.

---

## 8 · Cara memperbarui bila disetujui

`ketergantungan-disetujui.toml` bertambah baris pada `langsung`, masing-masing
dengan komentar yang menyebut **tanggal keputusan dan lisensinya** — bentuk
yang sudah dipakai sejak KB-017:

```toml
    # Ditambahkan Gerbang <n> fitur <nnn>, keputusan KB-<nnn>. Lisensi
    # diperiksa langsung ke PyPI pada <tanggal>, bukan dikutip dari ingatan.
```

Perubahan itu **keputusan tim, bukan keputusan agen** — berkas persetujuan
menyatakannya sendiri.

---

## 9 · Keputusan yang diambil atas pendelegasian — 13 Agustus 2026

Pemegang Gerbang 1–4 menyerahkan keputusan ini kepada agen dengan permintaan
agar rekomendasinya bersandar pada rujukan ilmiah yang sudah dipakai proyek.
Bagian ini mencatat hasilnya. Ia **dapat dibatalkan satu kalimat**; yang
dituliskan di sini adalah alasannya, bukan kewenangannya.

### 9.1 Keputusan A — model sematan

**Calon utama: `multilingual-e5-large-instruct`. Pembanding wajib:
`SEA-Embedding-E5-Large-600M`. Keduanya diputuskan final pada BT-29, bukan di
sini.**

Dasarnya **SEA-BED** (ACL 2026), tolok ukur sematan sepuluh bahasa Asia
Tenggara atas 169 himpunan data, yang menempatkan `multilingual-e5-large-instruct`
teratas bagi Bahasa Indonesia. Rujukannya masuk D-11 Bagian 3.4.

Yang membuat keputusan ini berbentuk **sepasang calon, bukan satu pilihan**,
adalah temuan SEA-BED sendiri: tidak ada satu model pun yang unggul merata
lintas bahasa dan tugas, dan keberhasilan pada satu tugas tidak dapat
diandalkan merambat ke tugas lain. Memilih satu model dari papan peringkat lalu
menyatakannya selesai adalah bentuk kekeliruan yang C-16 larang pada ambang.
Selisih pembandingnya sendiri kecil — 0,800 berbanding 0,789 pada rerata
SEA-BED — dan selisih sekecil itu justru yang paling wajib diukur pada gold set
sendiri alih-alih disalin.

**Satu temuan SEA-BED mengubah rancangan, bukan hanya pilihan model.** Model
teratas bagi Bahasa Indonesia tetap memberi kemiripan 0,75–0,81 pada pasangan
kalimat yang **tidak berkaitan**. Ambang kemiripan mutlak karena itu tidak
dapat memisahkan segmen relevan dari yang tidak, sehingga penilaian kecukupan
bukti D-07 Bagian 4.6 wajib bersandar pada **peringkat**. Penggabungan RRF yang
sudah dipilih (Cormack dkk. 2009) ternyata benar dengan alasan yang belum
diketahui saat ia dipilih.

**Kekhawatiran ukuran `torch` pada Bagian 3.1 dicabut sebagian.** Model berjalan
di sisi peladen, bukan di perangkat kepala sekolah; `web/` adalah PWA yang
memanggil rute. 527 MB menyentuh waktu pemasangan dan ukuran citra D-09 — dan
itu saja. Ia **tidak** menyentuh kemampuan bekerja luring pengguna.

### 9.2 Keputusan B — kerangka web

**`fastapi`, `uvicorn`, `httpx` — disetujui.** Ketiganya berlisensi permisif
(MIT, BSD-3-Clause, BSD-3-Clause), diperiksa ke PyPI pada 12 Agustus 2026.

Keputusan ini tidak menambah pilihan arsitektur melainkan **menyelaraskan
persetujuan dengan arsitektur yang sudah tertulis**: `AGENTS.md` menyebut
`src/api/` sebagai "FastAPI, satu-satunya titik masuk" sejak fitur 001.
KB-039 benar menolak membaca kalimat itu sebagai persetujuan; yang kurang
memang persetujuannya, bukan pilihannya.

### 9.3 Keputusan C — penggerak PostgreSQL

**`asyncpg` (Apache-2.0). `psycopg` ditolak.**

Alasannya bukan mutu teknis `psycopg`, melainkan **kelas lisensinya**.
Kesepuluh paket yang sudah disetujui berlisensi MIT, BSD-3-Clause, atau
Apache-2.0. LGPL-3.0-only akan menjadi kelas lisensi pertama yang tidak
permisif pada proyek yang menerbitkan artefak penelitian dan mengejar HKI
(FR-E05). Menerima kelas lisensi baru menuntut telaah yang tidak sebanding
dengan keuntungan yang diperoleh, sementara dua alternatif permisif tersedia.

`asyncpg` dipilih di atas `pg8000` karena FastAPI bersifat asinkron sejak
rancangannya, dan Apache-2.0 menyamai lisensi `transformers` serta
`sentence-transformers` pada tumpukan yang sama.

### 9.4 Yang **tidak** saya setujui, dan mengapa

**Bobot model sematan belum disetujui.** Lisensi paket Python dan lisensi
bobot model adalah dua artefak berbeda dengan lisensi berbeda, dan proyek ini
melarang menyimpulkan lisensi alih-alih membacanya — KL-01 menyatakannya bagi
korpus, dan alasannya berlaku sama di sini. Saya **tidak dapat**
memverifikasinya: kebijakan jaringan menutup `huggingface.co`. Menyetujuinya
dari ingatan akan mengulangi persis yang KB-041 tolak.

**Satu tugas untuk manusia, dan ia berlangsung semenit:** buka halaman model,
baca berkas lisensinya, catat hasilnya di sini. Sampai itu terjadi, fitur 019
tidak mengunduh bobot apa pun.

**`ketergantungan-disetujui.toml` sengaja belum disentuh.** Berkas itu
memasangkan daftar `langsung` dengan pohon transitif `[terkunci]`, dan V-04
menggagalkan `make check` pada selisih apa pun terhadap `uv.lock`. Menambah
nama tanpa memasang paketnya akan memutus berkas itu dari gunanya sendiri.
Barisnya ditambahkan **pada saat pemasangan**, oleh fitur yang membutuhkannya
— 019 bagi tumpukan sematan, 021 bagi kerangka web — dengan menyebut KB-044
sebagai keputusannya.
