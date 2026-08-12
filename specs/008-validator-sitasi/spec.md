# Spec: 008-validator-sitasi

| | |
|---|---|
| Kebutuhan | **FR-F03, FR-F15, FR-F16** · FR-F04 · VS-01, VS-02, VS-04, VS-06, VS-08, VS-09 |
| Dokumen terkait | **D-07 Bagian 6** · D-13 Bagian 6 dan KD-13 · D-14 Bagian 4.1 |
| Pasal konstitusi | **C-19**, C-01, C-17, C-18, C-16 |
| Urutan pembangunan | 008 pada `docs/D12.md` Bagian 7, sesudah 007 |
| Ketergantungan | **Nol paket Python baru** |
| Status | Menunggu Gerbang 1 |

## Tujuan

Sesudah fitur ini, sebuah keluaran LLM dapat diperiksa terhadap segmen yang
benar-benar diambil, dan keluaran yang tidak lolos **tidak dapat ditayangkan**.
D-04 ADR-04 menyebut validator sebagai *"komponen terpenting dalam sistem"*.

Yang belum ada sebelumnya bukan pemeriksaannya melainkan **bentuk yang membuat
jawaban tak-tervalidasi mustahil beredar** — dan, sama pentingnya, bentuk yang
membuat pemeriksaan yang **belum dapat dijalankan** tidak terbaca sebagai
pemeriksaan yang lulus.

## Bahaya yang membentuk seluruh spesifikasi ini

D-07 PR-03a menyatakannya lebih tajam daripada yang dapat saya tulis ulang:

> Validator sitasi membuktikan jawaban berasal dari suatu segmen. Ia **tidak**
> membuktikan segmen itu benar, sah, atau bukan hasil penyisipan instruksi.

Karena itu bahaya utama fitur ini bukan validator yang menolak terlalu banyak,
melainkan **validator yang melaporkan lulus atas pemeriksaan yang tidak
dijalankannya**. Tiga dari sembilan pemeriksaan D-07 Bagian 6.1 tidak dapat
dibangun hari ini. Validator yang mengembalikan "lulus" dalam keadaan itu
adalah laporan bersih yang tidak memeriksa apa pun — TA-01, pada tempat yang
paling berbahaya dalam sistem ini.

**R-10 menutupnya**: setiap pemeriksaan berstatus salah satu dari **tiga**
nilai — lulus, gagal, atau belum-dapat-diperiksa — dan jawaban yang memuat satu
saja pemeriksaan belum-dapat-diperiksa **tidak boleh ditayangkan**. Bentuknya
sengaja sama dengan `make compliance`: perkakas yang menegakkan pelajaran itu
pada proyek, kini menegakkannya pada sistem.

Akibatnya langsung dan disengaja: **sistem ini tetap tidak dapat menjawab
pertanyaan apa pun sesudah fitur 008.** Itu keadaan yang jujur, bukan cacat.

## Apa yang dapat dan tidak dapat dibangun

| VS | Pemeriksaan | Sekarang? | Menunggu |
|---|---|---|---|
| VS-01 | Setiap klaim punya ≥ 1 `id_segmen` | **Ya** | — |
| VS-02 | Setiap `id_segmen` ada di antara segmen yang diambil | **Ya** | — |
| VS-03 | Isi klaim didukung segmen, diukur kemiripan semantik | Tidak | Model sematan (019) **dan** ambang BT-29 |
| VS-04 | Tidak ada segmen `indeks_metadata` menjadi dasar klaim | **Ya** | — |
| VS-05 | Tidak ada kalimat menyalin segmen melebihi batas | Tidak | Ambang BT-29 |
| VS-06 | Tidak ada segmen dari regulasi dicabut dipakai | **Ya** | — |
| VS-07 | Tidak ada nama perorangan dalam keluaran | Tidak | Model NER (017) |
| VS-08 | Tidak ada klaim bersandar tunggal pada T3 atau T4 | **Ya** | — |
| VS-09 | Keluaran memenuhi kontrak D-14; tanpa instruksi, persona, tautan luar | **Ya** | — |

Enam dari sembilan. Ketiga sisanya menjadi **fitur 020**, dan ketergantungannya
**bukan satu melainkan dua**: VS-03 dan VS-05 menunggu fitur 019; VS-07
menunggu fitur 017 — dan fitur 017 menunggu korpus teranotasi, pekerjaan dua
mahasiswa bulan 2–4.

`src/nlp/anonimisasi/pola.py` menyatakannya sudah, pada fitur 015:

> Keduanya yang pertama menuntut pengenalan entitas bernama, dan model NER …

Pendeteksi yang ada mengenali enam jenis penanda berupa angka — NIK, NIP,
NISN, NUPTK, telepon, rekening. **Nama perorangan bukan salah satunya.**

## C-01 tidak berpindah pada fitur ini, dan itu koreksi terhadap daftar pasal

`perkakas/kepatuhan/daftar_pasal.py` mencatat C-01 dengan
`fitur_pengunci="008 validator sitasi"`. **Itu keliru, dan ketahuan baru
sekarang.**

C-01 berbunyi: *"Sistem tidak menayangkan klaim manajerial tanpa sitasi yang
**terverifikasi** terhadap segmen yang diambil."* Verifikasi yang dimaksud
D-07 Bagian 6 mencakup VS-03 — dukungan isi, bukan hanya keberadaan id. Tanpa
VS-03, yang ditegakkan hanyalah bahwa setiap klaim menyebut id segmen yang
sungguh ada; klaim yang mengutip segmen yang sama sekali tidak membahasnya
tetap lolos.

Menandai C-01 lulus dalam keadaan itu akan membuat MK-07 — cakupan sitasi 100%
— berarti "100% klaim menyebut id yang ada". Itu persis angka yang PR-03a
peringatkan, dan ia akan masuk naskah.

**C-01 karena itu tetap tertahan, dengan `fitur_pengunci` yang dikoreksi
menjadi menyebut apa yang sesungguhnya ditunggunya**: fitur 020, VS-03.
Yang berpindah pada fitur ini adalah **C-19** (VS-08), yang tidak menunggu apa
pun.

## Cakupan

| | Bagian | Menunggu? |
|---|---|---|
| **1** | VS-01, VS-02, VS-04, VS-06, VS-08, VS-09; tiga keadaan; tabel tindakan 6.2 | **Tidak** |
| **2** | VS-03, VS-05 (sematan + BT-29), VS-07 (NER) | **Ya** |

Bagian 2 diusulkan menjadi **fitur 020**.

## Di luar cakupan

- **Menyusun jawaban dan rute `/api/v1/tanya`.** Fitur 009. Validator ini
  memeriksa keluaran; yang meminta keluaran itu bukan urusannya.
- **Menetapkan arti `klaim[].peringkat_kepercayaan`** ketika satu klaim
  ditopang segmen berperingkat berbeda. **D-14 Bagian 4.1 menyatakannya
  keputusan BT-64, bukan keputusan pelaksana**, dan AG-01 serta AG-03 menutup
  jalan bagi agen untuk menetapkannya. Pemeriksaan VS-08 **tidak** bergantung
  padanya: sebuah klaim melanggar bila **seluruh** penopangnya T3 atau T4, dan
  pernyataan itu benar pada ketiga pilihan BT-64.
- **Menetapkan ambang VS-03 dan VS-05.** BT-29; C-16.
- **Peristiwa telemetri `answer_rejected_validator` dan `injection_suspected`.**
  Fitur 012; C-04 mensyaratkan persetujuan aktif yang belum ada mekanismenya.
- **Penyusunan ulang pada kegagalan VS-05.** D-07 Bagian 6.2 menetapkan satu
  kali penyusunan ulang; ia menuntut pemanggilan LLM, dan itu fitur 009.
- **Pemeriksaan keberlakuan sebagai tahap 6.** Validator memeriksa bahwa segmen
  dicabut tidak **dipakai** (VS-06); yang memelihara statusnya fitur 010.

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | **JIKA** sebuah klaim tidak memiliki `id_segmen`, **MAKA** validator **HARUS** menolaknya (VS-01) |
| R-02 | **JIKA** sebuah `id_segmen` tidak ada di antara segmen yang diambil, **MAKA** klaim itu **HARUS** ditolak (VS-02) |
| R-03 | **JIKA** sebuah klaim ditopang segmen dari `indeks_metadata`, **MAKA** seluruh jawaban **HARUS** dibuang tanpa perbaikan (VS-04, C-02) |
| R-04 | **JIKA** sebuah klaim ditopang segmen dari regulasi berstatus `dicabut`, **MAKA** seluruh jawaban **HARUS** dibuang tanpa perbaikan (VS-06, C-07) |
| R-05 | **JIKA** seluruh segmen penopang sebuah klaim berperingkat T3 atau T4, **MAKA** klaim itu **HARUS** diturunkan menjadi bacaan lanjutan (VS-08, C-19, FR-F15) |
| R-06 | **JIKA** ringkasan tindakan menjadi kosong setelah klaim dibuang atau diturunkan, **MAKA** seluruh jawaban **HARUS** dibatalkan (D-07 Bagian 6.2) |
| R-07 | Keluaran **HARUS** memenuhi kontrak D-14 Bagian 4.1; keluaran yang memuat instruksi, perubahan persona, atau tautan di luar metadata sumber **HARUS** dibuang tanpa perbaikan (VS-09, FR-F16) |
| R-08 | Validator **HARUS** melaporkan **kode pemeriksaan yang gagal**, bukan hanya kegagalannya (D-07 Bagian 6.2, RT-02) |
| R-09 | Jawaban yang belum melewati validator **TIDAK BOLEH** dapat dibentuk sebagai jawaban siap tayang (C-01 bentuk, ADR-13) |
| R-10 | Setiap pemeriksaan **HARUS** berstatus salah satu dari tiga — lulus, gagal, **belum dapat diperiksa** — dan jawaban yang memuat satu saja pemeriksaan belum-dapat-diperiksa **TIDAK BOLEH** dinyatakan tervalidasi |
| R-11 | Validator **TIDAK BOLEH** menulis apa pun maupun memanggil model (C-17, C-08) |
| R-12 | Ambang VS-03 dan VS-05 **TIDAK BOLEH** ada dalam bentuk apa pun pada fitur ini (C-16) |

### Tiga kebutuhan yang paling mudah dianggap berlebihan

**R-10 adalah inti fitur ini.** Validator yang mengembalikan `True` atas
sembilan pemeriksaan yang tiga di antaranya tidak berjalan tidak dapat
dibedakan dari validator yang benar. Ini pengulangan keenam pola "tiga keadaan,
bukan dua" — sesudah `HasilSistem` (015), `HasilKesepakatan` (003), `bendera`
(016), `Nilai` (004), dan `HasilHitung` (005).

**R-09 memindahkan C-01 dari aturan menjadi bentuk.** Mengikuti ADR-13, yang
membatasi pembentukan `Instruksi` pada satu modul: `JawabanTervalidasi` hanya
dapat dibentuk validator. Fitur 009 kemudian **tidak memiliki cara** menayangkan
jawaban yang melewatinya — bukan dilarang, melainkan tidak bisa.

**R-03 dan R-04 membuang seluruh jawaban, bukan klaimnya saja**, dan itu
mengikuti D-07 Bagian 6.2 apa adanya. Bedanya dengan VS-01 s.d. VS-03 disengaja:
kegagalan VS-04 dan VS-06 bukan kekeliruan penyusunan melainkan **insiden
kepatuhan** — segmen yang tidak boleh dijangkau ternyata terjangkau. Membuang
klaimnya saja akan menyembunyikan bahwa gerbangnya bocor.

## Keadaan yang wajib ditangani

| Keadaan | Perilaku yang dituntut |
|---|---|
| Klaim tanpa `id_segmen` | Klaim dibuang (VS-01) |
| `id_segmen` mengada-ada | Klaim dibuang (VS-02) |
| Sebagian klaim gagal, ringkasan masih terisi | Klaim bermasalah dibuang; jawaban lanjut |
| Seluruh klaim gagal | Jawaban dibuang; balasan tidak-ditemukan |
| Klaim ditopang segmen metadata | **Seluruh** jawaban dibuang; insiden kepatuhan |
| Klaim ditopang segmen regulasi dicabut | **Seluruh** jawaban dibuang; insiden kepatuhan |
| Klaim ditopang T1 dan T3 sekaligus | **Sah** — D-13 Bagian 6 mewajibkannya |
| Klaim ditopang T3 dan T4 saja | Diturunkan menjadi bacaan lanjutan |
| Ringkasan kosong setelah penurunan | Jawaban dibatalkan |
| Keluaran memuat tautan di luar metadata sumber | Dibuang tanpa perbaikan |
| Keluaran memuat kalimat berbentuk instruksi | Dibuang tanpa perbaikan |
| Jawaban tanpa klaim sama sekali | Sah bila `status_dasar` `tidak_ditemukan` |
| VS-03, VS-05, VS-07 tidak dapat dijalankan | Dilaporkan belum-dapat-diperiksa; jawaban **tidak** tervalidasi |

## Kriteria penerimaan

- [ ] R-01 s.d. R-12 masing-masing punya uji yang gagal sebelum implementasi
- [ ] Uji bahwa klaim ditopang T1 **dan** T3 diterima — bukan hanya bahwa T3 saja ditolak
- [ ] Uji bahwa `JawabanTervalidasi` tidak dapat dibentuk di luar validator
- [ ] Uji bahwa validator melaporkan **belum-dapat-diperiksa** bagi VS-03, VS-05, VS-07
- [ ] Uji bahwa jawaban dengan satu pemeriksaan belum-dapat-diperiksa **tidak** dinyatakan tervalidasi
- [ ] Uji bahwa kode pemeriksaan yang gagal ikut dilaporkan (R-08)
- [ ] Nol ketergantungan Python baru
- [ ] Cakupan uji tidak turun
- [ ] **`make compliance` menyusut satu** — C-19 berpindah; menjadi 11 lulus, 9 belum
- [ ] `fitur_pengunci` C-01 dikoreksi menyebut fitur 020

## Pertanyaan bagi Gerbang 1

**Satu.** `IndeksTujuan` **didefinisikan dua kali** — `src/llm/tipe.py` (fitur
001) dan `src/penyimpanan/indeks.py` (fitur 006). Keduanya mencerminkan
`segmen_teks.indeks_tujuan` pada D-14 Bagian 5 dengan nilai yang sama.

**Itu kekeliruan saya pada fitur 006**: saya menulis enum baru tanpa memeriksa
apakah ia sudah ada. Yang membuatnya lebih dari kerapian — **enum itu tempat
C-02 terbaca**, dan dua definisi berarti perubahan D-14 kelak dapat memperbarui
satu dan melewatkan yang lain, tanpa satu uji pun gagal.

`Peringkat` mengalami hal sejajar meski tidak kembar: ia tinggal di
`src/llm/tipe.py` sedangkan D-13 Bagian 6 dan D-14 Bagian 5 menyebutnya sifat
**segmen**. `src/ingest/` sudah mengimpornya dari sana — tepi `ingest → llm`
yang juga tidak tertulis pada `AGENTS.md`.

| | Pilihan | Akibat |
|---|---|---|
| **A** | Modul kamus baru `src/kamus/` bagi enum D-14 Bagian 5; ia tidak mengimpor apa pun, semua lapisan boleh mengimpornya | Satu definisi. Menambah satu direktori dan satu baris `AGENTS.md`. Cocok dengan sebutan D-14 sendiri: "kamus data" |
| **B** | `src/penyimpanan/indeks.py` mengimpor dari `src/llm/tipe.py` | Membalik lapisan — `AGENTS.md` menyebut penyimpanan "lapisan di bawah keempatnya" |
| **C** | `src/llm/tipe.py` mengimpor dari `src/penyimpanan/` | Membuat pembungkus model bergantung pada penyimpanan; ia sengaja ringan |
| **D** | Biarkan kembar, tambahkan uji bahwa nilainya sama | Menjaga dari penyimpangan nilai, **tidak** dari penyimpangan makna. Murah, dan jujur tentang batasnya |

**Saran saya: A**, dan tepi `ingest → llm` sekaligus dituliskan. B dan C
keduanya menempatkan enam kata milik D-14 pada modul yang punya urusan lain.
D adalah tambalan yang saya akan pilih hanya bila Anda menilai penambahan
direktori terlalu besar untuk fitur ini — dan bila begitu, kekembarannya wajib
tercatat sebagai utang, bukan diselesaikan.

**Dua.** `StatusKeberlakuan` (`berlaku | diubah | dicabut`) dituntut VS-06 dan
belum ada dalam kode. D-14 Bagian 4.1 menamainya pada `sitasi[]`. Ditambahkan
di fitur ini atau menunggu fitur 010 yang memelihara statusnya?

**Saran saya: ditambahkan sekarang**, dengan alasan yang sama seperti gerbang
karantina mendahului pendeteksi data pribadi (KB-010) dan pembagian data
mendahului modelnya (KB-028): **pengendali dibangun sebelum yang
dikendalikannya ada.** Validator yang menerima segmen tanpa status keberlakuan
tidak dapat menegakkan VS-06 sama sekali, dan menambahkannya kelak berarti
menyisipkan pemeriksaan ke jalur yang sudah berjalan.

**Tiga.** Apa yang terjadi ketika sebuah pemeriksaan berstatus
belum-dapat-diperiksa (R-10)?

| | Pilihan | Akibat |
|---|---|---|
| **A** | Jawaban tidak dinyatakan tervalidasi; tidak dapat ditayangkan | Sejalan D-07 Bagian 1 — "jawaban yang salah lebih merugikan daripada jawaban yang tidak ada". Sistem tetap tidak dapat menjawab sampai fitur 020 |
| **B** | Jawaban tervalidasi sebagian, ditandai pada tanggapan | Menambah bidang pada tanggapan `/tanya` — **AG-03 melarangnya tanpa persetujuan manusia** |
| **C** | Pemeriksaan yang tidak dapat dijalankan dianggap lulus | Persis TA-01 |

**Saran saya: A.** C ditolak tegas. B bukan sekadar kurang baik — ia menuntut
perubahan kontrak yang AG-03 tutup, dan menempuhnya berarti agen menetapkan
bentuk yang D-14 miliki.

Konsekuensi A wajib dinyatakan terbuka kepada tim: **sistem tidak dapat
menjawab pertanyaan apa pun sampai fitur 019 dan 020 selesai.** Itu bukan
kemunduran melainkan pembacaan jujur atas apa yang sudah dan belum ada.
