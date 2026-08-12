# Spec: 009-penyusunan-jawaban

| | |
|---|---|
| Kebutuhan | **FR-F05, FR-F10, FR-F13, FR-F14** · FR-F02, FR-F04, FR-F11 |
| Dokumen terkait | **D-14 Bagian 4.1** · D-07 Bagian 4.1, 4.5, 5 · D-05 |
| Pasal konstitusi | **C-20**, C-07, C-13, C-17, C-18 |
| Urutan pembangunan | 009 pada `docs/D12.md` Bagian 7, sesudah 008 |
| Ketergantungan | **Nol paket Python baru** |
| Status | Menunggu Gerbang 1 |

## Tujuan

Sesudah fitur ini, hasil pengambilan (007) dan hasil validasi (008) dapat
disusun menjadi **tanggapan berbentuk `docs/D14.md` Bagian 4.1** — dan bentuk
itu satu-satunya yang dapat dihasilkan.

D-14 menyebut rute `/api/v1/tanya` *"kontrak terpenting dalam sistem; ia
menjadi tempat seluruh kendali D-07 dan D-13 bertemu"*. Fitur ini membangun
**tanggapannya**, bukan rutenya — dan alasannya di bawah.

## FastAPI belum disetujui, dan itu menentukan pemisahan fitur ini

`AGENTS.md` menyebut `src/api/` sebagai "FastAPI, satu-satunya titik masuk".
`ketergantungan-disetujui.toml` **tidak memuat `fastapi`**, tidak memuat
`uvicorn`, dan tidak memuat `httpx` yang diperlukan untuk mengujinya.

C-12 berbunyi: *"Tidak ada ketergantungan baru tanpa persetujuan penanggung
jawab teknis."* Menambahkannya sendiri adalah pelanggaran, dan menambahkannya
"karena `AGENTS.md` sudah menyebut FastAPI" adalah pembacaan yang keliru:
`AGENTS.md` menyatakan **pilihan arsitektur**, sedangkan
`ketergantungan-disetujui.toml` menyatakan **persetujuan**. Keduanya berbeda,
dan berkas persetujuan menyebutkan sendiri bahwa perubahannya "keputusan tim,
bukan keputusan agen".

Karena itu:

| | Bagian | Menunggu? |
|---|---|---|
| **1** | Bentuk tanggapan D-14 Bagian 4.1, pemeriksaan cakupan domain, penanda keberlakuan, penafian, penyusun | **Tidak** |
| **2** | Rute `/api/v1/tanya`, kendali peran, sesi | **Ya — C-12** |

Bagian 2 diusulkan menjadi **fitur 021**.

**Pemisahan ini berbeda dari enam sebelumnya**, dan bedanya patut dicatat:
yang ditunggu bukan orang, bukan korpus, bukan model — melainkan **satu
keputusan yang dapat diambil dalam satu rapat**. Ia yang paling murah untuk
dibuka dari seluruh yang menunggu.

## Yang tetap tidak dapat dilakukan sesudah fitur ini

Sistem **tetap tidak dapat menjawab pertanyaan apa pun**, dan itu bukan akibat
fitur ini melainkan warisan dua fitur sebelumnya:

| Penghalang | Dibuka oleh | Yang ditunggu |
|---|---|---|
| Sumber kandidat vektor (R-05 fitur 007) | 019 | **Model sematan** — C-12 |
| VS-03, VS-05, VS-07 (R-10 fitur 008) | 020 | **Model sematan** dan model NER |
| Rute `/api/v1/tanya` | 021 | **FastAPI** — C-12 |

Ketiganya bermuara pada **dua keputusan C-12**: model sematan, dan FastAPI.
Bukan pada kode.

Yang berubah sesudah fitur ini: seluruh jalur dari pertanyaan sampai bentuk
tanggapan **ada dan diuji**, sehingga ketiga keputusan itu masing-masing
membuka bagian yang sudah siap menerimanya.

## Di luar cakupan

- **Rute, kendali peran, dan sesi.** Fitur 021; C-12.
- **Jawaban terkurasi 20 pertanyaan tersering** (FR-F12, tahap 2). Isinya
  disusun dan divalidasi kurator sebelum pilot — **pekerjaan orang**, dan D-06
  belum menetapkan siapa. Diusulkan masuk fitur 021 bersama rutenya.
- **Pemahaman pertanyaan K1–K8 dan ekstraksi entitas** (tahap 3). Menuntut
  model NER fitur 017 dan klasifikasi; ia menyempitkan ruang pencarian, bukan
  syarat menjawab.
- **Penanda keyakinan pada tanggapan** dalam bentuk terhitung (FR-F06).
  `status_dasar` diisi dari `PenilaianKecukupan` fitur 007, yang menuntut
  ambang BT-29. Bentuknya ada; nilainya menunggu.
- **Riwayat percakapan** (FR-F09). Menuntut penyimpanan percakapan dan rute
  `/api/v1/percakapan`.
- **Penilaian jawaban dan antrean kurasi** (FR-F07, FR-F08). Fitur 010.
- **Penyusunan ulang pada kegagalan VS-05** (D-07 Bagian 6.2). Menuntut VS-05,
  fitur 020.
- **Layar Tanya** (D-05). `web/` belum dimulai; ia pekerjaan tersendiri.

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | Tanggapan **HARUS** memuat persis bidang `docs/D14.md` Bagian 4.1 — tidak kurang, dan **TIDAK BOLEH** lebih (C-20, AG-03) |
| R-02 | **JIKA** pertanyaan berada di luar domain manajemen sekolah dasar, **MAKA** sistem **HARUS** menolaknya sebelum pengambilan dan **TIDAK BOLEH** mengirimnya ke LLM (FR-F13, D-07 Bagian 4.1) |
| R-03 | Penolakan domain **HARUS** menyebutkan cakupan sistem, bukan berupa pesan galat (D-07 Bagian 4.1) |
| R-04 | **JIKA** `status_dasar` bernilai `tidak_ditemukan` atau `di_luar_domain`, **MAKA** `ringkasan_tindakan` dan `klaim` **HARUS** kosong (D-14 Bagian 4.1) |
| R-05 | Setiap tanggapan **HARUS** memuat penafian bahwa keputusan akhir pada kepala sekolah (FR-F10) |
| R-06 | Setiap tanggapan **HARUS** memuat versi model, indeks, dan kode (KT-06, D-14 Bagian 4.1) |
| R-07 | **JIKA** sebuah sitasi berasal dari regulasi berstatus `diubah`, **MAKA** `catatan_keberlakuan` **HARUS** terisi beserta rujukan pengubahnya (FR-F14, KL-07) |
| R-08 | **JIKA** sebuah sitasi berstatus `dicabut`, **MAKA** tanggapan **TIDAK BOLEH** dapat dibentuk (VS-06, C-07) |
| R-09 | Sumber dari `indeks_metadata` **HARUS** muncul pada `bacaan_lanjutan` saja, **TIDAK PERNAH** pada `sitasi` (FR-D06, C-02, D-14 Bagian 6) |
| R-10 | Tanggapan **HARUS** hanya dapat dibentuk dari `JawabanTervalidasi`; keluaran yang belum tervalidasi **TIDAK BOLEH** dapat menjadi tanggapan (C-01 bentuk, R-09 fitur 008) |
| R-11 | Kalimat pada tanggapan **HARUS** ≤ 20 kata (NFR-19, C-13) |
| R-12 | Penyusunan **TIDAK BOLEH** menulis apa pun (C-17) |
| R-13 | Rute yang dideklarasikan **TIDAK BOLEH** berada di luar `docs/D14.md` Bagian 3 (C-20, AG-02) |

### Tiga kebutuhan yang paling mudah dianggap berlebihan

**R-01 adalah C-20 itu sendiri.** Bidang yang ditambahkan pada tanggapan
`/tanya` dilarang tanpa persetujuan manusia, dan D-14 menyatakan alasannya:
*"bentuk itu adalah tempat C-02, C-07, dan C-19 diwujudkan."* Bidang tambahan
yang tampak tidak berbahaya — `skor_keyakinan`, `waktu_proses` — memindahkan
penilaian dari sistem ke klien, dan klien tidak terikat konstitusi.

**R-04 tampak kerapian.** Ia bukan: D-14 menyatakan keadaan `tidak_ditemukan`
dan `di_luar_domain` memakai **bentuk yang sama** dengan ringkasan dan klaim
kosong, dan *"bentuk yang seragam inilah yang membuat layar D-05 dapat
menampilkannya sebagai jawaban sah, bukan pesan galat."* Penolakan yang tampak
seperti galat adalah penolakan yang membuat pengguna menyimpulkan sistemnya
rusak — dan D-02 titik kritis T3 menyatakan sebaliknya: sistem yang mengaku
tidak tahu justru memperkuat kepercayaan.

**R-13 tampak tidak perlu** sebab fitur ini tidak membangun rute sama sekali.
Justru itu waktunya: pemeriksanya berdiri **sebelum** rute pertama ada, sehingga
rute pertama lahir sudah terjaga. Pola KB-010, KB-028, dan KB-038 — pengendali
dibangun sebelum yang dikendalikannya ada.

## Keadaan yang wajib ditangani

| Keadaan | Perilaku yang dituntut |
|---|---|
| Pertanyaan di luar domain | `di_luar_domain`; tidak dikirim ke LLM |
| Tidak ada dasar rujukan | `tidak_ditemukan`; ringkasan dan klaim kosong |
| Validasi tidak lulus | Tanggapan tidak dapat dibentuk dari keluarannya |
| Seluruh sitasi berstatus `berlaku` | `catatan_keberlakuan` kosong |
| Ada sitasi berstatus `diubah` | `catatan_keberlakuan` terisi beserta pengubahnya |
| Ada sitasi berstatus `dicabut` | Tanggapan **tidak dapat dibentuk** |
| Segmen dari `indeks_metadata` | Muncul pada `bacaan_lanjutan` saja |
| Segmen tanpa penanda bagian | Tidak mungkin — ditolak sejak fitur 007 |
| Kalimat melampaui 20 kata | Ditolak saat tanggapan dibentuk |

## Kriteria penerimaan

- [ ] R-01 s.d. R-13 masing-masing punya uji yang gagal sebelum implementasi
- [ ] Uji bahwa bidang tanggapan **dibaca dari `docs/D14.md`**, bukan disalin ke uji
- [ ] Uji bahwa bidang tambahan ditolak (R-01, AG-03)
- [ ] Uji bahwa `di_luar_domain` tidak pernah mencapai pemanggilan LLM
- [ ] Uji bahwa segmen `indeks_metadata` tidak pernah muncul pada `sitasi`
- [ ] Nol ketergantungan Python baru
- [ ] Cakupan uji tidak turun
- [ ] **`make compliance` menyusut satu** — C-20 berpindah; menjadi 12 lulus, 8 belum

## Pertanyaan bagi Gerbang 1

**Satu.** C-20 memuat **dua** kewajiban: bentuk tanggapan, dan daftar rute.
Fitur ini membangun yang pertama dan tidak membangun rute sama sekali. Apakah
C-20 boleh berpindah menjadi terperiksa mesin?

| | Pilihan | Akibat |
|---|---|---|
| **A** | Ya — pemeriksanya menegakkan keduanya; separuh rute berbunyi "tidak ada rute di luar D-14", dan itu **benar** atas nol rute | Pemeriksanya sudah berdiri ketika fitur 021 menambah rute pertama. Bentuk yang sama dengan C-15, yang lulus atas basis data tanpa satu tabel pun |
| **B** | Tidak — tunggu fitur 021 | Tagihan tidak menyusut, dan rute pertama lahir tanpa penjagaan |

**Saran saya: A**, dan bedanya dengan kekeliruan C-01 pada fitur 008 perlu
dinyatakan tegas. C-01 menuntut sesuatu **ada dan benar** — sitasi
terverifikasi — sehingga menandainya lulus tanpa VS-03 adalah melaporkan
pemeriksaan yang tidak berjalan. C-20 separuh rute menuntut sesuatu **tidak
ada** — rute di luar D-14 — dan "nol rute, karena itu nol rute terlarang"
adalah pernyataan yang benar, bukan pernyataan yang hampa. Separuh bentuk
tanggapan menjadi nyata pada fitur ini.

**Dua.** Bagaimana pemeriksaan cakupan domain (FR-F13) bekerja tanpa
klasifikasi K1–K8 fitur 017?

| | Pilihan | Akibat |
|---|---|---|
| **A** | Daftar putih topik manajerial; di luarnya ditolak | Konservatif ke arah menolak. Pertanyaan manajerial sah yang tidak terduga ikut ditolak |
| **B** | Daftar hitam ranah terlarang — medis, hukum pidana, keuangan pribadi | Sesuai bunyi FR-F13 apa adanya. Meloloskan yang belum pernah terlihat |
| **C** | Belum dapat diperiksa; ditangguhkan seperti VS-03 | Setiap pertanyaan mencapai pengambilan, termasuk yang FR-F13 tolak |

**Saran saya: B**, dan alasannya berlawanan dengan pilihan daftar putih pada
fitur 006 — pembedaannya penting. Pada lisensi, kekeliruan ke arah longgar
**menggugurkan publikasi**; karena itu daftar putih. Di sini, kekeliruan ke
arah ketat **menolak kepala sekolah yang bertanya dengan wajar**, dan D-02
menyatakan jawaban pertama menentukan retensi (titik kritis T1). Arah
konservatifnya berlawanan karena kerugiannya berlawanan.

C ditolak: FR-F13 menyebut dua alasan — menghemat biaya, dan **mencegah sistem
memberi nasihat pada bidang yang tidak punya dasar rujukan sama sekali di
korpusnya**. Yang kedua bukan soal biaya, dan menangguhkannya berarti
menangguhkan kendali.

Batasnya wajib tertulis: daftar hitam meloloskan yang belum pernah terlihat,
dan penutupnya bukan pemeriksaan ini melainkan **kecukupan bukti** — pertanyaan
di luar domain tidak memiliki segmen pendukung, sehingga berakhir pada
`tidak_ditemukan`. FR-F13 memangkas biaya dan mempercepat; ia bukan lapisan
tunggal.

**Tiga.** `catatan_keberlakuan` menuntut **rujukan pengubah** (FR-F14). Dari
mana ia datang?

| | Pilihan | Akibat |
|---|---|---|
| **A** | Bidang pada `SegmenRujukan`, diisi pemanggil | Sejalan dengan `segmen_resmi` fitur 007: yang lapisan ini tidak dapat simpulkan, diserahkan pemanggil |
| **B** | Disimpulkan dari metadata dokumen di `src/ingest/` | Menciptakan tepi `rag → ingest` yang tidak tertulis — dan pemeriksa arah fitur 009 akan menolaknya |

**Saran saya: A.** B ditolak oleh pemeriksa yang baru saja dibangun, dan itu
tanda pemeriksanya bekerja.
