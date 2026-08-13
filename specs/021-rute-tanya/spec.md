# Spec: 021-rute-tanya

| | |
|---|---|
| Kebutuhan | FR-F01, FR-F09; kendali peran D-14 Bagian 3 |
| Dokumen terkait | D-14 Bagian 3 dan 4.1, D-07 Bagian 3 s.d. 6, D-05 Bagian 7 |
| Pasal konstitusi yang menyentuh fitur ini | C-02, C-07, C-13, C-17, C-18, C-19, C-20 |
| Status | Menunggu Gerbang 1 |

## Tujuan

Sesudah fitur ini, sebuah pertanyaan berbahasa Indonesia berjalan **dari ujung
ke ujung** menjadi `Tanggapan` D-14 Bagian 4.1 melalui **satu jalur yang
urutannya ditetapkan**, dan setiap rute D-14 Bagian 3 memiliki peran yang
menjaganya.

Seluruh potongannya sudah berdiri: praproses (015), pengambilan hibrida (007),
penilai kecukupan (007), pembungkus model (001), validator sitasi (008), dan
penyusun tanggapan (009). **Tidak ada satu pun yang menyambungkannya.** Selama
tidak ada, urutan pemanggilan hanya hidup pada D-07 sebagai prosa — dan prosa
tidak menolak pemanggil yang melewati satu tahap.

Itu bukan kekhawatiran yang jauh. Tiga pasal berdiri persis pada urutan itu:
C-19 menuntut validator berjalan **sebelum** tanggapan disusun; C-18 menuntut
segmen terambil tidak pernah menempati posisi instruksi pada permintaan yang
disusun **sesudah** pengambilan; C-02 menuntut segmen berlisensi tertutup tidak
pernah sampai ke pembungkus model sama sekali. Ketiganya dijaga masing-masing
lapisan hari ini. Yang belum ada adalah **tempat yang membuat melewatinya tidak
mungkin**, bukan sekadar salah.

## Di luar cakupan

Disebutkan tegas, dan masing-masing dengan sebabnya. Yang tidak disebut
sebabnya akan dikerjakan seseorang karena mengira ia terlupa.

- **Lapisan HTTP FastAPI.** Tertahan C-12. `usulan-ketergantungan.md` Bagian
  9.2 sudah menyetujui `fastapi`, `uvicorn`, dan `httpx` atas pendelegasian,
  tetapi `ketergantungan-disetujui.toml` **berkas keputusan tim** dan berkas
  itu menyatakannya sendiri. Agen tidak menambah barisnya. Yang dibangun di
  sini adalah seluruh isi rute tanpa kerangkanya — adaptor HTTP menjadi
  lapisan tipis yang memanggilnya.
- **Sumber vektor dan pemeringkat ulang** (fitur 019). Pengambilan tetap BM25
  saja. Orkestrator memanggil `ambil_hibrida` yang sudah menerima kedua sumber;
  sisi semantiknya masuk tanpa mengubah urutannya.
- **VS-03, VS-05, VS-07** (fitur 020). Validator sudah melaporkan ketiganya
  sebagai menunggu model lewat `pemeriksaan_menunggu_model`, dan orkestrator
  **meneruskan laporan itu apa adanya** — bukan menyembunyikannya.
- **Isi 20 jawaban terkurasi FR-F12.** Isinya pekerjaan kurator, bukan
  pekerjaan kode. Bentuk mekanismenya pun belum dapat diputuskan: ia bergantung
  pada apakah jawaban terkurasi membawa sitasi sendiri, dan itu baru terjawab
  ketika kurator menulis satu. Membangun tabel kosong sekarang berarti memilih
  jawabannya diam-diam.
- **Penyimpanan tetap riwayat percakapan.** Menunggu penggerak PostgreSQL
  (C-12, `usulan-ketergantungan.md` Bagian 9.3). Bentuk riwayatnya dibangun di
  sini; tempat tinggalnya menyusul, bentuk yang sama dengan `JejakKurasi`
  fitur 010.
- **Rute selain `/api/v1/tanya` dan `/api/v1/percakapan`.** Kendali perannya
  dibangun bagi **seluruh** rute D-14 Bagian 3 — daftar peran adalah satu
  tabel, dan tabel yang diisi separuh adalah tabel yang lubangnya tidak
  terlihat — tetapi isinya menunggu fiturnya masing-masing.

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | `Peran` **HARUS** memuat keenam peran D-14 Bagian 3 sebagai tipe, bukan untai bebas |
| R-02 | Setiap rute D-14 Bagian 3 **HARUS** memiliki tepat satu peran yang menjaganya; rute tanpa peran **TIDAK BOLEH** dapat dinyatakan |
| R-03 | **JIKA** sebuah rute dinyatakan pada kode tanpa ada pada D-14 Bagian 3, **MAKA** pemeriksa **HARUS** menolaknya (AG-02) |
| R-04 | Kendali peran **HARUS** menolak menurut daftar yang **dibaca dari `docs/D14.md`**, bukan yang disalin ke kode |
| R-05 | Jalur penjawaban **HARUS** berjalan pada urutan tetap: praproses → pengambilan → kecukupan → penyusunan permintaan → validasi → penyusunan tanggapan |
| R-06 | **JIKA** sebuah tahap dilewati, **MAKA** tanggapan **TIDAK BOLEH** dapat terbentuk — ditegakkan bentuk, bukan pemeriksaan berurutan |
| R-07 | **KETIKA** pertanyaan berada di luar domain, sistem **HARUS** berhenti sebelum pengambilan dan mengembalikan `di_luar_domain` (FR-F13) |
| R-08 | **KETIKA** bukti tidak cukup, sistem **HARUS** mengembalikan `tidak_ditemukan` **tanpa memanggil model** |
| R-09 | **JIKA** validator menahan jawaban, **MAKA** sistem **TIDAK BOLEH** menyusun tanggapan dari keluaran yang ditahan (C-19, VS-08) |
| R-10 | Jalur penjawaban **TIDAK BOLEH** memiliki kemampuan bertindak: tanpa parameter alat, tanpa akses tulis, tanpa pengiriman keluar (C-17) |
| R-11 | Segmen terambil **TIDAK BOLEH** menempati posisi instruksi pada permintaan ke model (C-18) |
| R-12 | Pemeriksaan validator yang menunggu model **HARUS** ikut pada hasil jalur, tidak disembunyikan (FR-F16) |
| R-13 | Riwayat percakapan **HARUS** menyimpan pertanyaan dan `id_pesan` tanggapannya, dan **TIDAK BOLEH** menyimpan salinan tanggapan (FR-F09) |
| R-14 | Riwayat percakapan **HARUS** bersifat tambah-saja; permukaannya **TIDAK BOLEH** menyediakan cara menyunting maupun menghapus baris |
| R-15 | Pesan galat kepada pengguna **HARUS** ≤ 20 kata, tanpa istilah teknis, tanpa kode galat (C-13, NFR-19) |
| R-16 | Bentuk tanggapan **HARUS** tetap persis `Tanggapan` D-14 Bagian 4.1; bidang tambahan **TIDAK BOLEH** ditambahkan (C-20, AG-03) |

**R-06 adalah inti fitur ini, dan ia bentuk — bukan aturan.** "Jalankan tahap
sesuai urutan" adalah kalimat yang benar dan tidak menjaga apa pun: pemanggil
berikutnya yang butuh jawaban cepat akan memanggil `susun` langsung, dan
kodenya berjalan. Yang menjaganya adalah `susun` yang **hanya menerima
`JawabanTervalidasi`** — dan itu sudah berlaku sejak fitur 009. Fitur ini
meneruskan bentuk yang sama satu tingkat ke atas: keluaran jalur adalah tipe
yang hanya dapat dibentuk jalur itu sendiri. Bentuk kelima sesudah `Instruksi`
(ADR-13), `JawabanTervalidasi` (008), `ButirTayang` (010), dan `Peristiwa`
(012).

**R-08 menyebut "tanpa memanggil model" dengan sengaja.** Bukti yang tidak
cukup lalu tetap dikirim ke model menghasilkan jawaban yang lancar dan tidak
tersitasi — persis kegagalan yang C-01 larang. Ia juga membakar biaya pada
pertanyaan yang jawabannya sudah diketahui. Urutan ini karena itu diuji
sebagai **ketiadaan panggilan**, bukan sebagai nilai kembalian.

**R-13 melarang menyimpan salinan tanggapan, dan itu bukan penghematan.**
Tanggapan yang tersimpan akan menua: status keberlakuan sitasinya berubah
ketika regulasinya dicabut, dan riwayat yang menyimpan salinannya akan
menayangkan klaim atas regulasi yang tidak berlaku — melanggar C-07 lewat
pintu yang tidak dijaga siapa pun. Riwayat menyimpan rujukan; isinya disusun
ulang saat dibuka.

## Keadaan yang wajib ditangani

| Keadaan | Perilaku yang dituntut |
|---|---|
| Pertanyaan di luar domain | Berhenti sebelum pengambilan; `di_luar_domain`, tanpa panggilan model |
| Bukti tidak cukup | `tidak_ditemukan`, tanpa panggilan model; bacaan lanjutan boleh menyertai |
| Bukti cukup tetapi validator menahan | `tidak_ditemukan`; keluaran yang ditahan **tidak** diteruskan, dan alasan penahanan tercatat pada hasil jalur — bukan pada tanggapan |
| Segmen T3 sebagai satu-satunya sandaran | Ditahan validator (C-19) — jalur tidak memeriksanya ulang, dan tidak boleh memeriksanya ulang |
| Layanan model gagal | `GalatLayananModel` fitur 001 menghasilkan pesan pengguna ≤ 20 kata; jalur **tidak** menelannya menjadi jawaban kosong |
| Peran tidak berwenang | Ditolak sebelum jalur berjalan sama sekali |
| Peran berwenang tanpa profil | Bukan galat — jalur berjalan; penyaringan prioritas milik fitur 011, bukan fitur ini |

## Pertanyaan yang wajib dijawab Gerbang 1

Empat, dan tidak satu pun dapat diputuskan saat menulis kode.

**1. Di mana `Peran` tinggal?** `src/kamus/` adalah rumah enum `docs/D14.md`
**Bagian 5**; `Peran` berasal dari **Bagian 3**. Menempatkannya di `src/kamus/`
melebarkan piagam modul itu diam-diam dari "kamus data" menjadi "enum apa pun
milik D-14", dan pelebaran yang tidak diputuskan adalah pelebaran yang tidak
punya batas berikutnya. **Usul: `src/api/peran.py`** — `AGENTS.md` sudah
menempatkan kendali peran di `src/api/`.

**2. Tepi `api → llm` belum tertulis.** `AGENTS.md` menyatakan `api` boleh
memanggil `nlp`, `rag`, `ingest`. Orkestrator menyusun permintaan lewat
`src/llm/`, dan tepi itu tidak ada pada daftar. Bentuknya persis tepi
`ingest → llm` yang ditemukan pada fitur 008: ada sejak lama, tidak pernah
dituliskan. **Usul: tuliskan tepinya** beserta alasannya — C-08 menuntut
seluruh pemanggilan model lewat `src/llm/`, sehingga setiap lapisan yang
memanggil model wajib memiliki tepi ke sana, dan yang tidak memilikinya adalah
lapisan yang tidak boleh memanggil model.

**3. Apakah orkestrator memanggil `pengguna` dan `telemetri`?** Keduanya juga
tanpa tepi. **Usul: tidak pada fitur ini.** Penyaringan terhadap prioritas
manajerial milik fitur 011; perekaman peristiwa tanya-jawab milik fitur 011
pula, sebab peristiwa yang direkam tanpa feed yang menghasilkannya adalah
peristiwa yang tidak dapat ditafsirkan. Menambah dua tepi bagi pemakaian yang
belum ada berarti membuka arah tanpa kebutuhan.

**4. Apakah kendali peran memeriksa rute yang belum dibangun?** **Usul: ya.**
Tabelnya diisi penuh dari D-14 Bagian 3 sejak sekarang, dan rute yang belum ada
kodenya tetap punya perannya. Tabel yang diisi separuh adalah tabel yang
lubangnya tidak terlihat — dan lubang pada tabel peran berarti rute yang, pada
hari ia dibangun, terbuka bagi siapa saja karena tidak ada baris yang
menolaknya.

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| FR-F01 | D-01 Bagian 6, Modul F |
| FR-F09 | D-01 Bagian 6, Modul F; D-14 Bagian 3.2 |
| Kendali peran | D-14 Bagian 3, keenam peran beserta penambahan `verifikator` (KB-011) |
| Urutan jalur | D-07 Bagian 3 s.d. 6 |
| Bentuk tanggapan | D-14 Bagian 4.1, C-20 |
| Keadaan layar | D-05 Bagian 7 |
