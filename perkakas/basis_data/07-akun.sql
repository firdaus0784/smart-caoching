-- Fitur 029 · Akun dan sesi — jalankan sebagai superuser pada basis data
-- `smart_coaching`, sesudah 01 s.d. 06.
--
-- Nama tabel dan kolom mengikuti D-14 Bagian 5.1 (versi 0.10) dan D-04
-- Bagian 7.1, yang ditulis lebih dulu pada T-1 — bukan sebaliknya.
--
-- Yang ditegakkan PELADEN, dengan hak per kolom (plan Bagian 3.2):
--
--   Layanan aplikasi    `peran_autentikasi` membaca akun, menaikkan penghitung
--                       kegagalan, membuat sesi, menyentuh dan mencabutnya.
--                       Ia TIDAK dapat membuat akun, mengubah sandi, peran,
--                       status, maupun pseudonim. Layanan yang disusupi tidak
--                       dapat menaikkan peran siapa pun.
--   Perkakas tim        `peran_pengelola_akun` membuat akun, mengatur ulang
--                       sandi, menonaktifkan, dan mencabut sesi. Ia tidak
--                       membaca turunan sandi, tidak membuat sesi, dan tidak
--                       dapat mengubah peran maupun pseudonim akun yang ada.
--   Tanpa hapus         Tidak satu peran pun memegang DELETE atau TRUNCATE.
--                       Sesi dicabut (R-06), akun dinonaktifkan; penarikan
--                       data (NFR-09) kelak berjalan dengan peran tersendiri.
--   C-05                Tidak satu kolom pun memuat identitas langsung; `id`
--                       berpola nama akun buatan tim, `pseudonim` berpola acak.
--
-- Pseudonim HURUF SAJA (KB-158). Semula 16 heksadesimal; T-5 menemukan sekitar
-- satu dari dua puluh pseudonim heksadesimal memuat deret sepuluh angka, yang
-- pendeteksi data pribadi FR-B04 baca sebagai nomor rekening — dan `Identitas`
-- menolaknya, sehingga pemilik akun itu tidak akan pernah dapat masuk.
--
-- Hak SELECT per kolom bagi perkakas ada karena UPDATE ... WHERE id = $1
-- menuntut hak baca atas kolom yang disebut WHERE.

CREATE SCHEMA IF NOT EXISTS akun;
REVOKE ALL ON SCHEMA akun FROM PUBLIC;

CREATE TABLE IF NOT EXISTS akun.pengguna (
  id              text        PRIMARY KEY CHECK (id ~ '^[a-z]{2,8}-[0-9]{3}$'),
  pseudonim       text        NOT NULL UNIQUE,
  peran           text        NOT NULL CHECK (peran IN ('pengguna', 'kurator', 'anotator',
                                                         'peneliti', 'verifikator', 'admin')),
  status_aktif    boolean     NOT NULL DEFAULT true,
  tanggal_dibuat  timestamptz NOT NULL,
  turunan_sandi   text        NOT NULL CHECK (turunan_sandi LIKE 'scrypt$%'),
  gagal_beruntun  integer     NOT NULL DEFAULT 0 CHECK (gagal_beruntun >= 0),
  ditahan_sampai  timestamptz
);

-- Batasan pola pseudonim ditulis terpisah dan DIPASANG ULANG tiap kali berkas
-- ini dijalankan. `CREATE TABLE IF NOT EXISTS` tidak menyentuh tabel yang sudah
-- ada, sehingga batasan yang diperbaiki di dalamnya tidak pernah sampai ke
-- basis data yang disiapkan sebelum perbaikan — ditemukan pada T-5 (KB-158).
-- `pengguna_pseudonim_check` adalah nama bawaan batasan semula yang tertulis di
-- dalam CREATE TABLE; ia dilepas agar pola lama tidak tertinggal di sampingnya.
ALTER TABLE akun.pengguna DROP CONSTRAINT IF EXISTS pengguna_pseudonim_check;
ALTER TABLE akun.pengguna DROP CONSTRAINT IF EXISTS pengguna_pola_pseudonim;
ALTER TABLE akun.pengguna
  ADD CONSTRAINT pengguna_pola_pseudonim CHECK (pseudonim ~ '^psd_[a-z]{16}$');

CREATE TABLE IF NOT EXISTS akun.sesi (
  turunan_pengenal bytea       PRIMARY KEY CHECK (octet_length(turunan_pengenal) = 32),
  id_pengguna      text        NOT NULL REFERENCES akun.pengguna (id),
  dibuat_pada      timestamptz NOT NULL,
  terakhir_aktif   timestamptz NOT NULL,
  kedaluwarsa_pada timestamptz NOT NULL CHECK (kedaluwarsa_pada > dibuat_pada),
  dicabut_pada     timestamptz
);

-- Pencabutan seluruh sesi satu akun — atur ulang sandi, penonaktifan.
CREATE INDEX IF NOT EXISTS sesi_pengguna_aktif
  ON akun.sesi (id_pengguna) WHERE dicabut_pada IS NULL;

REVOKE ALL ON akun.pengguna, akun.sesi FROM PUBLIC;

GRANT USAGE ON SCHEMA akun TO peran_autentikasi, peran_pengelola_akun;

GRANT SELECT ON akun.pengguna TO peran_autentikasi;
GRANT UPDATE (gagal_beruntun, ditahan_sampai) ON akun.pengguna TO peran_autentikasi;
GRANT SELECT, INSERT ON akun.sesi TO peran_autentikasi;
GRANT UPDATE (terakhir_aktif, dicabut_pada) ON akun.sesi TO peran_autentikasi;

GRANT INSERT ON akun.pengguna TO peran_pengelola_akun;
GRANT SELECT (id, status_aktif) ON akun.pengguna TO peran_pengelola_akun;
GRANT UPDATE (turunan_sandi, status_aktif, gagal_beruntun, ditahan_sampai)
  ON akun.pengguna TO peran_pengelola_akun;
GRANT SELECT (id_pengguna, dicabut_pada) ON akun.sesi TO peran_pengelola_akun;
GRANT UPDATE (dicabut_pada) ON akun.sesi TO peran_pengelola_akun;
