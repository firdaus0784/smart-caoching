# Plan: 001-kerangka-proyek

Disusun agen. Ditinjau manusia sebelum `tasks.md`.

| | |
|---|---|
| Spec | `specs/001-kerangka-proyek/spec.md` (lolos Gerbang 1) |
| Status | Menunggu Gerbang 2 |
| Yang diminta persetujuan | Daftar ketergantungan (C-12) · keputusan BT-14 · ambang ±30 tugas |

## Keputusan Gerbang 1 yang mengikat rencana ini

| # | Keputusan | Wujud dalam rencana |
|---|---|---|
| G1-1 | R-15 dan R-16 disetujui; tiga keadaan wajib, gagal bila diam | Bagian "Perancah kepatuhan" |
| G1-2 | C-17 dan C-18 tetap di pembungkus; D-12 Bagian 7 yang usang | Fase D + tugas dokumen pada Fase E |
| G1-3 | Kontainerisasi keluar; **pengunci versi ketergantungan tetap di 001** | Fase A, berkas `uv.lock` dan `ketergantungan-disetujui.toml` |
| G1-4 | Jangan dipecah; R-14…R-18 mendahului R-04…R-13 | Urutan fase B sebelum C dan D |

## Pendekatan

Rencana ini membalik urutan yang naluriah. Yang biasanya dikerjakan terakhir —
pemeriksa, gerbang, perancah kepatuhan — dikerjakan lebih dulu, dan pembungkus
model ditulis **di bawah pengawasan pemeriksa yang sudah berjalan**. Ini
penerapan G1-4, dan alasannya sama dengan alasan D-12 menempatkan fitur 008
sebelum 009: penjaga yang ditambahkan pada sistem yang sudah berfungsi
menyenangkan selalu lebih mahal, dan sering dipangkas diam-diam.

Empat fase, dengan satu fase dokumen di akhir.

| Fase | Isi | Kebutuhan |
|---|---|---|
| **A** | Perancah proyek, penempatan lapisan tata kelola, pengunci versi | R-01, R-02, sebagian R-18 |
| **B** | Gerbang mutu: `make check`, `make compliance`, pemeriksa berbasis AST | R-03, R-14 s.d. R-18 |
| **C** | Penulis `logbook/` sekali-tulis | R-11 s.d. R-13 |
| **D** | Pembungkus `src/llm/` beserta pemisahan struktural | R-04 s.d. R-10 |
| **E** | Penerapan keputusan pada dokumen: TK-39, D-12 Bagian 7, KM-001, KM-002 | KM-001 s.d. KM-003 |

Fase C mendahului D karena pembungkus menulis catatan versinya ke `logbook/`
(R-05 bertemu R-11). Keduanya tetap berada **sesudah** fase B, sesuai G1-4.

### Tiga keputusan teknis pokok

**1. Pemeriksa berbasis AST, bukan pustaka pihak ketiga.**
R-04 (tidak ada impor pustaka penyedia di luar `src/llm/`) dan R-13 (kode hanya
menambah baris pada `logbook/`) keduanya adalah pertanyaan tentang bentuk kode,
bukan tentang perilaku saat jalan. Modul `ast` pada pustaka baku sudah cukup.
Memakai pustaka pemeriksa arsitektur akan menambah ketergantungan untuk pekerjaan
yang selesai dalam ratusan baris — dan C-12 menjadikan setiap ketergantungan
berbiaya persetujuan. Pemeriksa yang sama dipakai ulang untuk aturan konstruksi
`Instruksi` pada Fase D.

**2. Permintaan ke penyedia berbentuk objek terstruktur, bukan untai teks.**
Ini yang membuat R-07 dapat diuji sama sekali. Bila pembungkus menghasilkan satu
untai teks, "posisi instruksi" tidak punya wujud yang dapat diperiksa mesin, dan
UK-10 yang berambang nol akan berakhir sebagai pemeriksaan mata. Dengan permintaan
berupa objek, uji dapat menegaskan bahwa untai penanda dari parameter data
**tidak pernah muncul** pada bidang instruksi objek itu.

**3. Tipe `Instruksi` hanya boleh dibentuk di satu modul.**
Memisahkan parameter (R-06) tidak cukup bila pemanggil dapat membentuk
`Instruksi` dari teks yang berasal dari luar. Konstruksi `Instruksi` dibatasi
pada `src/llm/instruksi.py`, yang tidak memuat pembentukan untai dari masukan
apa pun, dan pembatasan itu ditegakkan pemeriksa AST — bukan konvensi.

## Keputusan BT-14 — dinyatakan tegas

> **Pembungkus dibangun terhadap antarmuka abstrak dengan satu implementasi
> tiruan deterministik. Tidak ada penyedia konkret pada fitur 001.**

| | |
|---|---|
| **Alasan 1** | ADR-11 dan AP-03 memang menghendaki penyedia dapat diganti tanpa menyentuh logika aplikasi. Antarmuka abstrak adalah wujud keputusan itu, bukan penundaannya |
| **Alasan 2** | BT-14 dijadwalkan Bulan 2 dan belum diputuskan tim. Menulis adaptor konkret sekarang berarti memilih penyedia lewat kode — persis pengambilan keputusan diam-diam yang diperingatkan pada Gerbang 1 |
| **Alasan 3** | Adaptor konkret menuntut SDK penyedia sebagai ketergantungan, dan C-12 mensyaratkan persetujuan untuk keputusan yang belum diambil |
| **Alasan 4** | Kriteria penerimaan spec mensyaratkan tidak ada pemanggilan ke penyedia luar selama seluruh rangkaian uji |

**Risiko yang diterima.** Antarmuka yang dirancang tanpa penyedia nyata dapat
tidak pas ketika penyedia pertama dipasang. Dikurangi dengan menjaga antarmuka
tetap kecil — satu metode, satu bentuk tanggapan — dan diterima secara sadar:
adaptor nyata pertama menjadi penguji abstraksi ini, dan setiap penyesuaian
dicatat sebagai `logbook/` L4, bukan diperbaiki diam-diam. Tercatat sebagai
**RP-04** di bawah.

## Ketergantungan yang dimintakan persetujuan — C-12

Seluruhnya dimintakan sekaligus agar persetujuannya sadar, bukan tersirat.
Tanpa persetujuan pada Gerbang 2, Fase A tidak dimulai.

### Runtime

| Paket | Versi | Untuk apa | Bila ditolak |
|---|---|---|---|
| `pydantic` | ^2 | Tipe bertingkat untuk `Instruksi`, `Data`, `Konfigurasi`; validasi saat jalan yang menopang R-06 dan R-07 | `dataclasses` + `typing` pustaka baku; kehilangan validasi saat jalan, R-07 bergantung penuh pada uji |

Hanya satu. Pydantic dipilih karena akan dipakai FastAPI pada fitur berikutnya
(D-04 Bagian 5), sehingga ia bukan ketergantungan tambahan melainkan
ketergantungan yang didahulukan.

### Pengembangan

| Paket | Versi | Untuk apa | Bila ditolak |
|---|---|---|---|
| `pytest` | ^8 | Kerangka uji | — tidak ada pengganti yang wajar |
| `pytest-cov` | ^6 | Pengukuran cakupan untuk R-17 dan C-11 | `coverage.py` langsung; lebih banyak sambungan manual |
| `ruff` | ^0.9 | Linter dan pemformat dalam satu perkakas | `flake8` + `black` + `isort`; tiga ketergantungan menggantikan satu |
| `mypy` | ^1 | Pemeriksaan tipe statis; menopang R-06 dengan menjadikan pemisahan tipe kesalahan saat periksa, bukan saat jalan | `pyright` (memerlukan Node); atau tanpa pemeriksa tipe, R-06 melemah |

### Perkakas dasar

| Perkakas | Peran | Catatan |
|---|---|---|
| Python **3.12** | Bahasa | Dipilih di atas 3.13 karena ketersediaan *wheel* untuk tumpukan NLP (`torch`, `transformers`) pada fitur 004 lebih terjamin. Ini keputusan kelayakan, sejalan PA-03 |
| **uv** | Pengelola paket dan pengunci versi | Menghasilkan `uv.lock` dengan pohon transitif utuh — inilah yang membuat "versi kode" pada C-09 bermakna (G1-3). Alternatif: Poetry, setara untuk keperluan ini |
| GNU **make** | Titik masuk perintah | Sudah ada di lingkungan; bukan ketergantungan baru. Ia juga yang menyembunyikan pilihan `uv` dari alur kerja, sehingga penggantian ke Poetry tidak menyentuh `AGENTS.md` |

**Yang sengaja tidak diminta:** pustaka pemeriksa arsitektur, kerangka pencatatan
log, pustaka SDK penyedia LLM mana pun, dan seluruh perkakas kontainer.

## Berkas yang disentuh

| Berkas | Baru/ubah | Alasan |
|---|---|---|
| `AGENTS.md` | baru (salin) | R-01 |
| `CLAUDE.md` | baru (salin) | R-01 |
| `constitution.md` | baru (salin) | R-01 — agen tidak mengubah isinya |
| `docs/00-INDEKS.md`, `docs/D00.md` … `docs/D14.md` | baru (salin) | R-01; rujukan bagi `make compliance` |
| `specs/_template/{spec,plan,tasks}.md` | baru (salin) | R-02 |
| `pyproject.toml` | baru | Deklarasi ketergantungan langsung, konfigurasi ruff/mypy/pytest |
| `uv.lock` | baru | G1-3; pohon transitif terkunci |
| `ketergantungan-disetujui.toml` | baru | Rekaman himpunan paket yang disetujui Gerbang 2; pembanding bagi R-18 |
| `Makefile` | baru | `setup`, `test`, `test-unit`, `lint`, `check`, `compliance` |
| `perkakas/pemeriksa/ast_aturan.py` | baru | Inti pemeriksa AST; melayani R-04, R-13, aturan `Instruksi` |
| `perkakas/pemeriksa/placeholder.py` | baru | R-03 |
| `perkakas/pemeriksa/ketergantungan.py` | baru | R-18 |
| `perkakas/pemeriksa/cakupan.py` | baru | R-17 |
| `perkakas/kepatuhan/daftar_pasal.py` | baru | Daftar C-01 s.d. C-20 beserta status dan pemeriksanya |
| `perkakas/kepatuhan/jalankan.py` | baru | R-15, R-16 |
| `src/llm/__init__.py` | baru | Permukaan publik pembungkus |
| `src/llm/tipe.py` | baru | `Instruksi`, `Data`, `Konfigurasi`, `Tanggapan`, `Peringkat` |
| `src/llm/instruksi.py` | baru | Satu-satunya tempat `Instruksi` dibentuk |
| `src/llm/pembungkus.py` | baru | R-04 s.d. R-09 |
| `src/llm/adaptor/dasar.py` | baru | Antarmuka abstrak penyedia |
| `src/llm/adaptor/tiruan.py` | baru | R-10 |
| `src/logbook/penulis.py` | baru | R-11 s.d. R-13; hanya menambah |
| `logbook/L1-percobaan.jsonl` | baru | Ditulis kode |
| `logbook/L2-versi-artefak.jsonl` | baru | Ditulis kode |
| `logbook/L4-keputusan.md` | baru | KM-001; ditulis manusia |
| `logbook/L7-alat-bantu-ai.md` | baru | KM-002; ditulis manusia |
| `tests/**` | baru | Satu berkas uji per kelompok kebutuhan |
| `docs/D14.md` | **ubah** | KM-003: tambah `catatan_keberlakuan`, naikkan ke 0.2 |
| `docs/D00.md` | **ubah** | KM-003: catat TK-39 pada Bagian 7 |
| `docs/D12.md` | **ubah** | G1-2: perbarui Bagian 7, catat temuan AK-12 |

Pemisahan `perkakas/` dari `src/` disengaja. Isi `perkakas/` adalah alat bantu
pembangunan, bukan bagian sistem yang dinilai TKT 3, dan memisahkannya menjaga
angka cakupan uji modul inti (C-11, NFR-16) tetap bermakna.

## Kontrak

**Tidak ada rute baru.** Fitur 001 tidak menyentuh `docs/D14.md` Bagian 3, dan
tidak memerlukan rute yang belum ada di sana.

Satu bentuk dari D-14 dipakai ulang: **bentuk galat Bagian 4.2**. Ketika
pemanggilan ke penyedia gagal (R-09), pembungkus mengembalikan:

```json
{
  "galat": {
    "kode": "LAYANAN_MODEL_GAGAL",
    "pesan_pengguna": "Layanan sedang tidak dapat dihubungi. Pertanyaan Anda tersimpan.",
    "id_jejak": "trc_…"
  }
}
```

| Aturan | Penerapan pada fitur ini |
|---|---|
| `pesan_pengguna` tanpa rincian teknis | Diuji: pesan tidak memuat nama penyedia, kode HTTP, atau jejak tumpukan |
| `pesan_pengguna` ≤ 20 kata, tanpa singkatan tak diuraikan | C-13; diuji sebagai hitungan kata |
| Rincian teknis hanya ke log | Diuji: sebab asli tercatat di log operasional, tidak pada tanggapan |

Catatan bagi peninjau: contoh `pesan_pengguna` di atas berbunyi "Pertanyaan Anda
tersimpan" — pada fitur 001 belum ada yang menyimpannya. Kalimat final ditetapkan
pada fitur 009 bersama layar S-09; di sini yang diuji adalah **bentuknya**, dan
teks sementara ditandai demikian di dalam kode.

## Skema data

**Tidak ada tabel basis data.** Kamus data `docs/D14.md` Bagian 5 belum
diwujudkan; itu pekerjaan fitur berikutnya.

Dua bentuk data ditetapkan di sini, keduanya wajib selaras dengan D-14 Bagian 5
sejak sekarang agar tidak perlu diterjemahkan ulang nanti.

### Tipe pada `src/llm/tipe.py`

| Tipe | Bidang | Selaras dengan |
|---|---|---|
| `Peringkat` | enum `T1`, `T2`, `T3`, `T4` | `segmen_teks.peringkat_kepercayaan`, D-13 Bagian 6 |
| `Instruksi` | `teks: str` | — hanya dibentuk di `src/llm/instruksi.py` |
| `Data` | `id_segmen: str`, `teks: str`, `peringkat_kepercayaan: Peringkat`, `indeks_asal: IndeksTujuan` | `segmen_teks` |
| `IndeksTujuan` | enum `utama`, `metadata` | `segmen_teks.indeks_tujuan`, menopang C-02 kelak |
| `Konfigurasi` | `nama_model`, `versi_model`, `suhu`, `batas_token` | — |
| `Tanggapan` | `teks`, `versi_model`, `waktu_mulai`, `waktu_selesai`, `biaya`, `id_jejak` | C-08 |

`Data` sudah membawa `peringkat_kepercayaan` dan `indeks_asal` meskipun
pengambilan belum ada. Alasannya: bila bidang itu baru ditambahkan pada fitur
007, C-02 dan C-19 harus disisipkan ke jalur yang sudah berjalan — pola yang
persis ingin dihindari G1-4. Bidang ini **dideklarasikan, belum ditegakkan**;
C-02 dan C-19 tetap berstatus *belum dapat diperiksa* pada fitur ini.

### Catatan `logbook/`

| Berkas | Bentuk | Bidang | Sumber |
|---|---|---|---|
| `L1-percobaan.jsonl` | JSONL, tambah saja | Sesuai `docs/D10.md` Bagian 3 | Kode |
| `L2-versi-artefak.jsonl` | JSONL, tambah saja | Sesuai `docs/D10.md` Bagian 4 | Kode |
| `L4-keputusan.md` | Markdown | `id`, `tanggal`, `konteks`, `keputusan`, `alternatif`, `dampak`, `pemutus` | Manusia |
| `L7-alat-bantu-ai.md` | Markdown | Sesuai `docs/D10.md` Bagian 9 | Manusia |

Pemisahan bentuk mengikuti siapa penulisnya: yang ditulis kode berbentuk JSONL
agar dapat diperiksa mesin; yang ditulis manusia berbentuk Markdown agar dapat
dibaca. L5 dan L6 belum dibuat — belum ada insiden dan belum ada penyimpangan.

## Perancah kepatuhan — R-15, R-16

`make compliance` menghasilkan satu baris untuk **setiap** pasal C-01 s.d. C-20,
dengan tiga keadaan dan tanpa keadaan keempat.

| Keadaan | Arti | Akibat |
|---|---|---|
| `LULUS` | Pemeriksa ada dan tidak menemukan pelanggaran | — |
| `GAGAL` | Pemeriksa ada dan menemukan pelanggaran | Keluar tidak-nol |
| `BELUM-DAPAT-DIPERIKSA` | Belum ada pemeriksa; **wajib menyebut fitur yang akan mengaktifkannya** | — |

Dua aturan yang membuatnya tidak dapat berbohong:

- Pelaksana menegaskan kedua puluh pasal muncul **tepat sekali**. Pasal tanpa
  entri menggagalkan `make compliance`, sehingga menambah pasal tanpa menetapkan
  statusnya merusak pembangunan alih-alih lolos senyap.
- Keluaran kosong diperlakukan sebagai kegagalan (R-16). Diam bukan lulus.

**Tagihan awal pada fitur 001** — tujuh dapat diperiksa, tiga belas belum:

| Dapat diperiksa | Cara |
|---|---|
| C-08 | AST: impor pustaka penyedia di luar `src/llm/` |
| C-09 | Pembungkus menolak pemanggilan tanpa kelima bidang versi |
| C-11 | Cakupan dibanding penanda tersimpan |
| C-12 | `uv.lock` dibanding `ketergantungan-disetujui.toml` |
| C-15 | Penelusuran nama terlarang: poin, lencana, papan peringkat, pertemanan |
| C-17 | Permukaan pembungkus tidak memuat parameter pemanggilan alat |
| C-18 | Untai penanda dari parameter data tidak muncul pada bidang instruksi |

| Belum dapat diperiksa | Menunggu fitur |
|---|---|
| C-01, C-19 | 008 validator sitasi |
| C-02 | 006 indeks terpisah menurut lisensi |
| C-03 | 002 gerbang karantina |
| C-04, C-05 | 012 telemetri |
| C-06, C-07 | 010 pipeline pengetahuan dan gerbang kurasi |
| C-10 | 003 perangkat anotasi |
| C-13 | 013 antarmuka |
| C-14 | 010 s.d. 013 — sebagian dapat diperiksa lebih awal, ditinjau tiap fitur |
| C-16 | 007 kalibrasi ambang |
| C-20 | 009 rute `/api/v1/tanya` |

Daftar ini **wajib menyusut**, tidak pernah bertambah. Pemeriksaannya menjadi
tugas tetap pada setiap Gerbang 4 berikutnya.

## Pasal konstitusi

| Pasal | Bagaimana dipenuhi | Cara diuji |
|---|---|---|
| **C-08** | Seluruh pemanggilan model hanya lewat `src/llm/pembungkus.py`; pembungkus mencatat nama dan versi model, konfigurasi, waktu mulai dan selesai, biaya | Uji: berkas contoh yang mengimpor pustaka penyedia di luar `src/llm/` membuat pemeriksa AST gagal. Uji: `Tanggapan` tanpa salah satu bidang ditolak |
| **C-09** | Setiap pemanggilan menulis baris `logbook/L1` memuat versi kode, model, indeks, skema anotasi, pembagian data | Uji: pemanggilan dengan bidang versi kosong ditolak. Uji: bidang yang belum berlaku berisi `belum-berlaku`, bukan kosong (R-12) |
| **C-11** | Penanda cakupan disimpan; `make check` membandingkannya | Uji: penanda diturunkan secara buatan → `make check` gagal |
| **C-12** | `uv.lock` dibandingkan dengan `ketergantungan-disetujui.toml` | Uji: paket disisipkan ke lock tanpa masuk daftar → `make check` gagal |
| **C-15** | Penelusuran nama terlarang pada `src/` | Uji: berkas contoh bernama `lencana` → pemeriksa gagal |
| **C-17** | Antarmuka pembungkus dan adaptor tidak memuat parameter alat, pendaftaran fungsi, atau keluaran yang dapat dieksekusi | Uji: telaah tanda tangan `pembungkus.panggil` dan `AdaptorDasar` — tidak ada parameter semacam itu. Uji: adaptor tiruan menolak konfigurasi yang memuat kunci alat |
| **C-18** | Permintaan berbentuk objek; `instruksi` dan `data` menempati bidang berbeda; pembungkus tidak menggabungkannya menjadi satu untai | **Uji penanda:** `Data.teks` diisi untai unik, permintaan dihasilkan, ditegaskan untai itu **tidak muncul** pada bidang instruksi — **ambang nol**. Uji tambahan memakai muatan bergaya serangan D-13 Bagian 1 |

Pasal C-01 s.d. C-07, C-10, C-13, C-14, C-16, C-19, C-20 tidak disentuh fitur ini
dan tercatat sebagai *belum dapat diperiksa* dengan fitur penguncinya, sesuai
tabel di atas.

## Risiko

| Kode | Risiko | Bila terjadi |
|---|---|---|
| **RP-01** | Pemeriksa berbasis AST dapat dilewati: `importlib`, `getattr`, impor di dalam fungsi | **Diakui sebagai risiko sisa, tidak diklaim tertutup.** Sejalan PT-01 pada D-13: yang dirancang bukan pencegahan sempurna. Dikurangi dengan pemeriksaan tambahan saat jalan pada pembungkus, dan dinyatakan apa adanya pada keluaran `make compliance` |
| **RP-02** | Daftar *belum dapat diperiksa* menjadi tempat menyembunyikan pekerjaan | Setiap entri wajib menyebut fitur penguncinya; daftar diperiksa menyusut pada tiap Gerbang 4. Bila ia bertambah, itu temuan, bukan keadaan biasa |
| **RP-03** | `uv` relatif baru dan mungkin tidak dapat dipakai pada infrastruktur UPI | `Makefile` menyembunyikan pilihan perkakas; penggantian ke Poetry menyentuh satu berkas dan tidak mengubah `AGENTS.md` |
| **RP-04** | Antarmuka abstrak tidak pas ketika penyedia nyata dipasang (BT-14) | Antarmuka dijaga kecil: satu metode, satu bentuk tanggapan. Penyesuaian dicatat sebagai `logbook/` L4, tidak diperbaiki diam-diam |
| **RP-05** | Sifat tambah-saja `logbook/` ditegakkan pada kode, tetapi tidak terhadap penyuntingan berkas langsung maupun penulisan ulang riwayat git | Dinyatakan terbuka. Kendali sesungguhnya bersifat prosedural (`AGENTS.md`: jangan menyentuh `logbook/` selain menambah baris). Tidak diklaim lebih dari itu |
| **RP-06** | Jumlah tugas atomik mendekati ambang ±30 yang ditetapkan Gerbang 1 | Perkiraan **±29**. Bila `tasks.md` melampaui 30, ditinjau ulang di Gerbang 3 sesuai G1-4 — bukan dipecah sekarang |

## Yang tidak dikerjakan

Tegas. Bila salah satu tampak perlu selama implementasi: berhenti dan tanya.

- **Adaptor penyedia LLM konkret.** BT-14 belum diputuskan; lihat bagian keputusan di atas
- **Kontainerisasi, `docker-compose`, berkas penyebaran.** G1-3; milik jalur D-09
- **Basis data, migrasi, tabel mana pun** dari kamus data D-14 Bagian 5
- **Rute API mana pun.** `src/api/` belum dibuat pada fitur ini
- **Antarmuka web** dan tujuh keadaan layar D-05 Bagian 7
- **Pengambilan, penyusunan jawaban, validator sitasi, pemeriksa penyimpangan**
- **Penegakan C-02 dan C-19** meski bidangnya sudah ada pada tipe `Data` —
  penegakan tanpa pengambilan hanya menghasilkan uji yang menguji dirinya sendiri
- **Penerjemahan seluruh FR ke EARS** (BT-48) dan **berkas OpenAPI awal** (BT-58)
- **Pemangkasan `AGENTS.md`** ke bawah 120 baris dan penambahan pengetahuan tim —
  BACADULU menetapkannya pekerjaan manusia
- **Perubahan `constitution.md`** dalam bentuk apa pun

Satu hal yang tampak wajar ditambahkan dan tetap tidak dikerjakan: **integrasi
berkelanjutan**. `make check` dirancang agar dapat dijalankan alat CI mana pun,
tetapi pemilihan dan penyetelannya bukan bagian fitur ini dan akan menambah
ketergantungan serta keputusan infrastruktur yang belum diambil (BT-15).
