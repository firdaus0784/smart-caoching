-- Fitur 033 · Penarikan data, sisi basis data pseudonim — jalankan sebagai
-- superuser pada basis data `smart_coaching_pseudonim`, sesudah 03.
--
-- `peran_penarikan_pseudonim` menghapus pemetaan satu pseudonim dan hanya
-- membaca kolom pseudonimnya — bukan identitasnya. Ia tidak memegang CONNECT ke
-- basis data perilaku, sehingga tidak satu kredensial pun menjangkau kedua
-- basis data sekaligus (C-05). Perkakas memakai keduanya bergantian.

GRANT USAGE ON SCHEMA pseudonim TO peran_penarikan_pseudonim;
GRANT SELECT (pseudonim) ON pseudonim.peta_pseudonim TO peran_penarikan_pseudonim;
GRANT DELETE ON pseudonim.peta_pseudonim TO peran_penarikan_pseudonim;
