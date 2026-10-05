# Spec: 034-penyimpanan-dan-penyambungan-telemetri

| | |
|---|---|
| Kebutuhan | FR-J01, FR-J02, FR-J05; FR-A05; NFR-15; C-04, C-05, C-09, C-14, C-17, C-20 |
| Dokumen terkait | D-01 Bagian 9 dan 9.1 · D-04 Bagian 7.4 (`peristiwa`) · D-14 Bagian 3 dan 5.1 · D-12 Bagian 7 · spec fitur 012 |
| Status | **Usulan** — menunggu Gerbang 1 |

## Mengapa fitur ini diusulkan sekarang

Fitur 012 membangun taksonomi peristiwa, bentuk `Peristiwa`, dan gerbang
`rekam()` yang menegakkan C-04 — tetapi **tidak ada yang memanggilnya**, dan
peristiwa tidak tersimpan di mana pun. Fitur 030 menyediakan persetujuan yang
dibaca gerbang itu; fitur 013 menyediakan beranda dan butir. Hari ini, sesudah
pilot berjalan sebulan, rasio penemuan dan retensi D1/D7/D30 (D-01 Bagian 9.1)
akan bernilai **nol yang terbaca seperti temuan**.

Baris 034 pada D-12 menyebutnya **prasyarat pilot**. Ia tidak tertahan putusan
tim mana pun — kecuali satu pertanyaan bentuk di bawah (P-1).

## Temuan yang diajukan bersama usulan ini

**TK-73 · D-14 tidak memiliki rute penerima peristiwa.** Tujuh kode taksonomi
D-01 Bagian 9 hanya teramati di peramban: `discovery_read_complete` (lama baca,
kedalaman gulir), `citation_opened` (tautan sumber diketuk), dan sebagian
`session_start`/`session_end` (perangkat, kualitas jaringan). D-14 Bagian 3
tidak memuat rute yang dapat menerimanya, dan AG-02 melarang menambahkannya
tanpa putusan. Peristiwa lain **teramati di peladen** pada rute yang sudah ada.

## Di luar cakupan

- Panel analitik dan ekspor bagi peneliti (S-18, `/api/v1/analitik/*`) — baris 035
- Peristiwa milik fitur yang belum dibangun: *knowledge check* dan komitmen
  (031), `discovery_saved` dan `citation_opened` lewat `/sumber/{id}` (032),
  `answer_rated` (rute penilaian belum ada), `search_performed`,
  `export_performed` — **setiap baris itu merekam peristiwanya sendiri** saat
  dibangun, lewat jalur yang dibuat fitur ini
- `injection_suspected` — terpicu pada jalur ingesti dan penjawaban; menyentuh
  `src/rag/` dan `src/ingest/`, dan diajukan tersendiri
- Penarikan data peristiwa (NFR-09) — baris 033
- Metrik turunan D-01 Bagian 9.1 — dihitung saat analisis, bukan disimpan
- `src/rag/` dan `src/llm/` — tidak disentuh

## Kebutuhan (EARS) yang tidak bergantung pada pertanyaan

| ID | Kebutuhan |
|---|---|
| R-01 | Setiap peristiwa **HARUS** dibentuk lewat `rekam()` fitur 012; tidak ada jalur lain yang menyimpan peristiwa (C-04) |
| R-02 | **KETIKA** sebuah peristiwa hendak direkam, keadaan persetujuan **HARUS** dibaca dari penyimpan pengguna **pada saat itu**, bukan dari salinan sesi — pencabutan menghentikan perekaman pada permintaan berikutnya (C-04, FR-J05) |
| R-03 | **JIKA** persetujuan tidak berkeadaan `diberikan`, **MAKA** tidak ada apa pun yang tersimpan, dan tanggapan rute **TIDAK BOLEH** berbeda dari tanggapan bagi pengguna yang menyetujui (FR-A05) |
| R-04 | Peristiwa tersimpan **HARUS** membawa pseudonim akun, tidak pernah `pengguna.id`; peran basis data telemetri **TIDAK BOLEH** menjangkau basis data pseudonim (C-05) |
| R-05 | Tabel peristiwa **HARUS** tambah-saja, ditegakkan peladen: tidak satu peran aplikasi pun memegang `UPDATE`, `DELETE`, maupun `TRUNCATE` (R-07 fitur 012) |
| R-06 | `properti` **TIDAK BOLEH** memuat teks yang ditulis pengguna — pertanyaan, alasan "belum relevan" — melainkan ukurannya saja; penjagaan KM-03 fitur 012 tetap berlaku |
| R-07 | **JIKA** penyimpanan peristiwa gagal, **MAKA** tanggapan rute **TIDAK BOLEH** berubah; kegagalannya dicatat ke log operasional tanpa muatan peristiwa |
| R-08 | Setiap peristiwa **HARUS** membawa versi aplikasi dan versi model (FR-J02, C-09) |
| R-09 | Pemilihan beranda dan jawaban **TIDAK BOLEH** membaca peristiwa (C-14) — telemetri direkam, bukan dipakai menyesuaikan |
| R-10 | Waktu peristiwa disimpan UTC (KM-01) |

## Pertanyaan terbuka

Tiap pertanyaan disertai anjuran; anjuran bukan putusan.

**P-1 · Kanal peristiwa (TK-73).**

| Pilihan | Arti |
|---|---|
| A | **Peristiwa yang teramati peladen saja**, direkam di dalam rute yang sudah ada. Tanpa perubahan D-14 Bagian 3. Tujuh kode yang hanya teramati di peramban tidak terekam sampai ada putusan rute |
| B | Rute baru `POST /api/v1/peristiwa` bagi peristiwa dari peramban — perubahan D-14 Bagian 3 yang **menuntut putusan manusia** (AG-02); rute yang menerima masukan bebas dari klien juga menambah permukaan serangan |
| C | A sekarang; B diajukan sebagai baris tersendiri sesudah putusan D-14 |

**Anjuran: C.** Peristiwa yang dibutuhkan rasio penemuan dan retensi teramati
di peladen, sehingga pilot tidak tertahan. Rasio penuntasan (lama baca)
menunggu putusan rute, dan itu dinyatakan pada laporan analisis, bukan
diisi tebakan.

**P-2 · Himpunan peristiwa bila P-1 = A atau C.**

| Kode | Terpicu pada | Properti |
|---|---|---|
| `session_start` | masuk berhasil | — |
| `return_visit` | masuk berhasil, bila `session_start` sebelumnya lebih dari 24 jam lalu | jeda dalam jam |
| `session_end` | keluar tegas | durasi dalam menit |
| `question_asked` | `POST /tanya` diterima | panjang pertanyaan dalam karakter |
| `answer_served` | `POST /tanya` dijawab | status dasar, jumlah sitasi, waktu tanggap |
| `answer_rejected_validator` | jalur berhenti dengan alasan validator | kode alasan berhenti |
| `discovery_served` | butir baru tercatat pada beranda | id butir, jenis sumber, kategori |
| `discovery_opened` | `GET /butir/{id}` berhasil | id butir, menit sejak ditayangkan |
| `discovery_dismissed` | "belum relevan" tercatat | id butir, panjang alasan |

**Anjuran: sembilan kode ini.** Properti D-01 yang tidak tersedia tidak diisi
tebakan: kategori pertanyaan menunggu klasifikasi (fitur 017); skor relevansi
belum ada (BT-24); tingkat keyakinan tidak dihitung sebagai angka (FR-F06).

**P-3 · Tepi `api → telemetri` pada AGENTS.md.** Peristiwa teramati di rute,
dan rute tinggal di `src/api/`. **Anjuran:** tepi satu jurusan, dengan alasan
umum: `api` satu-satunya titik masuk, sehingga setiap peristiwa yang teramati
pada sebuah rute wajib direkam dari sana. Arah sebaliknya terlarang: telemetri
yang memanggil `api` membuat perekaman bergantung pada bentuk HTTP.

**P-4 · `versi_model` bagi peristiwa tanpa model.** Fitur 012 mewajibkannya
terisi. **Anjuran:** tetapan bernama `tanpa_model` bagi peristiwa yang tidak
melibatkan model (beranda, sesi); peristiwa jawaban membawa versi model dari
tanggapan. `versi_aplikasi` diserahkan titik jalan saat aplikasi disusun —
`pengembangan` pada `make jalan`.

**P-5 · `session_end` hanya pada keluar tegas.** Sesi yang berakhir karena
diam 30 menit tidak teramati sebagai peristiwa. **Anjuran:** diterima dan
dinyatakan; durasi sesi pada analisis dihitung dari peristiwa terakhir sesi
itu, bukan dari `session_end` saja.

**P-6 · Peran basis data.** **Anjuran:** skema `telemetri` dan
`peran_telemetri` tersendiri — `INSERT` dan `SELECT`, tanpa ubah dan hapus,
tanpa jangkauan skema lain maupun basis data pseudonim. `SELECT` dibutuhkan
`return_visit`; peran ekspor bagi peneliti milik baris 035.

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | C-04; `rekam()` fitur 012 |
| R-02 | C-04; FR-J05; uraian `gerbang.py` |
| R-03 | FR-A05 |
| R-04 | C-05; FR-J02; KA-03 |
| R-05 | R-07 fitur 012 |
| R-06 | KM-03; D-14 Bagian 5.1 |
| R-07 | FR-A05; AP-04 D-04 |
| R-08 | FR-J02; C-09 |
| R-09 | C-14 |
| R-10 | KM-01 |

## Kriteria penerimaan

- [ ] Baris D-12 034 dan TK-73 dibahas; P-1 s.d. P-6 diputus pada Gerbang 1
- [ ] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [ ] C-04 diuji ujung ke ujung lewat HTTP: tanpa persetujuan nol baris; sesudah mencabut, nol baris baru pada permintaan berikutnya
- [ ] R-05 diuji terhadap peladen PostgreSQL dengan sebab penolakannya
- [ ] Uji mutasi disusun pada `plan.md` dan dilaporkan apa adanya
- [ ] `make check` lulus enam gerbang
