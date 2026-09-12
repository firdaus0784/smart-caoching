-- T-9 fitur 024 · Skema dan hak akses — jalankan sebagai superuser pada
-- basis data `smart_coaching`.
--
-- Empat skema, dan pembagiannya bukan soal kerapian:
--   karantina        C-03 — jalur penjawaban dan pelatihan tidak menjangkaunya
--   korpus           bahan yang sudah lolos kurasi
--   indeks_utama     segmen yang boleh masuk konteks LLM
--   indeks_metadata  segmen yang TIDAK boleh masuk konteks LLM (C-02, FR-D06)
--
-- `indeks_metadata` dipisahkan dari `indeks_utama` karena C-02 menuntut
-- pemisahan pada tingkat indeks, bukan penyaringan saat kueri. Pemanggil LLM
-- karena itu tidak diberi USAGE atasnya sama sekali.

CREATE SCHEMA karantina;
CREATE SCHEMA korpus;
CREATE SCHEMA indeks_utama;
CREATE SCHEMA indeks_metadata;

REVOKE ALL ON SCHEMA public, karantina, korpus, indeks_utama, indeks_metadata
  FROM PUBLIC;

-- ── peran_penjawaban — baca korpus; kedua indeks; tanpa tulis ────────────
GRANT USAGE ON SCHEMA korpus, indeks_utama, indeks_metadata TO peran_penjawaban;

-- ── peran_verifikasi — baca karantina dan korpus; tulis korpus ───────────
GRANT USAGE ON SCHEMA karantina, korpus, indeks_utama, indeks_metadata
  TO peran_verifikasi;

-- ── peran_pemanggil_llm — korpus dan indeks_utama SAJA ──────────────────
-- Ketiadaan USAGE atas `indeks_metadata` adalah C-02 yang ditegakkan peladen.
GRANT USAGE ON SCHEMA korpus, indeks_utama TO peran_pemanggil_llm;

-- ─────────────────────────────────────────────────────────────────────────
-- HAK ATAS TABEL YANG BELUM ADA
--
-- `GRANT ... ON ALL TABLES IN SCHEMA` hanya berlaku bagi tabel yang ADA pada
-- saat perintah dijalankan. Tabel yang dibuat sesudahnya tidak mewarisi apa
-- pun, dan ketiadaannya baru terasa saat migrasi berikutnya — jauh dari sini.
--
-- ALTER DEFAULT PRIVILEGES menutup celah itu untuk tabel berikutnya.
-- ─────────────────────────────────────────────────────────────────────────

ALTER DEFAULT PRIVILEGES IN SCHEMA korpus
  GRANT SELECT ON TABLES TO peran_penjawaban, peran_pemanggil_llm;
ALTER DEFAULT PRIVILEGES IN SCHEMA indeks_utama
  GRANT SELECT ON TABLES TO peran_penjawaban, peran_pemanggil_llm;
ALTER DEFAULT PRIVILEGES IN SCHEMA indeks_metadata
  GRANT SELECT ON TABLES TO peran_penjawaban;

ALTER DEFAULT PRIVILEGES IN SCHEMA karantina
  GRANT SELECT, INSERT, UPDATE ON TABLES TO peran_verifikasi;
ALTER DEFAULT PRIVILEGES IN SCHEMA korpus
  GRANT SELECT, INSERT, UPDATE ON TABLES TO peran_verifikasi;
ALTER DEFAULT PRIVILEGES IN SCHEMA indeks_utama, indeks_metadata
  GRANT SELECT, INSERT, UPDATE ON TABLES TO peran_verifikasi;
