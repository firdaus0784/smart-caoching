-- Fitur 028 · Riwayat percakapan — jalankan sebagai superuser pada basis data
-- `smart_coaching`, sesudah 01 s.d. 05.
--
-- Nama tabel dan kolom mengikuti D-14 Bagian 5.1 (versi 0.8), yang ditulis
-- lebih dulu pada T-1 — bukan sebaliknya.
--
-- Tiga sifat yang ditegakkan PELADEN, bukan hanya oleh ketiadaan metode:
--
--   Tambah-saja (R-08)  `peran_riwayat` hanya SELECT dan INSERT. Tanpa UPDATE,
--                       DELETE, TRUNCATE, TRIGGER, maupun REFERENCES. Pemilik
--                       percakapan karena itu tidak dapat dipindahkan.
--   C-17                Jalur penjawaban tidak diberi USAGE atas skema ini
--                       sama sekali: tidak menulis, dan tidak membaca — R-07
--                       menetapkan jawaban tidak dipengaruhi riwayat.
--   C-05                Pemilik berupa pseudonim. Pemetaannya tinggal pada
--                       basis data `smart_coaching_pseudonim`, yang
--                       `peran_riwayat` tidak dapat sambungi (01).
--
-- Penarikan data pengguna (NFR-09) kelak berjalan dengan peran tersendiri,
-- sebagai satu tindakan bercatat — bukan dengan melonggarkan peran ini.

CREATE SCHEMA IF NOT EXISTS riwayat;
REVOKE ALL ON SCHEMA riwayat FROM PUBLIC;

CREATE TABLE IF NOT EXISTS riwayat.percakapan (
  id_percakapan uuid        PRIMARY KEY,
  pemilik       text        NOT NULL CHECK (char_length(pemilik) > 0),
  dibuat_pada   timestamptz NOT NULL
);

-- Daftar percakapan dibaca per pemilik, terbaru lebih dulu (D-14 4.3, K-1).
CREATE INDEX IF NOT EXISTS percakapan_pemilik_dibuat
  ON riwayat.percakapan (pemilik, dibuat_pada DESC);

CREATE TABLE IF NOT EXISTS riwayat.giliran (
  nomor         bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  id_percakapan uuid        NOT NULL REFERENCES riwayat.percakapan (id_percakapan),
  pertanyaan    text        NOT NULL CHECK (char_length(pertanyaan) > 0),
  id_pesan      text        NOT NULL CHECK (char_length(id_pesan) > 0),
  waktu         timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS giliran_percakapan_nomor
  ON riwayat.giliran (id_percakapan, nomor);

REVOKE ALL ON riwayat.percakapan, riwayat.giliran FROM PUBLIC;

GRANT USAGE ON SCHEMA riwayat TO peran_riwayat;
GRANT SELECT, INSERT ON riwayat.percakapan, riwayat.giliran TO peran_riwayat;
