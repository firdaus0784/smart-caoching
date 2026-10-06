-- Fitur 033 · Penarikan data — jalankan sebagai superuser pada basis data
-- `smart_coaching`, sesudah 01 s.d. 10. Pasangannya `11b-penarikan-pseudonim.sql`
-- pada basis data pseudonim.
--
-- Bentuk tabel D-14 Bagian 5.1 (versi 0.15); alur `plan.md` fitur 033 Bagian 2.
--
-- Yang ditegakkan PELADEN (plan Bagian 3 dan 4):
--
--   NFR-09, KM-02   `peran_penarikan` satu-satunya pemegang DELETE atas sepuluh
--                   tabel data pengguna, dan hanya membaca kolom pemiliknya.
--                   Peran ini dipegang perkakas tim, TIDAK dipegang layanan
--                   aplikasi; tambah-saja tetap berlaku bagi setiap peran yang
--                   dipakai aplikasi.
--   C-05            `peran_penarikan` tanpa CONNECT ke basis data pseudonim.
--   Bukti           Baris permintaan tidak dapat dihapus siapa pun; sesudah
--                   dipenuhi pseudonimnya kosong dan jumlah barisnya terisi.
--   Satu tertunda   Satu permintaan tertunda per pseudonim.

CREATE TABLE IF NOT EXISTS akun.permintaan_penarikan (
  nomor          bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  pseudonim      text        NULL,
  diminta_pada   timestamptz NOT NULL,
  dipenuhi_pada  timestamptz NULL,
  jumlah_baris   jsonb       NULL
);

-- Dipasang ulang tiap kali berkas dijalankan (KB-158): `CREATE TABLE IF NOT
-- EXISTS` tidak menyentuh tabel yang sudah ada.
ALTER TABLE akun.permintaan_penarikan
  DROP CONSTRAINT IF EXISTS permintaan_pola_pseudonim,
  DROP CONSTRAINT IF EXISTS permintaan_tertunda_berpemilik,
  DROP CONSTRAINT IF EXISTS permintaan_dipenuhi_berjumlah;
ALTER TABLE akun.permintaan_penarikan
  ADD CONSTRAINT permintaan_pola_pseudonim
    CHECK (pseudonim IS NULL OR pseudonim ~ '^psd_[a-z]{16}$'),
  ADD CONSTRAINT permintaan_tertunda_berpemilik
    CHECK ((dipenuhi_pada IS NULL) = (pseudonim IS NOT NULL)),
  ADD CONSTRAINT permintaan_dipenuhi_berjumlah
    CHECK ((dipenuhi_pada IS NULL) = (jumlah_baris IS NULL));

CREATE UNIQUE INDEX IF NOT EXISTS permintaan_tertunda_satu
  ON akun.permintaan_penarikan (pseudonim) WHERE dipenuhi_pada IS NULL;

REVOKE ALL ON akun.permintaan_penarikan FROM PUBLIC;

-- Layanan aplikasi: mencatat permintaan dan membaca apakah ada yang tertunda.
GRANT INSERT ON akun.permintaan_penarikan TO peran_autentikasi;
GRANT SELECT (pseudonim, dipenuhi_pada) ON akun.permintaan_penarikan TO peran_autentikasi;

-- Perkakas tim.
GRANT USAGE ON SCHEMA akun, pengguna, riwayat, penemuan, telemetri TO peran_penarikan;
GRANT SELECT (nomor, pseudonim, diminta_pada, dipenuhi_pada)
  ON akun.permintaan_penarikan TO peran_penarikan;
GRANT UPDATE (pseudonim, dipenuhi_pada, jumlah_baris)
  ON akun.permintaan_penarikan TO peran_penarikan;

GRANT SELECT (id, pseudonim) ON akun.pengguna TO peran_penarikan;
GRANT SELECT (id_pengguna) ON akun.sesi TO peran_penarikan;
GRANT SELECT (id_pengguna) ON pengguna.profil_sekolah, pengguna.prioritas_manajerial,
  pengguna.persetujuan TO peran_penarikan;
GRANT SELECT (id_percakapan, pemilik) ON riwayat.percakapan TO peran_penarikan;
GRANT SELECT (id_percakapan) ON riwayat.giliran TO peran_penarikan;
GRANT SELECT (id_pengguna) ON penemuan.tayang_harian, penemuan.belum_relevan TO peran_penarikan;
GRANT SELECT (pseudonim) ON telemetri.peristiwa TO peran_penarikan;

GRANT DELETE ON akun.pengguna, akun.sesi,
  pengguna.profil_sekolah, pengguna.prioritas_manajerial, pengguna.persetujuan,
  riwayat.percakapan, riwayat.giliran,
  penemuan.tayang_harian, penemuan.belum_relevan,
  telemetri.peristiwa
  TO peran_penarikan;
