# Persiapan basis data — T-9 fitur 024

Batas yang TK-56 kaburkan, dan yang berkas-berkas di sini tandai:

> **Menulis adaptornya adalah kode. Menyediakan peladennya adalah operasi.**

Berkas di sini milik sisi **operasi** (D-09), disimpan pada repositori agar
penyiapan berjalan sama di setiap lingkungan. Penyiapan yang hanya ada di
kepala satu orang adalah penyiapan yang berbeda di tiap mesin.

## Urutan menjalankan

```bash
psql -U <superuser> -d postgres                 -v ON_ERROR_STOP=1 -f 01-peran-dan-basis-data.sql
psql -U <superuser> -d smart_coaching           -v ON_ERROR_STOP=1 -f 02-skema-dan-hak.sql
psql -U <superuser> -d smart_coaching_pseudonim -v ON_ERROR_STOP=1 -f 03-basis-data-pseudonim.sql
```

Sandi tiap peran ditetapkan terpisah dan **tidak pernah** masuk repositori
(V-06). Setel lewat `ALTER ROLE <peran> PASSWORD ...` pada lingkungan
masing-masing.

## Empat peran, dan apa yang tidak dijangkaunya

| Peran | Menjangkau | **Tidak** menjangkau | Pasal |
|---|---|---|---|
| `peran_penjawaban` | korpus, kedua indeks — baca saja | karantina; basis data pseudonim; hak tulis | C-03, C-05, C-17 |
| `peran_verifikasi` | karantina dan korpus | basis data pseudonim | C-05 |
| `peran_pemanggil_llm` | korpus, `indeks_utama` saja | **`indeks_metadata`** | C-02, FR-D06 |
| `peran_pseudonim` | basis data pseudonim saja | seluruh data perilaku | C-05 |

Kolom "tidak menjangkau" yang penting, bukan kolom sebelahnya.

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

Tanpa peladen, uji itu **dilewati dengan sebab tertulis**. Dilewati bukan
lulus.
