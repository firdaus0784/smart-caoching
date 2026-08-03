# Spec: 001-kerangka-proyek

| | |
|---|---|
| Kebutuhan | NFR-15, NFR-16, NFR-21, NFR-22, FR-D03, FR-F17 (dari `docs/D01.md`) |
| Dokumen terkait | D-04 ADR-10, ADR-11, AP-01, AP-03, AP-06 · D-10 L1, L2, L4, L7 · D-12 Bagian 6, 7 · D-13 KD-07, KD-09, KD-10 · D-14 Bagian 4.2 |
| Pasal konstitusi yang menyentuh fitur ini | C-08, C-09, C-11, C-12, C-17, C-18 |
| Urutan pembangunan | 001 dari 013 (`docs/D12.md` Bagian 7) |
| Status | Menunggu Gerbang 1 |

## Tujuan

Setelah fitur ini ada, seluruh pekerjaan berikutnya berjalan di atas lantai yang
menegakkan aturannya sendiri: setiap pemanggilan model hanya mungkin lewat satu
pintu yang mencatat versinya, konten data secara struktural tidak dapat mencapai
posisi instruksi, sistem tidak memiliki jalur untuk bertindak, dan `make check`
menolak pekerjaan yang melanggar keduanya. Sebelum fitur ini, tidak ada satu pun
kendali yang dapat ditegakkan mesin — seluruh kepatuhan bergantung pada
kedisiplinan pembaca dokumen.

Fitur ini bukan sekadar penyiapan repositori. Pembungkus `src/llm/` adalah tempat
C-18 dan C-17 diwujudkan (D-13 KD-07 menegaskan pemisahan instruksi dan data
ditegakkan **pada lapisan pembungkus**, bukan pada penyusunan teks permintaan),
sehingga fitur 001 adalah gerbang kepatuhan pertama — dibangun sebelum hal yang
dijaganya, sesuai alasan yang sama yang menempatkan fitur 008 sebelum 009.

## Keputusan manusia yang mengikat fitur ini

Dicatat verbatim; dipindahkan ke `logbook/` sebagai tugas berkode dalam `tasks.md`.

| Kode | Keputusan | Pemutus | Tujuan catatan |
|---|---|---|---|
| KM-001 | "Saya memegang Gerbang 1–4 pada sesi ini. Ini keputusan sementara untuk jalur pengembangan sistem; BT-49 tetap terbuka dan akan diputuskan resmi di rapat tim." | Pemegang gerbang | D-10 **L4** |
| KM-002 | Pengecualian Gerbang 4 untuk fitur 001 disetujui dengan tiga syarat: (a) daftar periksa ditulis di `tasks.md` **sebelum** implementasi, bukan sesudah; (b) pengecualian berlaku **hanya** untuk fitur 001, bukan "sampai infrastruktur siap"; (c) `make check` dan `make compliance` yang berfungsi adalah bagian luaran fitur 001 — bila belum ada di akhir, fitur belum selesai. | Pemegang gerbang | D-10 **L7** |
| KM-003 | "Tambahkan `catatan_keberlakuan` ke D-14 Bagian 4.1. D-07 Bagian 5.1 sudah menetapkannya; yang keliru adalah D-14 yang tidak membawanya ke bentuk tanggapan. Naikkan D-14 ke 0.2 dan catat TK-39 pada D-00 Bagian 7. Bersifat sementara sampai dikonfirmasi rapat tim, tetapi tidak perlu menunggu — 008 dan 009 boleh dibangun dengan bentuk ini." | Pemegang gerbang | D-00 §7, D-14 §4.1 |

Syarat (c) pada KM-002 adalah kriteria penerimaan fitur ini, bukan catatan.
Ia muncul kembali sebagai butir pertama pada Kriteria penerimaan di bawah.

## Di luar cakupan

Tegas. Bila salah satu tampak perlu selama implementasi: berhenti dan tanya.

- **Pemilihan penyedia LLM** (BT-14). Yang dibangun adalah antarmuka adaptor;
  inti bersifat agnostik terhadap penyedia. Ini justru maksud ADR-11 dan AP-03.
- **Pemanggilan penyedia berbayar mana pun.** Seluruh uji berjalan pada adaptor
  tiruan deterministik.
- **Basis data, skema tabel, dan migrasi.** Kamus data D-14 Bagian 5 belum
  diwujudkan pada fitur ini.
- **Pengambilan, penyusunan jawaban, validator sitasi, pemeriksa penyimpangan.**
  Fitur 006 s.d. 009.
- **Antarmuka web dan tujuh keadaan layar.** Fitur 013.
- **Kontainerisasi dan penyebaran** (ADR-10, NFR-17). Ia milik jalur D-09 dan
  tidak diperlukan untuk menjalankan `make check` di lingkungan pengembangan.
- **Penerjemahan seluruh FR ke EARS** (BT-48) dan **berkas OpenAPI awal**
  (BT-58). Keduanya pekerjaan tersendiri, bukan bagian fitur 001.
- **Pemangkasan `AGENTS.md`** ke bawah 120 baris dan penambahan pengetahuan tim.
  BACADULU menetapkannya sebagai pekerjaan manusia; agen tidak melakukannya.
- **Perubahan `constitution.md`.** Agen tidak mengubah berkas itu.

## Kebutuhan (EARS)

### Lapisan tata kelola

| ID | Kebutuhan |
|---|---|
| R-01 | Repositori **HARUS** memuat `AGENTS.md`, `CLAUDE.md`, dan `constitution.md` di akar, serta `docs/00-INDEKS.md` dan `docs/D01.md` s.d. `docs/D14.md`, sesuai penempatan pada BACADULU |
| R-02 | Repositori **HARUS** memuat `specs/_template/` berisi `spec.md`, `plan.md`, dan `tasks.md` |
| R-03 | **JIKA** bagian "Perintah" pada `AGENTS.md` masih memuat penanda placeholder, **MAKA** `make check` **HARUS** gagal |

R-03 menutup risiko yang dinyatakan BACADULU: placeholder yang dibiarkan lebih
buruk daripada tidak ada bagian itu sama sekali, karena agen akan menjalankannya
dan gagal diam-diam.

### Pembungkus model — C-08, C-17, C-18

| ID | Kebutuhan |
|---|---|
| R-04 | Seluruh pemanggilan model **HARUS** melewati `src/llm/`. **JIKA** modul di luar `src/llm/` mengimpor pustaka penyedia model secara langsung, **MAKA** `make check` **HARUS** gagal |
| R-05 | **KETIKA** pembungkus dipanggil, ia **HARUS** mencatat nama dan versi model, konfigurasi, stempel waktu mulai dan selesai, serta biaya terhitung |
| R-06 | Antarmuka pembungkus **HARUS** menerima instruksi dan data sebagai parameter yang terpisah dan bertipe berbeda |
| R-07 | Konten yang masuk melalui parameter data **TIDAK BOLEH** dapat mencapai posisi instruksi melalui jalur mana pun yang disediakan antarmuka, termasuk melalui penggabungan teks di dalam pembungkus |
| R-08 | Antarmuka pembungkus **TIDAK BOLEH** menyediakan parameter pemanggilan alat, pendaftaran fungsi, keluaran terstruktur yang dapat dieksekusi, atau mekanisme setara |
| R-09 | **JIKA** pemanggilan ke penyedia gagal, **MAKA** pembungkus **HARUS** mengembalikan galat berbentuk `docs/D14.md` Bagian 4.2 dengan kode `LAYANAN_MODEL_GAGAL`, dan `pesan_pengguna` **TIDAK BOLEH** memuat rincian teknis |
| R-10 | Pembungkus **HARUS** menyediakan adaptor tiruan deterministik yang dipakai seluruh uji |

R-07 dinyatakan terpisah dari R-06 dengan sengaja. Memisahkan parameter saja
tidak cukup bila pembungkus kemudian menggabungkannya menjadi satu untai teks
sebelum dikirim; yang diuji adalah bahwa **tidak ada jalur** menuju posisi
instruksi, bukan bahwa antarmukanya terlihat rapi. Ini yang membuat UK-10
(`docs/D13.md` Bagian 8, ambang nol) dapat diuji sejak sekarang.

### Pencatatan versi — C-09, NFR-15

| ID | Kebutuhan |
|---|---|
| R-11 | **KETIKA** sebuah pemanggilan model atau percobaan menghasilkan luaran yang dicatat, sistem **HARUS** menulis satu baris ke `logbook/` memuat versi kode, versi model, versi indeks, versi skema anotasi, dan penanda pembagian data |
| R-12 | **JIKA** salah satu bidang versi pada R-11 belum berlaku pada tahap pengembangan berjalan, **MAKA** bidang itu **HARUS** diisi penanda eksplisit `belum-berlaku`, dan **TIDAK BOLEH** dikosongkan atau dihilangkan |
| R-13 | Kode aplikasi **HARUS** hanya dapat menambah baris pada `logbook/`; pengubahan dan penghapusan baris **TIDAK BOLEH** dimungkinkan melalui kode |

R-12 mencegah kebiasaan yang merusak reproduksibilitas dalam senyap: bidang yang
dikosongkan tidak dapat dibedakan antara "belum ada" dan "lupa dicatat", dan
selisih itu baru terasa pada Bulan 8 ketika naskah disusun.

### Gerbang mutu — C-11, C-12

| ID | Kebutuhan |
|---|---|
| R-14 | `make check` **HARUS** menjalankan V-01 s.d. V-06 (`docs/D12.md` Bagian 5) dan gagal bila salah satu tidak terpenuhi |
| R-15 | `make compliance` **HARUS** memeriksa pasal C-01 s.d. C-20 dan, untuk pasal yang belum dapat diperiksa mesin pada tahap berjalan, menampilkannya sebagai daftar **belum dapat diperiksa** yang eksplisit |
| R-16 | **JIKA** `make compliance` berakhir tanpa menampilkan daftar pada R-15, **MAKA** ia **HARUS** gagal |
| R-17 | **JIKA** cakupan uji modul inti turun dibanding penanda tersimpan, **MAKA** `make check` **HARUS** gagal |
| R-18 | **JIKA** manifes ketergantungan memuat butir yang tidak tercantum pada daftar ketergantungan yang disetujui, **MAKA** `make check` **HARUS** gagal |

R-15 dan R-16 adalah inti fitur ini. Pada tahap 001, sebagian besar pasal belum
dapat diperiksa mesin karena komponen yang dijaganya belum ada. `make compliance`
yang melaporkan "lulus" dalam keadaan itu adalah laporan palsu, dan justru
laporan palsu yang paling berbahaya — ia menghentikan kewaspadaan. Karena itu
keluarannya wajib membedakan **lulus**, **gagal**, dan **belum dapat diperiksa**,
dan diamnya sendiri diperlakukan sebagai kegagalan.

## Keadaan yang wajib ditangani

**Tidak berlaku.** Fitur 001 tidak memiliki antarmuka pengguna. Tujuh keadaan
`docs/D05.md` Bagian 7 mulai berlaku pada fitur yang menyentuh layar.

Satu keadaan tetap ditangani karena bersifat lintas fitur: kegagalan penyedia
model pada R-09 memakai bentuk galat D-14 Bagian 4.2, dan bentuk itulah yang
kelak dipakai keadaan KL-D pada layar.

## Kriteria penerimaan

- [ ] `make check` dan `make compliance` **ada dan berfungsi** — syarat (c) pada KM-002
- [ ] R-01 s.d. R-18 masing-masing punya uji yang **gagal sebelum implementasi**
- [ ] C-08 punya uji tersendiri: impor pustaka penyedia di luar `src/llm/` terdeteksi dan menggagalkan `make check`
- [ ] C-17 punya uji tersendiri: antarmuka pembungkus tidak mengekspos pemanggilan alat
- [ ] C-18 punya uji tersendiri: konten parameter data tidak mencapai posisi instruksi pada permintaan yang dihasilkan — **ambang nol**, cikal bakal UK-10
- [ ] C-09 punya uji tersendiri: pemanggilan tanpa kelima bidang versi ditolak
- [ ] C-11 punya uji tersendiri: penurunan cakupan menggagalkan `make check`
- [ ] C-12 punya uji tersendiri: ketergantungan di luar daftar disetujui menggagalkan `make check`
- [ ] `make compliance` membedakan lulus / gagal / belum dapat diperiksa, dan gagal bila diam
- [ ] Tidak ada pemanggilan ke penyedia luar selama seluruh rangkaian uji
- [ ] KM-001 tercatat pada `logbook/` sebagai L4; KM-002 sebagai L7 beserta alasan dan pemberi izin
- [ ] KM-003 diterapkan: `catatan_keberlakuan` masuk `docs/D14.md` Bagian 4.1, D-14 naik ke 0.2, TK-39 tercatat pada `docs/D00.md` Bagian 7
- [ ] Setiap berkas berubah dapat ditelusuri ke kode kebutuhan
- [ ] Daftar periksa Gerbang 4 tertulis di `tasks.md` **sebelum** implementasi — syarat (a) pada KM-002

## Pertanyaan terbuka

**Tidak ada.** Fitur ini dapat diserahkan ke agen.

Tiga butir terbuka yang bersinggungan sengaja **tidak** menghambat fitur ini,
dan alasannya dicatat agar tidak ditinjau ulang berkali-kali:

| Butir | Mengapa tidak menghambat |
|---|---|
| BT-14 penyedia LLM | Inti dibangun agnostik; penyedia menjadi adaptor. Ini maksud ADR-11 |
| BT-15 spesifikasi server | Fitur ini berjalan di lingkungan pengembangan; penyebaran di luar cakupan |
| BT-47 perkakas SDD | Alur `spec → plan → tasks → kode` dijalankan manual; perkakas mempercepat, tidak menentukan |

Satu hal yang **bukan** pertanyaan terbuka melainkan keputusan Gerbang 2:
pemilihan bahasa, pengelola paket, kerangka uji, dan seluruh daftar
ketergantungan awal. C-12 mensyaratkan persetujuan penanggung jawab teknis,
sehingga `plan.md` akan memuatnya sebagai daftar eksplisit agar persetujuannya
sadar, bukan tersirat.
