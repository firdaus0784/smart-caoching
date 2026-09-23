# Plan: 019-sumber-vektor-dan-pemeringkat-ulang

| | |
|---|---|
| Spec | Gerbang 1 lolos 20 September 2026, nol pertanyaan terbuka |
| Status | **Gerbang 4 lolos** — 23 September 2026 (KB-106). Gerbang 2 lolos 20 September 2026 |
| Gerbang 2 | Lolos 20 September 2026 |
| Kebutuhan | ADR-03 sisi semantik, ADR-05, ADR-12; BT-30; C-02, C-08, C-09, C-12 |

## 1. Letak modul — ditentukan pemeriksa, bukan oleh selera

```
src/llm/sematan.py                       (baru)  Penyemat abstrak + tiruan deterministik
src/rag/pengambilan/vektor.py            (baru)  SumberVektor — pelaksana SumberKandidat
src/rag/pengambilan/peringkat_ulang.py   (baru)  Pemeringkat ulang + jalur mundur BT-30
perkakas/basis_data/05-kolom-vektor.sql  (baru)  Migrasi kolom vektor
```

**Penyemat wajib di `src/llm/`, dan itu bukan pilihan.** `periksa_impor_penyedia`
menyenaraikan `torch`, `transformers`, dan `sentence_transformers` sebagai
pustaka model yang **hanya boleh diimpor di dalam `src/llm/`** — C-08, tanpa
pengecualian. Menaruh penyemat di `src/rag/` akan menjatuhkan V-02 pada commit
pertama.

`src/rag/` boleh mengimpornya: `llm` adalah **lapisan terbuka** menurut
`AGENTS.md`, sejajar `kamus`, `penyimpanan`, dan `logbook`. Diperiksa dengan
menjalankan pembaca arahnya, bukan dengan membaca kalimatnya.

`AGENTS.md` **tidak perlu** diperbarui: tidak ada tepi arah baru.

## 2. Perubahan kontrak yang Gerbang 1 sudah putuskan

`SumberKandidat.cari` menjadi asinkron. Yang tersentuh:

| Berkas | Sifat perubahan |
|---|---|
| `src/rag/pengambilan/kandidat.py` | `cari` menjadi `async def` |
| `src/rag/pengambilan/bm25.py` | pelaksana menyesuaikan |
| `src/rag/pengambilan/hibrida.py` | `ambil_hibrida` menjadi asinkron; pemanggilan sumber ditunggu |
| Uji yang memanggil keduanya | dibungkus `jalankan()` |

Dikerjakan **lebih dulu dan sendirian** (T-1), sebelum sumber vektor ada.
Menggabungkannya dengan penambahan sumber membuat kegagalan tidak dapat
ditelusuri ke perubahan yang mana — pelajaran T-2 fitur 024.

`ambil_hibrida` berubah **bentuknya** (menjadi asinkron), bukan **isinya**.
Bila isinya ternyata perlu berubah agar sumber vektor masuk, itu temuan:
kontraknya yang salah, dan perubahannya melewati Gerbang 2 tersendiri.

## 3. Bentuk penyemat

```python
class Penyemat(ABC):
    @property
    @abstractmethod
    def versi(self) -> Versi: ...          # C-09 — nama dan versi model
    @property
    @abstractmethod
    def dimensi(self) -> int: ...          # R-08 — dicocokkan saat penyusunan
    @abstractmethod
    async def sematkan(self, teks: Sequence[str]) -> Sequence[Sequence[float]]: ...
```

**Tiruan deterministik**, mengikuti ADR-12. Ia **bukan** penyemat sungguhan
yang disederhanakan: ia memetakan teks ke vektor tetap lewat fungsi hash yang
dinyatakan sendiri sebagai tiruan. Penyemat buatan sendiri yang "mirip
semantik" menghasilkan angka kemiripan yang tidak berarti apa-apa sambil
terbaca seperti berfungsi — itu yang spec tolak pada bagian Alternatif.

Adaptor sungguhan **tidak dibangun pada fitur ini**: bobotnya tidak terjangkau
dari lingkungan agen. Ia fitur 025.

## 4. Penyimpanan vektor

Kolom `vektor vector(N)` pada tabel `segmen_teks` di skema `indeks_utama` dan
`indeks_metadata` — keduanya sudah ada beserta hak aksesnya sejak T-9 fitur
024. Keputusan Gerbang 1 nomor 3.

Dua hal yang migrasinya wajib tangani:

- **Dimensi dinyatakan satu tempat** (R-08), dan ketidakcocokan antara dimensi
  penyemat dan dimensi kolom ditolak **saat penyusunan** — bukan saat kueri
  pertama, ketika pemanggilnya sudah di lingkungan sungguhan.
- **Segmen tanpa vektor tidak muncul sebagai kandidat**, dan **jumlahnya
  dilaporkan**. Indeks yang separuh terisi sambil terbaca penuh adalah bentuk
  kekeliruan yang sama dengan uji yang dilewati tanpa dilaporkan.

## 5. Pemeringkat ulang dan jalur mundurnya

BT-30 sudah memutuskan bentuknya: bila model lintas-enkoder untuk Bahasa
Indonesia tidak tersedia, tahap 5 memakai urutan hasil penggabungan apa adanya.

Yang plan ini tambahkan: **ketiadaannya wajib tercatat pada keluaran** (R-05).
Jalur mundur yang diam tidak dapat dibedakan dari pemeringkat ulang yang
berjalan dan kebetulan tidak mengubah urutan — dan kedua keadaan itu menuntut
tindakan yang berbeda.

## 6. Uji

### 6.1 Kontrak dijalankan dua pelaksana

`SumberKandidat` memperoleh rangkaian uji kontrak berparameter, bentuk yang
sama dengan `PenyimpanDasar` pada T-2 fitur 024: BM25 dan vektor menjalankan
rangkaian yang **sama**, tanpa satu pun uji diubah.

Hari ini `bm25.py` diuji terpisah. Menyatukannya menjadi uji kontrak adalah
bagian T-1, dan seperti T-2 fitur 024: **bila satu uji perlu diubah agar
berparameter, itu temuan** — catat, jangan rapikan.

### 6.2 Yang menuntut peladen

Kueri `pgvector` dan pencocokan dimensi menuntut PostgreSQL. `make check`
sudah menuntutnya sejak 12 September 2026, sehingga tidak ada jalur dilewati.

`pgvector` perlu dipasang sebagai **ekstensi peladen**, bukan hanya paket
Python. Itu pekerjaan operasi (D-09) dan berkas persiapannya menandai batasnya,
sejajar dengan T-9 fitur 024.

### 6.3 Uji mutasi

| | Mutasi | Yang wajib menangkapnya |
|---|---|---|
| M-1 | `indeks_tujuan` diperiksa sesudah kueri berjalan | R-03, C-02 |
| M-2 | Sumber vektor mencari `indeks_metadata` dengan kredensial penjawaban | R-03 |
| M-3 | Dimensi tidak dicocokkan saat penyusunan | R-08 |
| M-4 | Segmen tanpa vektor ikut muncul sebagai kandidat | Keadaan wajib |
| M-5 | Jumlah segmen tanpa vektor tidak dilaporkan | Keadaan wajib |
| M-6 | Jalur mundur pemeringkat ulang tidak mencatat ketiadaannya | R-05, BT-30 |
| M-7 | Versi penyemat tidak masuk keluaran | R-06, C-09 |
| M-8 | Penyemat menyusun dirinya sendiri alih-alih dipilih pemanggil | R-02 |

Hasilnya dilaporkan apa adanya, termasuk yang tidak menyala **beserta
sebabnya** — dan bila sebuah mutasi diam, yang pertama diperiksa adalah apakah
mutasinya terlalu lemah. Pelajaran M-3 fitur 024.

## 7. Ketergantungan

**Nol ketergantungan Python baru.** `torch`, `transformers`,
`sentence-transformers`, dan `pgvector` sudah pada berkas persetujuan (KB-083).
Diperiksa, bukan diperkirakan.

**Satu ketergantungan peladen baru, disetujui pada Gerbang 2**: ekstensi
`pgvector`, tercatat `[sistem.pgvector]` versi 0.6.0. Ia bukan paket Python —
paket Python `pgvector` hanya menyediakan tipe bagi `asyncpg` dan tidak dapat
menyimpan satu vektor pun tanpa ekstensi ini pada peladennya. Keduanya wajib
ada, dan keduanya dicatat terpisah karena dipasang orang yang berbeda dengan
perintah yang berbeda.

## 8. Urutan tugas yang diusulkan untuk `tasks.md`

1. `SumberKandidat.cari` menjadi asinkron — sendirian, tanpa sumber baru
2. Rangkaian uji kontrak `SumberKandidat` dijadikan berparameter — masih satu pelaksana
3. `src/llm/sematan.py` — antarmuka + tiruan deterministik
4. Migrasi kolom vektor + pencocokan dimensi saat penyusunan
5. `SumberVektor` — lulus rangkaian uji kontrak yang sama
6. Segmen tanpa vektor: dikeluarkan dari kandidat, jumlahnya dilaporkan
7. Pemeringkat ulang + jalur mundur BT-30 yang menyatakan dirinya
8. Uji mutasi M-1 s.d. M-8 dijalankan dan **dilaporkan apa adanya**
9. Berkas persiapan ekstensi `pgvector` beserta batas kode/operasi

## 9. Risiko yang diketahui sekarang

| Risiko | Bila terjadi |
|---|---|
| `SumberKandidat` ternyata tidak pas bagi sumber asinkron | Ajukan lewat Gerbang 2 tersendiri; jangan perbaiki sambil jalan |
| ~~Ekstensi `pgvector` tidak disetujui~~ | Tidak lagi berlaku — disetujui Gerbang 2, terpasang dan terbukti bekerja |
| Tiruan deterministik terbaca sebagai penyemat sungguhan | Uraiannya menyatakan dirinya tiruan, dan `versi` yang dikeluarkannya berbunyi demikian |

## 10. Berhenti di Gerbang 2

`tasks.md` dan kode menunggu putusan. Dua hal yang paling perlu Anda periksa:
**Bagian 2** (perubahan kontrak yang sudah diputuskan, tetapi ruang
tersentuhnya baru terbaca di sini) dan **Bagian 7** (ekstensi peladen baru —
penambahan pada berkas persetujuan, yang bukan keputusan agen).
