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
