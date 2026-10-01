# Plan: 029-autentikasi-dan-sesi

| | |
|---|---|
| Spec | **Gerbang 1 lolos** — 1 Oktober 2026 (KB-151); P-1 s.d. P-7 sesuai anjuran |
| Status | **Gerbang 2 lolos** — 1 Oktober 2026 (KB-153); K-1 s.d. K-7 dan angka P-4 sesuai anjuran |
| Kebutuhan | R-01 s.d. R-10 `spec.md`; FR-A01; NFR-05, NFR-06, NFR-08; KA-01, KA-03; C-05, C-13, C-17, C-20; TK-70 |

## 1. Letak dan batas

```
perkakas/basis_data/
  01-peran-dan-basis-data.sql   + peran_autentikasi, peran_pengelola_akun
  07-akun.sql                   baru — skema akun: pengguna, sesi
perkakas/akun.py                baru — perkakas tim: buat, atur ulang sandi, nonaktifkan (P-5)
perkakas/jalankan_lokal.py      + --autentikasi {sesi,pengembangan}
src/penyimpanan/akun.py         baru — PenyimpanAkun, AkunMemori, AkunPostgres
src/api/sandi.py                baru — turunan scrypt, pembandingan berwaktu tetap (P-3)
src/api/autentikasi.py          baru — masuk, keluar, penahanan, PenentuSesi
src/api/identitas.py            PenentuIdentitas menjadi async dan boleh mengembalikan None
src/api/aplikasi.py             dua rute D-14 3.1; 401 TIDAK_TERAUTENTIKASI; syarat JSON
src/api/peran.py                POLA_MASUK, POLA_KELUAR — diambil dari PETA_RUTE
web/src/                        Aplikasi.tsx, masuk/LayarMasuk.tsx; klien, kontrak, mikrokopi
docs/                           D-14 4.4 dan 5.1, D-04 7.1, D-05 S-01, D-00
```

**Tepi antarlapisan tidak bertambah.** Logika autentikasi tinggal di
`src/api/` — tempat AGENTS.md meletakkan kendali peran — dan penyimpanannya di
`src/penyimpanan/`. `api → penyimpanan` sudah tertulis. Tepi `api → pengguna`
**tidak** ada pada AGENTS.md, dan fitur ini tidak membutuhkannya: profil,
prioritas, dan persetujuan (fitur 022) tidak disentuh.

**`src/rag/` dan `src/llm/` tidak disentuh satu baris pun.** Rute masuk menulis
sesi, tetapi ia bukan jalur penjawaban; C-17 melarang akses tulis **dari jalur
penjawaban** (TK-44), dan `jalur.jawab` tetap tidak memegang kredensial tulis
apa pun.

**Tanpa telemetri.** D-01 mengenal peristiwa `session_start`, tetapi C-04
menuntut persetujuan aktif, dan persetujuan diambil layar S-02 fitur 013.
Masuk tidak merekam apa pun.

## 2. Blast radius, diukur di muka

| Yang berubah | Pemanggil yang terdampak |
|---|---|
| `PenentuIdentitas.identitas` menjadi `async` dan boleh mengembalikan `None` | `src/api/aplikasi.py`; `IdentitasPengembangan` pada `perkakas/jalankan_lokal.py`; tiruan `_Kosong` pada `perkakas/pemeriksa/rute_terdaftar.py`; `IdentitasTetap` dan pemakaiannya pada `tests/api/test_aplikasi.py`, `test_riwayat_http.py`, `test_galat_http.py` (sembilan tempat); `tests/api/test_identitas.py` |
| Rute masuk dan keluar terpasang | Pemeriksa `rute_terdaftar` — kedua rute sudah ada pada `PETA_RUTE`, sehingga hanya pola jalurnya yang diambil |
| Layar pertama berubah dari Tanya menjadi pemeriksaan sesi | `web/src/main.tsx`; uji `halaman.test.ts`; anggaran muat 150 KB |

Sembilan tempat pada `tests/api/` dimutakhirkan menjadi `async` **tanpa
melonggarkan satu pernyataan pun** — sama dengan T-4 fitur 028.

## 3. Akun dan sesi di basis data — P-1, P-2, R-03, R-06, R-07

### 3.1 Skema `akun` pada basis data perilaku

```sql
akun.pengguna (
  id               text PRIMARY KEY,   -- nama pengguna buatan tim, mis. ks-017
  pseudonim        text NOT NULL UNIQUE,
  peran            text NOT NULL,      -- enam peran D-14 Bagian 3, CHECK
  status_aktif     boolean NOT NULL DEFAULT true,
  tanggal_dibuat   timestamptz NOT NULL,
  turunan_sandi    text NOT NULL,      -- "scrypt$n$r$p$garam$turunan", base64
  gagal_beruntun   integer NOT NULL DEFAULT 0,
  ditahan_sampai   timestamptz
)
akun.sesi (
  turunan_pengenal bytea PRIMARY KEY,  -- SHA-256 atas pengenal di kuki
  id_pengguna      text NOT NULL REFERENCES akun.pengguna(id),
  dibuat_pada      timestamptz NOT NULL,
  terakhir_aktif   timestamptz NOT NULL,
  kedaluwarsa_pada timestamptz NOT NULL,
  dicabut_pada     timestamptz
)
```

Nama `pengguna`, `id`, `peran`, `status_aktif`, `tanggal_dibuat` mengikuti
D-04 Bagian 7.1; `pseudonim` mengikuti D-14 Bagian 5.1. Bidang lainnya baru
dan ditulis ke D-14 Bagian 5.1 **sebelum** kodenya (T-1).

### 3.2 Hak peladen, bukan hak kode

| Peran | Hak | Yang ditolak peladen |
|---|---|---|
| `peran_autentikasi` (layanan aplikasi) | `SELECT` pada kedua tabel; `UPDATE (gagal_beruntun, ditahan_sampai)` pada `pengguna`; `INSERT` dan `UPDATE (terakhir_aktif, dicabut_pada)` pada `sesi` | `INSERT` akun; `UPDATE` atas `turunan_sandi`, `peran`, `status_aktif`, `pseudonim`; `DELETE`; `CONNECT` ke basis data pseudonim |
| `peran_pengelola_akun` (perkakas tim) | `INSERT` pada `pengguna`; `UPDATE (turunan_sandi, status_aktif, gagal_beruntun, ditahan_sampai)`; `UPDATE (dicabut_pada)` pada `sesi` | `DELETE`; `UPDATE` atas `peran`, `pseudonim`; `CONNECT` ke basis data pseudonim |
| `peran_penjawaban`, `peran_riwayat` | — | Seluruh skema `akun` |

Hak per kolom adalah fitur PostgreSQL sendiri. Layanan aplikasi yang
disusupi **tidak dapat** mengubah sandi maupun menaikkan peran siapa pun —
bukan karena kodenya tidak menyediakan, melainkan karena peladennya menolak.
Setiap penolakan diuji dengan sebabnya, `permission denied` (KB-098).

### 3.3 Pseudonim tidak sama dengan nama pengguna — K-1

`id` dibagikan kepada peserta dan tercetak pada daftar tim; `pseudonim`
dibangkitkan acak oleh perkakas (`psd_` + 16 heksadesimal), tidak pernah
ditampilkan kepada siapa pun, dan menjadi **pemilik** riwayat serta penanda
telemetri. Ekspor penelitian membawa pseudonim, sehingga analis yang memegang
ekspor tetapi tidak memegang basis data **tidak dapat** menautkan baris ke
daftar akun yang dibagikan.

### 3.4 Arti peta pseudonim di bawah P-1 A — K-2

D-04 Bagian 7.1 menulis `peta_pseudonim (id_pengguna, pseudonim)` di basis data
terpisah. Di bawah P-1 A, satu-satunya hal yang layak dilindungi pemisahan itu
adalah **pasangan pseudonim dengan orang sungguhan** — `akun.pengguna` sudah
menyimpan pasangan akun dengan pseudonim di basis data perilaku, dan
menyalinnya ke basis data kedua tidak melindungi apa pun.

Diusulkan: bidang `peta_pseudonim.id_pengguna` **berarti rujukan orang
sungguhan yang dipegang tim**, dan pengisiannya tetap di luar layanan aplikasi
(KA-03, NFR-08 "akses terbatas ketua peneliti"). Fitur ini **tidak mengisi**
peta itu dan tidak membuka kredensialnya; ia hanya menuliskan arti bidangnya
pada D-04 dan D-14. `id_pengguna` pada model fitur 022 diisi `pseudonim` ketika
rute `/saya/*` dibangun fitur 013 — dicatat, tidak dikerjakan di sini.

## 4. Sandi — P-3, R-03

### 4.1 Parameter, dari sumber yang dibaca

OWASP *Password Storage Cheat Sheet* (salinan `OWASP/CheatSheetSeries` cabang
`master`, dibaca 1 Oktober 2026) menulis:

> Use one of the following settings:
> - N=2^17 (128 MiB), r=8 (1024 bytes), p=1
> - N=2^16 (64 MiB), r=8 (1024 bytes), p=2
> - N=2^15 (32 MiB), r=8 (1024 bytes), p=3
> - …
>
> These configuration settings provide a similar minimal level of defense,
> with the main trade-off between parallelism and RAM usage.

**Usulan: N=2^15, r=8, p=3.** Sumbernya menyatakan ketiganya setara dalam
pertahanan; yang membedakan adalah memori **per percobaan masuk**. Pada 2^17,
sepuluh percobaan bersamaan — termasuk dari penyerang — menuntut 1,25 GiB;
pada 2^15 seperempatnya. Diukur pada mesin pengembangan: 0,30 detik per
turunan, terhadap 0,51 detik pada 2^17.

**Temuan saat mengukur:** `hashlib.scrypt` dengan OpenSSL 3.0.13 **menolak**
kedua baris itu dengan `memory limit exceeded` bila `maxmem` tidak diisi.
`maxmem` karena itu ditetapkan tegas (64 MiB), dan diuji: tanpanya akun tidak
dapat dibuat sama sekali — kegagalan yang terang, tetapi baru terlihat pada
mesin penyebaran bila tidak diuji di sini.

Garam 16 bita dari `secrets.token_bytes`. Sumber yang dibaca tidak menyebut
panjangnya, sehingga ini **penetapan tim tanpa dasar literatur** (SI-01 pilihan
kedua). RFC 7914 dan NIST SP 800-63B **tidak dapat dibaca** dari lingkungan ini
— proksi menolak kedua alamatnya — dan karena itu tidak dikutip.

Parameter disimpan **di dalam** `turunan_sandi`, bukan pada konfigurasi:
menaikkannya kelak tidak membuat sandi lama tidak dapat diperiksa.

### 4.2 Sandi awal dibangkitkan, tidak dipilih

D-14 Bagian 3 tidak memuat rute ganti sandi, sehingga **pengguna tidak pernah
memilih sandinya sendiri**; perkakas tim yang membangkitkannya (P-5, P-7).
Panjangnya mengikuti OWASP *Authentication Cheat Sheet*: tanpa autentikasi
multifaktor, *"passwords shorter than 15 characters are considered to be
weak"*.

**Usulan:** 16 karakter acak dari 31 huruf dan angka yang tidak mudah tertukar
(tanpa `0 O 1 l I`), ditampilkan berkelompok `xxxx-xxxx-xxxx-xxxx` agar dapat
diketik pada ponsel; tanda hubung diabaikan saat masuk. Sekitar 79 bit — daftar
sandi umum tidak relevan karena tidak ada manusia yang memilihnya.

Sandi masukan dibatasi 128 karakter sebelum diturunkan, menutup penolakan
layanan lewat sandi sangat panjang yang disebut sumber yang sama.

### 4.3 Pembandingan dan waktu tanggap — R-04

- Pembandingan memakai `hmac.compare_digest`.
- **Akun yang tidak ada tetap menjalankan satu turunan** terhadap turunan
  tiruan yang dibangkitkan sekali saat aplikasi mulai. Tanpanya akun yang
  tidak ada dijawab dalam milidetik dan akun yang ada dalam 0,3 detik —
  perbedaan yang terbaca tanpa alat apa pun.
- Akun yang ditahan dan akun yang nonaktif juga menjalankan satu turunan, dan
  menerima tanggapan yang sama persis.

Waktu tanggap tidak diuji dengan stopwatch — uji seperti itu rapuh dan lulus
secara kebetulan. Yang diuji **jumlah turunan yang dijalankan**: tepat satu
pada keempat keadaan (tidak ada, sandi salah, ditahan, nonaktif), lewat
penghitung yang disuntikkan.

Turunan dijalankan pada utas lewat `asyncio.to_thread`, dibatasi semafor
**dua turunan bersamaan** (penetapan tim): percobaan berlebih menunggu, bukan
menghabiskan memori peladen.

## 5. Sesi — P-2, R-05, R-06

| Hal | Usulan | Dasar |
|---|---|---|
| Pengenal | `secrets.token_urlsafe(32)` — 256 bit | OWASP *Session Management*: CSPRNG *"with a size of at least 128 bits"* |
| Yang disimpan | SHA-256 atas pengenal, bukan pengenalnya | P-2 A; pembaca basis data tidak memperoleh sesi yang dapat dipakai |
| Kuki | `__Host-sesi`; `HttpOnly; Secure; SameSite=Strict; Path=/` | Contoh sumber yang sama kata demi kata: `Set-Cookie: __Host-SessionID=<value>; Secure; HttpOnly; SameSite=Strict; Path=/` |
| Peran | Dibaca dari `akun.pengguna` **setiap permintaan**, tidak disalin ke sesi | Penonaktifan dan perubahan peran berlaku seketika (KA-01) |
| Masuk | Selalu pengenal baru; sesi lama pada kuki yang sama dicabut | Fiksasi sesi tidak mungkin: peladen tidak pernah menerima pengenal buatan klien |
| Keluar | `dicabut_pada` diisi, kuki dikosongkan | R-06 — kuki lama yang disalin sebelum keluar ditolak |

**Masa sesi — P-4.** OWASP *Session Management* menulis: *"Common idle
timeouts ranges are 2-5 minutes for high-value applications and 15-30 minutes
for low risk applications"* dan, bagi pekerja kantor sehari penuh, batas
mutlak *"between 4 and 8 hours"*.

**Usulan: tanpa aktivitas 30 menit, mutlak 8 jam.** Keduanya batas atas rentang
sumber. Alasannya dinyatakan: data perilaku berisiko rendah dibanding data
keuangan, dan kepala sekolah menulis pertanyaan panjang dengan jeda; sesi yang
berakhir tidak menghilangkan apa pun karena draf tersimpan lokal (R-09 fitur
027). `terakhir_aktif` hanya ditulis bila sudah lebih dari satu menit, agar
tiap permintaan tidak menjadi satu penulisan.

## 6. Penahanan percobaan — P-4, R-04

OWASP *Authentication Cheat Sheet* menyebut tiga hal yang perlu ditetapkan —
ambang, jendela pengamatan, lama penahanan — dan menuntut penghitungnya
*"associated with the account itself, rather than the source IP address"*.
**Sumber itu tidak memberi angka.** Angka di bawah karena itu penetapan tim
tanpa dasar literatur (SI-01 pilihan kedua), sama dengan anggaran muat fitur
027:

| Hal | Usulan |
|---|---|
| Ambang | 10 kegagalan beruntun pada akun yang sama |
| Lama penahanan | 15 menit |
| Selama ditahan | Sandi benar pun ditolak; percobaan **tidak** memperpanjang penahanan |
| Sesudah masuk berhasil | Penghitung kembali nol |

Percobaan selama penahanan tidak dihitung, agar penyerang yang mengetahui
nama pengguna tidak dapat menahan akun seseorang selamanya — bahaya penolakan
layanan yang sumber itu sebut sendiri. Penaikan penghitung dan penetapan
penahanan terjadi dalam **satu pernyataan** `UPDATE … RETURNING`, sehingga dua
percobaan bersamaan tidak dapat sama-sama membaca angka sembilan.

**Akun yang ditahan menerima tanggapan yang sama** dengan sandi salah — K-3.

## 7. Bentuk rute — R-02, C-20

Ditulis ke D-14 Bagian 4.4 **sebelum** kodenya (T-1):

| Rute | Permintaan | Berhasil | Ditolak |
|---|---|---|---|
| `POST /api/v1/auth/masuk` | `{"nama_pengguna": "…", "sandi": "…"}`, `extra="forbid"` | 204 tanpa badan, `Set-Cookie` | 400 `VALIDASI_GAGAL` bila badan cacat; 401 `TIDAK_TERAUTENTIKASI` bagi keempat keadaan Bagian 4.3 |
| `POST /api/v1/auth/keluar` | tanpa badan | 204, kuki dikosongkan | 401 bila sesi tidak sah (R-05) |

**Tanpa badan tanggapan, dengan sengaja.** Layar tidak membutuhkan apa pun dari
masuk selain berhasil atau tidak; bidang yang tidak dibutuhkan adalah bidang
yang kelak dibaca orang sebagai janji.

**Syarat `Content-Type: application/json`** pada rute yang mengubah keadaan —
masuk, keluar, tanya — K-4. OWASP menyebut `SameSite` *"defense in depth
against CSRF, not as a replacement for a CSRF token"*. Formulir lintas situs
tidak dapat mengirim `application/json` tanpa *preflight*, dan peladen ini
tidak menjawab *preflight* — sehingga syarat ini menutup celah yang ditinggal
`SameSite` tanpa token tambahan maupun rute baru.

**Status 401 pada rute lain.** `_identitas_atau_tolak` menjawab 401
`TIDAK_TERAUTENTIKASI` bila penentu identitas mengembalikan `None`, sebelum
pemeriksaan peran. 403 tetap berarti peran tidak mencukupi.

## 8. Log — R-09

- Sandi, pengenal sesi, dan turunannya **tidak pernah** masuk log.
- Masuk yang ditolak **tidak mencatat nama pengguna yang diketik**. Orang
  sering mengetik sandinya pada isian nama pengguna; mencatat isian itu
  berarti mencatat sandi.
- Penahanan akun yang **ada** dicatat dengan `id` akunnya dan `id_jejak` —
  OWASP: *"Ensure that all account lockouts are logged and reviewed"*. `id`
  bukan data pribadi di bawah P-1 A; pseudonim tidak dicatat.

## 9. Perkakas tim — P-5, P-7

`python -m perkakas.akun buat --id ks-017 --peran pengguna`
`python -m perkakas.akun atur-ulang-sandi --id ks-017`
`python -m perkakas.akun nonaktifkan --id ks-017`

- Tersambung sebagai `peran_pengelola_akun`; alamat dari `PGHOST`, `PGPORT`.
- **Tidak menerima nama orang, NIP, surel, maupun nomor apa pun.** `--id`
  dicocokkan dengan pola `^[a-z]{2,8}-[0-9]{3}$` dan pendeteksi data pribadi
  FR-B04; selain itu ditolak.
- Sandi dicetak **sekali** ke terminal dan tidak ditulis ke berkas maupun log.
- Atur ulang sandi dan nonaktifkan **mencabut seluruh sesi** akun itu.

`nonaktifkan` di luar kata-kata P-5 — K-5. Pengguna yang mencabut keikutsertaan
penelitian membutuhkannya, dan tanpa perkakas ini tim harus menyunting basis
data dengan tangan.

## 10. Layar S-01 — P-6, R-08

- **Saat dibuka**, aplikasi memanggil `GET /api/v1/percakapan` — rute yang
  sudah ada. 401 menampilkan S-01; 200 menampilkan Tanya. Tidak ada rute
  "siapa saya" yang ditambahkan (AG-02).
- S-01: isian nama pengguna (`autocomplete="username"`) dan sandi
  (`type="password"`, `autocomplete="current-password"`), tombol Masuk, dan
  kalimat tentang menghubungi tim bila lupa sandi (P-7).
- **Kode aplikasi tidak menyimpan sandi** di mana pun — tidak di
  `localStorage`, tidak di keadaan sesudah dikirim. Pengelola sandi peramban
  tetap pilihan pengguna, dan atribut `autocomplete` membantunya.
- 401 dari rute mana pun sesudah masuk mengembalikan ke S-01; draf pertanyaan
  tetap tersimpan (R-09 fitur 027). `JenisGalat` layar memperoleh nilai
  `belum_masuk`, terpisah dari `tidak_berhak` — tipe layar, bukan enum D-14.
- **Tombol Keluar** pada layar Tanya. Sesudah keluar, **draf dan percakapan
  aktif pada simpanan lokal dihapus** — K-6. Peramban sekolah dapat dipakai
  bergantian, dan draf pertanyaan orang sebelumnya bukan milik orang
  berikutnya.
- Mikrokopi baru melewati pemeriksa C-13 seperti seluruh mikrokopi fitur 027.

## 11. Keputusan rancangan Gerbang 2

| Kode | Pertanyaan | Anjuran |
|---|---|---|
| K-1 | Pseudonim terpisah dari nama pengguna? | **Ya** — Bagian 3.3 |
| K-2 | Arti `peta_pseudonim.id_pengguna` di bawah P-1 A | **Rujukan orang sungguhan yang dipegang tim**; fitur ini tidak mengisinya — Bagian 3.4 |
| K-3 | Akun ditahan dan nonaktif dijawab sama dengan sandi salah? | **Ya** — tanggapan yang berbeda membocorkan bahwa akunnya ada (R-04) |
| K-4 | Syarat `Content-Type: application/json` pada rute pengubah keadaan | **Ya** — Bagian 7 |
| K-5 | Perkakas memuat `nonaktifkan` | **Ya** — Bagian 9 |
| K-6 | Keluar menghapus draf dan percakapan aktif lokal | **Ya** — Bagian 10 |
| K-7 | Bawaan `make jalan` | **`--autentikasi sesi`**; `pengembangan` hanya bila diminta tegas, dengan peringatan yang sudah ada |
| P-4 | Angka | scrypt N=2^15 r=8 p=3; sesi 30 menit / 8 jam; penahanan 10 kali / 15 menit; dua turunan bersamaan |

## 12. Uji

### 12.1 Di dalam `make check`

- Perilaku penyimpan akun dijalankan atas `AkunMemori` **dan** `AkunPostgres`.
- Penolakan peladen Bagian 3.2, tiap baris dengan sebabnya.
- Rute lewat `TestClient`: masuk, keluar, kuki dan atributnya, 401 pada ketiga
  rute lama tanpa sesi, kuki yang dicabut, sesi kedaluwarsa menurut jam yang
  disuntikkan, penahanan, `Content-Type` selain JSON ditolak.
- Log: tidak memuat sandi, pengenal sesi, maupun nama pengguna yang diketik.
- Perkakas: `--id` berpola NIK ditolak; sandi tidak tertulis ke berkas mana pun.
- Layar: Vitest untuk S-01, peralihan 401, dan pembersihan simpanan saat keluar.

### 12.2 Di luar `make check`

Playwright global terhadap `make jalan --autentikasi sesi`: buat akun lewat
perkakas, masuk, bertanya, muat ulang, keluar, kuki lama ditolak. Kuki
`Secure` dengan awalan `__Host-` pada `http://127.0.0.1` **diverifikasi di
sini**, bukan diandaikan; bila peramban menolaknya, pekerjaan berhenti dan
ditanyakan — atribut `Secure` tidak dilepas.

### 12.3 Uji mutasi

| Kode | Mutasi | Uji yang wajib merah |
|---|---|---|
| M-1 | Akun tidak ada tidak menjalankan turunan | jumlah turunan R-04 |
| M-2 | Pemeriksaan penahanan dihapus | penahanan |
| M-3 | Pengenal sesi disimpan apa adanya | baris `sesi` tidak sama dengan nilai kuki |
| M-4 | Keluar hanya mengosongkan kuki | kuki lama ditolak sesudah keluar |
| M-5 | `HttpOnly` dilepas | atribut kuki |
| M-6 | `SameSite=Lax` | atribut kuki |
| M-7 | `GRANT UPDATE (turunan_sandi)` kepada `peran_autentikasi` | penolakan peladen |
| M-8 | `GRANT CONNECT` basis data pseudonim kepada `peran_autentikasi` | penolakan peladen |
| M-9 | Penentu sesi jatuh ke peran `pengguna` bila tanpa sesi | 401 ketiga rute |
| M-10 | Batas tanpa aktivitas dihapus | sesi kedaluwarsa |
| M-11 | Peran disalin ke sesi saat masuk | penonaktifan berlaku seketika |
| M-12 | Syarat `Content-Type` dihapus | permintaan formulir ditolak |
| M-13 | Nama pengguna yang diketik dicatat pada penolakan | log |
| M-14 | Keluar tidak membersihkan simpanan lokal | Vitest |
| M-15 | `type="password"` dilepas | Vitest |

## 13. Urutan tugas

| Tugas | Isi |
|---|---|
| T-1 | Kontrak lebih dulu: D-14 4.4 dan 5.1, D-04 7.1, D-05 S-01 |
| T-2 | Peladen: `07-akun.sql`, dua peran, penolakan hak; M-7, M-8 |
| T-3 | `src/api/sandi.py`: turunan, `maxmem`, pembandingan; uji parameter tersimpan |
| T-4 | `src/penyimpanan/akun.py`: dua pelaksana, penahanan atomik, sesi |
| T-5 | `PenentuIdentitas` async; 401; sembilan tempat uji; M-9 |
| T-6 | Rute masuk dan keluar, kuki, syarat JSON, log; M-1 s.d. M-6, M-10 s.d. M-13 |
| T-7 | Perkakas `perkakas/akun.py`; `make jalan --autentikasi` |
| T-8 | Layar S-01, Keluar, peralihan 401; M-14, M-15; anggaran muat |
| T-9 | Putaran mutasi, Playwright, penutupan: D-00 TK-70, L8, HKI, L4 |

## 14. Yang menghentikan pekerjaan

| Keadaan | Yang dilakukan |
|---|---|
| Perubahan `src/rag/` atau `src/llm/` tampak perlu | Berhenti |
| Layanan aplikasi tampak perlu menjangkau basis data pseudonim | Berhenti; C-05 |
| Paket baru tampak perlu — JWT, Argon2, pembatas laju | Berhenti; C-12 |
| Peramban menolak kuki `__Host-` `Secure` pada pengembangan | Berhenti; tanyakan. `Secure` tidak dilepas |
| Rute selain dua rute D-14 3.1 tampak perlu | Berhenti; AG-02 |
| Uji `tests/api/` hanya lulus bila pernyataannya dilonggarkan | Berhenti; tanyakan |
