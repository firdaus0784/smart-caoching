-- Fitur 038 · Penulis segmen dan lisensi — jalankan sebagai superuser pada
-- basis data `smart_coaching`, sesudah 01 s.d. 15.
--
-- Bentuk D-14 Bagian 5.1 (versi 0.20); rancangan `plan.md` fitur 038 Bagian 2.
--
-- Yang ditegakkan PELADEN, bukan oleh ketiadaan metode:
--
--   P-2 A, C-03     `peran_pengindeks` satu-satunya penulis segmen: membaca
--                   teks dan metadata korpus, menambah dan menghapus segmen
--                   kedua indeks, tanpa karantina, tanpa kolom vektor, tanpa
--                   menyunting segmen yang ada — pengindeksan ulang mengganti.
--   TK-86           `peran_verifikasi`, yang membaca karantina, tidak lagi
--                   menambah maupun mengubah segmen — juga pada tabel indeks
--                   yang dibuat kelak.
--   P-3 A, KL-01    Lisensi boleh kosong (tertutup), tidak boleh hampa.

-- ── TK-86 · hak tulis indeks verifikator ─────────────────────────────
-- `02-skema-dan-hak.sql` memberinya SELECT, INSERT, UPDATE atas setiap tabel
-- baru di kedua skema indeks. SELECT dibiarkan: kredensial `VERIFIKASI`
-- membaca kedua indeks.
ALTER DEFAULT PRIVILEGES IN SCHEMA indeks_utama, indeks_metadata
  REVOKE INSERT, UPDATE ON TABLES FROM peran_verifikasi;
REVOKE INSERT, UPDATE ON indeks_utama.segmen_teks, indeks_metadata.segmen_teks
  FROM peran_verifikasi;

-- ── Lisensi dicatat saat menerima ────────────────────────────────────
ALTER TABLE karantina.penerimaan ADD COLUMN IF NOT EXISTS lisensi text NULL;
ALTER TABLE korpus.metadata_dokumen ADD COLUMN IF NOT EXISTS lisensi text NULL;

-- `coalesce`: CHECK lulus bila hasilnya NULL, dan NULL memang sah di sini.
ALTER TABLE karantina.penerimaan DROP CONSTRAINT IF EXISTS penerimaan_lisensi;
ALTER TABLE karantina.penerimaan ADD CONSTRAINT penerimaan_lisensi
  CHECK (lisensi IS NULL OR coalesce(char_length(btrim(lisensi)), 0) > 0);
ALTER TABLE korpus.metadata_dokumen DROP CONSTRAINT IF EXISTS metadata_lisensi;
ALTER TABLE korpus.metadata_dokumen ADD CONSTRAINT metadata_lisensi
  CHECK (lisensi IS NULL OR coalesce(char_length(btrim(lisensi)), 0) > 0);

-- ── peran_pengindeks ─────────────────────────────────────────────────
GRANT USAGE ON SCHEMA korpus, indeks_utama, indeks_metadata TO peran_pengindeks;
GRANT SELECT (id, isi) ON korpus.dokumen_sumber TO peran_pengindeks;
GRANT SELECT ON korpus.metadata_dokumen TO peran_pengindeks;
-- Kolom isi saja, tanpa vektor dan penanda modelnya: segmen baru menunggu
-- penyematan. `SELECT (id_segmen, id_dokumen)` karena penghapusan dan
-- `RETURNING` membaca kolom itu.
GRANT INSERT (id_segmen, id_dokumen, teks, lisensi, anonimisasi_terverifikasi, penanda_bagian),
  SELECT (id_segmen, id_dokumen), DELETE
  ON indeks_utama.segmen_teks, indeks_metadata.segmen_teks TO peran_pengindeks;
