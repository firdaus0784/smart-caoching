# Plan: 010-pipeline-kurasi

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 — 12 Agustus 2026, KB-042 |
| Status | Menunggu Gerbang 2 |
| Ketergantungan baru | **Nol paket Python** |
| Pertanyaan terbuka | **Nol** — ketiganya dijawab pada KB-042 |

---

## 1 · Jawaban atas ketiga pertanyaan

| | Pertanyaan | Putusan |
|---|---|---|
| 1 | Cakupan pemeriksa C-07 | **A** — ketiga lapis: VS-06, `Sitasi`, dan L3 |
| 2 | `KategoriMasalah` | **A** — dipakai ulang lewat tepi `ingest → nlp` |
| 3 | Kurator pada jejak | **A** — penanda peran dan id pseudonim |

---

## 2 · Letak modul

```
src/ingest/kurasi/
  butir.py      ButirPengetahuan, ButirTayang           R-01, R-02
  saring.py     L1 s.d. L4, HasilSaring tiga keadaan     R-03 s.d. R-06
  putusan.py    Putusan, AlasanTolak TL-01 s.d. TL-11    R-07, R-08
  antrean.py    panjang, rasio, pengereman               R-11, R-12
  tetapan.py    angka D-06 Bagian 8.3                    R-12
  jejak.py      jejak audit kurasi                       R-09, R-13
perkakas/pemeriksa/
  gerbang_kurasi.py   pemeriksa C-06                     R-02
  regulasi_dicabut.py pemeriksa C-07, tiga lapis          R-05
```

`src/ingest/kurasi/` mengikuti `AGENTS.md`, yang menempatkan "antrean kurasi"
pada `src/ingest/`. Tepi `ingest → nlp` sudah tertulis dan dipakai untuk
`KategoriMasalah`; pemeriksa arah fitur 009 memeriksanya.

**`tetapan.py` masuk `RUMAH_TETAPAN`** — rumah keempat, sesudah `ambang.py`
(003), `pembagian.py` (004), dan `rag/pengambilan/tetapan.py` (007). Aturan 3
pemeriksa C-16 menuntut setiap tetapannya menyebut asalnya, dan seluruhnya
berasal dari D-06 Bagian 8.3.

---

## 3 · Bentuk yang menentukan

### 3.1 `ButirTayang` hanya dibentuk gerbang kurasi

C-06 menjadi tipe, bukan aturan. Mengikuti `JawabanTervalidasi` fitur 008 dan
`Instruksi` ADR-13 — keduanya sudah punya pemeriksa yang terbukti.

`ButirPengetahuan` adalah kandidat; `ButirTayang` adalah butir yang sudah
melewati putusan kurator. Keduanya tipe berbeda, sehingga fitur 011 yang
menayangkan feed **tidak memiliki cara** menayangkan kandidat.

Dua lapis, dan yang kedua menutup yang pertama: tipe yang terpisah, dan
pemeriksa yang melarang pembentukannya di luar satu modul.

### 3.2 L4 menahan, tidak meloloskan dan tidak membuang

`HasilSaring` bernilai tiga: `LOLOS`, `GUGUR`, `MENUNGGU`.

Pengulangan keenam pola "tiga keadaan, bukan dua" — sesudah `HasilSistem`
(015), `HasilKesepakatan` (003), `bendera` (016), `Nilai` (004), `HasilHitung`
(005), dan `Status` validator (008). Di sini ia menahan hal yang berbeda:
bukan laporan yang keliru melainkan **pilihan yang tidak boleh diambil tanpa
dasar**.

D-06 menyebut kedua akibat yang salah dan tidak menyebut mana yang lebih
ringan:

| Bila L4 yang belum dapat dijalankan diperlakukan sebagai | Akibat |
|---|---|
| Lolos | **Membanjiri antrean kurasi** — dan kurator hanya punya 4 jam per minggu |
| Gugur | **Feed kekurangan isi**, memicu titik kritis T5 pada D-02 |

`MENUNGGU` adalah satu-satunya jawaban yang tidak memilih di antara keduanya.

### 3.3 Empat putusan, dan penolakan berkode

D-06 Bagian 7.3 menetapkan empat putusan setara — bukan tiga dengan satu
tambahan. `Tunda` khususnya mudah hilang: ia terlihat seperti "belum
diputuskan", padahal ia putusan yang membawa waktu kembalinya.

Penolakan menuntut kode TL-01 s.d. TL-11. D-06: *"Alasan terstandar diperlukan
agar penolakan menjadi data perbaikan, bukan sekadar pembuangan."* Untai bebas
menghasilkan sebelas cara menulis "tidak relevan", dan PM-05 menjadi angka yang
tidak dapat diuraikan sebabnya.

### 3.4 Pengereman menuntut tiga hari, bukan dua

FR-I08 dan D-06 Bagian 8.3: melampaui ambang **selama tiga hari berturut-turut**.

Uji yang hanya memeriksa "melampaui → direm" lulus juga pada implementasi yang
mengerem pada hari pertama — dan pengereman yang terlalu cepat menurunkan
frekuensi K-C setiap kali antrean naik sehari, lalu feed kekurangan isi.
Diuji dari **kedua** arah: dua hari tidak mengerem, tiga hari mengerem.

Urutan pengeremannya juga D-06: K-C lebih dulu, *"karena kanal jurnal
menghasilkan volume terbesar dengan tingkat kelolosan terendah, sehingga
pengurangannya paling sedikit merugikan."*

---

## 4 · Dua pemeriksa

### C-06 · gerbang kurasi

1. **`ButirTayang` hanya dibentuk pada `src/ingest/kurasi/putusan.py`.**
   Bentuk yang sama dengan aturan `Instruksi` ADR-13 dan `JawabanTervalidasi`
   C-19, keduanya sudah terbukti.
2. **`ButirTayang` tidak memiliki nilai bawaan pada bidang putusannya.**
   Bidang berbawaan membuat butir yang lupa diputuskan terbentuk sebagai butir
   yang disetujui.

### C-07 · regulasi dicabut, tiga lapis

Pasal ini dijaga tiga tempat sesudah fitur ini, dan pemeriksanya memeriksa
**ketiganya**:

| Lapis | Tempat | Fitur |
|---|---|---|
| Penjawaban | VS-06 pada `validator/sitasi.py` | 008 |
| Penyajian | `Sitasi` pada `jawaban/tanggapan.py` | 009 |
| Ingesti | L3 pada `kurasi/saring.py` | 010 |

Memeriksa satu lapis saja akan membuat pemeriksanya terbaca lengkap sementara
ia menjaga sepertiga — dan penghapusan dua lapis hilir tidak terlihat sampai
ada jawaban yang tayang.

**Diuji terhadap pohon yang sengaja dirusak**, masing-masing lapis terpisah.

---

## 5 · Rencana uji mutasi

| | Mutasi | Uji yang harus menyala |
|---|---|---|
| M-1 | `ButirTayang` dapat dibentuk di luar `putusan.py` | pemeriksa C-06 aturan 1 |
| M-2 | L4 `MENUNGGU` diperlakukan sebagai `LOLOS` | R-06 |
| M-3 | L4 `MENUNGGU` diperlakukan sebagai `GUGUR` | R-06 |
| M-4 | L3 meloloskan regulasi `dicabut` | R-05, pemeriksa C-07 |
| M-5 | VS-06 dihapus dari validator | pemeriksa C-07 lapis 1 |
| M-6 | Penolakan menerima untai bebas | R-08 |
| M-7 | Pengereman menyala pada hari kedua | uji dua hari tidak mengerem |
| M-8 | Butir tayang tidak ditarik saat sumber dicabut | R-10 |
| M-9 | Jejak kurasi memuat nama kurator | R-13 |

---

## 6 · Ketergantungan

**Nol paket baru.** Seluruhnya model pydantic, perbandingan himpunan, dan
pembacaan bentuk. `KategoriMasalah` dipakai ulang dari fitur 003.

---

## 7 · Yang tetap menunggu sesudah fitur ini

| | Menunggu |
|---|---|
| Skor relevansi L4 | Klasifikasi K1–K8 (fitur 017) **dan** ambang BT-24, bulan 3 |
| Antrean jawaban QA keliru (FR-I04) | FR-F07, yang menuntut rute — fitur 021 |
| Layar kurator S-15 dan S-16 | `web/`, belum dimulai |

Pipeline ini **belum dapat mengisi antrean kurasi** sampai L4 dapat
dijalankan. Yang berdiri sesudah fitur ini adalah seluruh jalur sesudahnya —
antrean, putusan, jejak, penarikan, pengereman — sehingga L4 mendarat pada
bagian yang sudah siap menerimanya.
