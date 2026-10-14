# Spec: 042-penjalan-uji-kepatuhan

| | |
|---|---|
| Kebutuhan | D-08 Bagian 8 (U5, UK-01 s.d. UK-08); D-13 Bagian 8 (UK-09 s.d. UK-15); D-09 PS-01, PS-14, langkah penyebaran 5; NFR-21, NFR-22; C-02, C-03, C-04, C-05, C-06, C-09, C-17, C-18, C-20 |
| Dokumen terkait | D-08 Bagian 8, 11 · D-13 Bagian 8, 9 · D-09 Bagian 2.1, 4.1 · D-10 Bagian 3 · D-14 Bagian 3 · `perkakas/basis_data/README.md` · spec fitur 024, 034, 040 |
| Status | **Gerbang 4 lolos** — 14 Oktober 2026 (KB-321). Enam dari enam tugas selesai |

## Mengapa fitur ini diusulkan sekarang

D-09 menjadikan UK-01 s.d. UK-08 prasyarat pilot (PS-01) dan UK-09 s.d. UK-15
prasyarat berikutnya (PS-14). Langkah penyebaran 5 mengulang UK-01 s.d. UK-08
**di lingkungan produksi**, *"sebab perbedaan konfigurasi antarlingkungan
adalah sumber kegagalan kepatuhan yang paling sering luput"*.

Sebagian besar sifat yang diuji sudah dibangun dan diuji — penolakan hak oleh
peladen (fitur 024 dan seterusnya), gerbang perekaman telemetri, dan validator
sitasi. Tetapi semuanya terbukti pada **peladen uji `make
check`**, bukan pada lingkungan yang akan melayani kepala sekolah. Tidak ada
alat yang menjalankannya terhadap sebuah lingkungan dan melaporkan
UK-01 s.d. UK-15 dalam satu laporan. Baris 042 disisipkan atas putusan
pemegang gerbang (KB-311).

## Yang tidak dikerjakan fitur ini, dinyatakan di muka

- **Uji adversarial D-13 Bagian 9** dan penyusunan himpunan serangannya.
  Penyusunnya wajib anggota tim yang tidak membangun komponen RAG.
- **Uji yang menuntut model penjawab atau *gold set***. Dinyatakan belum dapat
  diperiksa sampai bahannya ada.
- **Penyebaran itu sendiri** (D-09) dan pengelolaan rahasia lingkungan.
- **Ambang baru.** Seluruh ambang milik D-08 Bagian 8 dan D-13 Bagian 8.

## Peta pemeriksaan

Disusun dari D-08 dan D-13; kolom terakhir adalah keadaan **hari ini**.

| UK | Uji | Cara pada penjalan | Hari ini |
|---|---|---|---|
| UK-01 | Segmen berlisensi tertutup tidak masuk konteks LLM | Telusuri log 200 jawaban *gold set* | Belum: *gold set* (BT-35), model (ADR-12) |
| UK-02 | Karantina tidak terjangkau layanan RAG | Peran-peran layanan RAG mencoba membaca karantina | Dapat |
| UK-03 | Regulasi dicabut tidak dipakai menyusun jawaban | Pertanyaan jenis E | Belum: *gold set*, model |
| UK-04 | Kunci pseudonim tidak terjangkau layanan aplikasi | Peran-peran layanan aplikasi mencoba tersambung ke basis data pseudonim | Dapat |
| UK-05 | Telemetri tidak merekam tanpa persetujuan | Akun tanpa persetujuan memicu peristiwa; peristiwanya tetap nol | Dapat, dengan akun uji (P-3) |
| UK-06 | Data pribadi tidak lolos ke keluaran jawaban | Dokumen berpola data pribadi, lalu jawaban model | Belum: model |
| UK-07 | Kendali akses peran di lapisan API | Rute internal dengan token pengguna biasa | Dapat, dengan akun uji |
| UK-08 | Butir tidak tayang tanpa persetujuan kurator | Butir disisipkan langsung ke basis data tanpa putusan | Dapat |
| UK-09 | Pemanggil LLM tanpa tulis, karantina, kunci pseudonim | Peran pemanggil model mencoba ketiganya | Dapat |
| UK-10 | Konten terambil tidak di posisi instruksi | Pemeriksa pemisahan instruksi atas kode terpasang | Dapat (P-5) |
| UK-11 | Dokumen berpola adversarial tertahan ≥ 90% | Himpunan dokumen serangan | Belum: himpunan serangan D-13 Bagian 9 |
| UK-12 | Keluaran melanggar kontrak dibuang | Validator atas keluaran rekaan yang melanggar | Dapat (P-5) |
| UK-13 | Klaim bersandar tunggal pada T3/T4 tidak tayang | Validator atas klaim rekaan | Dapat (P-5) |
| UK-14 | Data pribadi yang diketik pengguna disamarkan sebelum keluar | Pertanyaan berpola data pribadi rekaan lewat API | Dapat, dengan akun uji |
| UK-15 | Pengguna biasa tidak menjangkau rute kurator, anotator, analitik | Setiap rute D-14 Bagian 3 berperan selain pengguna, dengan token pengguna biasa | Dapat, dengan akun uji |

## Kebutuhan (EARS) yang tidak bergantung pada pertanyaan

| ID | Kebutuhan |
|---|---|
| R-01 | Setiap laporan **HARUS** memuat UK-01 s.d. UK-15, masing-masing berkeadaan **lulus**, **gagal**, atau **belum dapat diperiksa** beserta sebabnya; tidak satu UK pun boleh hilang dari laporan |
| R-02 | Laporan keseluruhan **HARUS** berbunyi lolos hanya bila kelima belasnya lulus (ambang nol, D-08 Bagian 8, D-13 Bagian 8); keadaan belum dapat diperiksa **TIDAK BOLEH** terbaca lulus |
| R-03 | Pemeriksaan hak **HARUS** dijalankan sebagai peran yang diuji, pada lingkungan sasaran. Lulus **HANYA** bila peladen menolak dengan sebab hak — galat lain, termasuk sambungan gagal, dicatat gagal, bukan lulus |
| R-04 | Penjalan **TIDAK BOLEH** meninggalkan perubahan pada lingkungan sasaran (D-09 langkah 5 di produksi) |
| R-05 | Laporan dan catatan **TIDAK BOLEH** memuat data pribadi, rahasia sambungan, maupun token |
| R-06 | Setiap putaran **HARUS** tercatat beserta versi kode dan nama lingkungan sasaran (C-09, AP-04) |
| R-07 | Fitur ini **TIDAK BOLEH** menambah rute, peran, hak, maupun paket (C-12, C-17, C-20) |

## Pertanyaan terbuka

Tiap pertanyaan disertai anjuran; anjuran bukan putusan.

**P-1 · Bentuk penjalan.**

| Pilihan | Arti |
|---|---|
| A | **Perkakas** `python -m perkakas.kepatuhan jalankan --lingkungan <nama>`; laporan per UK dan kode keluar, seperti perkakas evaluasi fitur 040 |
| B | Rangkaian pytest bertanda yang diarahkan ke lingkungan lewat variabel |

**Anjuran: A.** Yang menjalankannya anggota teknis pada D-09 langkah 5, dan
laporannya bukti PS-01. Uji pytest yang lulus atau gagal tidak menyatakan
*belum dapat diperiksa* sebagai keadaan ketiga.

**P-2 · Perubahan pada lingkungan sasaran.**

| Pilihan | Arti |
|---|---|
| A | **Hanya percobaan yang semestinya ditolak, di dalam transaksi yang selalu dibatalkan**; tanpa data uji. Aman diulang di produksi |
| B | Data uji dibuat lalu dihapus sesudahnya |
| C | Hanya di lingkungan pementasan |

**Anjuran: A.** D-09 mengulang uji di produksi. Data uji yang gagal dihapus
karena penjalan terhenti di tengah akan tertinggal bersama data peserta.

**P-3 · Uji lapisan API** (UK-05, UK-07, UK-14, UK-15).

| Pilihan | Arti |
|---|---|
| A | **Terhadap API yang berjalan, dengan satu akun uji kepatuhan** berperan pengguna biasa dan tanpa persetujuan penelitian. Akun dibuat operator lewat `perkakas.akun` yang sudah ada, bukan oleh penjalan; tokennya diberikan lewat variabel lingkungan dan tidak pernah dicetak |
| B | Aplikasi dalam proses yang tersambung ke peladen sasaran — tidak menguji konfigurasi API yang sungguh berjalan |
| C | Ditunda; keempatnya belum dapat diperiksa |

**Anjuran: A.** Kendali akses yang diuji pada aplikasi dalam proses bukan
kendali akses lingkungan itu. Akun uji dibuat operator agar R-04 tetap
berlaku pada penjalan.

**P-4 · Tempat catatan putaran.**

| Pilihan | Arti |
|---|---|
| A | **Satu baris L1 per putaran**, `tugas` = `kepatuhan`, dengan kelima bidang versi, nama lingkungan, dan keadaan tiap UK; D-10 Bagian 3 bertambah |
| B | Berkas laporan di luar logbook yang dilampirkan pada PS-01 |

**Anjuran: A.** Jalur yang sama dengan pengujian U3 fitur 040, terbaca
pemeriksa catatan versi, dan tambah-saja.

**P-5 · UK yang sudah dijaga `make check`** (UK-10, UK-12, UK-13).

| Pilihan | Arti |
|---|---|
| A | **Dijalankan ulang oleh penjalan** atas kode yang terpasang, memanggil pemeriksa dan validator yang sama; laporan U5 utuh di satu tempat |
| B | Dirujuk ke hasil `make check` pada commit yang terpasang |

**Anjuran: A.** Laporan yang merujuk hasil lain menuntut pembacanya
memastikan commit keduanya sama, dan pemastian itu yang paling mudah luput.

**P-6 · UK yang bahannya belum ada** (UK-01, UK-03, UK-06, UK-11).

| Pilihan | Arti |
|---|---|
| A | **Belum dapat diperiksa** dengan sebabnya, sampai bahannya ada; fitur yang membawa bahannya menambahkan pemeriksaannya |
| B | Fitur ini juga menyediakan wadah himpunan serangan UK-11 — berkas di luar repositori seperti *gold set* fitur 040 |

**Anjuran: A.** Wadah UK-11 menuntut bentuk berkas dan aturan tertahan yang
belum dibahas D-13. Himpunan serangan juga wajib disusun anggota tim yang
tidak membangun RAG; wadahnya lebih baik dirancang bersama mereka.

## Putusan Gerbang 1 (KB-313)

Pemegang Gerbang 1–4 memilih anjuran pada setiap pertanyaan:

| Pertanyaan | Putusan |
|---|---|
| P-1 | **A** — perkakas `python -m perkakas.kepatuhan`; tiga keadaan per UK dan kode keluar |
| P-2 | **A** — hanya percobaan yang semestinya ditolak, di dalam transaksi yang selalu dibatalkan; tanpa data uji |
| P-3 | **A** — API yang berjalan, dengan satu akun uji kepatuhan buatan operator; token lewat variabel lingkungan, tidak pernah dicetak |
| P-4 | **A** — satu baris L1 per putaran, `tugas` = `kepatuhan`; D-10 Bagian 3 bertambah |
| P-5 | **A** — UK-10, UK-12, UK-13 dijalankan ulang atas kode yang terpasang |
| P-6 | **A** — UK-01, UK-03, UK-06, UK-11 belum dapat diperiksa sampai bahannya ada |

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | D-08 Bagian 8; D-13 Bagian 8; D-09 PS-01, PS-14 |
| R-02 | D-08 Bagian 8 "nol pelanggaran"; D-08 AP-02 |
| R-03 | D-08 UK-02, UK-04, UK-08, UK-09; spec fitur 024 |
| R-04 | D-09 Bagian 4.1 langkah 5 |
| R-05 | KM-03; C-05 |
| R-06 | C-09; D-08 AP-04 |
| R-07 | C-12, C-17, C-20 |

## Kriteria penerimaan

- [x] P-1 s.d. P-6 diputus pada Gerbang 1
- [x] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [x] Penjalan dijalankan atas PostgreSQL sebagai peran sungguhan dan atas
      API yang berjalan, dan lingkungan sesudahnya terbukti tidak berubah
- [x] `make check` lulus enam gerbang
