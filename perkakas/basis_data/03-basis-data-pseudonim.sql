-- T-9 fitur 024 · Basis data pseudonim — jalankan sebagai superuser pada
-- basis data `smart_coaching_pseudonim`.
--
-- C-05: kunci pemetaan pseudonim tidak berada pada basis data yang sama
-- dengan data perilaku, DAN tidak terjangkau dari layanan aplikasi.
--
-- Tuntutan pertama ditegakkan berkas 01 lewat REVOKE CONNECT.
-- Tuntutan kedua ditegakkan di sini: hanya `peran_pseudonim` yang diberi apa
-- pun, dan peran itu tidak dipakai layanan aplikasi mana pun.

CREATE SCHEMA IF NOT EXISTS pseudonim;
REVOKE ALL ON SCHEMA public, pseudonim FROM PUBLIC;
GRANT USAGE ON SCHEMA pseudonim TO peran_pseudonim;

ALTER DEFAULT PRIVILEGES IN SCHEMA pseudonim
  GRANT SELECT, INSERT ON TABLES TO peran_pseudonim;

-- ─────────────────────────────────────────────────────────────────────────
-- Tabel peta pseudonim — T-5 fitur 024, `peta_pseudonim` D-04 Bagian 7.1
--
-- Ia berada di basis data ini, dan hanya di sini. Itu tuntutan pertama C-05,
-- dan yang menegakkannya bukan kode melainkan REVOKE CONNECT pada berkas 01:
-- peran jalur penjawaban tidak dapat menyambung ke basis data ini sama sekali.
--
-- Dua batasan unik, dan keduanya menegakkan hal yang sama dari dua arah:
-- satu pengguna tidak dapat punya dua pseudonim, dan satu pseudonim tidak
-- dapat berpindah pemilik. Pseudonim yang berpindah pemilik membuat data
-- perilaku lama tertaut ke orang yang keliru — kekeliruan yang tidak dapat
-- diperbaiki sesudah pemetaan lamanya hilang.
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS pseudonim.peta_pseudonim (
    id_pengguna   text PRIMARY KEY,
    pseudonim     text NOT NULL UNIQUE,
    didaftar_pada timestamptz NOT NULL DEFAULT now()  -- KM-01: UTC
);

GRANT SELECT, INSERT ON pseudonim.peta_pseudonim TO peran_pseudonim;
