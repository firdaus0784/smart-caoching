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
