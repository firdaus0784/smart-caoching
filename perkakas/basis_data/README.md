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
psql -U <superuser> -d smart_coaching           -v ON_ERROR_STOP=1 -f 09-kurasi.sql
psql -U <superuser> -d smart_coaching           -v ON_ERROR_STOP=1 -f 10-telemetri.sql
psql -U <superuser> -d smart_coaching           -v ON_ERROR_STOP=1 -f 11-penarikan.sql
psql -U <superuser> -d smart_coaching_pseudonim -v ON_ERROR_STOP=1 -f 11b-penarikan-pseudonim.sql
psql -U <superuser> -d smart_coaching           -v ON_ERROR_STOP=1 -f 12-analitik.sql
psql -U <superuser> -d smart_coaching           -v ON_ERROR_STOP=1 -f 13-penilaian.sql
psql -U <superuser> -d smart_coaching           -v ON_ERROR_STOP=1 -f 14-sumber-dan-koleksi.sql
psql -U <superuser> -d smart_coaching           -v ON_ERROR_STOP=1 -f 15-ingesti.sql
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

## Kurasi dan penemuan — tiga peran (fitur 013)

`09-kurasi.sql` memisahkan tiga pemakai skema `kurasi` dan `penemuan`:

| Peran | Boleh | Ditolak peladen |
|---|---|---|
| `peran_pengisi_antrean` (perkakas tim) | menambah kandidat; memperbarui salinan status regulasi; menarik otomatis | menayangkan; memutus; mengubah isi kandidat |
| `peran_kurasi` (rute kurator) | membaca antrean; mencatat putusan dan penarikan; menayangkan | menambah kandidat; mengubah status regulasi; menyunting butir tayang; membaca perilaku pengguna |
| `peran_penayangan` (rute pengguna) | membaca butir tayang beserta jenis, peran, dan waktu putusannya; mencatat butir hari ini dan "belum relevan" | membaca antrean, pemutus dan alasan putusan, penarikan; menulis butir tayang |

**C-06 ditegakkan peladen dua kali.** Peran yang menayangkan tidak dapat
membaca kandidat, dan butir tayang hanya dapat merujuk putusan yang
**menyetujui** butir itu sendiri — kunci asing gabungan atas `(nomor,
id_butir, menyetujui)`. Ketiga peran tidak menjangkau karantina, korpus, maupun
basis data pseudonim.

## Telemetri — tambah-saja (fitur 034)

`10-telemetri.sql` memberi `peran_telemetri` **hanya** `SELECT` dan `INSERT`
atas `telemetri.peristiwa`. Tanpa ubah dan hapus; tanpa skema lain; tanpa
`CONNECT` ke basis data pseudonim. Persetujuan (C-04) tidak ditegakkan di sini
— ia dibaca gerbang `rekam()` fitur 012 pada setiap peristiwa.

## Penarikan data — dua peran di luar aplikasi (fitur 033)

`11-penarikan.sql` membuat `akun.permintaan_penarikan`: layanan aplikasi
(`peran_autentikasi`) hanya mencatat permintaan dan membaca apakah ada yang
tertunda. `peran_penarikan` satu-satunya pemegang `DELETE` atas tabel
data pengguna — sepuluh sejak fitur 033, lima belas sejak `13-penilaian.sql` fitur 036, enam belas sejak `14-sumber-dan-koleksi.sql` fitur 032 — dan hanya membaca kolom pemiliknya, tidak isinya.
`11b-penarikan-pseudonim.sql` memberi `peran_penarikan_pseudonim` hapus atas
`peta_pseudonim` pada basis data pseudonim.

**Kedua peran dipegang perkakas tim (`python -m perkakas.penarikan`), tidak
pernah layanan aplikasi.** Tidak satu pun menjangkau basis data yang lain
(C-05). Baris permintaan tidak dapat dihapus siapa pun; sesudah dipenuhi
pseudonimnya kosong, dan batasan tabel menolak pemenuhan yang lupa
mengosongkannya.

## Analitik penelitian — baca saja (fitur 035)

`12-analitik.sql` memberi `peran_analitik` `SELECT` atas `telemetri.peristiwa`
dan `SELECT`, `INSERT` atas `telemetri.ekspor` — jejak tambah-saja setiap
ekspor. Tanpa akun, profil, riwayat, maupun basis data pseudonim: pemegang
ekspor tidak dapat menautkan pseudonim ke akun (C-05).

## Penilaian jawaban dan aduan — salinan, bukan izin baca (fitur 036)

`13-penilaian.sql` menambah `riwayat.pesan`, `riwayat.penilaian`,
`kurasi.aduan`, `kurasi.aduan_digantikan`, dan `kurasi.tindak_lanjut_aduan`,
seluruhnya tambah-saja bagi peran aplikasi. `peran_riwayat` **menambah**
tanggapan tetapi tidak dapat membacanya, sehingga rute riwayat tidak dapat
menayangkan ulang jawaban (C-07). `peran_penilaian` (baru) menyalin pertanyaan
dan tanggapan ke aduan hanya bila peserta mencentang. `peran_kurasi` membaca
salinan itu tanpa hak apa pun atas skema `riwayat` dan tanpa kolom
`nomor_penilaian` — kurator tidak dapat menautkan aduan ke peserta (R-06).

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

## Catatan korpus, pembaca sumber, dan koleksi (fitur 032)

`14-sumber-dan-koleksi.sql` menambah `korpus.metadata_dokumen` dan
`korpus.status_dokumen` — dua catatan tambah-saja yang mewujudkan bidang
`dokumen_sumber` D-14 Bagian 5.1 (TK-82, TK-81) — serta `penemuan.koleksi`.

`peran_pembaca_sumber` membaca `id` dokumen korpus tetapi **tidak** `isi`-nya,
membaca segmen `indeks_utama` tanpa kolom vektor, dan tidak memegang USAGE atas
karantina maupun `indeks_metadata`: bagian yang dirujuk dapat ditampilkan,
dokumen utuh dan segmen berlisensi tertutup tidak (P-2 A, C-02, C-03).

`peran_koleksi` memegang tabel koleksi saja. `peran_penayangan` tidak memegang
hak apa pun atasnya, sehingga pemilihan beranda tidak dapat membaca koleksi
(R-03, C-14). Hak bawaan skema korpus memberi verifikator `UPDATE` atas tabel
baru; berkas ini mencabutnya, sebab kedua catatan tambah-saja.

## Catatan gerbang ingesti dan peran dokumen (fitur 037)

`15-ingesti.sql` menambah empat catatan tambah-saja di skema `karantina` —
`penerimaan`, `temuan_pola`, `tinjauan_temuan`, `jejak_area` — tempat keadaan
gerbang ingesti diturunkan (P-1 A), dan memasangkan tiap kredensial dokumen
dengan satu peran (TK-83, P-2 A):

- `peran_ingesti` menaruh dan mengganti teks karantina **tanpa dapat
  membacanya**, dan membaca kolom `id` korpus saja agar unggahan ulang atas
  dokumen korpus ditolak di dalam pernyataan sisipnya (TK-85 A). Penggantian
  memakai `UPDATE` lalu `INSERT`, bukan `ON CONFLICT`: `excluded.isi` menuntut
  hak baca `isi`.
- `peran_verifikasi` membaca karantina dan hanya dapat **mengeluarkan** dokumen
  darinya. Hak bawaan skema karantina yang memberinya tambah dan ubah dicabut,
  juga bagi tabel karantina kelak.
- `peran_penarikan_dokumen` mengeluarkan dokumen dari korpus dan menghapus
  segmennya dari kedua indeks tanpa membaca teksnya (TK-84 A).

Pelaku pada ketiga catatan berupa kode anggota tim berpola `tm-001`, bukan nama
orang (P-6 A); ditegakkan batasan tabel.
