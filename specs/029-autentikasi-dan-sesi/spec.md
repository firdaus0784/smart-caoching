# Spec: 029-autentikasi-dan-sesi

| | |
|---|---|
| Kebutuhan | FR-A01; NFR-05, NFR-06, NFR-08; KA-01, KA-03; C-05, C-13, C-17, C-20; TK-70 |
| Dokumen terkait | D-14 Bagian 3.1 dan 4 · D-04 Bagian 7.1 dan 10 · D-05 S-01 · D-12 Bagian 7 |
| Status | **Usulan — menunggu persetujuan baris D-12 dan Gerbang 1.** Tujuh pertanyaan terbuka |

## Mengapa fitur ini diusulkan

FR-A01: *"Pengguna masuk melalui akun yang dibuatkan tim peneliti (tanpa
registrasi mandiri publik, sesuai batas TKT 3)."*

Fitur 022 menyebut FR-A01 dalam cakupannya, tetapi yang dibangunnya model
profil, prioritas, dan persetujuan. **Alur masuknya tidak ada**: tidak ada
akun, tidak ada sesi, dan rute `POST /api/v1/auth/masuk` serta
`/auth/keluar` tercantum pada D-14 Bagian 3.1 tetapi tidak terpasang.
Akibatnya:

- Penentu identitas yang dipakai satu-satunya titik jalan adalah
  `IdentitasPengembangan` — setiap pemanggil diperlakukan sebagai kepala
  sekolah yang sama, tanpa pemeriksaan apa pun.
- Fitur 028 membangun **tempat** pemilik riwayat; tidak ada yang mengisinya.
- Aplikasi **tidak layak dihadapkan ke jaringan publik**, dan pilot tidak
  dapat dimulai.

Fitur ini tidak memiliki baris pada D-12. Ia diusulkan sebagai **029**,
disisipkan sebelum 013, sebab tiap layar fitur 013 berada di belakang layar
masuk. Penyisipan baris adalah keputusan tim; baris itu tidak ditulis sebelum
disetujui.

## Temuan saat menyusun usulan ini: TK-70

**Layanan aplikasi tidak memiliki jalur sah untuk mengetahui pseudonim
pengguna yang sedang masuk.** KA-03 menetapkan kunci pseudonim berada pada
basis data terpisah, *"tanpa jalur jaringan dari layanan aplikasi"*. Tetapi
telemetri (fitur 012) menuntut `pseudonim` dari pemanggilnya, dan riwayat
(fitur 028) menuntut pemilik berpseudonim — dan tidak ada satu jalur pun yang
menyediakannya saat aplikasi berjalan. Fitur 022 malah memakai `id_pengguna`
pada profil dan persetujuan. Tiga fitur, dua pengenal, dan tidak ada yang
menjembatani keduanya tanpa melanggar KA-03. Ini pertanyaan P-1.

## Di luar cakupan

- Registrasi mandiri — dilarang FR-A01
- Lupa sandi dan pemulihan lewat surel — lihat P-7
- Masuk lewat pihak ketiga (SSO, akun Google) — R-18 fitur 027 melarang
  pemuatan pihak ketiga, dan pilot tidak membutuhkannya
- Layar S-02 s.d. S-04 (persetujuan, *onboarding*, profil) — fitur 013
- `src/rag/` dan `src/llm/` — tidak disentuh

## Kebutuhan (EARS) yang tidak bergantung pada pertanyaan

| ID | Kebutuhan |
|---|---|
| R-01 | Pengguna **HARUS** masuk dengan akun yang dibuat tim peneliti; sistem **TIDAK BOLEH** menyediakan jalur registrasi mandiri (FR-A01) |
| R-02 | Bentuk permintaan dan tanggapan `POST /api/v1/auth/masuk` dan `/auth/keluar` **HARUS** ditulis ke D-14 Bagian 4 **sebelum** kodenya (C-20) |
| R-03 | Sandi **TIDAK BOLEH** tersimpan maupun tercatat dalam bentuk asli. Yang disimpan turunan fungsi derivasi kunci bergaram per akun, dan pembandingannya **HARUS** berwaktu tetap |
| R-04 | **KETIKA** masuk ditolak, tanggapan **TIDAK BOLEH** membedakan akun yang tidak ada dari sandi yang salah — pesan, status, dan waktu tanggapnya setara |
| R-05 | Peran dan pemilik **HARUS** ditentukan peladen dari sesi yang sah. **KETIKA** sesi tidak ada atau tidak sah, rute selain rute publik **HARUS** menolak dengan galat D-14 Bagian 4.2 `TIDAK_TERAUTENTIKASI`, status 401 |
| R-06 | **KETIKA** pengguna keluar, sesinya **HARUS** tidak berlaku seketika di peladen — bukan hanya dihapus dari peramban |
| R-07 | Layanan aplikasi **TIDAK BOLEH** menjangkau basis data pseudonim, dalam bentuk apa pun yang P-1 putuskan (C-05, KA-03) |
| R-08 | Layar S-01 Masuk **HARUS** memakai mikrokopi yang lolos C-13; sandi **TIDAK BOLEH** disimpan peramban oleh kode aplikasi |
| R-09 | Log operasional **TIDAK BOLEH** memuat sandi maupun pengenal sesi |
| R-10 | `IdentitasPengembangan` **HARUS** tetap hanya terjangkau `perkakas/jalankan_lokal.py`, dan penentu identitas sungguhan **HARUS** menolak bekerja tanpa sesi |

## Pertanyaan terbuka

Tiap pertanyaan disertai anjuran; anjuran bukan putusan.

**P-1 · Dari mana pseudonim pengguna yang sedang masuk (TK-70).**

| Pilihan | Arti |
|---|---|
| A | **Akun berpseudonim.** Basis data perilaku hanya mengenal nama pengguna buatan tim yang **tidak mengidentifikasi** (misalnya `ks-017`), turunan sandinya, perannya, dan pseudonimnya. Pemetaan ke orang sungguhan tinggal pada basis data pseudonim dan dikelola peneliti di luar layanan. Layanan aplikasi tidak pernah tahu siapa orangnya — hanya akunnya. `id_pengguna` pada profil dan persetujuan (fitur 022) diselaraskan menjadi pseudonim yang sama |
| B | Layanan identitas tersendiri yang menjangkau peta pseudonim dan menerbitkan sesi — bertentangan dengan KA-03 ("tanpa jalur jaringan dari layanan aplikasi") kecuali KA-03 diubah |
| C | Aplikasi menyimpan identitas langsung dan pseudonim berdampingan — **ditolak**; itu C-05 runtuh |

**Anjuran: A.** Ia satu-satunya pilihan yang memenuhi KA-03 apa adanya, dan
ia membuat pertanyaan "siapa orang ini" tidak dapat dijawab dari data
perilaku sama sekali. Konsekuensinya dinyatakan: nama pengguna dibagikan tim
kepada peserta di luar sistem, dan tim yang memegang daftar pasangannya.

**P-2 · Mekanisme sesi.**

| Pilihan | Arti |
|---|---|
| A | Kuki `HttpOnly`, `Secure`, `SameSite=Strict` berisi pengenal acak; sesi tersimpan di peladen dalam bentuk turunan, sehingga dapat dicabut seketika (R-06). Pustaka baku saja |
| B | Token bertanda tangan (JWT) — paket baru (C-12), dan tidak dapat dicabut sebelum kedaluwarsa tanpa daftar cabutan, yang mengembalikannya ke A |

**Anjuran: A.** Kuki `HttpOnly` tidak terbaca kode peramban, sehingga R-17
fitur 027 — tanpa token yang disimpan aplikasi — tetap utuh.

**P-3 · Fungsi derivasi sandi.**

| Pilihan | Arti |
|---|---|
| A | `scrypt` dari pustaka baku Python (`hashlib`) — tanpa paket baru. Parameternya ditetapkan pada `plan.md` terhadap sumber yang **dibaca**, bukan diingat (SI-01) |
| B | Argon2id lewat paket baru — menuntut persetujuan C-12 |

**Anjuran: A**, kecuali penanggung jawab teknis lebih memilih Argon2id dan
menyetujui paketnya.

**P-4 · Angka keamanan: pembatasan percobaan dan masa sesi.** Berapa kali
masuk gagal sebelum akun ditahan sementara, berapa lama, dan berapa lama sesi
berlaku. Angka-angka ini ambang, dan ambang yang dipilih pelaksana tanpa dasar
adalah bentuk yang C-16 tolak pada RAG.
**Anjuran:** `plan.md` mengusulkan angka beserta sumbernya; Gerbang 2
memutusnya. Bila tidak ada sumber yang layak, angkanya dicatat sebagai
penetapan tim tanpa dasar literatur (SI-01 pilihan kedua), sama dengan
anggaran muat fitur 027.

**P-5 · Siapa membuat akun.**

| Pilihan | Arti |
|---|---|
| A | Perkakas baris perintah pada `perkakas/` bagi tim peneliti, dengan peran basis data tersendiri yang hanya dapat membuat akun. Sandi awal acak ditampilkan sekali dan tidak pernah disimpan dalam bentuk asli |
| B | Rute admin — D-14 Bagian 3 tidak memuatnya, sehingga menuntut perubahan daftar rute (AG-02) dan panel internal yang belum ada |

**Anjuran: A.** Pilot berisi lima belas kepala sekolah (BT-05); perkakas
tim cukup, dan tidak menambah permukaan serangan pada peladen.

**P-6 · Layar S-01 dibangun di sini.** Tanpanya fitur ini hanya dapat dicoba
lewat `curl`, dan layar Tanya tidak dapat dipakai siapa pun.
**Anjuran:** ya — S-01 saja, dengan keadaan galat dan luring; layar lain
tetap fitur 013.

**P-7 · Lupa sandi.** Pemulihan lewat surel menuntut pengiriman keluar —
C-17 melarangnya bagi jalur penjawaban, dan sistem belum memiliki pengiriman
apa pun.
**Anjuran:** di luar cakupan. Tim mengatur ulang sandi lewat perkakas P-5;
layar S-01 menyebut cara menghubungi tim.

## Ketertelusuran

| Kebutuhan | Sumber |
|---|---|
| R-01 | FR-A01 |
| R-02 | D-14 Bagian 3.1; C-20 |
| R-03, R-04 | NFR-05; D-04 KA-01 |
| R-05 | NFR-06; KA-01; D-14 Bagian 4.2 |
| R-06 | KA-01 |
| R-07 | C-05; KA-03; NFR-08; TK-70 |
| R-08 | C-13; D-05 S-01; R-17 fitur 027 |
| R-09 | AGENTS.md Batas; KM-03 |
| R-10 | `perkakas/jalankan_lokal.py`; R-17 fitur 028 |

## Kriteria penerimaan

- [ ] Baris D-12 disetujui dan pertanyaan P-1 s.d. P-7 diputus pada Gerbang 1
- [ ] Setiap kebutuhan punya uji yang gagal sebelum implementasi
- [ ] Penolakan hak diuji terhadap peladen PostgreSQL dengan sebabnya
- [ ] Uji mutasi disusun pada `plan.md` dan dilaporkan apa adanya
- [ ] `make check` lulus enam gerbang
