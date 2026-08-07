# Tasks: 015-praproses-ocr-dan-data-pribadi

Ditinjau manusia sebelum kode ditulis. Satu tugas = satu commit.

| | |
|---|---|
| Spec | `spec.md`, lolos Gerbang 1 |
| Plan | `plan.md`, lolos Gerbang 2 |
| Status | **Menunggu Gerbang 3** |
| Jumlah tugas | **17** — di bawah ambang ±30 |
| Pelaporan | Per fase: A, B, C, D, E. Bila sebuah tugas tidak dapat diselesaikan tanpa melanggar konstitusi atau `plan.md`, pekerjaan berhenti saat itu juga |

## Fase A · Ketergantungan dan penjagaannya

Dikerjakan lebih dulu karena A-3 adalah yang menahan sisanya bila berkas model
tidak ada, dan menemukannya sesudah tiga fase terbangun berarti membongkar.

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| A-1 | Pasang kelima paket; `ketergantungan-disetujui.toml` diperbarui — `langsung` bertambah lima, `terkunci` disusun ulang dari `uv.lock` | Uji: `make check` gagal bila satu nama dihapus dari daftar. **Uji: paket terpasang yang tidak tercatat → gagal** | R-13, C-12 | [ ] |
| A-2 | Bagian `[sistem]` pada `ketergantungan-disetujui.toml`; R-18 diperluas membandingkannya | Uji: sidik berbeda → gagal. **Uji: mesin tidak terpasang → "belum dapat diperiksa", bukan "lulus"** | R-13, C-12, C-09 | [ ] |
| A-3 | **Periksa keberadaan `ind.traineddata`; catat versi dan sidiknya** | Bukan tugas berkode — hasilnya dilaporkan pada uraian commit A-2 | R-05 | [ ] |

**A-3 adalah titik henti.** Bila berkas model tidak dapat diperoleh, KB-018
sudah menetapkan apa yang terjadi: fase D dibatalkan, `pytesseract` dicabut
pada A-1, dan FR-B02 menjadi butir terbuka. Keputusannya sudah diambil justru
agar tidak perlu diambil di sini.

Uji A-2 yang kedua adalah pelajaran TA-01 diterapkan pada perkakas: pemeriksa
yang tidak menemukan bahannya dan melapor lulus adalah laporan palsu.

## Fase B · Ekstraksi berkas

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| B-1 | Bahan uji pada `tests/bahan/` — DOCX, XLSX, empat PDF | Uji: keenam berkas terbaca dan berukuran wajar. **Uji: tidak ada data pribadi sungguhan pada bahan** | — | [ ] |
| B-2 | Antarmuka abstrak `Pengekstrak` pada `src/ingest/ekstraksi/dasar.py`; `TeksKanonik` sebagai tipe tersendiri | Uji: setiap pelaksana mengembalikan `TeksKanonik`, bukan `str` telanjang | R-01, R-03 | [ ] |
| B-3 | `PengekstrakDocx` — teks final, bukan perubahan terlacak | Uji: DOCX berperubahan terlacak menghasilkan teks final; **uji: keputusan itu tertulis pada uraian modul** | R-01 | [ ] |
| B-4 | `PengekstrakXlsx` — nilai terhitung, bukan rumus | Uji: sel berumus menghasilkan nilainya | R-01 | [ ] |
| B-5 | `PengekstrakPdf` | Uji: PDF berlapis teks terekstrak; **uji: PDF tanpa lapisan teks → galat khusus yang mengalihkan ke OCR, bukan teks kosong** | R-01, R-02 | [ ] |
| B-6 | **Berkas rusak, kosong, dan terkunci menghasilkan penolakan** | Uji: ketiganya → galat. **Uji: tidak satu pun menghasilkan `TeksKanonik` berisi untai kosong** | R-02 | [ ] |
| B-7 | Pesan galat pengguna bagi keenam keadaan Bagian "Keadaan yang wajib ditangani" | Uji: tiap pesan ≤ 20 kata, Bahasa Indonesia, tanpa istilah teknis, tanpa nama pustaka | R-02, C-13 | [ ] |

**B-6 adalah tugas terpenting fase ini.** Pengekstrak yang mengembalikan untai
kosong pada berkas rusak menghasilkan dokumen yang lolos seluruh gerbang fitur
002 tanpa satu pun berbunyi — tidak ada temuan pola pada teks kosong, dan tidak
ada data pribadi pada teks kosong. Itu bentuk kegagalan diam yang paling mahal
pada fitur ini.

B-7 disendirikan agar pesan pengguna ditulis sekali sebagai kumpulan, bukan
ditempel satu per satu saat menulis pengekstraknya. Pesan yang ditulis
sambil lalu adalah pesan yang menyebut nama pustaka.

## Fase C · Praproses

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| C-1 | `Token` pada `src/nlp/praproses/token.py` — permukaan, stem, `mulai`, `akhir` | Uji: `Token` tidak dapat dibentuk tanpa rentang. **Uji: `Token` beku** | R-08, C-10 | [ ] |
| C-2 | Tokenisasi dan normalisasi | **Uji sifat:** bagi setiap token, `teks_kanonik[t.mulai:t.akhir] == t.permukaan` — atas seluruh bahan uji, bukan satu kalimat | R-07, R-08, C-10 | [ ] |
| C-3 | Stop-word dan stemming lewat PySastrawi | Uji: stemming mengubah `stem`, **tidak** mengubah `permukaan`, `mulai`, maupun `akhir` | R-07, R-08 | [ ] |
| C-4 | Uraian modul menyatakan batas kegunaannya | Uji: uraian menyebut bahwa keluaran praproses untuk pencarian, **bukan** untuk bahan anotasi | R-03, C-10 | [ ] |

**C-2 dinyatakan sebagai sifat, bukan sebagai kasus.** Uji yang memeriksa satu
kalimat akan lolos pada versi yang benar untuk ASCII dan salah untuk teks
ber-tanda baca atau ber-spasi ganda.

## Fase D · OCR

Dibatalkan seluruhnya bila A-3 gagal (KB-018).

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| D-1 | `PengekstrakOcr` — satu-satunya tempat `pytesseract` diimpor | Uji: pengekstrak tiruan menghasilkan `TeksKanonik`. **Uji: mesin tidak terpasang → galat tegas saat penyalaan, bukan teks kosong** | R-04, R-06 | [ ] |
| D-2 | Pemeriksa impor tunggal `pytesseract`, mengikuti pola `impor_penyedia.py` | Uji: impor pada modul kedua → pemeriksa menyala. **Uji mutasi:** impor disisipkan → `make check` gagal | R-05, C-08 | [ ] |
| D-3 | Pencatatan versi mesin dan berkas model ke `logbook/` tiap keluaran OCR | Uji: satu baris per keluaran, memuat versi mesin dan sidik model | R-05, C-09 | [ ] |
| D-4 | Satu uji terhadap mesin sungguhan, ditandai sehingga dapat dilewati | Uji: berjalan bila mesin ada, dilewati bila tidak — **bukan** lulus diam-diam bila tidak | R-04 | [ ] |

**D-2 mengikuti D-1, bukan mendahuluinya** — kebalikan dari urutan biasa, dan
sengaja. Pemeriksa impor tunggal yang dibangun sebelum ada yang diimpor akan
lulus karena tidak memeriksa apa pun; itu pelajaran T-7 fitur 014 yang sama.

## Fase E · Pendeteksi data pribadi

| # | Tugas | Uji lebih dulu | Kebutuhan | Selesai |
|---|---|---|---|---|
| E-1 | `PendeteksiPola` pada `src/nlp/anonimisasi/pola.py` — enam pengenal, mengembalikan temuan berrentang karakter | Uji: keenam pola tertangkap dengan rentang yang benar; **uji: teks biasa tidak menghasilkan temuan** | R-09, C-10 | [ ] |
| E-2 | **Temuan tidak memutuskan, dan nilainya tidak pernah masuk log** | Uji: `Temuan` tanpa bidang `lolos` maupun `skor`. **Uji: pesan galat dan log tidak memuat nilai yang dideteksi** | R-10, R-11 | [ ] |
| E-3 | Uraian modul menyatakan apa yang **tidak** dideteksinya | Uji: uraian menyebut nama perorangan dan alamat sebagai yang tidak tertangkap, dengan contoh | R-12 | [ ] |

**E-3 bukan pekerjaan dokumentasi.** Ia bentuk yang sama dengan uraian
pemeriksa pola adversarial fitur 002, dan alasannya sama: laporan bersih yang
terbaca sebagai dokumen bersih menghentikan kewaspadaan verifikator. Di sini
akibatnya nama orang yang tidak tersamarkan lolos ke korpus karena seseorang
mengira modul ini menanganinya.

## Urutan

Fase A mendahului seluruhnya karena A-3 dapat membatalkan fase D, dan A-1
menahan fase B, C, dan D sampai paketnya terpasang.

Fase C dan E dapat berjalan sejajar; keduanya hanya menuntut `TeksKanonik`
dari B-2. Fase D menuntut B-5 karena PDF tanpa lapisan teks yang mengalihkan
ke OCR adalah jalan masuknya.

Penyambungan ke gerbang fitur 002 **tidak ada pada daftar ini** dan itu
disengaja: ia menuntut perubahan pada `Gerbang.terima`, dan perubahan itu
diajukan sebagai fitur tersendiri sesudah 015 lolos Gerbang 4. Menyambungkan
sambil membangun berarti dua fitur bergerak sekaligus pada berkas yang sama.

## Verifikasi akhir

- [ ] `make check` lulus 6 gerbang
- [ ] `make compliance` **tidak berubah** — 8 lulus, 0 gagal, 12 belum. Fitur ini tidak memindahkan pasal mana pun, dan angka yang berubah berarti ada yang keliru
- [ ] R-01 s.d. R-13 punya uji yang gagal sebelum implementasi
- [ ] Uji mutasi D-2 dijalankan dan hasilnya dilaporkan pada uraian commit
- [ ] Cakupan uji tidak turun
- [ ] Nol ketergantungan di luar lima yang disetujui KB-017
- [ ] Setiap pesan galat pengguna ≤ 20 kata, tanpa istilah teknis (C-13)
- [ ] Tidak ada data pribadi sungguhan pada `tests/bahan/`
