# Persiapan basis data — T-9 fitur 024, T-9 fitur 019

Batas yang TK-56 kaburkan, dan yang berkas-berkas di sini tandai:

> **Menulis adaptornya adalah kode. Menyediakan peladennya adalah operasi.**

Berkas di sini milik sisi **operasi** (D-09), disimpan pada repositori agar
penyiapan berjalan sama di setiap lingkungan. Penyiapan yang hanya ada di
kepala satu orang adalah penyiapan yang berbeda di tiap mesin.

## Urutan menjalankan

```bash
psql -U <superuser> -d postgres                 -v ON_ERROR_STOP=1 -f 01-peran-dan-basis-data.sql
psql -U <superuser> -d smart_coaching           -v ON_ERROR_STOP=1 -f 01b-ekstensi-vektor.sql
psql -U <superuser> -d smart_coaching           -v ON_ERROR_STOP=1 -f 02-skema-dan-hak.sql
psql -U <superuser> -d smart_coaching_pseudonim -v ON_ERROR_STOP=1 -f 03-basis-data-pseudonim.sql
psql -U <superuser> -d smart_coaching           -v ON_ERROR_STOP=1 -f 04-tabel-dokumen.sql
psql -U <superuser> -d smart_coaching -v dimensi=<N> -v ON_ERROR_STOP=1 -f 05-kolom-vektor.sql
psql -U <superuser> -d smart_coaching           -v ON_ERROR_STOP=1 -f 06-riwayat.sql
psql -U <superuser> -d smart_coaching           -v ON_ERROR_STOP=1 -f 07-akun.sql
psql -U <superuser> -d smart_coaching           -v ON_ERROR_STOP=1 -f 08-pengguna.sql
```

`05` menuntut `-v dimensi=<N>` dan **tidak** berbawaan. Dimensi yang diam-diam
terpakai adalah dimensi yang tidak pernah dicocokkan dengan model yang
sebenarnya dipasang, dan ketidakcocokannya baru terlihat pada kueri pertama di
lingkungan sungguhan. Angkanya harus sama dengan `Penyemat.dimensi`;
`SumberVektor.susun` menolak bila berbeda.

Sandi tiap peran ditetapkan terpisah dan **tidak pernah** masuk repositori
(V-06). Setel lewat `ALTER ROLE <peran> PASSWORD ...` pada lingkungan
masing-masing.

## Riwayat percakapan — tambah-saja ditegakkan peladen (fitur 028)

`06-riwayat.sql` memberi `peran_riwayat` **hanya** `SELECT` dan `INSERT` atas
`riwayat.percakapan` dan `riwayat.giliran`. Tanpa `UPDATE`, sehingga pemilik
percakapan tidak dapat dipindahkan; tanpa `DELETE` dan `TRUNCATE`, sehingga
giliran yang tercatat tidak dapat hilang lewat aplikasi. Jalur penjawaban
tidak diberi `USAGE` atas skema `riwayat` sama sekali (C-17, R-07).

Kolom `giliran.nomor` berbentuk identitas; `INSERT` atasnya tidak menuntut hak
atas urutannya, sehingga hak itu sengaja tidak diberikan.

## Akun dan sesi — hak per kolom (fitur 029)

`07-akun.sql` memisahkan dua pemakai skema `akun` dengan **hak per kolom**:

| Peran | Boleh | Ditolak peladen |
|---|---|---|
| `peran_autentikasi` (layanan aplikasi) | membaca akun; menaikkan `gagal_beruntun` dan `ditahan_sampai`; membuat sesi; menyentuh `terakhir_aktif` dan mengisi `dicabut_pada` | membuat akun; mengubah sandi, peran, status, pseudonim; masa sesi; hapus |
| `peran_pengelola_akun` (perkakas tim) | membuat akun; mengatur ulang sandi; menonaktifkan; mencabut sesi | membaca turunan sandi; membuat sesi; mengubah peran dan pseudonim; hapus |

Layanan aplikasi yang disusupi karena itu tidak dapat menaikkan peran siapa
pun — peladennya yang menolak, bukan kode. Kedua peran tidak memegang
`CONNECT` ke basis data pseudonim (C-05).

## Profil, prioritas, persetujuan (fitur 030)

`08-pengguna.sql` memberi `peran_pengguna` hak baca dan tambah atas ketiga
tabel skema `pengguna`, ditambah hak ubah **per kolom**: tujuh kolom profil
selain `id_pengguna`, dan `dicabut_pada` saja pada persetujuan. Riwayat
prioritas tambah-saja. Pemilik tiap baris wajib berpola pseudonim akun.

## Ekstensi pgvector — batas kode dan operasi

> **Menulis kueri vektornya adalah kode. Memasang ekstensinya adalah operasi.**

`src/rag/pengambilan/vektor.py` menulis `<=>`, `vector(N)`, dan pengurutan
menurut jaraknya. Tidak satu baris pun di sana dapat memasang ekstensinya, dan
itu bukan kekurangan: `CREATE EXTENSION` menuntut superuser, dan layanan
penjawaban tidak boleh memilikinya (C-03, C-17).

**`CREATE EXTENSION` tidak memasang apa pun.** Ia mendaftarkan ke basis data
sesuatu yang sudah ada sebagai berkas pada mesin peladen. Bila paketnya belum
dipasang, PostgreSQL menjawab `could not open extension control file` — pesan
yang menyebut berkas, bukan menyebut paket, dan yang membacanya mencari di
tempat yang salah. `01b-ekstensi-vektor.sql` memeriksa lebih dulu dan menjawab
dengan perintah pemasangannya:

| Lingkungan | Perintah |
|---|---|
| Debian/Ubuntu | `apt-get install postgresql-16-pgvector` |
| RHEL/Rocky | `dnf install pgvector_16` |
| macOS/Homebrew | `brew install pgvector` |
| Dari sumber | `git clone https://github.com/pgvector/pgvector && make && make install` |

Versi yang disetujui tercatat pada `ketergantungan-disetujui.toml` bagian
`[sistem.pgvector]`. Menggantinya tunduk pada C-12, sama dengan ketergantungan
Python mana pun — ekstensi peladen adalah ketergantungan, meskipun ia tidak
muncul pada `uv.lock`.

## Mengapa berkas di sini tidak memakai `\quit`

`\quit` keluar dengan status **0**, dan argumen statusnya diabaikan diam-diam
(`warning: \quit: extra argument "1" ignored`). Penjagaan yang memakainya
membuat penyiapan yang gagal terbaca berhasil — bentuk kegagalan yang sama
dengan uji yang dilewati sambil dilaporkan lulus.

Jalur gagal di sini karena itu berupa `RAISE EXCEPTION` di dalam blok `DO`,
yang menghasilkan status bukan-nol. `tests/penyimpanan/test_persiapan_basis_data.py`
menyapu berkas `*.sql` di sini dan menolak `\quit` yang kembali.

Ditemukan pada T-9 fitur 019 dengan mencoba, bukan dengan membaca — dan
penjagaan dimensi pada `05` sudah bocor sejak T-4 karenanya.

## Lima peran, dan apa yang tidak dijangkaunya

| Peran | Menjangkau | **Tidak** menjangkau | Pasal |
|---|---|---|---|
| `peran_penjawaban` | korpus, kedua indeks — baca saja | karantina; basis data pseudonim; hak tulis | C-03, C-05, C-17 |
| `peran_verifikasi` | karantina dan korpus | basis data pseudonim | C-05 |
| `peran_pemanggil_llm` | korpus, `indeks_utama` saja | **`indeks_metadata`** | C-02, FR-D06 |
| `peran_pseudonim` | basis data pseudonim saja | seluruh data perilaku | C-05 |
| `peran_penyematan` | kedua tabel indeks — baca; **dua kolom** vektor — tulis | korpus; karantina; basis data pseudonim; teks segmen; tambah atau hapus segmen | C-03, C-05, TK-63 |

Kolom "tidak menjangkau" yang penting, bukan kolom sebelahnya.

**Tipe `vector` menuntut USAGE pada skema `public` (TK-64).** Ekstensi
terpasang di sana, dan `02-skema-dan-hak.sql` mencabut hak `public` dari
semua orang. Tanpa pemberian USAGE, peran penjawaban dan pemanggil model
gagal dengan `type "vector" does not exist` — dan uji yang tersambung
sebagai pengelola tidak pernah melihatnya. USAGE saja, tanpa CREATE; `public`
tidak memuat satu relasi pun, dan uji menjaga sifat itu.

## Dua baris yang paling mudah terlupa

**`REVOKE CONNECT ... FROM PUBLIC`.** PostgreSQL memberi hak `CONNECT` kepada
`PUBLIC` pada setiap basis data baru. Tanpa baris ini, membuat dua basis data
tidak memisahkan siapa pun dari siapa pun — dan daftar basis data, peran,
skema, serta hak tabel tetap terbaca benar seluruhnya. Ditemukan dengan
mencoba, bukan dengan membaca (KB-082).

**`ALTER DEFAULT PRIVILEGES`.** `GRANT ... ON ALL TABLES` hanya berlaku bagi
tabel yang ada saat perintah dijalankan. Tanpa baris ini, tabel yang dibuat
migrasi berikutnya tidak mewarisi hak apa pun, dan ketiadaannya baru terasa
jauh dari sini.

## Membuktikannya

```bash
PGHOST=... PGPORT=... PGUSER=... uv run pytest tests/penyimpanan/test_persiapan_basis_data.py
```

Sepuluh arah akses diuji: lima yang wajib **ditolak peladen**, lima yang wajib
diizinkan. Yang kedua adalah penjaga atas yang pertama — hak yang menolak
segalanya juga lulus uji penolakan.

Tanpa peladen, uji itu **gagal** — sejak keputusan tim 12 September 2026.
Sebelumnya ia dilewati dengan sebab tertulis, dan itu tidak cukup: gerbang
yang melaporkan lulus tanpa memeriksa lapisan penyimpanan sungguhan adalah
laporan palsu. Alasannya pada `tests/peladen.py`.
