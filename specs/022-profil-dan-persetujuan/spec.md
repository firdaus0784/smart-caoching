# Spec: 022-profil-dan-persetujuan

| | |
|---|---|
| Kebutuhan | FR-A01 s.d. FR-A06 |
| Pasal | **C-05**; prasyarat **C-04** |
| Dokumen | D-04 Bagian 7.1, D-14 Bagian 5.1, D-11 Bagian 3.6 |
| Ketergantungan baru | **Nol** |
| Status | **Lolos Gerbang 1–3** (KB-046) |

## 1 · Mengapa fitur ini ada, dan mengapa ia hampir tidak ada

FR-A01 s.d. FR-A06 **tidak dimiliki baris urutan pembangunan mana pun** sampai
13 Agustus 2026. Ketiadaannya ditemukan perhitungan cakupan, bukan mata
(KB-044). Isinya bukan pelengkap: akun, profil awal, prioritas manajerial,
*onboarding*, dan **persetujuan penelitian**.

Dua fitur bersandar padanya dan keduanya tidak dapat mendahuluinya:

| Yang bersandar | Pada apa | Akibat bila 022 tidak ada |
|---|---|---|
| **C-04** pada fitur 012 | FR-A05 | Telemetri tidak punya persetujuan untuk diperiksa |
| **FR-G01** pada fitur 011 | FR-A03 | Feed menyaring terhadap prioritas yang tidak ada |

Pipeline kurasi fitur 010 **sudah** menyaring terhadap prioritas manajerial
yang belum ada cara mengisinya. Itu bukan kekeliruan fitur 010.

## 2 · Cakupan

**Di dalam:** model profil sekolah, prioritas manajerial, catatan persetujuan
beserta pencabutannya, dan pemisahan peta pseudonim.

**Di luar:** seluruh layar (`web/`), rute (fitur 021), dan perekaman telemetri
itu sendiri (fitur 012). Fitur ini membangun **apa yang diperiksa**, bukan yang
memeriksanya.

`onboarding` empat layar FR-A04 karena itu tidak dibangun di sini. Yang dibangun
adalah naskah persetujuan berversi yang layar itu tayangkan.

## 3 · Kebutuhan

| Kode | Pernyataan |
|---|---|
| R-01 | Akun dibuat tim peneliti; sistem **TIDAK BOLEH** menyediakan jalur registrasi mandiri (FR-A01, batas TKT 3) |
| R-02 | Profil sekolah **HARUS** memuat tepat enam bidang D-04 Bagian 7.1 — jabatan, masa kerja, jumlah rombel, jumlah PTK, akreditasi, wilayah. Bidang ketujuh **TIDAK BOLEH** ditambahkan tanpa persetujuan manusia (FR-A02) |
| R-03 | Prioritas manajerial **HARUS** berjumlah 3 sampai 5, bernilai `KategoriMasalah` K1–K8, dan membawa urutannya (FR-A03) |
| R-04 | Satu kategori **TIDAK BOLEH** dipilih dua kali oleh pengguna yang sama |
| R-05 | Persetujuan penelitian **HARUS** berkeadaan salah satu dari empat: belum diminta, diberikan, ditolak, dicabut (FR-A05) |
| R-06 | **JIKA** persetujuan dicabut, **MAKA** perekaman perilaku **HARUS** berhenti seketika (C-04, FR-J05, `persetujuan.dicabut_pada`) |
| R-07 | **JIKA** pengguna menolak atau mencabut persetujuan, **MAKA** akses fitur inti **TIDAK BOLEH** berkurang (FR-A05, WMA Declaration of Helsinki, D-11 Bagian 3.6) |
| R-08 | Setiap catatan persetujuan **HARUS** menyebut **versi naskah** yang disetujui; persetujuan tanpa naskah yang dapat ditunjuk bukan persetujuan (FR-A05) |
| R-09 | Pemetaan pseudonim ke identitas **TIDAK BOLEH** terjangkau kredensial layanan aplikasi (C-05, KA-03, D-04 Bagian 7.1) |
| R-10 | Profil **HARUS** dapat diperbarui kapan saja, dan pembaruan **HARUS** mencatat waktunya (FR-A06) |
| R-11 | Bidang teks bebas **TIDAK BOLEH** menyimpan data pribadi (KM-03) |
| R-12 | Seluruh waktu disimpan UTC (KM-01) |

## 4 · Bentuk yang menentukan

### 4.1 Empat keadaan persetujuan, dan dua di antaranya sering disamakan

D-14 Bagian 5.1 sudah menetapkan bentuknya bagi persetujuan pemilik dokumen —
`belum_diminta`, `diberikan`, `ditolak`, `dicabut` — beserta alasannya:
*"`dicabut` menghentikan pemakaian seketika; persetujuan yang tidak dapat
ditarik bukan persetujuan."* Kosakata yang sama dipakai di sini, sebab ia
menamai hal yang sama pada subjek yang berbeda.

**Yang paling mudah disamakan adalah `belum_diminta` dengan `ditolak`.**
Keduanya berarti "tidak ada persetujuan" dan karena itu sama-sama menghentikan
perekaman. Tetapi keduanya berbeda bagi peneliti: yang pertama pekerjaan yang
belum dilakukan, yang kedua keputusan partisipan yang wajib dihormati.
Menyamakannya membuat laporan partisipasi tidak dapat membedakan orang yang
menolak dari orang yang belum ditanya.

**Dan `ditolak` berbeda dari `dicabut`.** Helsinki menyebut keduanya terpisah —
hak menolak, dan hak mencabut kapan saja. Sistem yang hanya mengenal satu
akan memaksa pencabutan dicatat sebagai penolakan, dan data yang sudah terekam
sebelum pencabutan kehilangan penjelasannya.

### 4.2 Keadaan dihitung, bukan disimpan

D-04 Bagian 7.1 menyimpan `disetujui` dan `dicabut_pada` sebagai dua bidang.
Dua bidang yang wajib dibaca bersama dapat berselisih: `disetujui = salah`
dengan `dicabut_pada` terisi tidak berarti apa pun, dan tidak ada yang
menghalanginya tersimpan.

Bentuk yang dipakai: bidangnya tetap seperti D-04 — **model data miliknya,
bukan milik fitur ini** — sedangkan keadaannya berupa **sifat terhitung**, dan
gabungan yang mustahil ditolak saat pembentukan. Bentuk yang sama dengan
`HasilSaring.boleh_masuk_antrean` (010) dan `HasilValidasi.tervalidasi` (008).

### 4.3 Peta pseudonim bukan nilai ketiga pada `Area`

C-05 menuntut kunci pemetaan berada pada basis data terpisah dan **tidak
terjangkau layanan aplikasi**. Menambahkannya sebagai `Area.PETA_PSEUDONIM`
akan terasa rapi dan **dilarang AG-04**: `Area` mewujudkan
`dokumen_sumber.area_simpan` milik D-14, yang bernilai `karantina` atau
`korpus` saja.

Alasannya bukan sekadar formal. Area adalah tempat **dokumen** berada; peta
pseudonim bukan dokumen, dan menaruhnya pada sumbu yang sama akan membuat
kredensial yang berhak membaca korpus tampak sebanding dengan kredensial yang
berhak membaca identitas. Preseden yang sudah berjalan: `IndeksTujuan` sengaja
bukan nilai ketiga pada `Area`, dengan alasan yang sejajar (fitur 006).

## 5 · Pertanyaan Gerbang 1

| # | Pertanyaan | Usul |
|---|---|---|
| 1 | Apakah C-05 berpindah menjadi terperiksa mesin pada fitur ini? | **Ya.** Ia pernyataan struktural tentang di mana kunci berada — bentuk yang sama dengan C-03 yang berpindah pada fitur 002 sebelum layanan RAG ada. Tagihan menyusut **14 → 15** |
| 2 | Apakah C-04 ikut berpindah? | **Tidak.** C-04 menuntut telemetri **tidak merekam** tanpa persetujuan, dan telemetri belum ada. Fitur ini menyediakan yang diperiksanya, bukan pemeriksanya. Pembedaan yang sama dengan C-01 pada fitur 008 (KB-037) |
| 3 | Enum prioritas dipakai ulang atau ditulis ulang? | **Dipakai ulang** — `KategoriMasalah` pada `src/nlp/anotasi/skema.py`, pemakaian ketiga sesudah fitur 003 dan 010 |

## 6 · Yang tidak dikerjakan di sini

Layar S-xx, rute, dan perekaman telemetri. FR-A04 empat layar *onboarding*
menunggu `web/`.

**Angka yang tidak berdasar literatur.** FR-A02 "maksimal 6 isian" dan FR-A04
"maksimal 4 layar" tidak memiliki rujukan terverifikasi; penelusuran 13 Agustus
2026 hanya menemukan tulisan pemasaran. Keduanya diusulkan dinyatakan
**penetapan tim tanpa dasar literatur** (SI-01 pilihan kedua, D-11 Bagian 5).
Fitur ini menegakkan angkanya apa adanya dan **tidak** mengaku ia berdasar.
