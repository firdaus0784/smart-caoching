# Spec: 010-pipeline-kurasi

| | |
|---|---|
| Kebutuhan | **FR-I01, FR-I02, FR-I03, FR-I05, FR-I06, FR-I07, FR-I08** |
| Dokumen terkait | **D-06 Bagian 5, 6, 7, 8** · D-03 Bagian 5 · D-01 Modul I |
| Pasal konstitusi | **C-06, C-07** · C-13, C-16, C-09 |
| Urutan pembangunan | 010 pada `docs/D12.md` Bagian 7, sesudah 009 |
| Ketergantungan | **Nol paket Python baru** |
| Status | Menunggu Gerbang 1 |

## Tujuan

Sesudah fitur ini, sebuah butir pengetahuan hasil ingesti **tidak dapat tayang
tanpa melewati kurator** — bukan karena dilarang, melainkan karena tidak ada
bentuk yang memungkinkannya.

C-06 berbunyi satu kalimat: *"Butir pengetahuan tidak tayang tanpa persetujuan
kurator."* Fitur ini membuatnya menjadi tipe, bukan aturan.

## Dua pasal berpindah, dan yang kedua sudah separuh berdiri

**C-06** seluruhnya baru. **C-07** — *"Sistem tidak menjawab berdasarkan
regulasi berstatus dicabut"* — sudah dijaga dua tempat sejak fitur 008 dan 009:
VS-06 menolak segmen `dicabut` menjadi dasar klaim, dan `Sitasi` menolak
dibentuk dari sumber `dicabut`.

Fitur ini menambahkan **tempat ketiga dan paling hulu**: lapis L3 pada
penyaringan otomatis, dan penarikan otomatis butir yang regulasi sumbernya
dicabut (D-06 Bagian 7.5).

Pemeriksa C-07 karena itu memeriksa **ketiga tempat sekaligus**. Pasal yang
dijaga tiga lapis dan hanya diperiksa pada satu di antaranya adalah pasal yang
lolos ketika lapis itu dipindahkan.

## Kapasitas kurator adalah kendala perancangan, bukan catatan kaki

D-06 Bagian 7.2 menyatakannya lebih tajam daripada yang dapat saya tulis ulang:

> Total beban kurasi dirancang **di bawah 4 jam per minggu**. Angka ini bukan
> target efisiensi melainkan batas kelayakan: kurator adalah dosen yang juga
> mengajar, dan pipeline yang menuntut lebih dari ini akan berhenti dijalankan
> pada minggu keempat — bukan karena kelalaian, melainkan karena rancangannya
> tidak masuk akal sejak awal.

Karena itu FR-I08 — pemantauan rasio antrean dan pengereman ingesti — **bukan
fitur tambahan melainkan syarat agar C-06 bertahan**. Gerbang kurator yang
antreannya membanjir akan dilewati orang, dan yang dilewati bersamanya adalah
C-06.

## L4 belum dapat dijalankan, dan itu menahan pipeline

Penyaringan otomatis D-06 Bagian 6 berlapis empat. Tiga dapat dibangun; **L4
tidak**.

| Lapis | Kriteria | Sekarang? | Menunggu |
|---|---|---|---|
| L1 · Lisensi | Terbaca dan diizinkan | **Ya** | — |
| L2 · Kebaruan | Bukan duplikat, bukan versi lama | **Ya** | — |
| L3 · Keberlakuan | Regulasi berstatus berlaku | **Ya** | — |
| L4 · Relevansi | Skor terhadap K1–K8 melampaui ambang | Tidak | Klasifikasi (fitur 017) **dan** ambang BT-24 |

**L4 tidak dipisahkan menjadi fitur tersendiri.** Ia mengikuti bentuk VS-03
pada fitur 008: melaporkan `BELUM_DAPAT_DIPERIKSA` beserta apa yang
ditunggunya, dan kandidat yang mencapainya **tidak masuk antrean dan tidak
dibuang** — ia menunggu.

Ketiga keadaan itu berbeda tajam, dan D-06 menyebutkan akibat keduanya yang
salah: kandidat yang lolos tanpa L4 **membanjiri antrean kurasi**; kandidat
yang dibuang tanpa L4 membuat **feed kekurangan isi** dan memicu titik kritis
T5 pada D-02. Menunggu adalah satu-satunya jawaban yang tidak memilih di
antara keduanya tanpa dasar.

Akibatnya wajib dinyatakan: **pipeline ini belum dapat mengisi antrean kurasi
sampai fitur 017 dan BT-24 selesai.** Itu keadaan yang jujur, bukan cacat.

## Di luar cakupan

- **Antrean jawaban QA yang ditandai keliru** (FR-I04). Menuntut FR-F07 —
  penilaian jawaban — yang menuntut rute `/api/v1/pesan/{id}/penilaian`,
  fitur 021.
- **Layar kurator** S-15 dan S-16 (D-05). `web/` belum dimulai.
- **Menetapkan ambang relevansi L4 dan ambang kemiripan parafrase.** BT-24,
  bulan 3; C-16.
- **Pengambilan dari keempat kanal** (D-06 Bagian 3). Ia ingesti, bukan
  kurasi; fitur 002 dan 015 membangun gerbangnya.
- **Skor relevansi terhadap prioritas pengguna.** Menuntut profil pengguna,
  Modul A — yang tidak memiliki satu pun fitur pada `docs/D12.md` Bagian 7.

## Kebutuhan (EARS)

| ID | Kebutuhan |
|---|---|
| R-01 | Butir pengetahuan **HARUS** memuat kedua belas bidang D-06 Bagian 5; bidang wajib **TIDAK BOLEH** berbawaan kosong |
| R-02 | Butir **HARUS** hanya dapat tayang setelah putusan kurator; bentuk butir tayang **TIDAK BOLEH** dapat dibentuk di luar gerbang kurasi (C-06, FR-I03) |
| R-03 | **JIKA** lisensi butir tidak terbaca atau tidak diizinkan, **MAKA** kandidat **HARUS** dibuang dan **TIDAK BOLEH** disimpan (L1, PP-01) |
| R-04 | **JIKA** kandidat duplikat atau versi lama, **MAKA** ia **HARUS** dibuang; versi lebih baru **HARUS** menggantikan yang lama (L2) |
| R-05 | **JIKA** regulasi sumber berstatus `dicabut`, **MAKA** butir **TIDAK BOLEH** masuk antrean tayang (L3, C-07, KL-07) |
| R-06 | **JIKA** lapis relevansi belum dapat dijalankan, **MAKA** kandidat **TIDAK BOLEH** masuk antrean maupun dibuang — ia menunggu (C-16) |
| R-07 | Setiap butir menerima tepat satu dari **empat** putusan D-06 Bagian 7.3 — setujui, sunting-lalu-setujui, tolak, tunda |
| R-08 | **JIKA** putusan berupa tolak, **MAKA** alasannya **HARUS** salah satu kode baku TL-01 s.d. TL-11 — **TIDAK BOLEH** untai bebas (FR-I02, FR-I05) |
| R-09 | Setiap tindakan kurasi **HARUS** tercatat: siapa, kapan, apa, alasan (FR-I05) |
| R-10 | **JIKA** regulasi sumber sebuah butir tayang berubah menjadi `dicabut`, **MAKA** butir **HARUS** ditarik (FR-I06, D-06 Bagian 7.5) |
| R-11 | Panjang antrean **HARUS** dipantau terhadap pagu kurasi harian; **JIKA** melampaui ambang tiga hari berturut-turut, **MAKA** ingesti **HARUS** diperlambat (FR-I08) |
| R-12 | Angka pagu dan ambang antrean **HARUS** mengikuti D-06 Bagian 8.3, dan **TIDAK BOLEH** tertulis di lebih dari satu tempat (C-16) |
| R-13 | Jejak kurasi **TIDAK BOLEH** memuat data pribadi kurator selain penanda perannya (C-05, KM-03) |

### Tiga kebutuhan yang paling mudah dianggap berlebihan

**R-02 adalah C-06 itu sendiri**, dan bentuknya mengikuti `JawabanTervalidasi`
fitur 008: `ButirTayang` hanya dapat dibentuk gerbang kurasi. Fitur yang
menayangkan butir kemudian **tidak memiliki cara** melewatinya.

**R-08 tampak birokratis.** D-06 menyatakan sebaliknya: *"Alasan terstandar
diperlukan agar penolakan menjadi data perbaikan, bukan sekadar pembuangan."*
Untai bebas menghasilkan sebelas cara menulis "tidak relevan", dan PM-05 —
tingkat penolakan per kanal — menjadi angka yang tidak dapat diuraikan sebabnya.

**R-06 adalah pengulangan keenam** pola "tiga keadaan, bukan dua", dan di sini
ia menahan hal yang berbeda dari lima sebelumnya: bukan laporan yang keliru
melainkan **pilihan yang tidak boleh diambil tanpa dasar**. Meloloskan
membanjiri kurator; membuang mengosongkan feed. D-06 menyebut kedua akibatnya,
dan tidak menyebut mana yang lebih ringan.

## Keadaan yang wajib ditangani

| Keadaan | Perilaku yang dituntut |
|---|---|
| Lisensi tidak terbaca | Dibuang, tidak disimpan |
| Duplikat butir yang sudah ada | Dibuang |
| Versi lebih baru dari yang ada | Menggantikan yang lama |
| Regulasi sumber `dicabut` | Tidak masuk antrean tayang |
| Regulasi sumber `diubah` | Masuk antrean; penanda ikut |
| L4 belum dapat dijalankan | Menunggu — tidak masuk antrean, tidak dibuang |
| Butir disetujui | Masuk kolam butir; dapat tayang |
| Butir ditolak tanpa kode baku | Ditolak saat putusan dibentuk |
| Butir ditunda | Kembali ke antrean pada waktu yang ditetapkan |
| Regulasi sumber butir tayang dicabut | Butir ditarik |
| Antrean melampaui ambang 3 hari | Ingesti diperlambat |
| Antrean melampaui ambang 2 hari | Belum diperlambat — tiga, bukan dua |

## Kriteria penerimaan

- [ ] R-01 s.d. R-13 masing-masing punya uji yang gagal sebelum implementasi
- [ ] Uji bahwa `ButirTayang` tidak dapat dibentuk di luar gerbang kurasi
- [ ] Uji bahwa L4 yang belum dapat dijalankan **menahan**, bukan meloloskan dan bukan membuang
- [ ] Uji bahwa pengereman menuntut **tiga** hari berturut-turut, bukan dua
- [ ] Uji bahwa angka D-06 Bagian 8.3 dibaca dari dokumennya
- [ ] `KategoriMasalah` fitur 003 **dipakai ulang**, tidak ditulis ulang
- [ ] Nol ketergantungan Python baru
- [ ] Cakupan uji tidak turun
- [ ] **`make compliance` menyusut dua** — C-06 dan C-07; menjadi 14 lulus, 6 belum

## Pertanyaan bagi Gerbang 1

**Satu.** C-07 dijaga tiga tempat sesudah fitur ini — VS-06 (008), `Sitasi`
(009), dan L3 (010). Pemeriksanya memeriksa berapa?

| | Pilihan | Akibat |
|---|---|---|
| **A** | Ketiganya | Pasal yang dijaga tiga lapis diperiksa tiga lapis. Memindahkan salah satunya menyalakan pemeriksa |
| **B** | L3 saja, sebab itu yang fitur ini bangun | Dua lapis lain dapat dihapus tanpa satu pemeriksa pun menyala |

**Saran saya: A.** B adalah bentuk yang membuat pemeriksa terbaca lengkap
sementara ia menjaga sepertiga — dan sepertiga yang paling hulu, sehingga
penghapusan dua lapis hilir tidak terlihat sampai ada jawaban yang tayang.

**Dua.** `KategoriMasalah` K1–K8 sudah ada pada `src/nlp/anotasi/skema.py`
(fitur 003). Dipakai ulang, atau butir memiliki enumnya sendiri?

| | Pilihan | Akibat |
|---|---|---|
| **A** | Dipakai ulang lewat tepi `ingest → nlp` yang sudah tertulis | Satu definisi. D-06 Bagian 5 sendiri merujuk "D-03 Bagian 5" |
| **B** | Enum tersendiri pada `src/ingest/` | Dua definisi bagi satu daftar D-03 — **persis kekeliruan `IndeksTujuan`** pada fitur 006 |

**Saran saya: A**, dan B ditolak dengan alasan yang sudah dibayar sekali:
`IndeksTujuan` ditulis dua kali dan lolos dua fitur. Kekeliruan yang sama
tidak perlu diulang untuk dipelajari.

**Tiga.** Siapa "kurator" pada jejak audit (R-09, R-13)?

| | Pilihan | Akibat |
|---|---|---|
| **A** | Penanda peran dan id pseudonim | Sejalan C-05 dan KM-03; jejak tetap dapat ditelusuri lewat pemetaan yang terpisah |
| **B** | Nama kurator | FR-I05 menuntut "siapa", dan nama menjawabnya paling langsung |

**Saran saya: A.** FR-I05 menuntut ketertelusuran, bukan nama — dan C-05
menempatkan kunci pemetaan pseudonim pada basis data terpisah yang tidak
terjangkau layanan aplikasi. Menuliskan nama pada jejak membuat kunci itu
tidak berarti apa pun untuk jejak kurasi.

Batasnya wajib dinyatakan: kurator berjumlah dua orang (D-06 Bagian 7.1),
sehingga pseudonim **tidak** menyembunyikan identitas dari tim. Ia menjaga
jejaknya tidak menjadi data pribadi yang ikut terekspor pada analitik — bukan
menjaga kurator dari timnya sendiri.
