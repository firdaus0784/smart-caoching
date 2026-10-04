-- Fitur 030 · Profil, prioritas manajerial, persetujuan penelitian — jalankan
-- sebagai superuser pada basis data `smart_coaching`, sesudah 01 s.d. 07.
--
-- Nama tabel dan kolom mengikuti D-14 Bagian 4.5 dan 5.1 (versi 0.11) dan
-- D-04 Bagian 7.1 (versi 0.11), yang ditulis lebih dulu pada T-1.
--
-- Yang ditegakkan PELADEN, dengan hak per kolom (plan Bagian 3.2):
--
--   C-05            Pemilik setiap baris berupa pseudonim akun — batasan pola
--                   menolak nama akun maupun nomor apa pun. `id_pengguna`
--                   profil tidak dapat diubah: profil tidak berpindah orang.
--   Tambah-saja     Riwayat prioritas tidak dapat diubah maupun dihapus (K-3):
--                   perubahan prioritas adalah data penelitian.
--   Persetujuan     Hanya `dicabut_pada` yang dapat diisi sesudah dicatat. Catatan
--                   persetujuan yang dapat disunting tidak membuktikan apa pun
--                   tentang apa yang disetujui.
--   Tanpa hapus     Tidak satu peran pun memegang DELETE atau TRUNCATE. Penarikan
--                   data (NFR-09) kelak berjalan dengan peran tersendiri.

CREATE SCHEMA IF NOT EXISTS pengguna;
REVOKE ALL ON SCHEMA pengguna FROM PUBLIC;

CREATE TABLE IF NOT EXISTS pengguna.profil_sekolah (
  id_pengguna      text        PRIMARY KEY,
  jabatan          text        NOT NULL CHECK (char_length(btrim(jabatan)) > 0),
  masa_kerja       integer     NOT NULL CHECK (masa_kerja >= 0),
  jumlah_rombel    integer     NOT NULL CHECK (jumlah_rombel > 0),
  jumlah_ptk       integer     NOT NULL CHECK (jumlah_ptk > 0),
  jalur_akreditasi text        NOT NULL CHECK (jalur_akreditasi IN ('visitasi', 'automasi')),
  wilayah          text        NOT NULL CHECK (char_length(btrim(wilayah)) > 0),
  tanggal_perbarui timestamptz
);

CREATE TABLE IF NOT EXISTS pengguna.prioritas_manajerial (
  nomor           bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_pengguna     text        NOT NULL,
  kategori        text[]      NOT NULL
                  CHECK (cardinality(kategori) BETWEEN 3 AND 5
                         AND kategori <@ ARRAY['K1','K2','K3','K4','K5','K6','K7','K8']),
  ditetapkan_pada timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS prioritas_pemilik_terbaru
  ON pengguna.prioritas_manajerial (id_pengguna, nomor DESC);

CREATE TABLE IF NOT EXISTS pengguna.persetujuan (
  nomor        bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_pengguna  text        NOT NULL,
  jenis        text        NOT NULL CHECK (jenis IN ('penelitian')),
  versi_naskah text        NOT NULL CHECK (char_length(btrim(versi_naskah)) > 0),
  disetujui    boolean     NOT NULL,
  tanggal      timestamptz NOT NULL,
  dicabut_pada timestamptz,
  CHECK (dicabut_pada IS NULL OR (disetujui AND dicabut_pada > tanggal))
);

CREATE INDEX IF NOT EXISTS persetujuan_pemilik_terbaru
  ON pengguna.persetujuan (id_pengguna, nomor DESC);

-- Pola pemilik dipasang ulang tiap kali berkas ini dijalankan — pelajaran
-- KB-158: batasan di dalam CREATE TABLE tidak sampai ke tabel yang sudah ada.
ALTER TABLE pengguna.profil_sekolah DROP CONSTRAINT IF EXISTS profil_pola_pemilik;
ALTER TABLE pengguna.profil_sekolah
  ADD CONSTRAINT profil_pola_pemilik CHECK (id_pengguna ~ '^psd_[a-z]{16}$');
ALTER TABLE pengguna.prioritas_manajerial DROP CONSTRAINT IF EXISTS prioritas_pola_pemilik;
ALTER TABLE pengguna.prioritas_manajerial
  ADD CONSTRAINT prioritas_pola_pemilik CHECK (id_pengguna ~ '^psd_[a-z]{16}$');
ALTER TABLE pengguna.persetujuan DROP CONSTRAINT IF EXISTS persetujuan_pola_pemilik;
ALTER TABLE pengguna.persetujuan
  ADD CONSTRAINT persetujuan_pola_pemilik CHECK (id_pengguna ~ '^psd_[a-z]{16}$');

REVOKE ALL ON pengguna.profil_sekolah, pengguna.prioritas_manajerial, pengguna.persetujuan
  FROM PUBLIC;

GRANT USAGE ON SCHEMA pengguna TO peran_pengguna;
GRANT SELECT, INSERT ON pengguna.profil_sekolah TO peran_pengguna;
GRANT UPDATE (jabatan, masa_kerja, jumlah_rombel, jumlah_ptk, jalur_akreditasi, wilayah,
              tanggal_perbarui)
  ON pengguna.profil_sekolah TO peran_pengguna;
GRANT SELECT, INSERT ON pengguna.prioritas_manajerial TO peran_pengguna;
GRANT SELECT, INSERT ON pengguna.persetujuan TO peran_pengguna;
GRANT UPDATE (dicabut_pada) ON pengguna.persetujuan TO peran_pengguna;
